#!/usr/bin/env python3
"""Control All relogé : cinq vraies boucles OS, touches et LEDs.

Les objets UI/projet, callbacks de paramètres et le pilote LED sont contrôlés.
Les trampolines, les branches natives et les événements propres s'exécutent.
"""
import argparse,json,pathlib,struct
from unicorn import m68k_const as mk,UC_HOOK_CODE
from test_seq_gen_menu import Rig,STACK,STOP,EVENT,OBJ,VT
from test_step_delete_reset import image
from test_sdvintage import main_os_from_syx
BOX,BVT,GETVAL,GETBOX,SETVAL,LEDS,OUT=0x93003000,0x93003100,0x9300d200,0x9300d300,0x9300d400,0x93006000,0x93006100
LOOPS=((0x4001d6f8,0x4001d754),(0x4001d5a2,0x4001d5d8),(0x4001ebd2,0x4001ebfe),(0x4001ac7a,0x4001ac8a),(0x400a2798,0x400a27e2))
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--tweak',required=True);a=p.parse_args()
 stock=main_os_from_syx(a.cycles);cat=json.loads(pathlib.Path(a.catalog).read_text())['tweaks'];t=json.loads(pathlib.Path(a.tweak).read_text())
 r=Rig(image(stock,cat),{'writes':[]},t);u=r.u;seen=[];fallback=[];led=[];active=0
 callbacks={0x400cf866:lambda a:OBJ,0x4000eb90:lambda a:OBJ,0x40012412:lambda a:active,GETVAL:lambda a:42,GETBOX:lambda a:BOX,SETVAL:lambda a:seen.append(a[3]) or 0,0x4007faf4:lambda a:0,0x4000b274:lambda a:seen.append(a[3]) or 0,0x4001abe2:lambda a:seen.append(a[1]) or 0,0x40009c1a:lambda a:seen.append(a[1]) or BOX,0x4001488a:lambda a:-1,0x40024078:lambda a:fallback.append(a[:2]) or 77,0x40023d8c:lambda a:0,0x400cfaf4:lambda a:LEDS,0x40005f86:lambda a:led.append(a[:4]) or 0,0x400760ba:lambda a:0}
 for at,fn in callbacks.items():
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 r.w32(OBJ,VT);r.w32(VT+124,GETVAL);r.w32(VT+128,GETBOX);r.w32(BOX,BVT);r.w32(BVT+32,SETVAL)
 for mask in range(64):
  u.mem_write(r.s['cac_mask'],bytes([mask]))
  for active in range(6):
   expected=[lane for lane in range(6) if not(mask&(1<<lane))]
   # cac_skip utilise D0, et non un argument de pile.
   for lane in range(6):
    u.reg_write(mk.UC_M68K_REG_D0,lane);assert r.call('cac_skip')==int(lane not in expected)
   for i,(start,end) in enumerate(LOOPS):
    seen.clear();u.mem_write(STACK,bytes(128));u.reg_write(mk.UC_M68K_REG_A7,STACK)
    for reg,val in ((mk.UC_M68K_REG_D2,0),(mk.UC_M68K_REG_D3,44),(mk.UC_M68K_REG_D4,0x93004000),(mk.UC_M68K_REG_D5,26),(mk.UC_M68K_REG_A2,OBJ),(mk.UC_M68K_REG_A3,0),(mk.UC_M68K_REG_A4,0x4007faf4)):
     u.reg_write(reg,val)
    if i==2:u.reg_write(mk.UC_M68K_REG_D2,32);u.reg_write(mk.UC_M68K_REG_A4,0x4000b274)
    if i==3:u.reg_write(mk.UC_M68K_REG_A2,0x4001abe2)
    if i==4:u.reg_write(mk.UC_M68K_REG_A4,0x40009c1a);u.reg_write(mk.UC_M68K_REG_A3,0x4001488a)
    u.emu_start(start,end,count=100000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==end,(i,mask,active,hex(u.reg_read(mk.UC_M68K_REG_PC)))
    assert u.reg_read(mk.UC_M68K_REG_A7)==STACK,(i,'pile')
    assert seen==expected,(i,mask,active,seen,expected)
    if i==4:assert u.reg_read(mk.UC_M68K_REG_D4)==0x93004048
   led.clear();r.w32(OUT,0x80000000);r.call('cac_leds',OBJ+104,0xffffffff,OUT)
   assert [(x[1],x[2]) for x in led]==[(lane+1,2 if lane in expected else 1) for lane in range(6)],(mask,active,led)
   assert r.r32(OUT)==0x8000007e
 print('ok : 64 masques × six actifs × cinq boucles natives ; LEDs exactes, pile équilibrée')
 u.mem_write(r.s['cac_mask'],b'\0');u.mem_write(r.s['cac_held'],b'\0')
 for lane in range(6):
  before=u.mem_read(r.s['cac_mask'],1)[0];assert r.call('cac_keys',OBJ,r.event(16+lane,1))==1
  assert u.mem_read(r.s['cac_mask'],1)[0]==before^(1<<lane)
  for flags in (9,33):assert r.call('cac_keys',OBJ,r.event(16+lane,flags))==1
  assert u.mem_read(r.s['cac_mask'],1)[0]==before^(1<<lane)
  assert r.call('cac_keys',OBJ,r.event(16+lane,0))==1
  assert r.call('cac_keys',OBJ,r.event(16+lane,0))==77
 for code in (2,15,22,31,32,44,45):assert r.call('cac_keys',OBJ,r.event(code,1))==77
 assert len(fallback)==13
 print('ok : press/release/repeat/long ; touches étrangères et releases antérieurs transmis ; essai matériel requis')
if __name__=='__main__':main()
