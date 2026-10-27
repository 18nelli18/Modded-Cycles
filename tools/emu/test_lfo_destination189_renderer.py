"""Executer le vrai renderer LFO1, y compris le tail-call qui reecrit la pile."""
from pathlib import Path
import sys,struct
v=sys.argv[1] if len(sys.argv)>1 else 'v189'
if len(sys.argv)==1:sys.argv.append(v)
exec(Path(__file__).with_name('test_lfo_clear189_fixture.py').read_text().split('seedall();before=')[0])
from unicorn import UC_HOOK_CODE
view=data+0x59000;callback=view+0x800
r.w32(callback,view);selected=[0]
bind(0x40012412,lambda a:selected[0])
bind(0x400cf9a8,lambda a:data+0x5a000)
bind(0x4006be48,lambda a:0);bind(0x4006b978,lambda a:0)
for t in range(6):r.w32(root+116+504+t*8,0x400fd134)
captures=[]
def before(uc,at,size,user):
 sp=uc.reg_read(C.UC_M68K_REG_A7)
 captures.append(struct.unpack('>4I',uc.mem_read(sp,16)))
def after(uc,at,size,user):uc.emu_stop()
u.hook_add(UC_HOOK_CODE,before,begin=0x4002650e,end=0x4002650e)
u.hook_add(UC_HOOK_CODE,after,begin=0x40026514,end=0x40026514)
count=0
for machine in range(25):
 if machine==17:continue
 for track in range(6):
  selected[0]=track;seed(track,machine,0)
  for dest in (0,1,2,3,5,6,7,8,10,11,12,13,14,18,23,24,25,127):
   u.mem_write(raw(track)+28,struct.pack('>H',dest<<8))
   try:r.call(0x400264a2,callback,0,0,0,0)
   except AssertionError:
    assert u.reg_read(C.UC_M68K_REG_PC)==0x40026514
   assert captures[-1][2:]==(dest,machine),captures[-1]
   got=r.string(u.reg_read(C.UC_M68K_REG_D0))
   if dest in (0,127):expected='NONE'
   elif machine==6 and dest in (13,14,24,25):expected={13:'FLT',14:'RES',24:'ERR',25:'ERR'}[dest]
   elif dest in (23,24,25):expected={23:'ATK',24:'FLT',25:'RES'}[dest]
   else:
    descriptor=r.call(0x4005a692,dest,machine)
    expected='ERR' if descriptor==0xffffffff else r.string(r.call(0x4000b208,root+116+504+track*8,descriptor))
   assert got==expected,(v,machine,track,dest,got,expected,captures[-1])
   count+=1
print('PASS',count,'real LFO1 renderer calls across24 audio machines/six tracks: native getter, mapper tail-call, rewritten arguments and destination names',flush=True)
print('PASS actual callback ABI is context/descriptor/destination/machine; Estus24 never replaces destination18 with Filter',flush=True)
