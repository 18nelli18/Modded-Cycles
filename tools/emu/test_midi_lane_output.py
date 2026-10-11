#!/usr/bin/env python3
"""Recherche voies MIDI (note 57) : routage natif, sans événement sonore.

Exécute 0x400826b0, sa sélection de port et la porte OUT/THRU stock/modifiée.
Les files de sortie DIN/USB et leurs verrous sont simulés ; aucune émission
matérielle, aucun firmware de voies MIDI n'est encore construit.
"""
import argparse,json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk
from test_midi_both import Rig,STACK,STOP,DEV
from test_sdvintage import main_os_from_syx
import build

def run(image,global_ports,thru,route,channel,on):
    r=Rig(image,thru);u=r.uc
    def bad(u,access,addr,size,value,data):
        print('mémoire',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),global_ports,thru,route,channel,on)
        return False
    u.hook_add(UC_HOOK_MEM_UNMAPPED,bad)
    packet=bytes([(0x90 if on else 0x80)|channel,60,100 if on else 0])
    ptr=0x90012000;u.mem_write(ptr,packet)
    u.mem_write(0x40fe4228,struct.pack('>I',1))
    out=[];locks=[]
    def hook(u,addr,size,data):
        sp=u.reg_read(mk.UC_M68K_REG_A7)
        if addr==0x40044e6c:result=global_ports
        elif addr in (0x40001100,0x40003396):
            n,p=struct.unpack('>II',u.mem_read(sp+4,8))
            out.append(('DIN' if addr==0x40001100 else 'USB',bytes(u.mem_read(p,n))))
            result=0
        elif addr in (0x400032ca,0x400032da):
            locks.append(addr);result=0
        else:
            raise AssertionError('aucun chemin de voix interne ne doit être appelé')
        u.reg_write(mk.UC_M68K_REG_D0,result)
        u.reg_write(mk.UC_M68K_REG_PC,struct.unpack('>I',u.mem_read(sp,4))[0])
        u.reg_write(mk.UC_M68K_REG_A7,sp+4)
    for addr in (0x40044e6c,0x40001100,0x40003396,0x400032ca,0x400032da,
                 0x4005894a,0x400548ce,0x40058e28):
        u.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr)
    u.mem_write(STACK,struct.pack('>IIII',STOP,3,ptr,route))
    u.reg_write(mk.UC_M68K_REG_SR,0x2000);u.reg_write(mk.UC_M68K_REG_A7,STACK)
    u.emu_start(0x400826b0,STOP,count=3000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
    assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
    assert locks==([0x400032ca,0x400032da] if any(p=='USB' for p,_ in out) else [])
    assert all(p==packet for _,p in out)
    return [p for p,_ in out]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    # La porte combinée suffit à établir les limites de routage en THRU.
    both=json.loads((DEV/'50-midi-both.json').read_text())
    patched,_=build.apply_writes(stock,[both])
    cases=0
    for image,combined in ((stock,False),(patched,True)):
      for global_ports in range(4):
       for thru in (0,1):
        for route in (1,2,3,4):
         expected=({0:[],1:['DIN'],2:['USB'],3:['DIN','USB']}[global_ports]
                   if route==1 else {2:['USB'],3:['DIN'],4:['DIN','USB']}[route])
         if thru and not combined:expected=[p for p in expected if p!='DIN']
         for channel in range(16):
          for on in (False,True):
            assert run(image,global_ports,thru,route,channel,on)==expected
            cases+=1
    print(f'ok : {cases} routages natifs note-on/off, 16 canaux, port par voie ou global, OUT/THRU ; aucun chemin sonore')
    print('NOTE : files physiques simulées ; ordonnanceur, interface et sauvegarde des voies restent à implémenter')

if __name__=='__main__':main()
