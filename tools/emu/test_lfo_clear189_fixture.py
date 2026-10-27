"""TRACK+COPY/PASTE natif : huit reglages LFO2, polarite et Undo, sans codec."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v187'
r,_,h,l,f,k,t,data,bind=fixture('staging/all-features-polivoks-cpu-trim-test-'+v);u=r.u
m=json.loads((R/'output/firmware/staging'/('all-features-polivoks-cpu-trim-test-'+v+'.json')).read_text());s=m['lfo_polarity']['symbols'];a=m['four_lfos']['aliases'];mx=m['four_lfos']['symbols']
r.call(0x4005a274);bind(0x400802ec,lambda a:0)
u.mem_map(0x93400000,0x400000);r.heap=0x93400000
allocs=[]
def alloc(args):
 size=args[0];at=r.new(args);guard=r.heap;r.heap+=16;u.mem_write(guard,b'\x5a'*16);allocs.append((at,size,guard));return at
bind(0x400802e0,alloc)
root=data+0x6000;table=data+0x10000;vt=data+0x20000;get=vt+0x100;notify=get+16;ctx=data+0x21000
r.w32(0x40fe4228,root);r.w32(0x40a78888,table);r.w32(a['lf2_context'],ctx);r.w32(a['lf2n_epoch'],0);r.w32(a['lf2n_seen'],0)
r.w32(vt+40,get);r.w32(vt+16,notify);bind(0x400cf866,lambda x:root);bind(0x4678eb16,lambda x:0)
handles_real=[r.call(0x40009c1a,root+116,t) for t in range(6)]
assert handles_real==[root+212+68*t for t in range(6)]
def handle(t):return handles_real[t]
def raw(t):return table+28+100*t
def settings(t):return ctx+192+16*t
for t in range(6):r.w32(handle(t),vt);r.w32(root+116+504+t*8+4,handle(t))
bind(get,lambda x:raw((x[0]-handle(0))//68));notified=[]
bind(notify,lambda x:notified.append(x[0]) or 0)
def seed(t,machine=0,flags=None):
 b=bytearray((i*37+t*19)&255 for i in range(100));b[38]=machine
 struct.pack_into('>5H',b,76,23000,0x400|(0xa0|flags if flags is not None else 0),0x200,0xb00,24576);u.mem_write(raw(t),bytes(b))
 u.mem_write(settings(t),struct.pack('>8H',23000,0x400|(0xa0|flags if flags is not None else 0),12000,0xb00,0x200,18000,0x300,24576))
 r.w32(s['lp_one']+4*t,1);r.w32(s['lp_two']+4*t,0)
def current(t):return bytes(u.mem_read(raw(t),100)),bytes(u.mem_read(settings(t),16))
# Real extra-bank initialization, hidden while the audio LFO count stays2.
u.mem_map(0x80000000,0x20000)
for t in range(6):u.mem_write(0x8000100c+16+66*t,struct.pack('>8H',0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000))
pattern=data+0x40000;r.w32(0x40a7887c,pattern);r.w32(pattern+30706,0);bind(0x4000eae2,lambda a:1)
assert r.call(mx['mx_copy_prepare'])==1
assert r.call(mx['mx_count_get'])==2


primary=struct.pack('>8H',0x7000,0x400,0x4000,0,0,0,0,0x4000)
secondary=struct.pack('>8H',0x7000,0x400,0x4000,0x7f00,0,0,0,0x4000)
extras=[r.r32(mx['mx_extra']+4*b) for b in range(2)]
def allstate(t):
 return (bytes(u.mem_read(raw(t)+22,16)),bytes(u.mem_read(settings(t),16)),*[bytes(u.mem_read(c+192+16*t,16)) for c in extras],r.r32(s['lp_one']+4*t),r.r32(s['lp_two']+4*t),*[r.r32(mx['mx_polarity']+4*(b*6+t)) for b in range(2)])
def seedall():
 for t in range(6):
  seed(t,machine=24,flags=3);u.mem_write(raw(t)+22,b'\x12\x00'*8);u.mem_write(0x40fde838+32*t,b'\x55'*32)
  for b,c in enumerate(extras):u.mem_write(c+192+16*t,struct.pack('>8H',19000,0x500,17000,0x1200,0x300,18000,0x200,29000));u.mem_write(c+32*t,b'\x55'*32);r.w32(mx['mx_polarity']+4*(b*6+t),1)
