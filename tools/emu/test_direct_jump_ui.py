"""Preference JUMP globale : menu natif, gestes, sauvegarde et cold reload."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text());j=m['direct_jump'];s=j['symbols'];g=m['groove_strum']['symbols'];al=j['aliases'];row=j['global_row']
bc.ROOT=a.output.parent/'ui-cache';realboot=bc.boot;fx.metadata=m;fx.boot=lambda path:realboot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0)
 return r,files,bind
r,files,bind=fixture()
def state(name,v):r.w32(al[name],v)
def key(code,flags=1):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(s['jp_key'],EVENT)
def turn(v):r.delta=v;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,1,0,0));return r.call(s['jp_encoder'],EVENT)
assert r.r32(j['bss'])==0
r.call(s['jp_service']);state('menu',1);state('gc_level',1);state('gc_tree_cursor',0)
for i in list(range(1,row+1))+[0]:turn(1);assert r.r32(al['gc_tree_cursor'])==i
turn(-1);assert r.r32(al['gc_tree_cursor'])==row
key(32);key(32,16);assert r.call(s['jp_edit'])==1
for d,w in [(1,1),(1,1),(-1,0),(-1,0),(1,1)]:turn(d);assert r.r32(j['bss'])==w
assert '/DirectJump.cfg' not in files
key(12);key(12,0);assert r.call(s['jp_edit'])==0
objects=[];bind(0x400423e4,lambda a:objects.append(a[0]) or 0);r.call(s['jp_draw'],0,0x93010000)
obj=objects[-1];vt=r.r32(obj);assert r.call(r.r32(vt+12),obj)==row+1;labels=[]
for i in range(row+1):
 r.u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);item=r.r32(0x931f0000);labels.append(r.string(r.r32(item+12)))
assert labels==['Pad','USB','Num','Mute','Dly','DX','QntM','Grv','LFOs','FX']+(['ACID'] if row==11 else [])+['JUMP'],labels
values=[];bind(0x40072260,lambda a:0);bind(0x40072080,lambda a:0);bind(0x40071a04,lambda a:values.append(r.string(a[6])) or 0)
for v in (0,1):r.call(s['jp_set'],v);r.call(s['jp_value'],0,0,0x93010000,122,32)
assert values==['OFF','ON']
# Les fichiers sont globaux et ecrits seulement a l'arret ; pas de reset au changement de projet.
state('menu',0);r.w32(0x40a7883c,1);r.call(s['jp_service']);assert '/DirectJump.cfg' not in files
r.w32(0x40a7883c,0);r.call(s['jp_service']);saved=files['/DirectJump.cfg'];assert len(saved)==8
rr,ff,bb=fixture();ff['/DirectJump.cfg']=saved;rr.call(s['jp_service']);assert rr.r32(j['bss'])==1
for bad in (saved[:5],saved+b'x',bytes(8),saved[:4]+bytes([2])+saved[5:]):
 rr,ff,bb=fixture();ff['/DirectJump.cfg']=bad;rr.call(s['jp_service']);assert rr.r32(j['bss'])==0
rr,ff,bb=fixture();ff['/DirectJump.cfg']=saved;rr.call(s['jp_set'],0);rr.call(s['jp_service']);assert rr.r32(j['bss'])==0
r.w32(j['code'],0x444a4d50);r.w32(j['code']+4,1);r.u.mem_write(j['code']+14,b'\0\1');r.call(s['jp_set'],0)
assert r.r32(j['code'])==r.r32(j['code']+4)==0 and bytes(r.u.mem_read(j['code']+14,2))==b'\0\0'
# FX et ACID gardent leur propre edition ; BACK depuis JUMP revient au parent.
state('menu',1);state('gc_level',1);state('gc_tree_cursor',9);key(32);key(32,16);assert r.call(al['mf_tree_edit'])==1;key(12);key(12,0)
if row==11:
 state('gc_tree_cursor',10);key(32);key(32,16);assert r.r32(al['ae_edit'])==1;key(12);key(12,0)
state('gc_tree_cursor',row);key(12);key(12,0);assert r.r32(al['gc_level'])==0
report=dict(sha256=m['sha256'],menu_labels=labels,display_values=values,data_edit_and_BACK=True,default_OFF=True,save_deferred_during_playback=True,cold_reload_ON=True,malformed_files_rejected=4,preload_changes_preserved=True,OFF_clears_pending_request=True,FX_ACID_edit_preserved=True,hardware_tested=False)
a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS JUMP global menu, save/reload, invalid files, prior FX/ACID controls',flush=True)
