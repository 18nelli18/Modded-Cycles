"""Vrai parcours ViewManager : touches musicales livrees sous chaque menu LFO."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
v=sys.argv[1] if len(sys.argv)>1 else 'v215';stem='staging/all-features-polivoks-cpu-trim-test-'+v
m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());mx=m['four_lfos']['symbols'];a=m['four_lfos']['aliases']
r,fx,held,log,files,key,turn,data,bind=fixture(stem);u=r.u;u.mem_map(0x93600000,0x200000)
manager=0x93600000;sentinel=manager+20;bottomnode=manager+0x100;topnode=manager+0x120;menu=manager+0x200;menuvt=manager+0x400;background=manager+0x600;backgroundvt=manager+0x800
event=manager+0x1000;recv=manager+0x1100
r.w32(sentinel,bottomnode);r.w32(sentinel+4,topnode)
for node,nxt,prev,view in ((bottomnode,topnode,sentinel,background),(topnode,sentinel,bottomnode,menu)):
 r.w32(node,nxt);r.w32(node+4,prev);r.w32(node+8,view)
r.w32(menu,menuvt);r.w32(menuvt+8,mx['mx_key']);r.w32(background,backgroundvt);r.w32(backgroundvt+8,recv)
for pc in (0x400e8684,0x400d08ce,0x40076f2a,0x400802ec):bind(pc,lambda args:0)
seen=[];bind(recv,lambda args:seen.append(tuple(struct.unpack('>6I',u.mem_read(args[1],24)))) or 1)
musical=(1,2,3,4,5,6,7,9,10,11,14,15,*range(16,32))
checks=0
for bank in range(3):
 r.w32(mx['mx_selected'],bank)
 for code in musical:
  for flags in (0,1,3,16,33,34):
   payload=(0x400fc20c,123,456,code,flags,789);u.mem_write(event,struct.pack('>6I',*payload));seen.clear()
   r.call(0x40077720,manager,event)
   if v=='v213':
    if code in (1,3,9):assert not seen
    continue
   assert seen==[payload],(bank,code,flags,seen)
   assert r.r32(sentinel+4)==topnode and r.r32(topnode+8)==menu
   checks+=1
if v=='v213':
 print('PASS native ViewManager reproduces swallowed FUNC/PATTERN/RECORD in v213',flush=True);raise SystemExit(0)
print('PASS',checks,'native ViewManager routes: all three LFO menus pass pattern/transport/record/modifiers/trigs, preserving complete events and open menu',flush=True)
wf=m['lfo_workflow'];sy=wf['symbols'];old={**sy,**wf['aliases']};encoder_seen=[]
bind(old['wf_old_encoder'],lambda args:encoder_seen.append(tuple(args[:2])) or 77)
for heldtrig in range(16,32):
 held.clear();held.add(heldtrig)
 for knob in range(1,18):
  u.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,knob,0,0));encoder_seen.clear();assert r.call(sy['wf_encoder'],menu,event)==0 and not encoder_seen
 # DATA click appartient aussi au trig pendant son maintien.
 u.mem_write(event,struct.pack('>6I',0x400fc20c,0,0,32,16,0));assert r.call(sy['wf_key'],menu,event)==0
 held.add(8);encoder_seen.clear();assert r.call(sy['wf_encoder'],menu,event)==77 and encoder_seen
held.clear();encoder_seen.clear();assert r.call(sy['wf_encoder'],menu,event)==77 and encoder_seen
print('PASS all16 held trigs pass DATA and17 encoder events for native edits; ordinary LFO editing and LFO-held quick assign retain their original handler',flush=True)
# Le clic menu et le cycle LFO restent propres a la vue.
r.w32(a['lf2p_row'],5);r.w32(a['lf2p_edit'],0);u.mem_write(event,struct.pack('>6I',0x400fc20c,0,0,32,16,0));assert r.call(sy['wf_key'],menu,event)==1 and r.r32(a['lf2p_edit'])==1
r.w32(mx['mx_count'],4);r.w32(mx['mx_selected'],0);r.w32(a['lf2p_assigned'],0);u.mem_write(event,struct.pack('>6I',0x400fc20c,0,0,8,0,0));assert r.call(sy['wf_key'],menu,event)==1 and r.r32(mx['mx_selected'])==1
print('PASS menu DATA editing and LFO2-to-LFO3 navigation remain available',flush=True)
