#!/usr/bin/env python3
"""Compilation exploratoire Banque sans Genie ni LFO2 audio obligatoire.

Noyau performance MIT sans sampler ; sauvegarde entièrement désactivée.
Sortie locale non flashable : hooks natifs et tests d'intégration à produire.
"""
import argparse,json,pathlib,struct,copy
import gen_performance_core as pc,gen_midi_bank_bundle as mb,sprites,build
from chord_keys_pr87 import load_stock

def generate(stock,repo,catalog,sampler=False,audio_lfo=False,genie=False,scramble=False):
 if sampler:
  if repo is None:raise ValueError("Le build du sampler sélectionné exige sa source Model-TG ; les autres fonctions sont autonomes")
  core=next(t for t in catalog if t['id']=='model-tg-st')
  syms=mb.symbols('m68k-elf-',pathlib.Path(repo)/'build/_b.elf')
  assert syms['reserved_end']==int(core['symbols']['reserved_end'],16)
  code=bytes.fromhex(core['append']['parts'][0]['hex'])
 else:core,code,syms=pc.generate(stock,repo,'m68k-elf-')
 supports=[]
 next_key=syms['key_hook']
 if genie:
  sg=copy.deepcopy(next(t for t in catalog if t['id']=='scale-gen-st-queued'))
  original=pc.original_symbols(repo)
  names=('key_hook','set_held','mod_used','mm_obj','rtg_on','sle_on','scale_state','key_state','led_hook','blk_clk')
  mapping={original[n]:syms[n] for n in names}
  for w in sg['writes']:
   body=bytearray.fromhex(w['new'])
   for i in range(0,len(body)-3,2):
    value=struct.unpack_from('>I',body,i)[0]
    if value in mapping:struct.pack_into('>I',body,i,mapping[value])
   w['new']=body.hex()
   if w['off']==0x4007240c-build.BASE:w['old']=(b'\x4e\xf9'+struct.pack('>I',syms['key_hook'])).hex()
   if w['off'] in [x-build.BASE for x in (0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18)]:w['old']=struct.pack('>I',syms['led_hook']).hex()
  sg['requires']=[core['id']];sg['conflicts']=[]
  supports.append(sg);next_key=int(sg['symbols']['sg_key'],16)
 if scramble:
  sc=copy.deepcopy(next(t for t in catalog if t['id']=='scramble-st-gen-queued'))
  original=pc.original_symbols(repo)
  names=('key_hook','set_held','mod_used','mm_obj','rtg_on','sle_on','scale_state','key_state','led_hook','blk_clk','show_popup')
  mapping={original[n]:syms[n] for n in names}
  old_sg=next(t for t in catalog if t['id']=='scale-gen-st-queued')
  mapping[int(old_sg['symbols']['sg_key'],16)]=next_key
  for w in sc['writes']:
   body=bytearray.fromhex(w['new'])
   for i in range(0,len(body)-3,2):
    value=struct.unpack_from('>I',body,i)[0]
    if value in mapping:struct.pack_into('>I',body,i,mapping[value])
   w['new']=body.hex()
   if w['off']==0x4007240c-build.BASE:w['old']=(b'\x4e\xf9'+struct.pack('>I',next_key)).hex()
  sc['requires']=[supports[-1]['id'] if supports else core['id']];sc['conflicts']=[]
  supports.append(sc);next_key=int(sc['symbols']['sc_key'],16)
 occupied=[(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for t in catalog if t['id'] not in ['midi-bank-bundle','chord-keys-supermodel','lfo-plus'] for w in t['writes']]
 occupied += [(build.BASE+w['off'],build.BASE+w['off']+len(bytes.fromhex(w['new']))) for w in core['writes']]
 free=[va for va,row in sprites.MASKS.items() if len(row)==4 and not any(va<hi and lo<va+row[0] for lo,hi in occupied)]
 loader=min(free,key=lambda va:(sprites.MASKS[va][0],va));free.remove(loader)
 start=syms['reserved_end'] if sampler else (syms['blob_start']+len(code)+15)&~15;limit=syms['blob_start']+(9 if sampler else 5)*16384
 support=next(t for t in catalog if t['id']=='lfo-secondary') if audio_lfo else None
 if support:supports.append(support)
 native_lfo=int(support['symbols']['lf2_dispatch'],16) if support else struct.unpack_from('>I',stock,0x400597c8-build.BASE)[0]
 lookup={t['id']:t for t in catalog};lookup.update({t['id']:t for t in supports})
 previous=build.load_catalog;build.load_catalog=lambda:{'model-cycles_OS1.13':({},lookup)}
 raw,stub,fragments,bsyms=mb.compile_code('m68k-elf-',syms,next_key,start,limit,0x401f8f76,loader,free,
  pattern_banks=True,stock_display=True,lfo_cc=True,storage=False,repeat=True,conditions=True,
  live_record=True,knob_cc=True,knob_locks=True,cc_slides=True,lfo_confirm=True,extended_storage=True,ram_layout=True,genie=genie,genie_chance=genie,audio_lfo_next=native_lfo,inline_merges=True)
 build.load_catalog=previous
 # ACR1 spécifique au sampler ne doit pas être installé sans Model-TG.
 offset=bsyms['ml_boot_clear']-start+8
 assert raw[offset:offset+10].hex()=='283c4c03e0004e7b4005'
 if not sampler:raw=raw[:offset]+b'\x4e\x71'*5+raw[offset+10:]
 return {'kind':'midi-optional-support-compilation','flashable':False,'sampler':sampler,'core':core,'start':hex(start),'size':len(raw),
  'loader':hex(loader),'stub':stub.hex(),'fragments':[(hex(at),body.hex()) for at,body in fragments],
  'raw':raw.hex(),'symbols':{k:hex(v) for k,v in bsyms.items()},
  'supports':supports,'audio_lfo_next':hex(native_lfo),'genie':genie,'scramble':scramble,'storage':False,
  'pending':['writer_chains','all_optional_profiles','native_boot_ui_audio_midi_proofs','hardware_test']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--model-tg',help='Clone requis seulement si le sampler Model-TG est demandé');p.add_argument('--catalog',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');p.add_argument('--sampler',action='store_true');p.add_argument('--audio-lfo',action='store_true');p.add_argument('--genie',action='store_true');p.add_argument('--scramble',action='store_true');a=p.parse_args()
 t=generate(load_stock(a.cycles),a.model_tg,json.loads(pathlib.Path(a.catalog).read_text()),a.sampler,a.audio_lfo,a.genie,a.scramble);text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : compilation optionnelle,',t['size'],'octets ; Genie',t['genie'],'; LFO2 audio',a.audio_lfo,'; sampler',a.sampler,'; aucun stockage, non flashable')
if __name__=='__main__':main()
