#!/usr/bin/env python3
"""Note78 : vraie chaîne boot TG/moteurs/MIDI, hashes Python et navigateur.

MOVEC cache non simulé ; processeur exécuté jusqu'au dernier flush du loader.
Le MIDI RAW décompressé doit rester exact pour chaque sélection facultative.
"""
import argparse,importlib.util,json,pathlib,sys,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--syntakt',required=True);p.add_argument('--build-module',required=True);a=p.parse_args()
 spec=importlib.util.spec_from_file_location('optional_build',a.build_module);ob=importlib.util.module_from_spec(spec);spec.loader.exec_module(ob)
 stock=main_os_from_syx(a.cycles);cases=json.loads(pathlib.Path('work/optional-refs.json').read_text())['cases']
 for row in cases:
  cat=json.loads(pathlib.Path('work/optional-'+row['name']+'-catalog.json').read_text())['tweaks'];bank=next(t for t in cat if t['id']=='midi-bank-bundle')
  img,_=build.apply_writes(stock,sorted(cat,key=lambda t:t['order']));extra,_=ob.build_payload(cat,stock,a.syntakt);full=bytes(img)+extra
  import hashlib
  assert hashlib.sha256(full).hexdigest()==row['sha'],row['name']
  r=Rig(full,{'writes':[]},{'writes':[],'symbols':bank['symbols']});s=r.s;u=r.u
  u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000);u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
  events=[]
  def hook(u,pc,size,data):
   b=bytes(u.mem_read(pc,4))
   if b[:2]==b'\x4e\x7b':events.append(pc);u.reg_write(mk.UC_M68K_REG_PC,pc+4)
  u.hook_add(UC_HOOK_CODE,hook)
  def bad(u,access,address,size,value,data):
   print('unmapped',row['name'],hex(address),'pc',hex(u.reg_read(mk.UC_M68K_REG_PC)),flush=True);return False
  u.hook_add(UC_HOOK_MEM_INVALID,bad)
  end=s['ml_boot_copy']+42
  u.emu_start(0x40000530,end,count=12000000)
  assert u.reg_read(mk.UC_M68K_REG_PC)==end,(row['name'],hex(u.reg_read(mk.UC_M68K_REG_PC)))
  raw=bytes.fromhex(bank['append']['parts'][0]['hex']);dest=int(bank['append']['dest'],16)
  assert bytes(u.mem_read(dest,len(raw)))==raw,row['name']
  assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-4
  print('ok :',row['name'],'hash Python exact, vraie chaîne boot, RAW MIDI',len(raw),'octets exacts ; cache hors simulation',flush=True)
if __name__=='__main__':main()
