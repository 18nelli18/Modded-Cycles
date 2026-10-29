"""Menu ACID global : onze lignes, preference unique et migration du prototype."""
from pathlib import Path
import inspect,json,sys,struct,argparse
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools/emu'),str(R/'tools')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
bc.ROOT=a.output.parent/'ui-cache'
import test_fx_menu_control as fx
meta=json.loads((a.build/'BUILD.json').read_text());fx.metadata=meta;realboot=bc.boot;fx.boot=lambda path:realboot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
from test_seq_gen_menu import EVENT
sy=meta['per_track_fx']['symbols'];gc=meta['groove_strum']['symbols'];ga=meta['groove_strum']['aliases']
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');sel=[0];bind(gc['sx_track'],lambda args:sel[0]);bind(gc['gc_input_quiet'],lambda args:1)
 return r,files,bind,sel
r,files,bind,sel=fixture()
def state(name,value):r.w32(sy.get(name,gc.get(name,ga.get(name))),value)
def mode():return r.r32(sy['ae_mode'])
def event(code,flags=1):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(sy['ae_key'],EVENT)
def rotate(delta):r.delta=delta;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,1,0,0));return r.call(sy['ae_encoder'],EVENT)
assert mode()==0
r.call(sy['ae_service']);state('menu',1);bind(0x400423e4,lambda args:0);r.call(gc['gc_draw'],0,0x93010000);state('gc_level',1);state('gc_tree_cursor',0)
for i in list(range(1,11))+[0]:rotate(1);assert r.r32(gc['gc_tree_cursor'])==i
rotate(-1);assert r.r32(gc['gc_tree_cursor'])==10
event(32,1);event(32,16);assert r.r32(sy['ae_edit'])==1
for delta,want in [(-1,1),(-1,1),(1,0),(1,2),(1,2)]:rotate(delta);assert mode()==want
sel[0]=4;assert mode()==2;rotate(-1);assert mode()==0;rotate(1);assert mode()==2
event(12,1);assert r.r32(sy['ae_edit'])==0;event(12,0)
event(12,1);assert r.r32(gc['gc_level'])==0;event(12,0)
# Le natif recoit une vraie table contigue de onze lignes, pas les labels.
seen=[];objects=[]
bind(0x400423e4,lambda args:objects.append(args[0]) or 0);state('gc_level',1);state('gc_tree_cursor',10);r.call(sy['ae_draw'],0,0x93010000)
obj=objects[-1];vt=r.r32(obj);assert r.call(r.r32(vt+12),obj)==11
from unicorn import m68k_const as C
for i in range(11):
 r.u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);item=r.r32(0x931f0000);seen.append(r.string(r.r32(item+12)))
assert seen==['Pad','USB','Num','Mute','Dly','DX','QntM','Grv','LFOs','FX','ACID'],seen
state('menu',0);state('gc_level',0);state('gc_tree_cursor',0)
# Ecriture differee en lecture et reprise apres l'arret.
state('menu',0);r.w32(0x40a7883c,1);r.call(sy['ae_service']);assert '/AcidEnv.cfg' not in files
r.w32(0x40a7883c,0);r.call(sy['ae_service']);saved=files['/AcidEnv.cfg'];assert len(saved)==8
rr,ff,bb,ss=fixture();ff['/AcidEnv.cfg']=saved;rr.call(sy['ae_service']);assert rr.r32(sy['ae_mode'])==mode()
for bad in [saved[:5],saved+b'x',bytes(18),saved[:4]+bytes([3])+saved[5:]]:
 rr,ff,bb,ss=fixture();ff['/AcidEnv.cfg']=bad;rr.call(sy['ae_service']);assert rr.r32(sy['ae_mode'])==0
rr,ff,bb,ss=fixture();ff['/AcidEnv.cfg']=saved;rr.call(sy['ae_set'],1);rr.call(sy['ae_service']);assert rr.r32(sy['ae_mode'])==1
rr,ff,bb,ss=fixture();labels=[]
bb(0x40072260,lambda args:0);bb(0x40072080,lambda args:0);bb(0x40071a04,lambda args:labels.append(rr.string(args[6])) or 0)
for mode in (1,0,2):rr.call(sy['ae_set'],mode);rr.call(sy['ae_value'],0,0,0x93010000,122,32)
assert labels==['A','F','AF'],labels
# La valeur globale migre les preferences uniformes et ne choisit pas une piste arbitraire.
for old,want in [([2]*6,2),([1,0,2,0,0,0],0)]:
 rr,ff,bb,ss=fixture();ff['/AcidEnv.cfg']=bytes([65,69,1,6,*old,*[(~v)&255 for v in old],165,90]);rr.call(sy['ae_service']);assert rr.r32(sy['ae_mode'])==want;assert len(ff['/AcidEnv.cfg'])==8
# Le menu Track original reste a trois lignes ; FX reste editable dans Global.
objects.clear();state('menu',1);state('gc_level',2);state('gc_tree_cursor',0);r.call(sy['ae_draw'],0,0x93010000);obj=objects[-1];vt=r.r32(obj);assert r.call(r.r32(vt+12),obj)==3
state('gc_level',1);state('gc_tree_cursor',9);event(32,1);event(32,16);assert r.call(sy['mf_tree_edit'])==1;event(12,1);event(12,0);assert r.call(sy['mf_tree_edit'])==0
report=dict(sha256=meta['sha256'],default_F=True,display_order=['A','F','AF'],eleven_native_global_menu_rows=seen,displayed_values=labels,data_edit_back_navigation=True,single_global_choice=True,save_deferred_during_playback=True,reload_preserves_choices=True,invalid_files_rejected=4,preload_changes_preserved=True,legacy_migration=True,original_track_menu_restored=True,FX_edit_preserved=True,hardware_tested=False)
a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS',report,flush=True)
