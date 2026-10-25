"""Meme regulateur avant/apres optimisation DSP : charges et decisions natives."""
from pathlib import Path
import sys,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_governor_recovery import load,reset,call,GB,END,NOMINAL,AFTER,BUF,GATE
rigs=[load('staging/all-features-polivoks-cpu-trim-test-'+v) for v in ('v142','v143')]
traces=[]
for r,m in rigs:
 reset(r,m);states=[];r.w32(GB+0xf00,1000000-NOMINAL)
 for t in range(6):r.u.mem_write(GB+0x3a+2*t,struct.pack('>H',80));r.w32(GB+0x0a+4*t,8000)
 for i,pct in enumerate([50]*8+[95]*12+[70]*40+[120]*8+[65]*12):
  start=1000000+i*NOMINAL;r.w32(GB+0x80,start);r.w32(0xfc07000c,start+pct*NOMINAL//100);call(r,END);states.append(bytes(r.u.mem_read(GB,0x1200)))
 traces.append(states)
assert traces[0]==traces[1]
for lane in range(6):
 samples=[]
 for r,m in rigs:
  reset(r,m);r.u.mem_write(GB+0x58+lane,b'\x02');r.u.mem_write(GB+0x52+lane,b'\x08');r.u.mem_write(BUF,struct.pack('>32i',*([0x40000000]*32)));call(r,AFTER,lane,BUF)
  call(r,GATE,lane,1,1);r.u.mem_write(BUF,struct.pack('>32i',*([-0x40000000]*32)));call(r,AFTER,lane,BUF);samples.append(bytes(r.u.mem_read(BUF,128)))
 assert samples[0]==samples[1]
print('PASS native governor: same thresholds, load tracking, overload decisions, six-track fade/retrigger recovery, saved registers and stack')
