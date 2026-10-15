"""Vrai parseur sampler ; lectures bloc et allocation simulées aux frontières.

Aucune affirmation de persistance ou de lecture flash physique.
"""
import pathlib,subprocess,struct
from unicorn import UC_HOOK_CODE,m68k_const as m
from test_seq_gen_menu import Rig
from chord_keys_pr87 import load_stock
p=pathlib.Path('work/supermodel-sampler-prototype');s={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output(['m68k-elf-nm',str(p/'guard.elf')],text=True).splitlines() if len(r.split())==3 and r.split()[1]!='U'}
raw=(p/'guard.bin').read_bytes();stock=load_stock('firmware/model-cycles_OS1.13.syx')
for case in ['valid','clamp','rate','empty','zero_chunks','overflow','too_large','table_error','data_error','no_room']:
 r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x4a800000,0x30000);u.mem_write(0x401ab750,raw);calls=[];alloc=[]
 chunks={'zero_chunks':0,'overflow':0x40000,'too_large':1537}.get(case,1)
 table=bytearray(65536);off=3*128
 for at,val in [(0,0x20001),(4,16400),(12,0x12345678),(36,chunks),(40,7)]:struct.pack_into('>I',table,off+at,val)
 payload=bytearray(16384);struct.pack_into('>I',payload,4,0 if case=='empty' else (100000 if case=='clamp' else 2000));struct.pack_into('>I',payload,8,44100 if case=='rate' else 48000)
 def read(args):
  block,size,dest=args[:3];calls.append((block,size,dest))
  if block==1835088:
   if case=='table_error':return 1
   assert size==65536 and dest==0x4a800000;u.mem_write(dest,bytes(table));return 0
  assert (block,size,dest)==(1851472+7*32,16384,0x4a810000)
  if case=='data_error':return 1
  u.mem_write(dest,bytes(payload));return 0
 r.stubs[0x4008b24a]=read;u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4008b24a,end=0x4008b24a)
 r.stubs[s['pick_dest']]=lambda args:alloc.append(u.reg_read(m.UC_M68K_REG_D0)) or (0 if case=='no_room' else 0x4a810000)
 u.hook_add(UC_HOOK_CODE,r.stub,begin=s['pick_dest'],end=s['pick_dest'])
 r.w32(s['want_hash'],0x12345678)
 ok=r.call(s['load_at']);assert ok==int(case in ['valid','clamp']),(case,ok)
 expected_error=0 if ok else (3 if case in ['table_error','data_error'] else (5 if case=='no_room' else 4))
 assert r.r32(s['fail_why'])==expected_error,(case,r.r32(s['fail_why']))
 if ok:assert r.r32(s['out_count'])==(8160 if case=='clamp' else 1000) and r.r32(s['want_ino'])==3
 if case in ['zero_chunks','overflow','too_large','table_error']:assert alloc==[] and len(calls)==1
print('PASS 10 cas chargeur : inode, PCM borné, format/IO/allocation en échec, chunks vides et débordement refusés avant allocation.')
