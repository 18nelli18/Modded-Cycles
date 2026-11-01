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
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0);return r,files,bind


cases=[]
for name,payload,expected in [('absent',None,0),('invalid',b'garbage!',0),('saved_sil',bytes([77,66,1,1,1,254,165,90]),1),('saved_stk',bytes([77,66,1,1,0,255,165,90]),0)]:
 r,files,bind=fixture();assert r.r32(s['mb_silent'])==0,(name,'initializer')
 if payload is not None:files['/MachineBrowse.cfg']=payload
 r.call(s['mb_service']);assert r.r32(s['mb_silent'])==expected,(name,r.r32(s['mb_silent']))
 cases.append(name)
r,files,bind=fixture();r.call(s['mb_set'],1);r.call(s['mb_service']);assert files['/MachineBrowse.cfg'][4]==1
r2,f2,b2=fixture();f2.update(files);r2.call(s['mb_service']);assert r2.r32(s['mb_silent'])==1
r2.call(s['mb_set'],0);r2.call(s['mb_service']);assert f2['/MachineBrowse.cfg'][4]==0
print('PASS Stk initializer, absent/invalid settings, saved Sil/Stk and saving both modes',flush=True)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(default='Stk',cases=cases,sil_selectable=True,saved_preference_retained=True),indent=2)+'\n')
