"""Charge le vrai bootstrap et ses deux banques SRAM pour les preuves release."""
import pathlib,sys,struct,random,argparse
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE

def load(case):
 img,mem,ts=boot_case(case);t=next(t for t in ts if t.get('gov'));sy={k:int(v,16) for k,v in t['gov'].items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}})
 for at,size in ((0x43000000,0x800000),(0x46700000,0x500000),(0x80000000,0x200000),(0xfc070000,0x1000)):r.u.mem_map(at,size)
 for at,raw in mem:r.u.mem_write(at,raw)
 blob=next(raw for at,raw in mem if at==int(t['append']['dest'],16))
 for off,at,size in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,blob[off:off+size])
 r.count=0
 def count(u,pc,size,data):r.count+=1
 r.u.hook_add(UC_HOOK_CODE,count)
 body=bytes(r.u.mem_read(sy['voice_after'],256));i=body.index(bytes.fromhex('263c'));r.idle_threshold=int.from_bytes(body[i+2:i+6],'big')
 return r,sy
