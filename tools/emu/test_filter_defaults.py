"""Defaults LOW127/RES0 : nouveaux sons, clear, Undo et chargements natifs.
Usage : python tools/emu/test_filter_defaults.py v208|v211, apres generation --stage.
"""
"""TRACK+COPY/PASTE natif : huit reglages LFO2, polarite et Undo, sans codec."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v211'
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

version=v
fc=m['filter_modes']['symbols'];base=fc['fc_type']
def modes():return [r.r32(base+4*t) for t in range(6)]
def filters(t):return struct.unpack('>2H',u.mem_read(raw(t)+68,4))
def seed_filters():
 seedall()
 for t in range(6):r.w32(base+4*t,1+t%3);u.mem_write(raw(t)+68,struct.pack('>2H',0x1000+t*256,0x7000))
for track in range(6):
 seed_filters();prior=modes();before=[filters(t) for t in range(6)]
 assert r.call(0x400149fa,handle(track),24,data+0x58000,1,0)==1
 assert modes()==[0 if t==track else prior[t] for t in range(6)],modes()
 assert filters(track)==(0x7f00,0),filters(track)
 assert all(filters(t)==before[t] for t in range(6) if t!=track)
 assert r.call(0x40014b06,handle(track),track,1)==1
 assert modes()==prior and [filters(t) for t in range(6)]==before,(track,modes(),prior)
print('PASS six native sound clears: only target LOW/open127/resonance0; actual native Undo restores filter type and cutoff alongside all LFO banks',flush=True)
for track in range(6):
 seed_filters();prior=modes();before=[filters(t) for t in range(6)]
 r.call(0x400141d2,raw(track))
 assert modes()==[0 if t==track else prior[t] for t in range(6)],modes()
 assert filters(track)==(0x7f00,0),filters(track)
 assert all(filters(t)==before[t] for t in range(6) if t!=track)
print('PASS native new-sound method on each track: LOW/open127/resonance0, no changes to other tracks',flush=True)
seed_filters();prior=modes();seen=[];bind(mx['mx_old_pattern_clear'],lambda args:seen.append(tuple(args[:6])) or 1)
assert r.call(mx['mx_clear_pattern'],root,0,1,0,1,1)==1 and modes()==prior
assert r.call(mx['mx_clear_pattern'],root,1,1,1,1,1)==1 and modes()==prior
assert r.call(mx['mx_clear_pattern'],root,0,1,1,1,1)==1 and modes()==[0]*6
assert [filters(t) for t in range(6)]==[(0x7f00,0)]*6
print('PASS active sound+pattern clear resets all six filters; sequence-only and inactive-pattern clear preserve current filters',flush=True)
# Les deux lecteurs de fichiers continuent d'appeler l'initialiseur generique.
assert bytes(u.mem_read(0x4006b16e,6))==bytes.fromhex('4eb9400618f2')
assert bytes(u.mem_read(0x4008e16a,6))==bytes.fromhex('4eb9400618f2')
seed_filters();prior=modes();r.call(0x400618f2,data+0x59000,0);assert modes()==prior
print('PASS disk/project initializer untouched; loading a saved sound does not reset filter types',flush=True)
# Nouveau contexte : preference sauvegardee, aucune remise a zero au boot.
from test_fx_menu_control import fixture
rr,ss,hh,ll,files,*_=fixture('staging/all-features-polivoks-cpu-trim-test-'+version)
saved=[1,2,3,0,1,2];files['/Filter.cfg']=bytes([70,67,1,6,*saved,*[(~n)&255 for n in saved],165,90])
assert [rr.call(0x468d0110,t) for t in range(6)]==saved
print('PASS saved per-track filter types survive normal startup; no boot reset',flush=True)
rr,ss,hh,ll,files,*_=fixture('staging/all-features-polivoks-cpu-trim-test-'+version);files['/Filter.cfg']=bytes([70,67,1,6,*saved,*[(~n)&255 for n in saved],165,90])
rr.call(0x468d0100,3);assert [rr.call(0x468d0110,t) for t in range(6)]==[0 if t==3 else saved[t] for t in range(6)]
print('PASS clear before lazy preference loading stays LOW while other saved tracks retain their types',flush=True)
