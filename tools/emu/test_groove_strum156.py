"""Groove/Strum : noyaux natifs, reference entiere et navigation reelle."""
from pathlib import Path
import sys,json,struct,random
R=Path(__file__).resolve().parents[2];W=R/'output/firmware'
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT,STACK,STOP
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v156';stem='staging/all-features-polivoks-cpu-trim-test-'+v
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['groove_strum']['symbols'];b=m['symbols']
r,sy,h,log,files,key,turn,data,bind=fixture(stem);r.s.update(s);u=r.u;u.reg_write(C.UC_M68K_REG_SR,0x2700)
P=0x931b0000;H=s['gc_amounts']-40;r.w32(0x40a7887c,P)
sgn=lambda n:n-0x100000000 if n&0x80000000 else n
def reg(n,v):u.reg_write(getattr(C,'UC_M68K_REG_'+n),v&0xffffffff)
def get(n):return u.reg_read(getattr(C,'UC_M68K_REG_'+n))
def groove(mode,t,step,sw,word,vel,ht=0,hv=0):
 u.mem_write(s['gc_groove'],bytes([mode]));u.mem_write(H+40,bytes(12));u.mem_write(H+40+t,bytes([ht]));u.mem_write(H+46+t,bytes([hv]))
 u.mem_write(STACK,bytes(80));r.w32(STACK,STOP);r.w32(STACK+0x34,vel);u.mem_write(STACK+0x3e,b'\x06')
 for n,x in [('A7',STACK),('A3',P),('A0',6),('D0',sw),('D1',word),('D3',step),('D5',0),('D6',t)]:reg(n,x)
 u.emu_start(s['G'],STOP,count=5000);assert get('PC')==STOP and get('A7')==STACK+4
 return sgn(get('D5')),r.r32(STACK+0x34)
tables=json.loads((R/'tools/machines/groove_strum/grooves.json').read_text())['grooves']
for mode in range(8):
 for st in range(64):
  for sw in (0,7,30):
   for vel in (1,40,100,127):
    for word in (0x81,0x91):
     got=groove(mode,st%6,st,sw,word,vel)
     if mode==0:expected=(6*12*sw if word&16 else 0,vel)
     else:
      tab=next(x for x in tables if x['index']==mode);off=tab['offset_256th_step'][st];vv=tab['velocity'][st]
      expected=((off*sw*30)>>6,max(1,vel-((vel*(127-vv)*sw*165)>>20)))
     assert got==expected,(mode,st,sw,word,vel,got,expected)
 print('PASS native timing/velocity table',mode,flush=True)
rnd=0x1234567;r.w32(s['gc_rng'],rnd)
for i in range(800):
 ht=[0,1,4,50,100,101][i%6];hv=[0,100,30,0,100,200][(i//6)%6];vel=[1,40,100,127][i%4]
 got=groove(0,i%6,i%64,0,0x81,vel,ht,hv);st=((ht if ht<=100 else 0)*77)>>7;sv=((hv if hv<=100 else 0)*77)>>7
 if st or sv:rnd=(rnd*1664525+1013904223)&0xffffffff
 dt=(((((rnd>>16)&0x7fff)-0x4000)*72*st)>>17) if st or sv else 0
 dv=(sgn((((rnd>>1)&0x7fff)-0x4000)*sv*vel*5&0xffffffff)+0x800000)>>24 if st or sv else 0
 assert got==(dt,max(1,min(127,vel+dv))),(i,got,dt,dv)
 assert r.r32(s['gc_rng'])==rnd
print('PASS native Humanize reference, six tracks, invalid values and RNG',flush=True)
# Epilogue reel CHORD : registres preserves et enveloppe de chaque note.
counts=[0x55555555]*6;random.seed(156);saved=[0xd2000002,0xd3000003,0xd4000004,0xd5000005,0,0xa3000003,0xa4000004]
u.mem_write(s['gc_ticks'],b'\x55'*24)
for bl in range(1000):
 sv=random.choice([0,1,4,32,80,-80,-32,-1,81,-81]);u.mem_write(s['gc_strum'],bytes([sv&255]));stride=(abs(sv)*96)>>6 if -80<=sv<=80 else 0
 for t in range(6):
  voice=0x42308828+t*796;trig=random.random()<.03;gains=[random.randrange(1<<31) for _ in range(3)];r.w32(voice+56,trig);u.mem_write(voice+12,struct.pack('>3I',*gains))
  counts[t]=0 if trig else min(0xffff,counts[t]+1) if counts[t]<0xffff else counts[t]
  ex=[]
  for k,g in enumerate(gains,1):
   d=counts[t]-(3-k if sv<0 else k)*stride;ex.append(g if not stride or d>1 else 0 if d<0 else g>>(2 if d==0 else 1))
  d=counts[t]-(3*stride if sv<0 else 0);g0=0x20000000 if not stride or d>7 else 0 if d<0 else (d+1)<<26
  saved[4]=voice;u.mem_write(STACK,b'\xee'*8+struct.pack('>8I',*saved,STOP));reg('A7',STACK);reg('A2',voice);reg('D6',0xd6d6d6d6);reg('D7',0xd7d7d7d7)
  u.emu_start(s['ST'],STOP,count=5000)
  assert list(struct.unpack('>3I',u.mem_read(voice+12,12)))==ex and r.r32(s['gc_g0'])==g0,(bl,t,sv)
  assert [get(n) for n in ('D2','D3','D4','D5','A2','A3','A4')]==saved and get('A7')==STACK+40 and get('D6')==0xd6d6d6d6 and get('D7')==0xd7d7d7d7
print('PASS 6000 native CHORD blocks, both Strum directions/zero/bounds and saved ABI',flush=True)
# En-tete Chord Keys : chemins OS sans chevauchement avec Humanize.
A,B=0x931c0000,0x931c1000;u.mem_write(A,bytes(range(64)));u.mem_write(B,b'\xee'*64)
before=bytes(u.mem_read(s['gc_amounts'],12));assert r.call(0x4005b3b4,B,A)&255==1;assert bytes(u.mem_read(s['gc_amounts'],12))==before
u.mem_write(B,b'\x33'*64);r.call(0x40061526,B,0);assert bytes(u.mem_read(s['gc_amounts'],12))==before
print('PASS native pattern header load/init',flush=True)
def event(code,flags):u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,code,flags,0));return r.call('gc_key',EVENT)
def click():event(32,1);event(32,16)
def back():event(12,1);event(12,16)
def enc(delta):r.delta=delta;u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,1,0,0));r.call('gc_encoder',EVENT)
r.w32(b['menu'],1);r.w32(b['row'],9);click();assert r.r32(s['gc_page'])==1
for row in range(5):
 assert r.r32(s['gc_row'])==row;click();assert r.r32(s['gc_edit'])==1;enc(1);back();assert not r.r32(s['gc_edit']) and r.r32(s['gc_page']);enc(1)
back();assert not r.r32(s['gc_page']) and r.r32(b['row'])==9
u.mem_write(H+40,bytes(12));r.w32(s['gc_track'],6);r.w32(s['gc_row'],2);r.call('gc_adjust',1000);assert bytes(u.mem_read(H+40,6))==bytes([100]*6);r.call('gc_adjust',(-999)&0xffffffff);assert bytes(u.mem_read(H+40,6))==bytes(6)
print('PASS native menu open/edit/BACK, all five rows and per-track/All clamps',flush=True)
r.call('gc_frame');assert '/Groove.cfg' in files and len(files['/Groove.cfg'])==20
print('PASS stopped settings persistence',flush=True)
