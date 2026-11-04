"""Preuve UI Wizard : DATA borne, releases, delegation et pixels de pan."""
from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE
import argparse
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,default=ROOT.parent/'wizard-pan371/proof-build');p.add_argument('--capture',type=Path);a=p.parse_args();b=a.capture or a.build;m=json.loads((a.build/'BUILD.json').read_text());s=m['wizard_pan371']['symbols'];r=Rig((b/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(b/'runtime.bin').read_bytes())
view,event,params,canvas,fb=0x93020000,0x93021000,0x93022000,0x93023000,0x93024000
state=dict(lane=0,func=0,popup=0);delegated=[];labels=[]
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
bind(s['sx_track'],lambda a:state['lane']);bind(s['ws_params'],lambda a:params+128*a[0]);bind(s['ws_previous_key'],lambda a:delegated.append(a[:2]) or 17);bind(s['ws_previous_draw'],lambda a:0)
bind(0x4007faf4,lambda a:state['func']);bind(0x400cf9a8,lambda a:0x93025000)
for a in (0x4006b704,0x4006b736,0x4006bb18):bind(a,lambda a:state['popup'])
bind(0x40072260,lambda a:0);bind(0x40072080,lambda a:0);bind(0x40071a04,lambda a:labels.append(r.string(a[6])) or 0)
bind(0x40076bee,lambda a:0)
bind(0x40000e6e,lambda a:u.mem_write(a[0],b'T1\0') or 0)
r.w32(view,0x400ffe20);r.w32(view+284,0);r.w32(canvas+12,2);r.w32(canvas+16,fb)
for t in range(6):u.mem_write(params+128*t+18,struct.pack('>H',6<<8))
def key(k=32,flags=1):
 u.mem_write(event,struct.pack('>6I',0x400fc20c,0,1,k,flags,0));return r.call('ws_key',view,event)
assert key()==1 and r.r32(s['ws_pan_mode'])==1
assert key()==1 and r.r32(s['ws_pan_mode'])==1
assert key(flags=16)==1
assert key()==1 and r.r32(s['ws_pan_mode'])==0;key(flags=16)
for attr in ('func','popup'):
 state[attr]=1;assert key()==17;state[attr]=0
assert key(10)==17
u.mem_write(params+18,b'\0\0');assert key()==17;u.mem_write(params+18,struct.pack('>H',6<<8))
r.w32(view+284,1);assert key()==17;r.w32(view+284,0)
for t in range(6):
 state['lane']=t;before=r.r32(s['ws_pan_mode']);assert key()==1;assert r.r32(s['ws_pan_mode'])==before^(1<<t);key(flags=16)
state['lane']=0;r.w32(s['ws_pan_mode'],1);renders=[]
for value in (0,64,127):
 u.mem_write(params+44,struct.pack('>H',value<<8));labels.clear();r.call('ws_draw',view,canvas);assert 'L' in labels and 'R' in labels;renders.append(bytes(u.mem_read(fb,1024)))
assert len(set(renders))==3
def lit(raw,x,y):
 yy=63-y;word=struct.unpack_from('>I',raw,4*(x*2+(yy>>5)))[0]
 return bool(word&(1<<(31-(yy&31))))
# Interieurs des sept blocs : centre plein, extension symetrique et cadres vides.
for raw,expected in zip(renders,((1,1,1,1,0,0,0),(0,0,0,1,0,0,0),(0,0,0,1,1,1,1))):
 assert tuple(int(lit(raw,33+6*i,59)) for i in range(7))==expected
 assert all(lit(raw,32+6*i,59) for i in range(7))
# Le centre est exclusivement64 : meme un seul cran remplit le cote concerne.
for value,expected in ((63,(0,0,1,1,0,0,0)),(65,(0,0,0,1,1,0,0))):
 u.mem_write(params+44,struct.pack('>H',value<<8));r.call('ws_draw',view,canvas)
 raw=bytes(u.mem_read(fb,1024))
 assert tuple(int(lit(raw,33+6*i,59)) for i in range(7))==expected
u.mem_map(0x80000000,0x20000);r.w32(0x40a7883c,1)
for value,expected in zip((0,64,127),renders):
 u.mem_write(params+44,struct.pack('>H',(127-value)<<8));u.mem_write(0x8000100c+14+44,struct.pack('>H',value<<8));r.call('ws_draw',view,canvas)
 assert bytes(u.mem_read(fb,1024))==expected
r.w32(0x40a7883c,0)

if 'native_input' in m['wizard_pan371']:
 # Le vrai bus global a UN argument ; le test de la vue native seule
 # ne prouvait pas que DATA arrivait jusque la sur le materiel.
 old=[];bind(s['ws_previous_model_key'],lambda a:old.append(a[0]) or 19)
 app=0x41008000;head=app+84;r.w32(0x40fe4178,app);r.w32(head,head)
 bind(0x400cf866,lambda a:0)
 r.w32(s['ws_cpu_open'],0);r.w32(s['ws_mod_menu'],0)
 state.update(lane=0,func=0,popup=0);r.w32(s['ws_pan_mode'],0);r.call('ws_draw',view,canvas)
 entry=m['wizard_pan371']['native_input']
 def native(code=32,flags=1):
  u.mem_write(event,struct.pack('>6I',0x400fc20c,0,1,code,flags,0));return r.call(entry,event)
 assert native()==1 and r.r32(s['ws_pan_mode'])==1
 assert native(flags=9)==1 and r.r32(s['ws_pan_mode'])==1
 assert native(flags=16)==1
 for field in ('ws_cpu_open','ws_mod_menu'):
  r.w32(s[field],1);assert native()==19;r.w32(s[field],0)
 assert native(10)==19
 # Le RTTI du vrai type de fenetre peut pointer une chaine non alignee.
 node=app+0x100;overlay=app+0x200;vt=app+0x400;ti=app+0x500;name=app+0x601
 r.w32(head,node);r.w32(node,head);r.w32(node+8,overlay);r.w32(overlay,vt);r.w32(vt-4,ti);r.w32(ti+4,name);u.mem_write(name,b'17PresetBrowserView\0')
 assert native()==19;r.w32(head,head)
 r.w32(head,node)
 for upgrade in (0x40111104,0x40111544,0x40111054):r.w32(overlay,upgrade);assert native()==19
 r.w32(head,head)
 bind(s['ws_previous_draw'],lambda a:1);r.call('ws_draw',view,canvas);assert native()==19
 bind(s['ws_previous_draw'],lambda a:0);r.call('ws_draw',view,canvas);assert native()==1 and r.r32(s['ws_pan_mode'])==0;native(flags=16)
 calls=[];bind(s['ws_previous_controller_key'],lambda a:calls.append(a[:2]) or 23)
 for opener in (4,5,8,13,15):
  r.call('ws_draw',view,canvas);u.mem_write(event,struct.pack('>6I',0x400fc20c,0,1,opener,1,0))
  assert r.call(m['wizard_pan371']['controller_input'],app+64,event)==23 and calls[-1]==(app+64,event)
  # Aucune nouvelle frame sous le navigateur : DATA doit rester delegue.
  assert native()==19
 r.call('ws_draw',view,canvas);assert native()==1;native(flags=16)
 print('PASS actual one-argument Model-TG input path; CPU/menu/browser priority and native delegation')

(b/'ui-proof.json').write_text(json.dumps(dict(toggle_per_track=True,paired_release=True,repeat_safe=True,other_screens_and_keys_delegate=True,pan_0_64_127_distinct=True,audio_hooks=False,hardware_tested=False),indent=2))
print('PASS Wizard DATA pan: six track toggles, paired releases, native delegation and distinct L/C/R pixels')
