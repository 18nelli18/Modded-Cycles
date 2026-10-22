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
stem=__import__('sys').argv[1];im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));meta=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());new=meta['playability_symbols'];profile=json.loads((ROOT/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());sy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
from chord_boot_fixture import boot_chord_waves
from boot_candidate import load
mem=[(mem[0][0],boot_chord_waves(load(ROOT/'firmware/model-cycles_OS1.13.syx'),mem[0][0],mem[0][1]))]
e=E.Engine(im,extra_code=[(0x40100000,0x100000)],payload=mem[0])
e.uc.mem_map(0x40800000,0x1800000);e.uc.mem_map(0xfc078000,0x1000)
for off,at,size in [(0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)]:e.uc.mem_write(at,mem[0][1][off:off+size])
def stub(u,pc,size,data):
 sp=u.reg_read(C.UC_M68K_REG_A7);u.reg_write(C.UC_M68K_REG_D0,0);u.reg_write(C.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(C.UC_M68K_REG_A7,sp+4)
for name in ['ck_audio_config','ck_audio_locked_controls']:e.uc.hook_add(UC_HOOK_CODE,stub,begin=sy[name],end=sy[name])

for lane in range(6):
 e.machine_defaults(lane,'CHORD');e.uc.mem_write(E.VOICE0+lane*E.VSTRIDE+56,struct.pack('>I',1));e.uc.mem_write(0x40a78c08+lane*4,struct.pack('>I',0x20000000))
e._write_params()
for lane in range(6):
 p=E.PARAMS+14+lane*66;e.uc.mem_write(p+46,struct.pack('>3H',32<<8,32512,0));e.uc.mem_write(sy['gv_gain']+lane*4,struct.pack('>I',16777216))
e.block()
delegate=int.from_bytes(e.uc.mem_read(new['mx_attack_delegate'],4),'big')
def w(a,v):e.uc.mem_write(a,struct.pack('>I',v))
def samples():return struct.unpack('>32i',e.uc.mem_read(E.TRACK_BASE,128))
def fill(x):e.uc.mem_write(E.TRACK_BASE,struct.pack('>32i',*x))
# Le filtre ouvert reste celui de la variante, avec ses coefficients natifs.
for lane in range(6):
 w(sy['atk_gain']+4*lane,16777216);fill([0x10000000]*32);e.call(new['mx_chord_attack'],E.TRACK_BASE,lane);last=samples()[-1]
 w(sy['atk_gain']+4*lane,0);fill([0x10000000]*32);e.call(new['mx_chord_attack'],E.TRACK_BASE,lane);assert samples()[0]==last,(lane,last,samples()[0])
 fill([0x10000000]*32);e.call(new['mx_chord_attack'],E.TRACK_BASE,lane)
 # Fin du raccord : le bloc suivant est exactement la rampe native.
 gain=int.from_bytes(e.uc.mem_read(sy['atk_gain']+4*lane,4),'big');fill([0x10000000]*32);e.call(delegate,E.TRACK_BASE,lane);ref=samples()
 w(sy['atk_gain']+4*lane,gain);fill([0x10000000]*32);e.call(new['mx_chord_attack'],E.TRACK_BASE,lane);assert samples()==ref
print('PASS six CHORD lanes: exact restart continuity; 64-sample fade ends; native Attack timing retained',flush=True)
rng=random.Random(133)
for lane in range(6):
 for machine,step in [(5,0),(4,1024),(6,1024),(17,1024)]:
  w(sy['trk_mach']+4*lane,machine);w(sy['atk_step']+4*lane,step);w(sy['atk_gain']+4*lane,0)
  raw=[rng.randrange(-0x40000000,0x40000000) for i in range(32)];fill(raw);e.call(delegate,E.TRACK_BASE,lane);ref=samples()
  w(sy['atk_gain']+4*lane,0);fill(raw);e.call(new['mx_chord_attack'],E.TRACK_BASE,lane);assert samples()==ref,(lane,machine,step)
print('PASS Attack=0 and other machines: sample-exact native output across six lanes',flush=True)
# Cout d'instructions, sans le presenter comme des cycles materiels.
counts={};counter=[0]
def count(u,pc,size,data):counter[0]+=1
e.uc.hook_add(UC_HOOK_CODE,count)
w(sy['trk_mach'],5);w(sy['atk_step'],682)
for kind in ['steady','restart']:
 w(sy['atk_gain'],16777216);fill([0x10000000]*32);e.call(new['mx_chord_attack'],E.TRACK_BASE,0)
 gain=0 if kind=='restart' else 16777216
 w(sy['atk_gain'],gain);fill([0x10000000]*32);counter[0]=0;e.call(delegate,E.TRACK_BASE,0);native=counter[0]
 w(sy['atk_gain'],gain);fill([0x10000000]*32);counter[0]=0;e.call(new['mx_chord_attack'],E.TRACK_BASE,0);wrapped=counter[0]
 counts[kind]=[native,wrapped,wrapped-native]
assert counts['steady'][2]<180 and counts['restart'][2]<1400,counts
print('PASS bounded wrapper instruction overhead (native/wrapped/extra)',counts,'not hardware cycles',flush=True)
