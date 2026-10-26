"""157 : arborescence reelle, tous setters et retour des sous-menus."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v157';stem='staging/all-features-polivoks-cpu-trim-test-'+v;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());s=m['groove_strum']['symbols'];b=m['symbols'];q=m['mute_quant']['symbols'];du=m['sidechain']['symbols'];sc=m['scramble_mask']['symbols']
r,sy,h,log,files,key,turn,data,bind=fixture(stem);r.s.update(s);u=r.u;u.reg_write(C.UC_M68K_REG_SR,0x2700)
def event(c,f):u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,c,f,0));return r.call('gc_key',EVENT)
def click():event(32,1);event(32,16)
def back():event(12,1);event(12,16)
def enc(d):r.delta=d;u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,100,1,0,0));r.call('gc_encoder',EVENT)
r.w32(b['menu'],1);enc(1);assert r.r32(s['gc_level'])==0 and r.r32(s['gc_tree_cursor'])==1
enc(-1);click();assert r.r32(s['gc_level'])==1
for i,old in enumerate([0,1,2,3,4,5,8,9]):
 assert r.r32(b['row'])==old and r.r32(s['gc_tree_cursor'])==i
 if i<6:
  click();assert r.call(b['wf_menu_edit']);enc(1);back();assert not r.call(b['wf_menu_edit']) and r.r32(b['menu'])
 elif i==6:
  click();assert r.r32(q['mq_page']);click();assert r.r32(q['mq_enabled']);back();assert not r.r32(q['mq_page']) and r.r32(s['gc_level'])==1
 else:
  click();assert r.r32(s['gc_page'])==1;click();enc(1);assert u.mem_read(s['gc_groove'],1)==b'\x01';back();enc(1);assert r.r32(s['gc_row'])==4;click();enc(-10);assert u.mem_read(s['gc_strum'],1)==b'\xf6';back();back();assert not r.r32(s['gc_page'])
 enc(1)
print('PASS Global all eight entries, historical setters, nested QntM/Groove and BACK',flush=True)
back();assert r.r32(s['gc_level'])==0;enc(1);click();assert r.r32(s['gc_level'])==2
for i,(old,page) in enumerate([(6,sc['sx_submenu']),(7,du['du_page']),(8,s['gc_page'])]):
 assert r.r32(b['row'])==old
 click();assert r.r32(page)
 if i<2:back()
 else:
  assert r.r32(page)==2 and r.r32(s['gc_row'])==1;enc(1);click();enc(7);assert u.mem_read(s['gc_amounts'],1)==b'\x07';back();back()
 assert not r.r32(page) and r.r32(s['gc_level'])==2
 enc(1)
print('PASS Track Scramble/Sidechain/Humanize, selected-track amount and return to category',flush=True)
back();assert r.r32(s['gc_level'])==0;back();assert not r.r32(b['menu']);r.w32(b['menu'],1);r.call(s['gc_tree_row']);enc(-1);assert r.r32(s['gc_level'])==0
print('PASS close/reopen starts at Global/Track root, release ownership retained',flush=True)
