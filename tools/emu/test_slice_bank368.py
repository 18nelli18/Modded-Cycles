"""Clavier normal reel : FUNC/slices, KbT, notes tenues et relachements natifs."""
from pathlib import Path
import argparse,json,struct,sys
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig,EVENT,OBJ,RAW
from slice_bank368 import apply
from unicorn import UC_HOOK_CODE
p=argparse.ArgumentParser(description=__doc__)
for key in ('build','capture','output'):p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);m=json.loads((a.build/'BUILD.json').read_text());n=bytearray((a.capture/'native.bin').read_bytes());rt=bytearray((a.capture/'runtime.bin').read_bytes());module=m.get('slice_bank368') or apply(m,n,rt,a.output.parent/'module')
r=Rig(bytes(n),{'writes':[]},{'writes':[],'symbols':{}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,bytes(rt))
state=dict(track=0,machine=6,func=0,track_held=0,pattern_held=0,grid=0,pattern_select=0)
on=[];off=[];VIEW=0x41006000;VECTOR=0x41007000
def install(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
for at,fn in [
 (0x4007240c,lambda args:r.r32(args[0]+12)),
 (0x400cf9a8,lambda args:0x41005000),
 (0x4006b978,lambda args:state['grid']),
 (0x4006bb18,lambda args:state['pattern_select']),
 (0x4000eb90,lambda args:0x41005000),
 (0x40012442,lambda args:state['track']),
 (0x40012412,lambda args:state['track']),
 (0x4001e318,lambda args:state['machine']),
 (0x4000f208,lambda args:0x41005000),
 (0x4000cfcc,lambda args:OBJ),
 (0x4000d0dc,lambda args:0x41005000),
 (0x4000ccc0,lambda args:0),
 (0x4018a79e,lambda args:0),
 (0x4007faf4,lambda args:{1:state['func'],2:state['track_held'],3:state['pattern_held']}.get(args[0],0)),
 (0x40019e7a,lambda args:on.append(tuple(args[1:4])) or 0),
 (0x40019c84,lambda args:off.append(tuple(args[1:3])) or 0),
 (0x40075f3c,lambda args:0),
]:install(at,fn)
rows=[];modes=m['wizard_display']['symbols']['ws_mode']
for machine,mode,physical,flags in [(6,2,1,3),(6,2,0,3),(6,2,1,1),(6,2,0,1),(6,0,1,3),(6,3,1,3),(0,2,1,3),(5,2,1,3)]:
 for transpose in (-12,0,12):
  for key in range(16):
   state.update(track=2,machine=machine,func=physical,track_held=0,pattern_held=0,grid=0,pattern_select=0)
   r.w32(modes+8,mode);u.mem_write(RAW+721,bytes([transpose&255]));u.mem_write(VIEW,bytes(512));r.w32(VIEW+148,VECTOR);r.w32(VIEW+152,VECTOR);r.w32(VIEW+156,VECTOR+320);u.mem_write(VECTOR,bytes(320));on.clear();off.clear()
   u.mem_write(EVENT,struct.pack('>6I',0,0,key,16+key,flags,127));r.call(0x4001a0d2,VIEW,EVENT)
   shift=16 if machine==6 and mode==2 and (physical or flags&2) else 0;expected=52+key+transpose+shift
   assert len(on)==1 and on[0][0:2]==(2,expected),(machine,mode,physical,flags,transpose,key,on)
   assert r.r32(VIEW+152)==VECTOR+20 and r.r32(VECTOR+4)==key and r.r32(VECTOR+8)==expected
   # Relacher FUNC d'abord et changer de piste ne modifie pas le note-off.
   state.update(func=0,track=4);r.w32(EVENT+16,16);r.call(0x4001a0d2,VIEW,EVENT)
   assert off==[(2,expected)],(key,on,off)
   assert r.r32(VECTOR+16)==0
   rows.append(dict(machine=machine,mode=mode,physical_FUNC=physical,flags=flags,transpose=transpose,key=key,note=expected))
for grid,pattern in [(1,0),(0,1)]:
 state.update(grid=grid,pattern_select=pattern);on.clear();u.mem_write(EVENT,struct.pack('>6I',0,0,0,16,3,127));r.call(0x4001a0d2,VIEW,EVENT);assert not on
a.output.write_text(json.dumps(dict(module=module,cases=rows,native_note_tracking_and_release=True,grid_and_pattern_priority=True,added_audio_hooks=0,hardware_tested=False),indent=2)+'\n')
print('PASS',len(rows),'normal keyboard attacks/releases; upper/lower slices, other modes/machines, KbT and selection changes')
