"""Texte DX : pixels exacts, frontieres32bits, couleurs, ponctuation et cout."""
from pathlib import Path
import argparse,json,random,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from cpu_text370 import apply
from unicorn import UC_HOOK_CODE
p=argparse.ArgumentParser(description=__doc__)
for key in ('build','capture','output'):p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
m=json.loads((a.build/'BUILD.json').read_text());n=(a.capture/'native.bin').read_bytes();old=(a.capture/'runtime.bin').read_bytes();new=bytearray(old);d=apply(m,bytearray(n),new,a.output.parent/'module')
rigs=[]
for raw in (old,new):
 r=Rig(n,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,0x300000);r.u.mem_write(0x46700000,bytes(raw));rigs.append(r)
s=m['cpu_monitor']['symbols'];rng=random.Random(370);text=0x93180000;count=0;cost=[0,0]
for y in (0,1,12,20,22,25,26,27,28,29,30,31,32,42,56,57):
 for color in (0,1):
  for value in ('0123456789ABCDEFGHIJKL','MNOPQRSTUVWXYZ :+>?/.'):
   initial=bytes(rng.randrange(256) for _ in range(1024));got=[]
   for i,r in enumerate(rigs):
    r.u.mem_write(s['pixels'],initial);r.u.mem_write(text,value.encode()+b'\0');c=[0];h=r.u.hook_add(UC_HOOK_CODE,lambda *unused:c.__setitem__(0,c[0]+1));r.call(s['text.constprop.0'],y,text,color);r.u.hook_del(h);cost[i]+=c[0];got.append(bytes(r.u.mem_read(s['pixels'],1024)))
   assert got[0]==got[1],(y,color,value);count+=1
assert cost[1]<cost[0],cost
a.output.write_text(json.dumps(dict(cases=count,pixels_exact=True,instructions=cost,reduction=1-cost[1]/cost[0],module=d,hardware_cycles=False),indent=2)+'\n')
print('PASS',count,'exact pixel cases; text instruction totals',cost,'reduction',round(100*(1-cost[1]/cost[0]),1),'percent')
