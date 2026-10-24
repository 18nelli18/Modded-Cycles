"""Navigateur WAVE : vrai key/parent natifs, seul stockage fichier simule."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from boot_candidate import boot
from lofi_ui import UI,SCRATCH
version=sys.argv[1] if len(sys.argv)>1 else 'v115'
im,mem=boot(R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+version+'.syx'));u=UI(im,mem[0],end=0x40000400+len(im))
from unicorn import UC_HOOK_CODE,m68k_const as C
PM=SCRATCH+0x1000;FSD=SCRATCH+0x2000;VT=SCRATCH+0x3000;FVT=SCRATCH+0x4000;WVT=SCRATCH+0x5000;EVENT=SCRATCH+0x6000;SOUNDS=SCRATCH+0x7000
def w(a,v):u.uc.mem_write(a,struct.pack('>I',v&0xffffffff))
for at,v in [(PM,VT),(PM+640,FSD),(PM+632,FSD),(PM+56,WVT),(FSD,FVT),(0x40a78888,SOUNDS),(0x40a700c4,0),(0x4677ab66,1),(0x4677ab6e,100)]:w(at,v)
u.uc.mem_write(SOUNDS+66,bytes([14]))
for at,fn in [(FVT+48,SCRATCH+0x8000),(FVT+44,SCRATCH+0x8010),(VT+152,SCRATCH+0x8020),(VT+160,SCRATCH+0x8030),(VT+28,SCRATCH+0x8040),(WVT+40,SCRATCH+0x8050)]:w(at,fn)
state={'closed':0,'mode':1,'refresh':0,'parent':0}
def stub(uc,pc,size,data):
 sp=uc.reg_read(C.UC_M68K_REG_A7);args=struct.unpack('>4I',bytes(uc.mem_read(sp,16)));value=0
 if pc==SCRATCH+0x8000:value=1
 elif pc==SCRATCH+0x8010:
  state['parent']+=1;current=u.u32(FSD+272);w(FSD+272,{300:200,200:100}.get(current,current))
 elif pc==SCRATCH+0x8020:value=state['mode']
 elif pc==SCRATCH+0x8030:state['refresh']+=1
 elif pc==SCRATCH+0x8050:state['closed']+=1
 elif pc==0x4007240c:value=u.u32(args[1]+12)
 uc.reg_write(C.UC_M68K_REG_D0,value);uc.reg_write(C.UC_M68K_REG_PC,args[0]);uc.reg_write(C.UC_M68K_REG_A7,sp+4)
for pc in [SCRATCH+0x8000,SCRATCH+0x8010,SCRATCH+0x8020,SCRATCH+0x8030,SCRATCH+0x8040,SCRATCH+0x8050,0x4007cce4,0x4007cc64,0x4007240c]:u.uc.hook_add(UC_HOOK_CODE,stub,begin=pc,end=pc)
def key(flags):
 u.uc.mem_write(EVENT,struct.pack('>6I',0,0,0,12,flags,0));result=u.call(0x400a6d5c,PM,EVENT)
 assert u.sp_ok and not u.bad,(u.sp_ok,u.bad)
 return result
for mode in [0,1]:
 state['mode']=mode;w(FSD+272,300);state['closed']=0
 for want in [200,100]:
  assert key(1)==1;assert u.u32(FSD+272)==want and state['closed']==0,(mode,want,state)
  snapshot=state.copy();assert key(0x21)==1;assert state==snapshot
  assert key(0x20)==1;assert state==snapshot
 assert state['closed']==0
print('PASS BACK down/repeat/release: nested folder -> parent -> Wavetables, both native browser modes, no selector close, balanced stack',flush=True)
state['mode']=1;state['closed']=0;key(1);assert state['closed']==1
print('PASS BACK at Wavetables root uses native selector close',flush=True)
u.uc.mem_write(SOUNDS+66,bytes([0]));w(FSD+272,300);state['mode']=0;before=state['parent'];key(1)
assert state['parent']==before
print('PASS other-machine browsers keep the native mode-switch path',flush=True)
