#!/usr/bin/env python3
"""Interfaces Chord réelles dans le candidat Banque, avec pads natifs.

Runtime installé aux destinations finales après proof bootstrap distincte.
Allocation et writer physiques simulés ; aucun coût matériel revendiqué.
"""
import argparse,json,pathlib,sys,importlib.util
import build
from chord_keys_pr87 import load_stock
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'chord_keys_compat'))
spec=importlib.util.spec_from_file_location('optional_chord_ui',HERE/'chord_keys_compat/chord_ui_checks.py');ck=importlib.util.module_from_spec(spec);spec.loader.exec_module(ck)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--candidate',required=True);a=p.parse_args();data=json.loads(pathlib.Path(a.candidate).read_text());bank=data['bank'];recipes=([data['engine']] if data.get('engine') else [])+[data['core']]+data.get('supports',[])+[bank]
 stock=load_stock(a.cycles);patched,_=build.apply_writes(stock,recipes);blob=bytearray(patched)
 for t in recipes:
  for part in t.get('append',{}).get('parts',[]):
   if 'hex' not in part:continue
   off=int(part['dest'],16)-build.BASE;raw=bytes.fromhex(part['hex'])
   if len(blob)<off+len(raw):blob.extend(bytes(off+len(raw)-len(blob)))
   blob[off:off+len(raw)]=raw
 chord=next(t for t in data['supports'] if t['id']=='chord-keys-supermodel');syms={k:int(v,16) for k,v in chord['symbols'].items()}
 for lane in range(6):
  r,config,selected,*_=ck._ui_rig(bytes(blob),syms);selected[0]=lane
  for key in range(1,17):
   ck._key(r,key,True);ons=[args for name,args in r.calls if name=='on'];assert len(ons)==1 and ons[0][0]==lane
   note=ons[0][1];ck._key(r,key,False);assert r.calls==[('off',(lane,note,64))]
 for secondary in [False,True]:
  for pad in range(1,7):
   r,*_=ck._ui_rig(bytes(blob),syms);ck._pad(r,pad,True,secondary=secondary);assert ('select',(pad-1,)) in r.calls
   ck._pad(r,pad,False,secondary=secondary);assert any(name=='off' for name,args in r.calls)
  r,*_=ck._ui_rig(bytes(blob),syms);ck._key(r,1,True);ck._pad(r,2,True,secondary=secondary);assert not any(name=='select' for name,args in r.calls)
  ck._key(r,1,False);ck._pad(r,2,False,secondary=secondary);assert bytes(r.uc.mem_read(syms['held_pads'],6))==bytes(6)
 print('ok : Chord+Banque, 96 touches/releases ; six pads x deux interfaces sélectionnent sans TRIG, HARMONY capturé/libéré')
if __name__=='__main__':main()
