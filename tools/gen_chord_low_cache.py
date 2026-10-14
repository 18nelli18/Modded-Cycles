#!/usr/bin/env python3
"""Reloge les fragments Chord en un seul bloc cache, sans installer Banque.

Le conteneur neutre ne sert qu'au linker existant : ses hooks et symboles
Banque ne sont jamais exportés. Produit le manifeste propre non flashable.
"""
import argparse,copy,json,pathlib
from chord_keys_pr87 import load_stock
from gen_chord_keys_compat import generate as place
from gen_chord_independent_payload import generate as isolate

def generate(stock,layout,template,prebuilt):
 layout=copy.deepcopy(layout);neutral=copy.deepcopy(template)
 old=min(int(r['at'],16) for r in layout if r['kind']=='bank');start=0x401ab750
 for row in layout:
  if row['kind']=='bank':row['at']=hex(int(row['at'],16)-old+start)
 neutral['append']['dest']=hex(start);neutral['append']['size']=16384
 neutral['append']['parts']=[{'dest':hex(start),'hex':bytes(16384).hex()}]
 neutral['midi_reclaim']['free_spans']=[[hex(start),hex(start+16384)]]
 chord,container=place(stock,layout,None,neutral,prebuilt)
 payload=isolate(chord,container)
 at=int(payload['parts'][0]['dest'],16)
 assert start<=at and at+payload['audit']['runtime_span']<start+16384
 payload['low_cache_layout']=layout;payload['relocation_audit']=chord['relocation_audit']
 return payload

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--layout',required=True);p.add_argument('--bank-template',required=True);p.add_argument('--prebuilt',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 read=lambda f:json.loads(pathlib.Path(f).read_text())
 t=generate(load_stock(a.cycles),read(a.layout),read(a.bank_template),read(a.prebuilt));text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==text
 else:out.write_text(text)
 print('ok : placement Chord sans TG/Banque dans un seul bloc cache ; bootstrap et preuve séparés')
if __name__=='__main__':main()
