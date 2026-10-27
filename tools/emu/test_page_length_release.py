"""Horloge native, codec natif, controles et claims LED du nouveau champ."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import m68k_const as C,UC_HOOK_CODE
stem=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v194';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['page_length']['symbols']
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
# Le vrai writer LED garde la premiere revendication de chaque pad.
view=model+0x1000;vec=view+0x1000;item=vec+0x100;led=vec+0x1000
r.w32(view,0x40103f34);r.w32(view+4,vec);r.w32(view+8,vec+8);r.w32(view+20,0);r.w32(view+24,0);r.w32(vec,item);r.w32(item+56,s['pl_draw'])
bind(0x400cfaf4,lambda a:led);bind(0x4008e942,lambda a:0);bind(0x4008e964,lambda a:0);bind(0x4008e998,lambda a:0)
old_calls=[]
def legacy_led(a):
 old_calls.append(a)
 for i in range(16):r.call(0x40005f86,led,i+1,2,0x404a8cb8)
 return 19
# Eviter l'imbrication emu_start dans un stub : le callback natif est observe.
bind(s['pl_old_led'],lambda a:old_calls.append(a) or 19)
for n in range(1,17):
 tag(n);u.mem_write(led,bytes(512));assert r.call(s['pl_led'],view,0,0)==19
 assert [r.r32(led+40+4*i) for i in range(1,17)]==[2]*n+[1]*(16-n)
u.mem_write(item+56,bytes(4));u.mem_write(led,bytes(512));r.call(s['pl_led'],view,0,0);assert not any(u.mem_read(led,512))
print('PASS trig LEDs1..N active and N+1..16 inactive for all16values only while Page Len selected; native LED delegation retained',flush=True)

native_off=[]
for enabled in (0,1):
 u.mem_write(led,bytes(512));r.call(0x40005fe6,led,1,enabled,0x404a8cb8);native_off.append(r.r32(led+44))
assert native_off==[1,2]
r.w32(item+56,s['pl_draw'])
for n in range(1,17):
 for playing in (0,1):
  r.w32(0x40a7883c,playing)
  for phase in (0,1,2,3,15,16,31,63):
   r.w32(0x40a78628,phase*900000);tag(n);u.mem_write(led,bytes(512));r.call(0x4002fd38,view,0,0)
   states=[r.r32(led+40+4*i) for i in range(1,17)]
   assert states==[native_off[1]]*n+[native_off[0]]*(16-n) and 3 not in states
print('PASS256 native LED frames: all page lengths, playing/stopped, eight clock phases; inactive steps use native OFF, never blink',flush=True)
