#!/usr/bin/env python3
"""Candidat navigateur : hash Python exact et vraie chaîne boot/cache.

Les catalogues proviennent des contrôles jsdom. MOVEC cache non simulé ;
MIDI/USB physiques et cycle de vie complet restent à tester sur machine.
"""
import argparse,hashlib,importlib.util,json,pathlib,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--syntakt',required=True);p.add_argument('--build-module',required=True);p.add_argument('--case');a=p.parse_args()
 spec=importlib.util.spec_from_file_location('candidate_build',a.build_module);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 stock=main_os_from_syx(a.cycles);rows=json.loads(pathlib.Path('work/chord-independent-refs.json').read_text())['cases']
 for row in rows:
  if a.case and a.case!=row['name']:continue
  cat=json.loads(pathlib.Path('work/chord-independent-'+row['name']+'-catalog.json').read_text())['tweaks']
  img,_=build.apply_writes(stock,sorted(cat,key=lambda t:t['order']));extra,_=module.build_payload(cat,stock,a.syntakt);full=bytes(img)+extra
  assert hashlib.sha256(full).hexdigest()==row['sha'],row['name']
  bank=next((t for t in cat if t['id']=='midi-bank-bundle'),None)
  t=bank or next(t for t in cat if t['id']=='chord-keys-supermodel')
  r=Rig(full,{'writes':[]},{'writes':[],'symbols':t['symbols']});u=r.u
  u.mem_map(0x43000000,0x800000);u.mem_map(0x46700000,0x400000);u.mem_map(0x80000000,0x200000)
  u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
  def cache(u,pc,size,data):
   if bytes(u.mem_read(pc,2))==b'\x4e\x7b':u.reg_write(mk.UC_M68K_REG_PC,pc+4)
  # Instrumenter seulement MOVEC : un hook Python à chaque instruction du
  # clear de 33 Mio rendait la preuve inutilement lente, sans mieux la couvrir.
  ranges=[(build.BASE,full)]
  for recipe in cat:
   for part in recipe.get('append',{}).get('parts',[]):
    if 'hex' in part:ranges.append((int(part['dest'],16),bytes.fromhex(part['hex'])))
  sites=set()
  for at,code in ranges:
   sites.update(at+i for i in range(0,len(code)-3,2) if code[i:i+2]==b'\x4e\x7b')
  for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
  stop=r.s['ml_boot_copy']+42 if bank else r.s['chord_clear']
  u.emu_start(0x40000530,stop,count=12000000)
  assert u.reg_read(mk.UC_M68K_REG_PC)==stop,(row['name'],'timeout boot')
  raw=bytes.fromhex(t['append']['parts'][0]['hex']);dest=int(t['append']['dest'],16)
  assert bytes(u.mem_read(dest,len(raw)))==raw,(row['name'],'depack')
  if not bank:
   u.emu_start(stop,0x4000053a,count=30000000)
   assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a
   assert bytes(u.mem_read(dest,len(raw)))==raw
   r.call(0x4007929c);nodes=[];node=r.r32(0x401eb894);previous=0
   while node:
    assert node not in nodes and r.r32(node+16)==previous
    nodes.append(node);previous=node;node=r.r32(node+12)
   blocks=(r.s['chord_end']-0x401ab750+16383)//16384
   assert nodes==[0x401eb750+20*i for i in range(blocks,16)]
   assert bytes(u.mem_read(dest,len(raw)))==raw
  print('ok :',row['name'],'hash navigateur/Python, boot et RAW exacts'+(' ; clear/cache natifs' if not bank else ''),flush=True)
if __name__=='__main__':main()
