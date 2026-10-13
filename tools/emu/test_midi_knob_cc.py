#!/usr/bin/env python3
"""Potards CC B : voies isolées, bornes, assignation silencieuse, canaux/ports."""
import argparse,pathlib,subprocess,tempfile,struct
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp)
  subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'k.o'),str(root/'tools/machines/midi_lanes/knob_cc.s')],check=True)
  subprocess.run([cross+'ld','-Ttext=0x93050000','-e','mlkc_edit','-o',str(p/'k.elf'),str(p/'k.o')],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'k.elf'),str(p/'k.bin')],check=True)
  code=(p/'k.bin').read_bytes();syms=symbols(cross,p/'k.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 state=0x93060000
 def reset():r.u.mem_write(state,bytes((255,64))*72)
 def edit(lane,knob,delta,assign=0,channel=None,port=4):return r.call('mlkc_edit',state,lane,knob,delta&0xffffffff,assign,lane+6 if channel is None else channel,port)
 reset();assert edit(0,0,1)==0
 for lane in range(6):
  for knob in range(12):
   reset();assert edit(lane,knob,75,1)==0
   assert bytes(r.u.mem_read(state+(lane*12+knob)*2,2))==bytes((74,64))
   assert edit(lane,knob,1)==((0xb6+lane)<<24)|(74<<16)|(65<<8)|4
   assert bytes(r.u.mem_read(state,144)).count(74)==1
   assert edit(lane,knob,1000)==((0xb6+lane)<<24)|(74<<16)|(127<<8)|4
   assert edit(lane,knob,1)==0
   assert edit(lane,knob,-1000)==((0xb6+lane)<<24)|(74<<16)|4
   assert edit(lane,knob,-1)==0
   assert edit(lane,knob,-1000,1)==0 and r.u.mem_read(state+(lane*12+knob)*2,1)==b'\xff'
 reset();before=bytes(r.u.mem_read(state,144))
 for args in ((6,0,1),(0,12,1),(0,0,0)):
  assert edit(*args)==0 and bytes(r.u.mem_read(state,144))==before
 for channel,port in ((16,4),(0,1),(0,5)):
  assert edit(0,0,1,1,channel,port)==0 and bytes(r.u.mem_read(state,144))==before
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2700)
 assert edit(0,0,1,1)==0 and bytes(r.u.mem_read(state,144))==before
 print('ok : 72 assignations indépendantes, OFF/CC0..127, vélocité CC bornée, déduplication, canaux7..12, ports validés, IRQ refusée')
 print('Limite : noyau seul ; page, affichage, transport et sauvegarde non raccordés')
if __name__=='__main__':main()
