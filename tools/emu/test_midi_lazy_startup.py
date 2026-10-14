#!/usr/bin/env python3
"""Premier service UI : aucune allocation/tâche Banque avant l’entrée B.

Les périphériques/cache matériels ne sont pas simulés ; notes/95.
"""
import argparse,json,pathlib
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig
from chord_keys_pr87 import load_stock
import build
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--matrix',required=True);p.add_argument('--baseline',required=True);a=p.parse_args();stock=load_stock(a.cycles)
for row in json.load(open(pathlib.Path(a.matrix)/'matrix.json')):
 if row['tg']:continue
 d=json.load(open(pathlib.Path(a.matrix)/(row['key']+'.json')));b=d['bank'];cat=[d['core']]+d['supports']+[b];image,_=build.apply_writes(stock,cat);r=Rig(bytes(image),{'writes':[]},{'writes':[],'symbols':b['symbols']});s=r.s;raw=bytes.fromhex(b['append']['parts'][0]['hex']);r.u.mem_write(int(b['append']['dest'],16),raw);calls=[]
 def refuse(u,pc,size,data):calls.append(pc);raise AssertionError('Allocation ou scheduler pendant le démarrage UI')
 for va in (0x400802e0,0x400019ec,0x40001a38):r.u.hook_add(UC_HOOK_CODE,refuse,begin=va,end=va)
 for i in range(8):r.call(s['ml_ui_drain'])
 assert r.r32(s['ml_context'])==0 and r.r32(s['ml_worker_context'])==0 and not calls,row['key']
 old=json.load(open(pathlib.Path(a.baseline)/(row['key']+'.json')))['bank'];q=Rig(bytes(image),{'writes':[]},{'writes':[],'symbols':old['symbols']});q.u.mem_write(int(old['append']['dest'],16),bytes.fromhex(old['append']['parts'][0]['hex']));oldcalls=[]
 def baseline_heap(u,pc,size,data):oldcalls.append(pc);raise RuntimeError('heap observé')
 q.u.hook_add(UC_HOOK_CODE,baseline_heap,begin=0x400802e0,end=0x400802e0)
 try:q.call(q.s['ml_ui_drain'])
 except RuntimeError:pass
 assert oldcalls==[0x400802e0],row['key']
 print('PASS',row['key'],'ancien : heap ; nouveau : zéro heap/scheduler avant B',flush=True)
