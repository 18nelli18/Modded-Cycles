#!/usr/bin/env python3
"""Note 57 : writer fichier natif, offset/erreurs/verrou observés sans disque.

Exécute 0x4007bb0a ; backend physique et sémaphore simulés. Aucun hook livré.
"""
import argparse
from unicorn import UC_HOOK_CODE
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
        assert r.call(0x4007bb0a,1616,buffer,handle)==count&0xffffffff
        assert calls==[('lock',0x40fe6df0),('write',0x12345678,80,buffer,1616),('unlock',0x40fe6df0)],calls
        assert r.r32(handle+4)==80+max(0,count)
    for ready,mode,active in ((0,1,1),(1,0,1),(1,2,1),(1,1,0)):
        r.w32(0x40f07cf4,ready);r.w32(handle+8,mode);r.w32(handle+12,active)
        calls.clear();assert r.call(0x4007bb0a,1616,buffer,handle)==0xffffffff
        assert not calls
    print('ok : writer natif réel, taille/tampon/handle, offset après écriture complète/partielle, zéro/erreur, lock/unlock')
    print('ok : système absent, handle fermé ou non inscriptible refusés avant backend ; aucun disque écrit')
    print('Limites : chemins/création/fermeture durable et raccordement Save/Save As non prouvés')


if __name__=='__main__':main()
