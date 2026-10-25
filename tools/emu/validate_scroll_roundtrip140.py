"""Retour reel : chaque moteur retrouve les dials observes a l'aller."""
from pathlib import Path
import sys,json,struct
W=Path(__file__).resolve().parents[2];R=W;sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_keep_machine_params import fixture,SLOTS,T,C
v=sys.argv[1] if len(sys.argv)>1 else 'v140';stem='staging/all-features-polivoks-cpu-trim-test-'+v
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());sy=m['keep_params']['symbols'];order=m['tiny_extra']['menu_order']
for lane in range(6):
 u,obj,snd=fixture(stem);this=0x93900000
 for a in (0x400f44c6,0x4001416c):del u.hooks[a]
 u.uc.mem_map(0xfc070000,4096)
 u.hooks[0x40012412]=('lane',lane);u.hooks[0x400802ec]=('free',0);u.hooks[0x400802e0]=('alloc',0x93200000)
 u.uc.mem_write(snd,bytes(100));u.uc.mem_write(snd+38,bytes(2));u.call(0x40014072,obj)
 for slot,value in zip(SLOTS,(64,90,79,110,88,25)):u.uc.mem_write(snd+20+slot*2,struct.pack('>H',value*256))
 u.uc.mem_write(this+0x70+4*lane,bytes(4));u.uc.reg_write(C.UC_M68K_REG_D2,lane)
 u.call(sy['kr_snapshot'],obj);u.uc.mem_write(this+136+12*lane,bytes(u.uc.mem_read(T.SCRATCH,12)))
 u.hooks[0x400802e0]=('alloc',0x93220000);tick=0
 def values():return tuple(struct.unpack('>H',u.uc.mem_read(snd+20+2*x,2))[0] for x in SLOTS)
 def turn(delta):
  clock=turn.clock+6000000;turn.clock=clock
  u.uc.mem_write(0xfc07000c,struct.pack('>I',clock));u.call(0x400a2712,this,delta,0,0)
 turn.clock=0
 forward={0:values()}
 for machine in order[1:]:turn(1);assert u.uc.mem_read(snd+38,1)[0]==machine;forward[machine]=values()
 failures=[]
 for machine in reversed(order[:-1]):
  turn(0xffffffff);actual=values()
  if actual!=forward[machine]:failures.append((machine,forward[machine],actual))
 assert not failures,('scroll-back lost forward values',lane,failures)
 assert not u.bad
 print('PASS track',lane+1,'all24 machines: forward dial values restored on scroll back',flush=True)
