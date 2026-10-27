"""Horloge native, codec natif, controles et claims LED du nouveau champ."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import m68k_const as C,UC_HOOK_CODE
stem='staging/all-features-polivoks-cpu-trim-test-v199';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['page_length']['symbols']
r,fx,held,log,files,key,turn,data,bind=fixture(stem);u=r.u;u.mem_map(0x93400000,0x400000);r.heap=0x93500000
p=0x93400000;other=p+0x10000;serial=p+0x20000;model=p+0x40000;h=p+30642
r.call(0x400615e8,p,0);r.call(0x400615e8,other,0)
def tag(n):u.mem_write(h+60,bytes([80,76,n,(~n)&255]))
assert r.call(s['pl_length'],h)==16
for n in range(1,17):
 tag(n)
 for length in range(2,65):
  wanted=[x for x in range(length) if x%16<n]
  assert r.call(s['pl_effective'],p,length)==len(wanted)
  step=0;visited=[]
  for i in range(len(wanted)*2):
   visited.append(step);step=r.call(s['pl_next'],p,step+1)
   if step>=length:step=0
  assert visited==wanted*2,(n,length,visited,wanted)
print('PASS all16 page lengths x63 pattern lengths; exact active-step order and master duration',flush=True)
# Vraie boucle native des six compteurs, tous les sous-pas et retours inclus.
wrapped=[];bind(0x4009162a,lambda a:wrapped.append(a[0]) or 0)
def fragment(start,end,pattern):
 u.reg_write(C.UC_M68K_REG_A7,0x93008000);u.reg_write(C.UC_M68K_REG_A2,pattern);u.emu_start(start,end,count=100000)
 assert u.reg_read(C.UC_M68K_REG_PC)==end
cases=0
for n in range(1,17):
 tag(n)
 for length in (2,7,16,17,31,32,35,48,64):
  for mode in (0,1):
   u.mem_write(p+30667,bytes([mode]));u.mem_write(p+30662,struct.pack('>H',length))
   lengths=[length]*6 if not mode else [2,7,16,31,48,64]
   for t,k in enumerate(lengths):u.mem_write(p+722*t+713,struct.pack('>H',k))
   u.mem_write(0x40a78848,struct.pack('>6I',*([1]*6)));u.mem_write(0x40a78860,bytes(12));u.mem_write(0x40a788b5,bytes([2]*6));u.mem_write(0x40a78630,bytes(4));u.mem_write(0x40a788d4,bytes(2))
   expected=[[x for x in range(k) if x%16<n] for k in lengths];previous=[0]*6;counts=[0]*6;last=[0]*6
   ticks=6*(max(map(len,expected))*2+1);wrapped.clear()
   for tick in range(ticks):
    fragment(0x4005528a,0x4005537e,p)
    actual=list(u.mem_read(0x40a78860,6))
    if (tick+1)%6==0:
     for t in range(6):counts[t]+=1;previous[t]=expected[t][counts[t]%len(expected[t])]
    assert actual==previous,(n,length,mode,tick,actual,previous)
   assert len(wrapped)==sum(counts[t]//len(expected[t]) for t in range(6))
   cases+=1
print('PASS',cases,'real six-track native clock cases, 6subticks per step, common/per-track lengths, native wrap notifications',flush=True)
# Lecture du master : le vrai crochet conserve le diviseur/tempo natif.
for n in range(1,17):
 tag(n);u.mem_write(p+30667,b'\0');u.mem_write(p+30668,b'\x02');r.w32(0x40a7883c,1)
 for length in (2,7,16,17,32,48,64):
  u.mem_write(p+30662,struct.pack('>H',length));fragment(0x40055424,0x40055452,p)
  assert u.reg_read(C.UC_M68K_REG_D0)==len([x for x in range(length) if x%16<n])
  assert u.reg_read(C.UC_M68K_REG_D2)==6
print('PASS native master length and scale divisor;16-step default retains native durations',flush=True)
# Header setter UI et native serialization, pas de fichier auxiliaire.
obj=model+44;vt=model+0x100;get=vt+0x100;notify=get+16
r.w32(obj,vt);r.w32(vt+40,get);r.w32(vt+16,notify);bind(get,lambda a:h);notifications=[];bind(notify,lambda a:notifications.append(a[:2]) or 0);bind(0x4000f208,lambda a:model);bind(0x4000d0dc,lambda a:obj)
u.mem_write(p+30667,b'\0');u.mem_write(p+30662,b'\0\x40');tag(16)
snapshot=bytes(u.mem_read(p,30710));r.call(s['pl_change'],0,0,0xfffffff9);assert r.call(s['pl_length'],h)==9
after=bytearray(snapshot);after[30702:30706]=bytes([80,76,9,246]);assert bytes(u.mem_read(p,30710))==bytes(after)
assert notifications[-1]==(obj,0)
for delta,want in ((-999,1),(999,16),(-4,12)):
 r.call(s['pl_change'],0,0,delta&0xffffffff);assert r.call(s['pl_length'],h)==want
assert r.call(0x4005ba0a,serial,p,0xffffffff)&255
assert bytes(u.mem_read(serial+0x3990+60,4))==bytes([80,76,12,243])
assert r.call(0x4005b894,other,serial,0)&255 and r.call(s['pl_length'],other+30642)==12
assert r.call(0x4008f1f0,other,p,30710)==other and r.call(s['pl_length'],other+30642)==12
r.call(0x40061526,other+30642,0);assert r.call(s['pl_length'],other+30642)==16
u.mem_write(serial+0x3990+60,b'PL\x00\xff');assert r.call(0x4005b894,other,serial,0)&255 and r.call(s['pl_length'],other+30642)==16
print('PASS UI edits clamp1..16, native header notification, unchanged notes/locks, native pattern save/load/copy and default/malformed tags',flush=True)

u.reg_write(C.UC_M68K_REG_SR,0x2200);r.w32(0x40a7883c,1);r.w32(0x40a78874,0)
r.w32(0x40a7887c,p)
def warp_tag(n,on=True):u.mem_write(h+60,bytes([80,87 if on else 76,n,(~n)&255]))
def reset(n,on=True):
 warp_tag(n,False);r.w32(0x40a78628,0);r.call(s['wp_begin']);r.call(s['wp_finish']);warp_tag(n,on)

u.mem_map(0x80000000,0x20000);u.mem_map(0xfc048000,4096)
u.mem_map(0x4e200000,0x200000)
for at in (0x40082512,0x40001fba,0x40091f82,0x40091fdc):
 if at not in (0x40091f82,0x40091fdc):bind(at,lambda a:0)
bind(0x40091770,lambda a:0)
notes=[];scheduled=[];cancelled=[];pool=[0]
def event(a):
 addr=0x93600000+80*(pool[0]%1000);pool[0]+=1;u.mem_write(addr,bytes(80));return addr
bind(0x40091eb6,event)
lockbuf=0x93780000
bind(0x40091e66,lambda a:u.mem_write(lockbuf,bytes(4096)) or lockbuf)
bind(s['wp_old_insert'],lambda a:notes.append((a[1],bytes(u.mem_read(a[0],80)))) or 1)
bind(s['wp_old_schedule'],lambda a:scheduled.append(a[:3]) or 0);bind(s['wp_old_cancel'],lambda a:cancelled.append(a[:3]) or 0)
kit=0x93450000;u.mem_write(kit,bytes(1024));r.w32(0x40a78888,kit);r.w32(0x40a78890,kit);r.w32(0x40a7888c,kit)
for at in (0x40a7887c,0x40a78880,0x40a78884):r.w32(at,p)
for at in (0x40a78914,0x40a788f4,0x40a788f8,0x40a78920,0x40a78630,0x40a78638):r.w32(at,0)
r.w32(0x40a78634,0xffffffff);u.mem_write(0x40a788bb,b'\0');r.w32(0x40a7883c,1);r.w32(0x40a78874,0)
u.mem_write(p+30667,b'\0');u.mem_write(p+30662,b'\0\x10');u.mem_write(p+30668,b'\x02');u.mem_write(0x40a788b4,bytes([2]*7))
u.mem_write(0x40a78848,struct.pack('>6I',*([1]*6)));u.mem_write(0x40a78860,bytes(18));u.mem_write(0x40a788dc,bytes([5]*6));u.mem_write(0x40a788d6,bytes([255]*6));u.mem_write(0x40a788d4,bytes(2));u.mem_write(0x40a788e2,bytes(2))
for t in range(6):
 for step in range(64):u.mem_write(p+722*t+step*2,b'\0\x01')

def setup(n,enabled,scale):
 notes.clear();scheduled.clear();cancelled.clear();pool[0]=0
 for at in (0x40a7887c,0x40a78880,0x40a78884):r.w32(at,p)
 for at in (0x40a78914,0x40a788f4,0x40a788f8,0x40a78920,0x40a78630,0x40a78638,0x40a78840):r.w32(at,0)
 r.w32(0x40a78634,0xffffffff);u.mem_write(0x40a788bb,b'\0');r.w32(0x40a7883c,1);r.w32(0x40a78874,0)
 u.mem_write(p+30667,b'\0');u.mem_write(p+30662,b'\0\x10');u.mem_write(p+30668,bytes([scale]));u.mem_write(0x40a788b4,bytes([scale]*7))
 period=r.r32(0x4010afa4+scale*4)
 u.mem_write(0x40a78848,struct.pack('>6I',*([1]*6)));u.mem_write(0x40a78860,bytes(18));u.mem_write(0x40a788dc,bytes([period-1]*6));u.mem_write(0x40a788d6,bytes([255]*6));u.mem_write(0x40a788d4,bytes(2));u.mem_write(0x40a788e2,bytes(2))
 r.w32(0x40a7863c,p);r.w32(0x40a78640,kit);r.w32(0x40a78638,1);reset(n,enabled);r.w32(0x40a78628,0);return period
def tick():
 u.reg_write(C.UC_M68K_REG_A7,0x93008000);u.reg_write(C.UC_M68K_REG_SR,0x2200);u.emu_start(0x40054c1e,0x40055970,count=300000)
 assert u.reg_read(C.UC_M68K_REG_PC)==0x40055970
def track_notes(t):return [(time,v) for time,v in notes if struct.unpack_from('>I',v,0)[0]==0 and struct.unpack_from('>I',v,8)[0]==t]

def fulltick():
 u.reg_write(C.UC_M68K_REG_A7,0x93008000);u.reg_write(C.UC_M68K_REG_SR,0x2200);u.emu_start(0x40054c1e,0x40055a7a,count=300000)
 assert u.reg_read(C.UC_M68K_REG_PC)==0x40055a7a
mode=[0];bind(0x40091770,lambda a:mode[0]);cases=0
for n in range(1,17):
 for scale in (0,2,5):
  for clockmode in (0,1):
   mode[0]=clockmode
   for enabled in (False,True):
    period=setup(n,enabled,scale);u.mem_write(0x40a78844,b'\0');clocks=period*48;calls=clocks*(4 if clockmode==0 else 1)
    for i in range(calls):fulltick()
    assert r.r32(0x40a78628)==clocks*900000
    tracks=[track_notes(t) for t in range(6)];times=[x[0] for x in tracks[0]];assert len(times)>n,(n,scale,clockmode,enabled,len(times))
    for tr in tracks:assert [x[0] for x in tr]==times
    page=period*900000*(16 if enabled else n)
    for i in range(len(times)-n):assert times[i+n]-times[i]==page,(n,scale,clockmode,enabled,i,times[:20])
    for i,t in enumerate(times):assert abs(t-times[0]-i*page//n)<=1
    hearts=[t for t,v in notes if struct.unpack_from('>I',v,0)[0]==5];assert hearts==[(i+1)*900000 for i in range(clocks)]
    cases+=1
 print('PASS page length',n,'full ISR scales/modes/On-Off',flush=True)
print('PASS',cases,'complete native timer-interrupt cases; all six tracks; quarter-tick and whole-tick paths; exact warped pages and unchanged physical clock',flush=True)
