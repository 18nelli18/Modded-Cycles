#!/usr/bin/env python3
"""SCRAMBLE sans sampler : constructeur natif, combo et locks frais.

Frontières UI/observateurs simulées comme dans test_scramble_steps ; aucune
preuve matérielle ni validation des bootstraps moteurs supplémentaires.
"""
import argparse,json,pathlib
from unicorn import UC_HOOK_CODE
from chord_keys_pr87 import load_stock
from test_scramble import setup
from test_scramble_steps import check

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--candidate',required=True);a=p.parse_args()
 data=json.loads(pathlib.Path(a.candidate).read_text());core=data['core'];sc=data['scramble']
 assert core['requires']==[] and sc['requires']==['performance-core']
 assert not any(t.get('id','').startswith(('model-tg','midi-bank','scale-gen')) for t in (core,sc))
 r=setup(load_stock(a.cycles),core,sc)
 r.tg={k:int(v,16) for k,v in core['symbols'].items()}
 at=r.tg['show_popup'];r.stubs[at]=lambda args:r.popup.append(r.string(args[0]).strip()) or 0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 check(r)
 print('ok : mêmes contrôles SCRAMBLE sans sampler, Banque ni Genie')
if __name__=='__main__':main()
