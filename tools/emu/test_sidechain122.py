"""Preuves natives122 : routage, gain, UI, codecs et ancien121."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from boot_candidate import boot
from test_seq_gen_menu import Rig,OBJ,VT,STACK,STOP,EVENT
from unicorn import UC_HOOK_CODE,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v122';S=R/'output/firmware/staging';stem='all-features-polivoks-cpu-trim-test-'+v
m=json.loads((S/(stem+'.json')).read_text());im,mem=boot(S/(stem+'.syx'));p=m['fx_project'];d=m['sidechain'];s={**p['symbols'],**d['symbols']};sx=m['scramble_mask']['symbols']
r=Rig(im,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
for at,b in mem:u.mem_map(at,len(b));u.mem_write(at,b)
u.mem_map(0x80000000,0x20000);u.mem_map(0xfc070000,0x1000)
RAW=0x41400000;SER=0x41800000;CB=0x93015000;CLIP=0x93040000;STRIDE=30710;SIZE=0x210404
r.w32(VT+40,0x400d3af6);r.w32(OBJ+16,RAW);r.w32(0x40fe4228,OBJ)
def forbidden(a):raise AssertionError('constructing singleton called')
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
bind(0x400cf866,forbidden);bind(0x400d0a10,lambda a:1);bind(0x4007bc5e,lambda a:0xffffffff)
def call(fn,*args):
 if isinstance(fn,str):fn=s[fn]
 sp=STACK-0x400;u.mem_write(sp,struct.pack('>I'+'I'*len(args),STOP,*args));u.reg_write(C.UC_M68K_REG_A7,sp);u.emu_start(fn,STOP,count=250_000_000)
 assert u.reg_read(C.UC_M68K_REG_PC)==STOP,(fn,hex(u.reg_read(C.UC_M68K_REG_PC)));assert u.reg_read(C.UC_M68K_REG_A7)==sp+4
 return u.reg_read(C.UC_M68K_REG_D0)
def state():return [r.r32(at) for at in p['field_addresses']]+list(u.mem_read(sx['sx_masks'],6))+list(u.mem_read(s['du_config'],30))
def setstate(values):
 for at,n in zip(p['field_addresses'],values):r.w32(at,n)
 u.mem_write(sx['sx_masks'],bytes(values[36:42]));u.mem_write(s['du_config'],bytes(values[42:]));call('du_reset')
def activate(i):
 ptr=RAW+28+i*STRIDE;r.w32(ptr+30706,i);u.reg_write(C.UC_M68K_REG_A2,ptr);u.reg_write(C.UC_M68K_REG_A7,STACK-0x400);u.emu_start(0x40055c5c,0x40055c62,count=1_000_000);assert r.r32(0x40a7887c)==ptr
def save():u.mem_write(SER,b'\xa5'*SIZE);assert call(0x4005d18a,SER,RAW,0,255,CB)&255;return bytes(u.mem_read(SER,SIZE))
def load(blob):u.mem_write(SER,bytes(blob));assert call(0x4005d3dc,RAW,SER,CB)&255
u.mem_write(CB,bytes(16))
if len(sys.argv)>2 and sys.argv[2]=='--restart':
 load((R/'output/firmware/fxd-restart-fixture.bin').read_bytes());call('fxp_sync')
 expected=json.loads((R/'output/firmware/fxd-restart-expected.json').read_text())
 for i in (0,1):activate(i);assert state()==expected[i]
 activate(95);assert state()==p['defaults']+[60]*6+[0,9,0,0,6]*6
 print('PASS fresh emulator reload restores72 settings in A/B and blank defaults',flush=True);sys.exit(0)
call(0x40061738,RAW);call('fxp_sync');activate(0)
defaults=p['defaults']+[60]*6+[0,9,0,0,6]*6;assert state()==defaults,(state(),defaults)
a=defaults.copy();a[0]=11;a[18]=11;a[20]=16;a[36:42]=[0,1,2,4,8,63]
for i in range(6):a[42+5*i:47+5*i]=[63&~(1<<i),15,7,3,15]
b=defaults.copy();b[0]=7;b[18]=1;b[36:42]=[63,62,61,60,59,58];b[42:47]=[2,12,2,1,8]
setstate(a);activate(1);assert state()==defaults;setstate(b);activate(0);assert state()==a;activate(1);assert state()==b;activate(95);assert state()==defaults;activate(0);assert state()==a
print('PASS72independent FX/Scramble/Duck values, all6source masks, blank pattern defaults and native activation',flush=True)
# Requete native differee : ne publier aucune configuration avant l'echeance.
queue=0x93017000;r.w32(queue,RAW+28+STRIDE);r.w32(queue+4,0x41c00000);r.w32(0x40a7883c,1);r.w32(0x40a78920,0)
call(0x40055cd6,queue,1);call('fxs_ui');assert state()==a and r.r32(0x40a7887c)==RAW+28
activate(1);assert state()==b;r.w32(0x40a7883c,0);activate(0)
print('PASS queued native pattern request keeps routing/Scramble/FX until real activation',flush=True)
header=RAW+28+30642;u.mem_write(header+32,struct.pack('>I',0x434b01a7));u.mem_write(header+40,struct.pack('>6I',*[0x86000000+i for i in range(6)]));guard=bytes(u.mem_read(header,64))
blob=save();assert blob[512+0x39d0:512+0x39d2]==b'F2';load(blob);activate(0);assert state()==a;activate(1);assert state()==b
protected=set(range(64))-{29,30,31,36,37,39};encoded=blob[512+0x3990:512+0x39d0]
assert all(encoded[i]==guard[i] for i in protected)
print('PASS native metadata and all ChordKeys bytes preserved outside six reserved padding bytes',flush=True)
bad=bytearray(blob);bad[512+0x39d5]^=1;load(bad);activate(0);assert state()==defaults;activate(1);assert state()==b
load(blob);activate(0);call('fxs_copy',CLIP,RAW+28,STRIDE);call('fxs_copy',RAW+28+3*STRIDE,CLIP,STRIDE);activate(3);assert state()==a
call(0x400615e8,RAW+28+3*STRIDE,0);assert state()==defaults
activate(0);assert call(0x4005ba0a,SER,RAW+28,0)&255;assert call(0x4005b894,RAW+28+4*STRIDE,SER,4)&255;activate(4);assert state()==a
print('PASS native project/pattern codecs, compact CRC rejection isolated, clipboard copy, native initialization',flush=True)
cache=0x93018000;disk={}
def writer(args):disk[args[1]]=bytes(u.mem_read(SER,SIZE));return 1
for at,fn in [(0x400cfdaa,lambda a:cache),(0x4006a216,lambda a:SER),(0x4006a4d6,writer),(0x4006a3ac,lambda a:SER)]:bind(at,fn)
assert call(0x4000f762,OBJ,9,CB)&255
u.mem_write(SER,disk[9]);assert call(0x4006a5a0,cache,9,RAW,CB)&255;activate(0);assert state()==a;activate(1);assert state()==b
print('PASS high-level native Save Project and cache Load Project keep72 settings',flush=True)
# Ancien fichier121 : effets conserves, nouvelles fonctions par defaut.
old=(R/'output/firmware/fxs-restart-fixture.bin').read_bytes();load(old);activate(0);assert state()[36:]==defaults[36:];assert state()[:36]!=defaults[:36]
print('PASS older121 project retains FX and starts Scramble/Duck at defaults',flush=True)
load(blob);activate(0);setstate(defaults)
# Le rendu6pistes mid/side doit appliquer un gain commun uniquement aux cibles.
side=0x80004000;flags=0x80005000;br=m['beat_repeat_symbols'];r.w32(br['br_side'],side);r.w32(br['br_side_on'],flags);u.mem_write(flags,struct.pack('>6I',*([1]*6)))
def refill():
 for t in range(6):u.mem_write(0x80001858+128*t,struct.pack('>32i',*([400000000]*32)));u.mem_write(side+128*t,struct.pack('>32i',*([-200000000]*32)))
def lane(t,base=0x80001858):return struct.unpack('>32i',bytes(u.mem_read(base+128*t,128)))
refill();before=bytes(u.mem_read(0x80001858,768));counts=[0];h=u.hook_add(UC_HOOK_CODE,lambda *args:counts.__setitem__(0,counts[0]+1));call('du_process');u.hook_del(h);assert bytes(u.mem_read(0x80001858,768))==before
print('PASS disabled duck bit-exact bypass:',counts[0],'instructions including call return',flush=True)
cfg=defaults.copy();cfg[42:47]=[34,15,0,0,6];setstate(cfg);call('du_voice_triggers',1);refill();call('du_process')
for t in range(6):
 if t in (1,5):assert lane(t)[-1]<10000 and lane(t,side)[-1]>-10000
 else:assert lane(t)==(400000000,)*32 and lane(t,side)==(-200000000,)*32
assert lane(1)[0]>lane(1)[-1]>0
for _ in range(240):refill();call('du_process')
assert lane(1)==(400000000,)*32
print('PASS source/self/untargeted lanes untouched, selected mid/side duck equally, smooth attack ramp and release back to unity',flush=True)
# Le constructeur en amont de la file ne declenche rien ; filtre a l'echeance seulement.
u.mem_write(EVENT,struct.pack('>24I',0,1,0,1,*([0]*20)));r.w32(EVENT+40,513);r.w32(s['du_pending'],0)
call(sx['sx_step'],EVENT);assert not r.r32(s['du_pending'])
call('du_note_filter',EVENT);assert r.r32(s['du_pending'])==1
for onoff,src,flags in [(2,1,513),(1,0xffffffff,513),(1,1,2)]:
 r.w32(s['du_pending'],0);r.w32(EVENT+4,onoff);r.w32(EVENT+12,src);r.w32(EVENT+40,flags);call('du_note_filter',EVENT);assert not r.r32(s['du_pending'])
print('PASS due-note filter pulses; constructor, note-offs, suppressed notes and trigless locks never pulse',flush=True)
# Entree complete voix : arguments, registres et SR rejoues au trampoline natif.
regs=[C.UC_M68K_REG_D0+i for i in range(8)]+[C.UC_M68K_REG_A0+i for i in range(7)];values=[0x12340000+i for i in range(15)];seen=[]
for reg,value in zip(regs,values):u.reg_write(reg,value)
u.reg_write(C.UC_M68K_REG_SR,0x2505)
def native_voice(args):
 assert list(args[:4])==[0x80001858,0x92000000,17,0]
 assert [u.reg_read(reg) for reg in regs]==values
 assert u.reg_read(C.UC_M68K_REG_SR)==0x2505
 seen.append(1);return 0
bind(s['du_native_voice'],native_voice);call(0x400a7d4a,0x80001858,0x92000000,17,0);assert seen and r.r32(s['du_pending'])==1
u.reg_write(C.UC_M68K_REG_SR,0x2000)
print('PASS real voice-entry wrapper preserves all live registers, arguments and SR before native continuation',flush=True)
# Cout maximal borne : six sources vers toutes les autres, mid/side presents.
setstate(a);call('du_voice_triggers',63);refill();counts[0]=0;h=u.hook_add(UC_HOOK_CODE,lambda *args:counts.__setitem__(0,counts[0]+1));call('du_process');u.hook_del(h)
assert counts[0]<14000,counts[0]
print('PASS six-source six-target stereo ramp cost:',counts[0],'emulated instructions; not a hardware CPU percentage',flush=True)
assert m['fx_menu']['symbols']['fx_hot_end']<=d['code']
assert d['end']<=p['bss']<p['symbols']['fxp_end']<m['fundamentals']['code']
assert m['private_retrosyn']['end']<=m['fx_menu']['symbols']['gate_predelay_ring']<m['fx_menu']['symbols']['gate_buffer_end']<=m['wave_starter']['custom_buffer']
print('PASS predelay/Sidechain/pattern-state/WAVE memory ranges disjoint',flush=True)
(R/'output/firmware/fxd-restart-fixture.bin').write_bytes(disk[9]);(R/'output/firmware/fxd-restart-expected.json').write_text(json.dumps([a,b]))
print('SAVED122restart fixture',flush=True)
