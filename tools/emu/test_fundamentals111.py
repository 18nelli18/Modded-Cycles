"""Preuves natives : detune centiemes, sustain/release ACID et gain Elder."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
import test_wizard_playback,emac,numpy as np
from boot_candidate import boot
from test_macro_fine import FineUI
from lofi_ui import SCRATCH
from test_wizard_playback import fixtures
from mcengine import VOICE0,VSTRIDE,PARAMS
version=sys.argv[1] if len(sys.argv)>1 else 'v111';stem='staging/all-features-polivoks-cpu-trim-test-'+version;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());sy=m['fundamentals']['symbols']
im,mem=boot(R/'output/firmware'/(stem+'.syx'));lo=min(at for at,raw in mem);hi=max(at+len(raw) for at,raw in mem);buf=bytearray(hi-lo)
for at,raw in mem:buf[at-lo:at-lo+len(raw)]=raw
u=FineUI(im,(lo,bytes(buf)));u.call(0x400e7dbc);u.call(0x400ab7b8,1,count=50000000);u.hooks[m['fx_menu']['symbols']['fx_frame_prepare']]=('frame',0)
assert u.lookup(10,4,False)==u.lookup(10,4,True)==91
u.call(sy['bf_prepare']);rec=u.call(0x4004df40,91);assert u.u32(rec+80)==sy['bf_fine']
value=16384;seen=[]
for i in range(100):value=u.edit_func(91,value,256);seen.append(value)
assert value==16640 and len(set(seen))==100
for delta,expected in [(256,16387),(-256,16381),(512,16389)]:assert u.edit_func(91,16384,delta)==expected
assert u.edit_func(91,22528,256)==22528 and u.edit_func(91,10240,-256)==10240
assert u.edit_normal(91,16387,256)==16643
for value,want in [(16384,'+0.00'),(16387,'+0.01'),(16381,'-0.01'),(22528,'+24.00'),(10240,'-24.00')]:
 u.call(u.u32(rec+32),0,value,SCRATCH+0x5500);assert u.cstr(SCRATCH+0x5500)==want
raw,record,loaded=SCRATCH+0x6000,SCRATCH+0x6100,SCRATCH+0x6200
for value in [10240,16381,16387,16512,22528]:
 sound=bytearray(100);sound[38]=10;struct.pack_into('>H',sound,42,value);struct.pack_into('>H',sound,40,64<<8);struct.pack_into('>H',sound,54,64<<8)
 u.uc.mem_write(raw,bytes(sound));assert u.call(0x4005afa0,record,raw)==1;assert u.call(0x4005aecc,loaded,record)==1;assert int.from_bytes(u.uc.mem_read(loaded+42,2),'big')==value
print('PASS SY BITS: true FUNC/native setter, 100 distinct steps/semitone, bounds, decimal labels and native sound save/load',flush=True)
# Toutes les autres machines gardent les callbacks partages d origine.
for machine in [1,7,8,9,11,12,13,16,21,22]:
 u.lookup(machine,4,False)
 if u.call(sy['bf_active']):raise AssertionError(machine)
print('PASS SY BITS conditional on machine10; shared descriptor remains delegated for every other engine',flush=True)
def engine(v):
 st='staging/all-features-polivoks-cpu-trim-test-'+v;mm=json.loads((R/'output/firmware'/(st+'.json')).read_text());e=fixtures(False,127,0,[st],native_chordkeys=True,audit_count=False)[0]
 if mm.get('fundamentals'):
  d=mm['fundamentals'];e.emac.install(emac.disasm(str(R/'output/firmware'/('governor-recovery-'+v)/'fundamentals.bin'),d['code'],d['code'],d['code']+d['code_bytes']))
 return e
e=engine(version)
def rd(at):return int.from_bytes(e.uc.mem_read(at,4),'big')
for lane in range(6):e.set(lane,machine=13 if lane<2 else 17,note=48,pitch=64,color=70,shape=50,sweep=80,contour=0,decay=127 if lane==1 else 0,gate=0)
for block in range(12):
 out=e.block(3 if block==0 else 0)
 if block>1:assert rd(VOICE0+0x230)==rd(VOICE0+VSTRIDE+0x230)==0x80000000,('held envelope',block,hex(rd(VOICE0+0x230)))
assert rd(sy['trk']+52)!=rd(sy['trk']+136+52),'filter DECAY must change filter envelope'
start=abs(int.from_bytes(e.uc.mem_read(VOICE0+0x230,4),'big',signed=True))
for block in range(24):e.block(0,3 if block==0 else 0)
end=abs(int.from_bytes(e.uc.mem_read(VOICE0+0x230,4),'big',signed=True));assert end<start//1000,('release',start,end)
assert rd(VOICE0+0x230)==rd(VOICE0+VSTRIDE+0x230),'release must not depend on filter DECAY'
print('PASS ACID: DECAY0/127 hold the same amplitude, different filter envelopes; note-off release independent of DECAY and stock Gate switch',flush=True)
for velocity,want in [(96,0),(97,1057),(127,32767)]:
 for off,val in [(0x2c,0),(0x34,1),(0x38,0),(0x3c,0)]:e.uc.mem_write(VOICE0+off,struct.pack('>I',val))
 e.uc.mem_write(0x40fe4cd0,struct.pack('>h',velocity));e.call(sy['acid_update'],48<<16,VOICE0,PARAMS+14)
 assert rd(sy['trk']+124)==want,(velocity,rd(sy['trk']+124));assert rd(sy['trk']+92)==want
print('PASS ACID: native velocity96 unaccented,97..127 progressive accent reaches filter/gain inputs',flush=True)
old=engine('v105retro');new=engine(version)
for lane in range(6):
 for eng in [old,new]:eng.set(lane,machine=16,note=36+lane*7,pitch=64,color=lane*24,shape=lane*20,sweep=0,contour=0,decay=100,gate=0)
peak=0
for block in range(10):
 a=old.block(63 if block==0 else 0);b=new.block(63 if block==0 else 0);expected=np.clip(a*2,-2147483648,2147483647)
 assert np.max(np.abs(b-expected))<=1,('Elder gain/common gain rounding',block,np.max(np.abs(b-expected)))
 peak=max(peak,int(np.max(np.abs(b))))
assert peak>1000000 and not old.unmapped and not new.unmapped
print('PASS Elder: six native voices, 2x PCM within1LSB of common gain rounding, bounded peaks; tone/envelopes unchanged',peak,flush=True)
