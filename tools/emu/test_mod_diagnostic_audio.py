"""Raccord CHORD : vrais Attack/filtre, six pistes, zero et autres machines exacts.
Argument : nom sans extension du candidat local sous output/firmware.
"""
import json,struct,subprocess
from pathlib import Path
import random
from boot_candidate import ROOT,boot
import mcengine as E
from unicorn import UC_HOOK_CODE,m68k_const as C
original=subprocess.run
def cross(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[str((ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe').resolve()),*cmd[1:]]
 return original(cmd,*args,**kw)
subprocess.run=cross
stem=__import__('sys').argv[1];im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());new=meta['dx_symbols'];profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());sy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
from chord_boot_fixture import boot_chord_waves
from boot_candidate import load
mem=[(mem[0][0],boot_chord_waves(load(ROOT/'firmware/model-cycles_OS1.13.syx'),mem[0][0],mem[0][1]))]
e=E.Engine(im,extra_code=[(0x40100000,0x100000)],payload=mem[0])
e.uc.mem_map(0x40800000,0x1800000);e.uc.mem_map(0xfc078000,0x1000)
for off,at,size in [(0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)]:e.uc.mem_write(at,mem[0][1][off:off+size])
def stub(u,pc,size,data):
 sp=u.reg_read(C.UC_M68K_REG_A7);u.reg_write(C.UC_M68K_REG_D0,0);u.reg_write(C.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(C.UC_M68K_REG_A7,sp+4)
for name in ['ck_audio_config','ck_audio_locked_controls']:e.uc.hook_add(UC_HOOK_CODE,stub,begin=sy[name],end=sy[name])


# Comparer les etats du regulateur reel, observateur DX OFF et ON.
e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
oldstate=bytes(e.uc.mem_read(0x46732000,0x1200));runs=[]
for enabled in [-1,0,1]:
 e.uc.mem_write(0x46732000,oldstate);e.uc.mem_write(0x40a7883c,struct.pack('>I',1));e.call(new['dx_set'],int(enabled==1))
 states=[]
 for index,percent in enumerate([50]*8+[110]*8+[70]*8):
  start=100000+index*90112;now=start+percent*90112//100;e.uc.mem_write(0x46732080,struct.pack('>I',start));e.uc.mem_write(0xfc07000c,struct.pack('>I',now))
  e.uc.reg_write(C.UC_M68K_REG_D1,now);e.call(0x8000e6e6 if enabled==-1 else 0x8000e6e0);states.append(bytes(e.uc.mem_read(0x46732000,0x1200)))
 runs.append(states)
 counters=[int.from_bytes(e.uc.mem_read(new[k],4),'big') for k in ['dx_peak','dx_over','dx_new']]
 assert (counters[0]>0)==bool(enabled==1),counters
 print('PASS native audio_end returns; DX',enabled,'counters',counters,flush=True)
print('DIFF',[(b,[(hex(0x46732000+i),x,y) for i,(x,y) in enumerate(zip(a,c)) if x!=y][:12]) for b,(a,c) in enumerate(zip(runs[0],runs[1])) if a!=c][:3],flush=True)
assert runs[0]==runs[1]==runs[2]
print('PASS native governor state exact across24blocks with DX OFF/ON; counter observer only',flush=True)

e.call(new['dx_set'],1);e.uc.mem_write(0x46732058,bytes([1,0,0,0,0,0]));e.call(new['dx_before'],100000)
e.uc.mem_write(0x46732058,bytes([1,1,0,1,0,0]));e.call(new['dx_after']);assert int.from_bytes(e.uc.mem_read(new['dx_new'],4),'big')==2
e.call(new['dx_set'],0);e.call(new['dx_after']);assert bytes(e.uc.mem_read(new['dx_new'],4))==bytes(4)
print('PASS N counts two new cuts only; switching OFF resets and disables counters',flush=True)
