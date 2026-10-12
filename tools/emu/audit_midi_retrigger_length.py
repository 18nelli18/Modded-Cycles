#!/usr/bin/env python3
"""Mesurer Len dans le vrai armement retrigger stock, avant portage B.

--cycles firmware/model-cycles_OS1.13.syx. Allocation, copie d'événement et
déclenchement sonore sont témoins ; le calcul temporel reste le code OS réel.
Ne valide ni la courbe de vélocité des répétitions ni le scheduler complet.
"""
import argparse,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_midi_both import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cycles',required=True);a=ap.parse_args()
 r=Rig(main_os_from_syx(a.cycles),0);u=r.uc
 u.mem_map(0x80000000,0x10000)
 event=0x93010000;copy=event+0x100;rtg=0x40a78d58
 def read32(addr):return struct.unpack('>I',u.mem_read(addr,4))[0]
 def write32(addr,value):u.mem_write(addr,struct.pack('>I',value&0xffffffff))
 calls=[]
 def witness(uc,address,size,user):
  sp=uc.reg_read(mk.UC_M68K_REG_A7)
  if address==0x40091eb6:uc.reg_write(mk.UC_M68K_REG_D0,copy)
  elif address==0x40091f20:
   dst,src=struct.unpack('>2I',uc.mem_read(sp+4,8));uc.mem_write(dst,bytes(uc.mem_read(src,80)))
  elif address==0x40058552:calls.append(True)
  else:return
  uc.reg_write(mk.UC_M68K_REG_PC,read32(sp));uc.reg_write(mk.UC_M68K_REG_A7,sp+4)
 u.hook_add(UC_HOOK_CODE,witness)
 for now,gate_end,latency in ((0,5400000,0),(1000000,6400000,800),(0xffff0000,0x005166c0,0)):
  for length in range(128):
   u.mem_write(rtg,bytes(28));u.mem_write(event,bytes(80))
   write32(event+40,0x8000);write32(event+56,16);write32(event+60,length)
   write32(0x8000184c,now);write32(0x40149310,latency)
   u.reg_write(mk.UC_M68K_REG_A7,STACK)
   u.mem_write(STACK,struct.pack('>4I',STOP,event,gate_end,0))
   u.emu_start(0x400585a8,STOP,count=20000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
   assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
   if length==127:expected=0xffffffff
   else:
    delta=(gate_end-now)&0xffffffff
    if delta&0x80000000:delta-=0x100000000
    expected=((delta>>1)+read32(0x4010d814+4*(length+1))-latency)&0xffffffff
   assert read32(rtg+4)==expected,(now,length,read32(rtg+4),expected)
   assert read32(rtg+24)==16
 assert len(calls)==384
 print('ok : armement stock, 128 valeurs Len, trois horloges/latences dont wrap, INF127 confirmé')
 print('Len fini = moitié du gate restant + table native Len - latence ; conversion B et courbe restent à raccorder')
if __name__=='__main__':main()
