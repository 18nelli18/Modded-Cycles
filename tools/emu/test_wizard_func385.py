"""Wizard : FUNC momentane, valeurs numeriques Num, delegation et pan live."""
from pathlib import Path
import sys,json,struct,argparse
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();m=json.loads((a.build/'BUILD.json').read_text());s=m['wizard_pan371']['symbols'];r=Rig((a.capture/'native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{k:hex(v) for k,v in s.items()}});u=r.u;u.mem_map(0x46700000,0x300000);u.mem_write(0x46700000,(a.capture/'runtime.bin').read_bytes());u.mem_map(0x80000000,0x20000)
view,event,params,canvas,fb=0x93020000,0x93021000,0x93022000,0x93023000,0x93024000
state=dict(lane=0,func=0,popup=0,level=64,previous=0);delegated=[];labels=[];redraw=[]
def bind(at,fn):
 if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
 r.stubs[at]=fn
bind(s['sx_track'],lambda a:state['lane']);bind(s['ws_params'],lambda a:params+128*a[0]);bind(s['ws_previous_key'],lambda a:delegated.append(('view',a[:2])) or 17);bind(s['ws_previous_model_key'],lambda a:delegated.append(('model',a[0])) or 19);bind(s['ws_previous_controller_key'],lambda a:delegated.append(('controller',a[:2])) or 23);bind(s['ws_previous_draw'],lambda a:state['previous'])
bind(0x4007faf4,lambda a:state['func'] if a[0]==1 else 0);bind(0x400cf9a8,lambda a:0x93025000)
for at in (0x4006b704,0x4006b736,0x4006bb18):bind(at,lambda a:state['popup'])
bind(0x40072260,lambda a:0);bind(0x40072080,lambda a:0);bind(0x40071a04,lambda a:labels.append(r.string(a[6])) or 0);bind(0x40076bee,lambda a:redraw.append(a[0]) or 0)
bind(0x400cf866,lambda a:0x41001000);bind(0x4000eb9c,lambda a:0x41002000);bind(0x40009c5a,lambda a:state['level']|0xabcd0000)
def fmt(a):
 f=r.string(a[1]);n=f.count('%');text=(f%tuple(a[2:2+n])) if n else f;u.mem_write(a[0],text.encode()+b'\0');return len(text)
bind(0x40000e6e,fmt)
r.w32(view,0x400ffe20);r.w32(canvas+12,2);r.w32(canvas+16,fb);r.w32(0x40fe4178,0x41008000)
for t in range(6):u.mem_write(params+128*t+18,struct.pack('>H',6<<8))
def draw(func,num,value,playing=False):
 state['func']=func;u.mem_write(s['ws_num_off'],bytes([not num]));u.mem_write(params+128*state['lane']+44,struct.pack('>H',value<<8));state['level']=value;r.w32(0x40a7883c,playing);labels.clear();assert r.call('ws_draw',view,canvas)==1;return bytes(u.mem_read(fb,1024))
for lane in range(6):
 state['lane']=lane
 for value in (0,1,63,64,65,126,127):
  draw(0,True,value);assert 'LVL '+str(value) in labels and not any(x.startswith('PAN ') for x in labels)
  draw(1,True,value);assert 'PAN '+str(value) in labels and not any(x.startswith('LVL ') for x in labels)
  draw(0,True,value);assert 'LVL '+str(value) in labels
state['lane']=0
bars=[]
for value in (0,64,127):
 bars.append(draw(1,False,value));assert 'L' in labels and 'R' in labels and not any(x.startswith('PAN ') for x in labels)
assert len(set(bars))==3
for value in (0,64,127):
 draw(0,False,value);assert not any(x.startswith(('PAN ','LVL ')) for x in labels)
# Pan p-locke du bloc audio et retour a la valeur sauvegardee a l arret.
u.mem_write(0x8000100c+14+44,struct.pack('>H',127<<8));draw(1,True,0,True);assert 'PAN 127' in labels
draw(1,True,0,False);assert 'PAN 0' in labels
# DATA n est jamais capture ; les trois voies d entree restent natives.
for key in (32,1,4,5,8,13,15):
 for flags in (1,9,16,0):
  u.mem_write(event,struct.pack('>6I',0x400fc20c,0,1,key,flags,0));assert r.call('ws_key',view,event)==17;assert r.call(m['wizard_pan371']['native_input'],event)==19;assert r.call(m['wizard_pan371']['controller_input'],0x41008040,event)==23
assert len(redraw)==4
state['popup']=1;assert r.call('ws_draw',view,canvas)==0;state['popup']=0
r.w32(view+284,1);assert r.call('ws_draw',view,canvas)==0;r.w32(view+284,0)
u.mem_write(params+18,b'\0\0');assert r.call('ws_draw',view,canvas)==0
state['previous']=7;assert r.call('ws_draw',view,canvas)==7
assert 'ws_pan_mode' not in s
proof=dict(sha256=m['sha256'],FUNC_momentary=True,DATA_delegates=True,six_tracks=True,numeric_level_and_pan=True,Num_off_graphs=True,live_pan_locks=True,UI_priority_preserved=True,hardware_tested=False)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(proof,indent=2)+'\n');print('PASS Wizard FUNC hold/release, numeric level/pan, six tracks, live p-locks, graphs and native DATA/menu delegation')
