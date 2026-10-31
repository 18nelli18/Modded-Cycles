"""Preuve native des reglages ACID, navigation et sauvegarde globale."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));s=m['activity_masks']['symbols'];al=m['direct_jump']['aliases']
bc.ROOT=a.output.parent/'ui-cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text(encoding='utf-8'))",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0);return r,files,bind


r,files,bind=fixture();feature=m['activity_masks'];r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);bind(0x40000542,lambda a:0);r.call(s['am_boot_finish'])
for h in feature['late_hooks']:assert bytes(r.u.mem_read(h['at'],6))==b'\x4e\xf9'+struct.pack('>I',h['target']),hex(h['at'])
EVENT=0x93001000;log=[];selected=[0]
bind(0x400cf866,lambda a:0x41400000);bind(0x40012412,lambda a:selected[0]);bind(0x4001e318,lambda a:0);bind(0x4007240c,lambda a:r.r32(a[0]+12))
bind(s['mb_native_rotate'],lambda a:log.append(tuple(a[:4])) or 77);bind(s['mb_native_key'],lambda a:66);bind(s['fx_notice'],lambda a:0)
r.w32(s['mb_silent'],1)
for i in range(4):r.call(s['mb_rotate'],0x931c0000,1,0,0)
assert not log and r.r32(s['mb_pending']) and r.r32(s['mb_candidate'])==4

def key(code,flags):
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,code,flags,0));return r.call(s['mb_key'],0x931c0000,EVENT)
assert key(32,1)==1 and len(log)==1 and not r.r32(s['mb_pending']);assert key(32,16)==1 and len(log)==1
r.call(s['mb_rotate'],0x931c0000,1,0,0);key(12,1);assert len(log)==1 and not r.r32(s['mb_pending'])
r.call(s['mb_rotate'],0x931c0000,1,0,0);selected[0]=1;key(32,1);key(32,16);assert len(log)==1 and not r.r32(s['mb_pending'])
r.w32(s['mb_silent'],0);assert r.call(s['mb_rotate'],0x931c0000,1,0,0)==77 and len(log)==2
for k,v in [('menu',1),('gc_level',1),('gc_page',0),('sx_submenu',0),('du_page',0),('mq_page',0),('gc_tree_cursor',0)]:r.w32(s[k],v)
def turn(d):
 r.delta=d;r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,1,d&0xffffffff,0));return r.call(s['mb_gc_encoder'],EVENT)
turn(1);assert r.r32(s['gc_tree_cursor'])==1
for flags in (1,16):r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,0,32,flags,0));r.call(s['mb_gc_key'],EVENT)
assert r.call(s['mb_edit'])==1;turn(-1);assert r.r32(s['mb_silent'])==1;turn(1);assert r.r32(s['mb_silent'])==0
r.call(s['mb_service']);assert '/MachineBrowse.cfg' in files
r2,files2,bind2=fixture();files2.update(files);r2.call(s['mb_service']);assert r2.r32(s['mb_silent'])==0
print('PASS silent browse, DATA commit/release ownership, BACK cancel, track-change safety, Stk delegation, Mac row and global save',flush=True)
a.output.write_text(json.dumps(dict(silent_browse=True,data_commit=True,back_cancel=True,track_change_safe=True,stock_delegated=True,global_mac_after_pad=True,global_saved=True,hardware_tested=False),indent=2)+'\n')
