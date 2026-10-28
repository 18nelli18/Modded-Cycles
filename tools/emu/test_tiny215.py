"""52 moteurs natifs : neutralite, sustain, relachement compare au natif et PUNCH.
Comparer le relachement a chaque modele natif, plutot que supposer un
coefficient universel. Le cache doit remettre la valeur avant l'update natif.
"""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from unicorn import UC_HOOK_CODE,m68k_const as C
stem='staging/all-features-polivoks-cpu-trim-test-v215';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['tiny_sustain']['symbols'];stride=m['tiny_sustain']['state_stride']
r,fx,held,log,files,key,turn,data,bind=fixture(stem);u=r.u;u.mem_map(0x93400000,0x400000);param=0x93400000;out=0x93401000
def params(model,gate,punch,decay=60):
 a=bytearray(66)
 for off,value in ((18,18<<8),(20,64<<8),(22,64<<8),(24,model<<8),(26,64<<8),(28,64<<8),(30,punch<<8),(32,gate<<8),(34,64<<8),(36,decay<<8)):struct.pack_into('>H',a,off,value)
 u.mem_write(param,bytes(a))
def reset(lane=0):
 v=0x42308828+796*lane;core=0x46780000+2108*lane;u.mem_write(v,bytes(796));u.mem_write(core,bytes(2108));u.mem_write(s['states']+stride*lane,bytes(stride));return v,core
def block(fn,v,trig=False,release=False):
 r.w32(v+56,int(trig));r.w32(v+60,int(release));r.call(fn,60<<16,v,param);r.call(0x4677c2f2,out,v);return tuple(struct.unpack('>32i',u.mem_read(out,128)))
late=[];native_release=[];held_models=0
for model in range(52):
 params(model,0,0);v,core=reset();a=[block(s['tn_old_update'],v,b==0) for b in range(8)]
 v,core=reset();b=[block(0x4677c000,v,i==0) for i in range(8)];assert a==b,('neutral PCM',model)
 params(model,1,0);v,core=reset()
 for i in range(140):block(s['tn_old_update'],v,i==0)
 block(s['tn_old_update'],v,release=True);release_ref=r.r32(core+16);native_release.append(release_ref)
 v,core=reset();pk=end=0;forced=False
 for i in range(140):
  samples=block(0x4677c000,v,i==0);pk=max(pk,max(map(abs,samples)))
  if i>=100:end=max(end,max(map(abs,samples)))
  if r.r32(s['states']+12):assert r.r32(core+16)==65536,('held coefficient',model,i);forced=True
 assert pk,('silent',model);late.append(end);held_models+=forced
 block(0x4677c000,v,release=True)
 assert r.r32(core+16)==release_ref,('release differs from native coefficient',model,r.r32(core+16),release_ref)
 assert r.r32(s['states'])==0 and r.r32(s['states']+12)==0,('release latch',model)
 # Couper GATE pendant une note doit aussi remettre le coefficient natif.
 params(model,1,0);v,core=reset();block(0x4677c000,v,True);params(model,0,0);block(0x4677c000,v);assert r.r32(s['states']+12)==0
 if model%8==7 or model==51:print('PASS models0..'+str(model)+': neutral PCM, held gate, native release and Gate-off',flush=True)
print('PASS all52 models audible; Gate/Punch off PCM exact; release restores each native model coefficient, including model44',flush=True)
notes=[]
def note(uc,pc,size,data):sp=uc.reg_read(C.UC_M68K_REG_A7);notes.append(r.r32(sp+4))
h=u.hook_add(UC_HOOK_CODE,note,begin=s['tn_old_update'],end=s['tn_old_update'])
for model in range(52):
 params(model,1,1);v,core=reset();notes.clear();snap=12<<16
 for i in range(8):
  block(0x4677c000,v,i==0);assert notes[-1]==(60<<16)+snap,(model,i,notes[-1],snap);snap=snap*7//8
 params(model,1,0);block(0x4677c000,v);assert notes[-1]==60<<16
u.hook_del(h)
print('PASS PUNCH on all52 models: 12-semitone attack, native pitch input, 7/8 decay and immediate Punch-off',flush=True)
for lane in range(6):
 params(35,1,1);v,core=reset(lane);block(0x4677c000,v,True);assert r.r32(s['states']+stride*lane)==1
for lane in range(6):
 params(35,1,1);v=0x42308828+796*lane;block(0x4677c000,v,release=True)
 assert [r.r32(s['states']+stride*t) for t in range(6)]==[0 if t<=lane else 1 for t in range(6)]
print('PASS all six track states isolated, no held-note latch survives its release',flush=True)
Path('tiny215-result.json').write_text(json.dumps(dict(sha256=m['sha256'],models=52,neutral_pcm_exact=True,gate_models=held_models,late_peaks=late,native_release_coefficients=native_release,release_matches_native=True,punch_all_models=True,six_tracks_isolated=True,hardware_tested=False),indent=2)+'\n')

for model in (14,49,50,51):
 for gate in (0,1):
  params(model,gate,0);v,core=reset();last=[]
  for i in range(1800):
   samples=block(0x4677c000,v,i==0)
   if i>=1700:last.append(samples)
  peak=max(abs(x) for b in last for x in b)
  assert bool(peak)==bool(gate),(model,gate,peak)
  if gate:
   assert len(set(last))>1,('frozen waveform',model)
   for i in range(800):samples=block(0x4677c000,v,release=i==0)
   assert max(map(abs,samples))==0,('stuck after release',model)
 print('PASS model'+str(model)+': long audible sustain, moving waveform, Gate off natural decay, note-off silence',flush=True)
