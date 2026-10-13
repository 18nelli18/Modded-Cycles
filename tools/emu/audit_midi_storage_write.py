#!/usr/bin/env python3
"""Note 57 : writer fichier natif, offset/erreurs/verrou observés sans disque.

Exécute 0x4007bb0a ; backend physique et sémaphore simulés. Aucun hook livré.
"""
import argparse,struct
from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    a=ap.parse_args();r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    handle,buffer=0x93070000,0x93071000
    calls=[];result=[1616]
    def write(args):
        calls.append(('write',*args[:4]));return result[0]
    for addr,fn in ((0x4007b972,write),
                    (0x40001cc4,lambda a:calls.append(('lock',a[0])) or 0),
                    (0x40001df6,lambda a:calls.append(('unlock',a[0])) or 0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    for count in (1616,100,0,-1):
        r.w32(0x40f07cf4,1)
        for off,value in enumerate((0x12345678,80,1,1)):r.w32(handle+off*4,value)
        result[0]=count;calls.clear()
        assert r.call(0x4007bb0a,buffer,1616,handle)==count&0xffffffff
        assert calls==[('lock',0x40fe6df0),('write',0x12345678,80,1616,buffer),('unlock',0x40fe6df0)],calls
        assert r.r32(handle+4)==80+max(0,count)
    for ready,mode,active in ((0,1,1),(1,0,1),(1,2,1),(1,1,0)):
        r.w32(0x40f07cf4,ready);r.w32(handle+8,mode);r.w32(handle+12,active)
        calls.clear();assert r.call(0x4007bb0a,buffer,1616,handle)==0xffffffff
        assert not calls
    print('ok : writer natif réel, tampon/taille/handle, offset après écriture complète/partielle, zéro/erreur, lock/unlock')
    print('ok : système absent, handle fermé ou non inscriptible refusés avant backend ; aucun disque écrit')
    # Lecture native : ordre tampon/taille/handle, confirmé par les appelants OS.
    def read(args):calls.append(('read',*args[:4]));return result[0]
    r.stubs[0x4007b8b2]=read
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4007b8b2,end=0x4007b8b2)
    for count in (1616,100,0,-1):
        for off,value in enumerate((42,80,0,1)):r.w32(handle+off*4,value)
        r.w32(0x40f07cf4,1);result[0]=count;calls.clear()
        assert r.call(0x4007baaa,buffer,1616,handle)==count&0xffffffff
        assert calls==[('lock',0x40fe6df0),('read',42,80,1616,buffer),('unlock',0x40fe6df0)]
    print('ok : reader natif confirme ordre tampon/taille/handle, lectures partielles et erreurs observées')
    # close ne fait que retirer le bit de handle ouvert : pas de flush ici.
    r.w32(handle,42);r.w32(handle+12,1);r.w32(0x40fe8e10+4,1<<10)
    calls.clear();assert r.call(0x4007bc1c,handle)==0
    assert calls==[('lock',0x40fe6df0),('unlock',0x40fe6df0)]
    assert r.r32(handle+12)==0 and r.r32(0x40fe8e10+4)==0
    calls.clear();assert r.call(0x4007bc1c,handle)==0xffffffff and not calls
    print('ok : close natif retire le handle/bitmap ; aucun flush explicite, fermeture seule ne prouve pas la durabilité')
    # Le chemin Model-TG appelle aussi ce wrapper avant close.
    status=[0]
    def commit(a):calls.append(('commit',a[0]));return status[0]
    r.stubs[0x4007e13a]=commit
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4007e13a,end=0x4007e13a)
    r.w32(handle,42);r.w32(0x40f07cf4,1)
    for result in (0,1,-1):
        status[0]=result;calls.clear()
        assert r.call(0x4007e2f6,handle)==result&0xffffffff
        assert calls==[('lock',0x40fe6df0),('commit',42),('unlock',0x40fe6df0)]
    print('ok : wrapper de finalisation natif conserve retour/erreur sous verrou ; backend durable encore simulé')
    # Preuve indépendante : exécuter le vrai FileWriter OS jusqu'à son appel.
    # Aucun adaptateur propre ni ordre d'arguments simulé dans ce fragment.
    captured=[];fp=0x93078000
    r.u.reg_write(mk.UC_M68K_REG_A6,fp);r.u.reg_write(mk.UC_M68K_REG_D2,handle)
    r.u.reg_write(mk.UC_M68K_REG_A7,0x93008000)
    def native_call(u,addr,size,ctx):
        sp=u.reg_read(mk.UC_M68K_REG_A7)
        captured.append(struct.unpack('>3I',u.mem_read(sp+4,12)));u.emu_stop()
    hook=r.u.hook_add(UC_HOOK_CODE,native_call,begin=0x4007bb0a,end=0x4007bb0a)
    r.u.emu_start(0x400a2bd0,0,count=100)
    assert captured==[(fp-48,48,handle)],captured
    r.u.hook_del(hook)
    print('ok : appelant FileWriter OS indépendant confirme tampon, longueur, handle')
    print('Limites : chemins/création/fermeture durable et raccordement Save/Save As non prouvés')


if __name__=='__main__':main()
