"""Potard physique Swing : TrackAccessor natif, puis temps des vrais events.
Le delta accelere est calibre en Q8 ; le setter et le lecteur sont natifs.
Argument : nom sans extension du candidat local sous output/firmware.
"""
import json,struct
from boot_candidate import ROOT,boot
import sys
sys.path.insert(0,str(ROOT/'output/firmware'))
import test_step_rec_legacy as S
from lofi_ui import UI,PAGE_VT
stem=__import__('sys').argv[1];m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text());im,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));r=S.Rig(im,mem);ui=UI(im,mem[0],end=0x40200000)
# Initialiser les vraies tables UI du singleton natif.
r.call(0x400de244,count=50000000);r.call(0x400e7dbc)
native_table=ui.call(0x4004df5c,1);r.uc.mem_write(native_table,bytes(ui.uc.mem_read(native_table,76)))
params=r.call(m['playability_symbols']['mm_params'],0);r.uc.mem_write(params+18,struct.pack('>H',17<<8));r.call(m['playability_symbols']['mm_setup'],params)
r.hooks[0x4006f96a]=lambda a:a[2]*256;r.hooks[0x4006f7c8]=lambda a:0;r.uc.mem_map(0xec090000,0x10000);r.hooks[0x40001fba]=lambda a:0; r.hooks[0x4007faf4]=lambda a:0;r.hooks[0x40076bee]=lambda a:0
vec=S.VIEW+0x900;data=vec+0x100;r.uc.mem_write(data,struct.pack('>6I',1,2,3,4,5,6));r.uc.mem_write(vec,struct.pack('>3I',data,data+24,data+24));r.call(0x4001ecd6,S.VIEW,vec);r.w32(S.VIEW+44,S.VC)
r.uc.mem_write(r.ui+357,b'\x00');r.w32(r.ui+348,0);r.w32(r.ui+352,0)
head=S.VC+20;node=S.VIEW+0x800;r.w32(head,node);r.w32(head+4,node);r.w32(node,head);r.w32(node+4,head);r.w32(node+8,S.VIEW)

from unicorn import m68k_const as C
r.uc.reg_write(C.UC_M68K_REG_SR,0x2000)
for fn in [0x4001e93e,0x4001e9e2,0x4000b274,0x40016378,0x4006be48]:r.watch[fn]=lambda a:None
print('SOUND ACC',hex(r.acc(0)),hex(r.u32(r.acc(0))),flush=True)
for machine in [4,17]:
 r.uc.mem_write(params+18,struct.pack('>H',machine<<8))
 for key,k in [(12,6),(13,8)]:
  r.uc.mem_write(S.EVT,struct.pack('>6I',0x400fbebc,0,0,key,1,10000))
  raw=r.call(r.u32(r.u32(r.track(0))+40),r.track(0));before=bytes(r.uc.mem_read(params,66))
  print('MACHINE',machine,'EVENT',key,'RET',r.call(r.u32(0x401005c8+8),S.VIEW+4,S.EVT),'P6',r.s16(params+12),'P8',r.s16(params+16),'SWING',bytes(r.uc.mem_read(raw+718,2)).hex(),'POP',r.popup,flush=True)

  if key==12:assert r.uc.mem_read(raw+718,1)[0]==(4 if machine==4 else 8)
print('PASS physical encoder delegates to native TrackAccessor and keeps changed Swing',flush=True)

# Mesurer le temps des vrais evenements apres le geste physique ci-dessus.
pat=r.call(0x4000f208,r.proj);patraw=r.call(r.u32(r.u32(pat)+40),pat)
kit,evt,out=0x93060000,0x93070000,0x93071000
r.uc.mem_write(kit,bytes(7094));r.uc.mem_write(kit+66,b'\x11')
r.hooks[0x40091eb6]=lambda a:evt;r.hooks[0x40091e66]=lambda a:0;r.hooks[0x400913a8]=lambda a:1;r.hooks[0x400913f0]=lambda a:0
for step in range(4):r.call(0x40017b48,r.track(0),step,1)
r.uc.mem_write(patraw+30668,b'\x02')
times=[]
for step in range(4):
 r.w32(out,0xdeadbeef);r.call(0x400548ce,0,patraw,kit,step,0,out);times.append(r.u32(out))
assert times==[0,8*108000,0,8*108000],times
print('PASS physical Swing knob -> native sequencer timing',times,flush=True)
