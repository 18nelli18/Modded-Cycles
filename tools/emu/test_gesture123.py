"""123 : gestes natifs repetes, protection releases et routage de gain."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT,RAW,OBJ
from unicorn import UC_HOOK_CODE,m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v123';stem='staging/all-features-polivoks-cpu-trim-test-'+v;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());sy=m['symbols'];sc=m['scramble_mask']['original'];wm=m['gesture_swap'];r,s,held,log,files,key,turn,data,bind=fixture(stem)
edit=0x931a0000;bind(0x400cf9a8,lambda a:edit);bind(0x40012412,lambda a:0)
steps=[];runs=[];held_steps=[False]
bind(sc['sc_steps_toggle'],lambda a:steps.append(1) or int(held_steps[0]));bind(sc['sc_run'],lambda a:runs.append(1) or 1)
def key(code,flags=1):
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,code,flags,127));return r.call(sy['wf_key'],EVENT)
def close():key(12);key(12,16)
for reverse in (False,True):
 for repeated in (False,True):
  n=len(runs);key(13);key(2);assert not r.r32(sy['menu']) and len(runs)==n
  if repeated:key(2,9)
  if reverse:key(13,0);key(2,16)
  else:key(2,16);key(13,0)
  assert r.r32(sy['menu']) and len(runs)==n
  key(2,16);assert len(runs)==n
  key(32,16);assert r.r32(sy['editing']);close();assert not r.r32(sy['menu'])
  assert not r.r32(sy['settings']) and not r.r32(sy['track_owned']) and not r.r32(sy['pending'])
print('PASS short combo opens menu only, DATA/BACK work, both release orders and repeats leave no held/pending state',flush=True)
for reverse in (False,True):
 for longflags in (33,34):
  n=len(runs);key(13);key(2);key(2,9);key(2,longflags);assert len(runs)==n+1 and not r.r32(sy['menu'])
  key(2,longflags);key(2,longflags);assert len(runs)==n+1
  if reverse:key(13,0);key(2,16)
  else:key(2,16);key(13,0)
  assert len(runs)==n+1 and not r.r32(sy['menu']) and not r.r32(sc['sc_taken'])
print('PASS native hold/release long flags Scramble once only; repeats and either key release never open menu or Scramble twice',flush=True)
held_steps[0]=True
for long in (False,True):
 n=len(runs);before=len(steps);key(13);key(2)
 if long:key(2,33)
 key(2,16);key(13,0);assert len(steps)==before+1 and len(runs)==n and not r.r32(sy['menu'])
held_steps[0]=False
print('PASS held-step tap and hold use the step marker without randomizing base sound or opening menu',flush=True)
# Execution reelle du marqueur, sans remplacer son implementation.
r,s,held,log,files,oldkey,turn,data,bind=fixture(stem);bind(0x400cf9a8,lambda a:edit);bind(0x40012412,lambda a:0)
bind(sc['sc_run'],lambda a:runs.append(1) or 1)
r.w32(r.r32(OBJ)+60,0x400d63ce)
r.u.mem_write(edit,bytes(512));r.w32(edit+352,1);r.u.mem_write(RAW,bytes(722));r.u.mem_write(RAW,struct.pack('>H',513));r.u.mem_write(RAW+713,struct.pack('>H',64));r.w32(edit+92,1)
for expected in (577,513):
 key(13);key(2);key(2,16);key(13,0);assert struct.unpack('>H',r.u.mem_read(RAW,2))[0]==expected;assert not r.r32(sy['menu'])
assert len(runs)==n
print('PASS actual native step setters toggle Scramble mark on/off and consume held-step release',flush=True)
f=m['fundamentals'];t=m['tiny_extra'];table=t['data'];count=t['machine_count']
assert r.r32(table+4*(count*2+16))==f['elder_render_original']
assert r.r32(table+4*(count*2+19))==f['symbols']['shadow_gain_render']
revision=int(v[1:].removesuffix('adult'))
assert f['elder_gain_db']==0 and f['shadow_gain_db']==(12.0412 if revision>=124 else 6.0206)
assert m['sidechain']['menu_label']==('S.Chn' if revision>=125 else 'S.Chain')
assert m['fx_project']['code']+m['fx_project']['code_bytes']<=wm['code']<wm['end']<0x4684f000
print('PASS native render table: Elder original, Shadow gain wrapper only; S.Chain label and disjoint UI code',flush=True)
