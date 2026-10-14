#!/usr/bin/env python3
"""Supports Genie/SCRAMBLE autonomes sans sampler ni Banque MIDI.

Le noyau local et ses accroches sont fusionnés ; le LFO2 reste son mod natif.
Prototypes privés : publication seulement après preuves de chaque combinaison.
"""
import argparse,copy,json,pathlib,struct
import build,gen_performance_core as pc
from chord_keys_pr87 import load_stock
from gen_scramble_independent_boot import generate as boot

def mapped(t,mapping):
 t=copy.deepcopy(t)
 for w in t['writes']:
  data=bytearray.fromhex(w['new'])
  for i in range(0,len(data)-3,2):
   old=struct.unpack_from('>I',data,i)[0]
   if old in mapping:struct.pack_into('>I',data,i,mapping[old])
  w['new']=data.hex()
 return t

def generate(stock,catalog,genie=False,scramble=False,chord=None):
 core,_,syms=pc.generate(stock,cross='m68k-elf-');legacy=pc.original_symbols()
 mapping={old:syms[name] for name,old in legacy.items()};key=syms['key_hook'];supports=[]
 original_gen=next(t for t in catalog if t['id']=='scale-gen-st-queued')
 if genie:
  sg=mapped(original_gen,mapping)
  for w in sg['writes']:
   if w['off']==0x4007240c-build.BASE:w['old']='4ef9'+struct.pack('>I',key).hex()
   if w['off'] in [x-build.BASE for x in (0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18)]:w['old']=struct.pack('>I',syms['led_hook']).hex()
  sg['requires']=[core['id']];sg['conflicts']=[];supports.append(sg);key=int(sg['symbols']['sg_key'],16)
 if scramble:
  sc=mapped(next(t for t in catalog if t['id']=='scramble-st-gen-queued'),dict(mapping,**{})|{int(original_gen['symbols']['sg_key'],16):key})
  for w in sc['writes']:
   if w['off']==0x4007240c-build.BASE:w['old']='4ef9'+struct.pack('>I',key).hex()
  sc['requires']=[supports[-1]['id'] if supports else core['id']];sc['conflicts']=[];supports.append(sc)
 build.apply_writes(stock,[core]+supports)
 merged={};symbols={}
 for t in supports:
  symbols.update(t['symbols'])
  for w in t['writes']:
   if w['off'] in merged:
    previous=merged[w['off']];assert previous['new']==w['old'];previous['new']=w['new']
   else:merged[w['off']]=copy.deepcopy(w)
 adapter={'writes':sorted(merged.values(),key=lambda w:w['off']),'symbols':symbols}
 t=boot(stock,{'core':core,'scramble':adapter},chord=chord)
 t.update(id='supermodel-support-independent',status='experimental',profile={'genie':genie,'scramble':scramble,'chord':chord is not None,'sampler':False,'midi_bank':False})
 return t

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--output',required=True);p.add_argument('--genie',action='store_true');p.add_argument('--scramble',action='store_true');p.add_argument('--chord');a=p.parse_args()
 cat=json.loads(pathlib.Path(a.catalog).read_text());chord=json.loads(pathlib.Path(a.chord).read_text()) if a.chord else None
 t=generate(load_stock(a.cycles),cat,a.genie,a.scramble,chord);pathlib.Path(a.output).write_text(json.dumps(t,indent=1)+'\n');print('Own support',t['profile'],len(bytes.fromhex(t['append']['compressed_hex'])))
