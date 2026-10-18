"""Prototype machine MIDI : vrai dispatch, silence, audio stock et masque64cas.

Aucune preuve de MIDI physique ou CC : cette etape n'est pas publiable seule.
"""
import json,pathlib,sys,struct,tempfile,shutil,os
from types import SimpleNamespace
import numpy as np
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
import build,gen_sdvintage_7th as g7,mcengine as E,test_macro as M,test_sdvintage_7th as T

def main():
 alias=tempfile.TemporaryDirectory();objdump=shutil.which('m68k-linux-gnu-objdump') or shutil.which('m68k-elf-objdump');assert objdump
 os.symlink(objdump,pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
 root=HERE.parent.parent;stock=g7.cycles_main(str(root/'firmware/model-cycles_OS1.13.syx'));t=json.loads((root/'build/midi-machine/core.json').read_text())
 patched,_=build.apply_writes(stock,[t]);payload,_=build.build_payload([t],stock,None);runtime=build.payload_runtime(t,stock,None);pay=int(t['append']['dest'],16)
 fw=SimpleNamespace(img=bytes(patched)+payload,payload=(pay,runtime),runtime=runtime,tweaks=[dict(t,id='macro-midi-prototype')])
 M.boot(fw)
 def engine(changed=True):return E.Engine(fw.img if changed else stock,payload=fw.payload if changed else None)
 for machine in range(6):
  old,new=engine(False),engine()
  for r in (old,new):
   for lane in range(6):r.machine_defaults(lane,machine)
  for block in range(8):assert np.array_equal(old.block(63 if block%4==0 else 0),new.block(63 if block%4==0 else 0)),machine
  print('PASS stock audio exact',machine,flush=True)
 e=engine();sy={k:int(v,16) for k,v in t['symbols'].items()};count=[0]
 e.uc.hook_add(UC_HOOK_CODE,lambda *args:count.__setitem__(0,count[0]+1))
 for lane in range(6):e.set(lane,machine=6,note=60,pitch=64,color=127,shape=127,sweep=127,contour=127,decay=127)
 for block in range(32):assert not np.any(e.block(63 if block%4==0 else 0)),block
 print('PASS six MIDI machines: 32 blocks silent including retriggers, no audio engine',flush=True)
 for mask in range(64):
  for lane in range(6):e.set(lane,machine=6 if mask>>lane&1 else lane)
  e._write_params()
  assert e.call(sy['mm_mask'],E.PARAMS+14,6)==mask
 assert e.call(sy['mm_mask'],0,6)==0 and e.call(sy['mm_mask'],E.PARAMS+14,128)==0
 print('PASS 64 track assignments, native pattern parameters, invalid inputs',flush=True)
 ui=T.UI(bytes(patched),runtime);ui.call(0x4005a274)
 assert ui.u32(T.ROW_COUNT)==7
 assert ui.call(0x4005a692,12,6)==77
 print('PASS native machine menu has seven entries and MIDI descriptors',flush=True)
 print('LIMITES : CC, UI, notes et sauvegarde MIDI pas encore raccordes ; ne pas publier ce prototype seul')
if __name__=='__main__':main()
