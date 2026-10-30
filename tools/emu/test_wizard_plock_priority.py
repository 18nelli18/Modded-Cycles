"""CTRL-ALL et vrai refresh audio40058308 ; locks et refresh natifs ; delegation encodeur simulee."""
from pathlib import Path
source=(Path(__file__).parent/'test_acid_articulation_ui.py').read_text().split('r,files,bind=fixture();')[0]
source=source.replace("m['acid_articulation']['symbols']","m.get('wizard_priority',m.get('acid_articulation'))['symbols']")
exec(compile(source,__file__,'exec'))
OriginalRig=fx.Rig
class RealLocks(OriginalRig):
 def stub(self,u,addr,size,data):
  if addr==0x4000da2a:return
  return super().stub(u,addr,size,data)
fx.Rig=RealLocks
r,files,bind=fixture();r.u.mem_map(0x80000000,0x20000)
kit,frame,object0,owner=0x93140000,0x800015a0,0x93160000,0x93170000
r.w32(0x40a78888,kit);r.w32(0x40a7887c,0x406fa040);r.w32(0x40a78874,1)
held={2};step=[0];locked=[10]
bind(0x4007faf4,lambda a:int(a[0] in held));bind(0x4000f208,lambda a:0x93171000);bind(0x400cfd0e,lambda a:0x93172000);bind(0x4006a984,lambda a:step[0]);bind(0x4000cfcc,lambda a:object0+128*a[1]);bind(0x4000da2a,lambda a:8888 if a[1]==0 and a[2]==0 and a[3]==locked[0] else -1)
project0,raw=0x42080000,0x42180000
pattern0=project0+5192;owner=pattern0+640;object0=pattern0+112
bind(0x400d0f6c,lambda a:0);bind(0x4000cfcc,lambda a:object0+88*a[1])
r.u.mem_write(pattern0,bytes(732));r.w32(0x40fe4228,project0);r.w32(project0+48,0x400fd8c0);
r.w32(pattern0,0x400fda54);r.w32(pattern0+44,0x400fd8c0);r.w32(owner,0x400fddf4)
def init_locks(slot):
 r.call(0x400615e8,raw,0)
 for t in range(6):
  ob=object0+88*t;r.w32(ob,0x400ff894);r.w32(ob+44,owner);r.w32(ob+56,t);r.w32(ob+60,pattern0)
  queue=project0+83148+40*t;r.w32(queue+24,0x420c0000+0x1000*t);r.w32(queue+32,0x420c0800+0x1000*t)
 r.call(0x4000c5d0,pattern0,raw);r.call(0x4000c9c4,pattern0+44,64)
 for t in range(6):r.w32(object0+88*t+44,owner)
 assert r.call(0x4000dece,owner,0,0,slot,8888)&255
 assert r.call(0x4000da2a,owner,0,0,slot)==8888
 assert r.call(0x4000da2a,owner,0,1,slot)==0xffffffff
def w16(at,v):r.u.mem_write(at,struct.pack('>H',v))
def r16(at):return int.from_bytes(r.u.mem_read(at,2),'big')
def sound(t):return kit+28+100*t
for t in range(6):
 r.w32(object0+128*t+44,owner);r.w32(0x800017ec+4*t,sound(t));r.u.mem_write(sound(t)+38,bytes([6 if t<2 else 4]))
def delegate(args):
 slot=locked[0]
 for t in (0,1,2):
  w16(sound(t)+20+2*slot,12345);w16(frame+14+66*t+2*slot,12345);r.w32(0x800011e8+4*(7+33*t+slot),12345<<16)
 return 77
bind(s['aa_old_encoder'],delegate)
for slot in [10,11,12,13,14,23]+[v for v in range(33) if v not in (9,10,11,12,13,14,23)]:
 init_locks(slot);locked[0]=slot;step[0]=0;r.u.mem_write(0x423087f8,bytes(48));r.u.mem_write(frame,bytes(480))
 for t in (0,1,2):
  w16(frame+14+66*t+2*slot,8888);r.w32(0x800011e8+4*(7+33*t+slot),8888<<16)
 r.w32(0x423087f8+4*(slot>>5),1<<(slot&31))
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,4,1,0));assert r.call(s['aa_face_encoder'],0,EVENT)==77
 assert r.r32(0x423087f8+4*(slot>>5))==1<<(slot&31),'Active lock restoration mask changed'
 assert r.r32(0x800011e8+4*(7+slot))==8888<<16
 assert r16(frame+14+2*slot)==8888,('Wizard locked',slot)
 assert r16(frame+14+66+2*slot)==12345,('Wizard unlocked',slot)
 assert r16(frame+14+132+2*slot)==12345,('other machine',slot)
 assert r16(sound(0)+20+2*slot)==12345,'CTRL-ALL base edit lost'
 step[0]=1;r.call(0x40058308,0,frame,sound(0));assert r16(frame+14+2*slot)==12345,('following unlocked',slot)
print('PASS pitch/start/end and all tested slots: locked Wizard protected, base edits and unlocked/other machines native',flush=True)
a.output.write_text(json.dumps(dict(native_audio_refresh=True,native_p_lock_storage_and_getter=True,slots_tested=32,pitch_start_end=True,unlocked_steps=True,other_machines=True,base_edits_retained=True,hardware_tested=False),indent=2)+'\n')
