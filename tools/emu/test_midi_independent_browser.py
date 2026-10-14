#!/usr/bin/env python3
"""Même image Python/navigateur, puis chaîne boot/cache des choix Banque.

MOVEC cache observé sans cohérence matérielle ; MIDI physique à tester.
"""
import argparse,hashlib,importlib.util,json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from chord_keys_pr87 import load_stock
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--syntakt',required=True);p.add_argument('--build-module',required=True);p.add_argument('--references',required=True);p.add_argument('--case');a=p.parse_args();spec=importlib.util.spec_from_file_location('candidate_build',a.build_module);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);stock=load_stock(a.cycles)
 for row in json.loads(pathlib.Path(a.references).read_text())['cases']:
  if a.case and a.case!=row['name']:continue
  cat=json.loads(pathlib.Path('work/midi-independent-browser-'+row['name']+'.json').read_text())['tweaks'];img,_=build.apply_writes(stock,cat);extra,_=module.build_payload(cat,stock,a.syntakt);full=bytes(img)+extra
  assert hashlib.sha256(full).hexdigest()==row['sha'],(row['name'],'hash')
  bank=next((t for t in cat if t['id']=='midi-bank-bundle'),None)
  if bank:
   r=Rig(full,{'writes':[]},{'writes':[],'symbols':bank['symbols']});u=r.u
   u.mem_map(0x43000000,0x800000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000)
   import gen_syntakt_engines as gs
   for src,end,to in gs.CY_SRAM_INIT:u.mem_write(to,full[src-build.BASE:end-build.BASE])
   u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
   ranges=[(build.BASE,full)]
   for t in cat:
    for part in t.get('append',{}).get('parts',[]):
     if 'hex' in part:ranges.append((int(part['dest'],16),bytes.fromhex(part['hex'])))
   sites=set()
   for at,code in ranges:sites.update(at+i for i in range(0,len(code)-3,2) if code[i:i+2]==b'\x4e\x7b')
   def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
   for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
   u.emu_start(0x40000530,0x4000053a,count=40000000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,(row['name'],'boot')
   raw=bytes.fromhex(bank['append']['parts'][0]['hex']);dest=int(bank['append']['dest'],16)
   assert bytes(u.mem_read(dest,len(raw)))==raw,(row['name'],'raw')
   r.call(0x4007929c);nodes=[];node=r.r32(0x401eb894);previous=0
   while node:
    assert node not in nodes and r.r32(node+16)==previous
    nodes.append(node);previous=node;node=r.r32(node+12)
   assert nodes==[0x401eb750+20*i for i in range(bank['cache_blocks'],16)]
   assert bytes(u.mem_read(dest,len(raw)))==raw,(row['name'],'cache')
  print('PASS',row['name'],'hash Python/navigateur'+(' ; boot/cache natifs' if bank else ' ; recette existante'),flush=True)
if __name__=='__main__':main()
