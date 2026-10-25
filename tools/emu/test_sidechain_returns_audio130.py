"""130 : mixeur natif et retours, ancien DSP exact lorsque les cases sont Off."""
from pathlib import Path
import sys,subprocess,struct,json
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
original_run=subprocess.run
def local_run(args,*a,**kw):
 if args[0]=='m68k-linux-gnu-objdump':args=[str(R.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe'),*args[1:]]
 return original_run(args,*a,**kw)
subprocess.run=local_run
from test_fx_menu_audio import fixture
from test_fx_combo_cpu import prep
from test_delay_crush_sends import run
from test_new_delays import native_rig
from test_vinyl_dust import IN,OUT
from collections import deque
from unicorn import UC_HOOK_CODE,m68k_const as C
old='staging/all-features-polivoks-cpu-trim-test-v129'
new='staging/all-features-polivoks-cpu-trim-test-'+(sys.argv[1] if len(sys.argv)>1 else 'v130')
if new.endswith('adult'):old+='adult'
def config(f,targets):
 e,m,sy,g=f;d=m['sidechain']['symbols'];e.uc.mem_write(d['du_config'],bytes([0,15,0,3,6]+[0,9,0,0,6]*5))
 e.uc.mem_write(d['du_fx'],bytes([targets,0,0,0,0,0]));e.call(d['du_reset']);return d
for rev,delay in ([] if '--targets-only' in sys.argv else [(x,0) for x in (0,1,2,3,7,8,9,10,11)]+[(0,x) for x in (1,2,5,9,10,11)]):
 fs=[fixture(stem,0) for stem in (old,new)]
 for f in fs:
  s=prep(f,rev,delay,100,21,True)
  if delay>=5:
   for key,v in [('cr_mode',delay),('nd_active',delay),('nd_ready',1),('nd_gain',256),('nd_prior',256)]:f[0].uc.mem_write(s[key],struct.pack('>I',v))
 for b in range(12):
  got=[run(f,1) for f in fs]
  assert all(got[0][k]==got[1][k] for k in ('post','wet','rev_wet','send','rev_input')),(rev,delay,b)
 print('PASS native mixer exact129 with FX targets Off: Rev',rev,'Del',delay,flush=True)
# Le callback commun doit agir apres chaque type reverb, y compris la
# correction Vinyl, sans modifier ni entree ni etat du moteur lui-meme.
for rev in (0,1,2,3,7,8,9,10,11):
 fs=[fixture(new,i) for i in (0,1)]
 for f in fs:prep(f,rev,0,100,21,True)
 ds=[config(f,i) for i,f in enumerate(fs)]
 seen=[{},{}]
 for index,(f,d) in enumerate(zip(fs,ds)):
  def capture(uc,pc,size,unused,index=index,d=d):
   sp=uc.reg_read(C.UC_M68K_REG_A7);out,slot=struct.unpack('>II',uc.mem_read(sp+4,8))
   before,after=[int.from_bytes(uc.mem_read(d[name]+4*slot,4),'big') for name in ('du_fx_gain','du_fx_goal')]
   seen[index][slot]=(before,after,struct.unpack('>64i',uc.mem_read(out,256)))
  f[0].uc.hook_add(UC_HOOK_CODE,capture,begin=d['du_return'],end=d['du_return'])
 for b in range(20):
  for f,d in zip(fs,ds):f[0].call(d['du_voice_triggers'],1)
  got=[run(f,1) for f in fs]
  assert got[0]['send']==got[1]['send'] and got[0]['rev_input']==got[1]['rev_input']
  assert got[0]['wet']==got[1]['wet']
  if rev==3:
   raw=[struct.unpack('>64i',f[0].uc.mem_read(f[1]['fx_menu']['symbols']['correction'],256)) for f in fs]
  else:raw=[struct.unpack('>64i',g['rev_wet']) for g in got]
  before,after,pre=seen[1][0]
  expected=tuple(x*(before+((after-before)*(i//2+1)>>5))>>16 for i,x in enumerate(pre))
  assert raw[1]==expected,(rev,b,before,after,next(((i,a,z) for i,(a,z) in enumerate(zip(raw[1],expected)) if a!=z),None))
  assert pre==seen[0][0][2],('Reverb internal tail/input changed',rev,b)
 print('PASS native Rev return only ducked, dry/send/Delay untouched: mode',rev,flush=True)
# Vrai delay et DMA simule : le gain wet ne rentre jamais dans la boucle.
for mode in (0,1,2,5,9,10,11):
 fs=[native_rig(new) for _ in range(2)];rings=[deque([bytes(256)]*8) for _ in fs]
 for index,(r,s,m,mac) in enumerate(fs):
  r.s.update(m['sidechain']['symbols']);u=r.u
  u.mem_write(r.s['du_config'],bytes([0,15,0,3,6]+[0,9,0,0,6]*5));u.mem_write(r.s['du_fx'],bytes([2 if index else 0,0,0,0,0,0]));r.call('du_reset')
  for key,val in [('cr_mode',mode),('nd_active',mode if mode>=5 else 0),('nd_ready',1),('nd_gain',256),('nd_prior',256)]:r.w32(s[key],val)
  u.mem_write(IN+1024,struct.pack('>hh',11000,12000))
 for b in range(48):
  samples=[];feedback=[]
  for index,(r,s,m,mac) in enumerate(fs):
   work=r.r32(0x8000b570);raw=rings[index].popleft();bank=raw+raw[-8:]*2;r.u.mem_write(work,bank+bank)
   sig=[180000000,-110000000]*32 if b<4 else [0]*64;r.u.mem_write(IN,struct.pack('>64i',*sig))
   r.call('du_voice_triggers',1);r.call('du_process');r.call('fx_dfx',OUT,IN,IN+1024)
   feedback.append(bytes(r.u.mem_read(work,256)));rings[index].append(feedback[-1]);samples.append(struct.unpack('>64i',r.u.mem_read(OUT,256)))
   assert mac.macsr==0xa0 and all(mac.physical(k)==0 for k in range(4))
  assert feedback[0]==feedback[1],('feedback',mode,b)
  if b:assert samples[1]==tuple(x>>16 for x in samples[0]),('wet',mode,b)
 print('PASS native Del return only ducked, feedback exact and EMAC restored: mode',mode,flush=True)
print('PASS full native mixer/FX callback integration; no hardware CPU percentage claimed',flush=True)
