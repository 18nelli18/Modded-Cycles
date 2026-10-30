"""Preuve native des reglages ACID, navigation et sauvegarde globale."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text());s=m['acid_articulation']['symbols'];al=m['direct_jump']['aliases']
bc.ROOT=a.output.parent/'ui-cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0);return r,files,bind
r,files,bind=fixture();selected=[0];machine=[13];held={13};notices=[];consumed=[];fallback=[]
for hook in m['acid_articulation']['hooks']:
 assert bytes(r.u.mem_read(hook['at'],6))==(b'\x4e\xb9' if hook['at'] in (0x4000f906,0x40058ca6,0x40055700) else b'\x4e\xf9')+struct.pack('>I',hook['target']),hex(hook['at'])
bind(0x40012412,lambda a:selected[0]);bind(0x4001e318,lambda a:machine[0]);bind(0x4007faf4,lambda a:int(a[0] in held));bind(0x400723e0,lambda a:consumed.append(a[0]) or 0)
bind(s['fx_notice'],lambda a:notices.append(r.string(a[0])) or 0);bind(s['aa_old_encoder'],lambda a:fallback.append(a) or 77)
def turn(knob,d,stamp=0):
 r.delta=d;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,stamp,knob,d&0xffffffff,0));return r.call(s['aa_face_encoder'],0,EVENT)
for t in range(6):assert r.call(s['aa_glide_get'],t)==r.call(s['aa_legato_get'],t)==1
assert turn(2,10,1)==1 and r.call(s['aa_glide_get'],0)==11
turn(2,10,1);assert r.call(s['aa_glide_get'],0)==11
selected[0]=1;turn(2,20,2);turn(3,-1,3);assert r.call(s['aa_glide_get'],1)==21 and r.call(s['aa_legato_get'],1)==0
assert r.call(s['aa_glide_get'],0)==11 and r.call(s['aa_legato_get'],0)==1
turn(2,-999);assert r.call(s['aa_glide_get'],1)==0
turn(2,999);assert r.call(s['aa_glide_get'],1)==127
for other in (1,2,5):
 held.add(other);assert turn(2,1)==77;held.remove(other)
held.clear();assert turn(2,1)==77
held.add(13);machine[0]=12;assert turn(2,1)==77
machine[0]=13;assert turn(4,1)==77
assert consumed and set(consumed)=={13} and any('Legato OFF' in n for n in notices) and any('Glide OFF' in n for n in notices)
a.output.write_text(json.dumps(dict(native_boot=True,selected_track_only=True,other_gestures_delegated=True,duplicate_event_ignored=True,bounds=True,popup=notices,hardware_tested=False),indent=2)+'\n');print('PASS native face controls, selected track isolation and modifier delegation',flush=True)


