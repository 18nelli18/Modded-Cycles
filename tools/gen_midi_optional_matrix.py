#!/usr/bin/env python3
"""Compile les 32 choix Banque/TG/Genie/LFO/SCRAMBLE/Chord, sans stockage.

Candidats locaux seulement ; aucune publication automatique.
"""
import argparse,itertools,json,pathlib
import gen_midi_optional_support as support
import gen_midi_independent_candidate as candidate
import gen_midi_optional_chord as chord
from chord_keys_pr87 import load_stock

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--model-tg',required=True);p.add_argument('--catalog',required=True);p.add_argument('--layout',required=True);p.add_argument('--prebuilt',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text());stock=load_stock(a.cycles);cat=read(a.catalog);layout=read(a.layout);prebuilt=read(a.prebuilt);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True);rows=[]
 for tg,sg,lfo,sc in itertools.product([False,True],repeat=4):
  data=support.generate(stock,a.model_tg,cat,tg,lfo,sg,sc)
  for ck in [False,True]:
   key=''.join(str(int(x)) for x in [tg,sg,lfo,sc,ck]);compiled=chord.generate(stock,data,layout,prebuilt) if ck else data
   recipe=candidate.generate(stock,compiled);text=json.dumps(recipe,indent=1,ensure_ascii=False)+'\n';path=out/(key+'.json')
   if a.check:assert path.read_text()==text
   else:path.write_text(text)
   rows.append(dict(key=key,tg=tg,genie=sg,lfo=lfo,scramble=sc,chord=ck,cache_blocks=recipe['bank']['cache_blocks'],packed_size=len(recipe['bank']['append']['compressed_hex'])//2))
   print('ok :',key,'cache',rows[-1]['cache_blocks'],'packed',rows[-1]['packed_size'],flush=True)
 text=json.dumps(rows,indent=1)+'\n'
 if a.check:assert (out/'matrix.json').read_text()==text
 else:(out/'matrix.json').write_text(text)
if __name__=='__main__':main()
