"""121 exact approuve : activation native, padding, save/load et copies FX."""
from pathlib import Path
import sys,json,struct,zlib,os
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from boot_candidate import boot
from test_seq_gen_menu import Rig,OBJ,VT,STACK,STOP
from unicorn import UC_HOOK_CODE,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v121';stem='all-features-polivoks-cpu-trim-test-'+v;S=Path(os.environ.get('MC_TEST_STAGING_DIR',R/'output/firmware/staging'))
m=json.loads((S/(stem+'.json')).read_text());meta=m['fx_project'];s=meta['symbols'];fx=m['fx_menu']['symbols'];im,mem=boot(S/(stem+'.syx'))
r=Rig(im,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
for at,b in mem:u.mem_map(at,len(b));u.mem_write(at,b)
u.mem_map(0xfc070000,0x1000)
RAW=0x41400000;SER=0x41800000;OTHER=0x41c00000;CB=0x93015000;CLIP=0x93040000;STRIDE=30710;SIZE=0x210404
r.w32(VT+40,0x400d3af6);r.w32(OBJ+16,RAW);r.w32(0x40fe4228,OBJ)
def forbidden(a):raise AssertionError('constructing singleton called')
r.stubs[0x400cf866]=forbidden
def call(fn,*args):
 if isinstance(fn,str):fn=s[fn]
 sp=STACK-0x400;u.mem_write(sp,struct.pack('>I'+'I'*len(args),STOP,*args));u.reg_write(C.UC_M68K_REG_A7,sp)
 u.emu_start(fn,STOP,count=250_000_000)
 assert u.reg_read(C.UC_M68K_REG_PC)==STOP,hex(u.reg_read(C.UC_M68K_REG_PC))
 assert u.reg_read(C.UC_M68K_REG_A7)==sp+4
 return u.reg_read(C.UC_M68K_REG_D0)
def stub(at,fn):
 fresh=at not in r.stubs;r.stubs[at]=fn
 if fresh:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
stub(fx['fx_previous_draw'],lambda a:0x12345678);stub(0x400d0a10,lambda a:1);stub(0x4007bc5e,lambda a:0xffffffff)
def state():return [r.r32(at) for at in meta['field_addresses']]
def setstate(values):
 for at,n in zip(meta['field_addresses'],values):r.w32(at,n)
def activate(i):
 sp=STACK-0x400;u.mem_write(sp,struct.pack('>I',STOP));u.reg_write(C.UC_M68K_REG_A7,sp);u.reg_write(C.UC_M68K_REG_A2,RAW+28+i*STRIDE)
 regs=[C.UC_M68K_REG_D0,C.UC_M68K_REG_D1,C.UC_M68K_REG_A0,C.UC_M68K_REG_A1]
 for j,reg in enumerate(regs):u.reg_write(reg,0x13370000+j)
 sr=u.reg_read(C.UC_M68K_REG_SR);u.emu_start(0x40055c5c,0x40055c62,count=1_000_000)
 assert u.reg_read(C.UC_M68K_REG_PC)==0x40055c62 and u.reg_read(C.UC_M68K_REG_A7)==sp
 assert [u.reg_read(reg) for reg in regs]==[0x13370000+j for j in range(4)]
 assert u.reg_read(C.UC_M68K_REG_SR)&0xff00==sr&0xff00
 assert r.r32(0x40a7887c)==RAW+28+i*STRIDE
def save():
 u.mem_write(SER,b'\xa5'*SIZE);assert call(0x4005d18a,SER,RAW,0,255,CB)&255
 return bytes(u.mem_read(SER,SIZE))
def load(b):u.mem_write(SER,bytes(b));assert call(0x4005d3dc,RAW,SER,CB)&255
def prec(i):return 512+14848*i+0x39d0
u.mem_write(CB,bytes(16));call(0x40061738,RAW);call('fxp_sync');activate(0);defaults=meta['defaults'];assert state()==defaults
a=[(17+7*i)%128 for i in range(36)];a[0]=7;a[18]=1;a[20]=9
b=[(93-3*i)%128 for i in range(36)];b[0]=11;b[18]=5;b[20]=16
setstate(a);activate(1);assert state()==defaults;setstate(b);activate(0);assert state()==a
activate(1);assert state()==b;activate(95);assert state()==defaults;activate(0);assert state()==a
print('PASS actual activation hook: blank patterns default; A/B and last pattern retain independent36 fields, including sends; registers/IPL preserved',flush=True)
# Requete native pendant lecture : le pattern actif ne change pas encore.
queue=0x93017000;r.w32(queue,RAW+28+STRIDE);r.w32(queue+4,OTHER);r.w32(0x40a7883c,1);r.w32(0x40a78920,0)
call(0x40055cd6,queue,1);call('fxs_ui');assert state()==a and r.r32(0x40a7887c)==RAW+28
activate(1);assert state()==b;r.w32(0x40a7883c,0)
print('PASS native queued request leaves FX alone until actual pattern publication',flush=True)
blob=save();assert blob[0x1c0+4]==2
assert blob[prec(0)+8:prec(0)+44]==bytes(a) and blob[prec(1)+8:prec(1)+44]==bytes(b)
assert blob[prec(95):prec(95)+48]==bytes(48)
load(blob);activate(0);assert state()==a;activate(1);assert state()==b;activate(2);assert state()==defaults
print('PASS full native project codecs preserve pattern FX records; untouched slots stay blank/default',flush=True)
# Corruption d un seul record : ce pattern seulement revient aux defauts.
bad=bytearray(blob);bad[prec(0)+12]^=1;load(bad);activate(0);assert state()==defaults;activate(1);assert state()==b
print('PASS invalid per-pattern CRC defaults only that pattern',flush=True)
load(blob);activate(0)
call('fxs_copy',CLIP,RAW+28,STRIDE);call('fxs_copy',RAW+28+3*STRIDE,CLIP,STRIDE);r.w32(RAW+28+3*STRIDE+30706,3)
activate(3);assert state()==a;call(0x400615e8,RAW+28+3*STRIDE,0);assert state()==defaults
print('PASS native RawPattern copy through clipboard carries FX; native pattern initialization clears them',flush=True)
# Codecs pattern hors projet : record transporte avec le pattern seul.
activate(0);assert call(0x4005ba0a,SER,RAW+28,0)&255
assert call(0x4005b894,RAW+28+4*STRIDE,SER,4)&255;activate(4);assert state()==a
print('PASS standalone native pattern encode/decode carries FX',flush=True)
# Sauvegarde native de haut niveau ; cache et disque seuls sont simules.
cache=0x93018000;disk={}
def writer(args):disk[args[1]]=bytes(u.mem_read(SER,SIZE));return 1
for at,fn in [(0x400cfdaa,lambda a:cache),(0x4006a216,lambda a:SER),(0x4006a4d6,writer),(0x4006a3ac,lambda a:SER)]:stub(at,fn)
assert call(0x4000f762,OBJ,9,CB)&255;assert disk[9][prec(4)+8:prec(4)+44]==bytes(a)
u.mem_write(SER,disk[9]);assert call(0x4006a5a0,cache,9,RAW,CB)&255;activate(1);assert state()==b
print('PASS real Save Project and Load Project cache retain all pattern FX in the normal file',flush=True)
fixture=R/'output/firmware/fxs-restart-fixture.bin';fixture.parent.mkdir(parents=True,exist_ok=True);fixture.write_bytes(disk[9]);print('SAVED restart fixture',flush=True)
# Nouvelle instance : seuls le firmware et le projet sauvegarde sont repris.
r=Rig(im,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
for at,data in mem:u.mem_map(at,len(data));u.mem_write(at,data)
u.mem_map(0xfc070000,0x1000)
r.w32(VT+40,0x400d3af6);r.w32(OBJ+16,RAW);r.w32(0x40fe4228,OBJ)
r.stubs[0x400cf866]=forbidden
stub(fx['fx_previous_draw'],lambda args:0x12345678)
stub(0x400d0a10,lambda args:1);stub(0x4007bc5e,lambda args:0xffffffff)
u.mem_write(CB,bytes(16));call(0x40061738,RAW);load(fixture.read_bytes())
activate(1);assert state()==b
activate(0);assert state()==a
activate(2);assert state()==defaults
print('PASS fresh emulator restores per-pattern FX using only the saved native project',flush=True)
