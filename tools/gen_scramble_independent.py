#!/usr/bin/env python3
"""Prototype SCRAMBLE autonome, sans Banque ni sampler ; catalogue inchangé.

Réutilise les helpers MIT du noyau performance. Les variantes avec moteurs
exigeront un bootstrap commun avant toute publication au flasher.
"""
import argparse,copy,json,pathlib,struct
import build,gen_performance_core as pc
from gen_seq_gen import symbols
from chord_keys_pr87 import load_stock

def generate(stock,repo,catalog):
 core,_,syms=pc.generate(stock,repo,'m68k-elf-')
 original=symbols('m68k-elf-',pathlib.Path(repo)/'build/_b.elf')
 sc=copy.deepcopy(next(t for t in catalog if t['id']=='scramble-st-gen-queued'))
 sg=next(t for t in catalog if t['id']=='scale-gen-st-queued')
 names=('key_hook','set_held','mod_used','mm_obj','rtg_on','sle_on','scale_state','key_state','led_hook','blk_clk','show_popup')
 mapping={original[n]:syms[n] for n in names}
 mapping[int(sg['symbols']['sg_key'],16)]=syms['key_hook']
 for w in sc['writes']:
  body=bytearray.fromhex(w['new'])
  for off in range(0,len(body)-3,2):
   value=struct.unpack_from('>I',body,off)[0]
   if value in mapping:struct.pack_into('>I',body,off,mapping[value])
  w['new']=body.hex()
  if w['off']==0x4007240c-build.BASE:w['old']=(b'\x4e\xf9'+struct.pack('>I',syms['key_hook'])).hex()
 sc.update(id='scramble-independent-prototype',requires=[core['id']],conflicts=[],status='experimental',flashable=False)
 build.apply_writes(stock,[core,sc])
 return {'core':core,'scramble':sc,'prototype_only':True,'pending':['engine_bootstrap_combinations','native_input_proofs','hardware_test']}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('cycles','model-tg','catalog','output'):p.add_argument('--'+name,required=True)
 p.add_argument('--check',action='store_true');a=p.parse_args()
 result=generate(load_stock(a.cycles),a.model_tg,json.loads(pathlib.Path(a.catalog).read_text()))
 text=json.dumps(result,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : SCRAMBLE autonome ; aucune dépendance sampler, Banque ou Genie')
if __name__=='__main__':main()
