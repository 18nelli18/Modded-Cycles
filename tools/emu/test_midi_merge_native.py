#!/usr/bin/env python3
"""Exécute les fragments placés, le RX natif et le writer/DMA natif OS1.13.

Le UART/DMA est représenté par ses registres et anneaux ; pas de temps matériel.
"""
import argparse,json,pathlib
from unicorn import m68k_const as mk
import build
from test_sdvintage import main_os_from_syx
from test_midi_thru import Rig,RING,MSG,VAL


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2]
 t=json.loads((root/'tweaks/model-cycles_OS1.13/experimental/midi-bank/60-midi-bank-bundle.json').read_text())
 stock=main_os_from_syx(a.cycles);cat=build.load_catalog()['model-cycles_OS1.13'][1]
 chosen=sorted([cat[x] for x in t['requires']]+[t],key=lambda x:x['order'])
 image,_=build.apply_writes(stock,chosen);r=Rig(image);u=r.uc
 s={k:int(v,16) for k,v in t['symbols'].items()}
 u.mem_write(s['ML_BANK_START'],bytes.fromhex(t['append']['parts'][0]['hex']))
 ctx=0x90190000;r.w32(s['mm_context'],ctx);r.w32(s['ml_worker_context'],0)
 regs={name:0x12340000+i for i,name in enumerate(('d2','d3','d4','d5','d6','d7','a2','a3','a4','a5','a6'))}
 def call(fn,*args,ipl=0):
  u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8))
  end,start,got=r.call(fn,*args,regs=regs)
  assert end==start+(0 if fn==0x400012cc else 4) and got==regs,(hex(fn),end,start,got)
  assert u.reg_read(mk.UC_M68K_REG_SR)&0x2700==0x2000|(ipl<<8)
  return u.reg_read(mk.UC_M68K_REG_D0)
 def rx(b):
  call(0x400012cc,b,ipl=4)
  assert r.next and r.next[1]==b
 def reset(mode=2):
  r.idle_io();u.mem_write(ctx,bytes(8256));u.mem_write(VAL,bytes([mode]))
 def wire():return bytes(u.mem_read(RING,r.r32(0x4049dcb8)))
 for split in range(4):
  reset();cc=[0xb6,74,100]
  for b in cc[:split]:rx(b);call(s['mm_service'],ctx,8)
  u.mem_write(MSG,b'\x86\x3c\x00');call(0x40001584,3,MSG)
  for b in cc[split:]:rx(b);call(s['mm_service'],ctx,8)
  for b in (74,80):rx(b);call(s['mm_service'],ctx,8)
  expected=(b'\xb6\x4a\x64\x86\x3c\x00' if split==3 else b'\x86\x3c\x00\xb6\x4a\x64')+b'\xb6\x4a\x50'
  assert wire()==expected,(split,wire(),expected)
  assert not r.tx
 print('ok : RX placé + writer/DMA natifs, toutes coupures CC/note-off et running status')
 reset(0);rx(0x90);assert not r.tx and not wire() and r.r32(ctx+16)==0
 reset(1);rx(0x90);rx(60);rx(100);assert r.tx==[0x90,60,100] and not wire()
 reset(2);rx(0xf8);assert r.tx==[0xf8] and not wire()
 print('ok : OUT sans relais, THRU pur inchangé, realtime immédiat, ABI et SR préservés')
 reset();sysex=bytes([0xf0]+[2]*1022+[0xf7])
 for b in sysex:rx(b)
 assert call(s['mm_service'],ctx,8)==1 and wire()==sysex
 print('ok : SysEx1024 entier envoyé par le vrai anneau DMA4096')
 assert not r.bad,r.bad
 print('Limite : cadence réelle UART et scheduler complet à vérifier sur matériel')
if __name__=='__main__':main()
