"""Enveloppes ACID : render natif, six couples mode/Gate et routage filtre/ampli."""
from pathlib import Path
import sys,json,struct,hashlib,inspect,gc,argparse
import numpy as np
R=Path(__file__).resolve().parents[2];T=R/'tools'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();W=args.output.parent;W.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(R.parent/'boot-check-deps'),str(T/'emu'),str(T)]
import boot_candidate
DEV=Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo')
sys.path.extend([str(DEV/'tools/emu'),str(DEV/'tools')])
boot_candidate.ROOT=DEV
real_boot,real_load=boot_candidate.boot,boot_candidate.load
current={}
def mapped(path):
 path=Path(path)
 return current['path'] if path.name==current.get('source_name') else path
def cached_boot(path):
 saved=boot_candidate.ROOT
 try:boot_candidate.ROOT=W/'history-cache';return real_boot(mapped(path))
 finally:boot_candidate.ROOT=saved
boot_candidate.boot=cached_boot;boot_candidate.load=lambda p:real_load(mapped(p))
import test_wizard_playback as tw
from test_chord_cpu import configure
from unicorn import m68k_const as C
import mcengine as E,emac
source=inspect.getsource(tw.fixtures)
source=source.replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())","m=history_metadata()")
source=source.replace("folder=ROOT/'tmp/emu-runtime-code'",'folder=pathlib.Path('+repr(str(W/'history-code'))+')')
tw.history_metadata=lambda:current['meta'];exec(compile(source,'history-fixtures','exec'),tw.__dict__)

meta=json.loads((args.build/'BUILD.json').read_text());path=next(args.build.glob('*.syx'));stem='staging/all-features-polivoks-cpu-trim-test-v215';current.update(path=path,source_name=Path(stem).name+'.syx',meta=meta)
e=tw.fixtures(False,127,0,[stem],native_chordkeys=False,audit_count=False)[0];configure(e,False)
fx=meta['per_track_fx'];sy=fx['symbols'];f=W/'env-module.bin';f.write_bytes(e.uc.mem_read(fx['code'],fx['code_bytes']));e.emac.install(emac.disasm(str(f),fx['code'],fx['code'],fx['code']+fx['code_bytes']))
e.emac.fast[0x400a82cc]=lambda:None;e.emac.next[0x400a82cc]=sy['dry_osc']
art=meta['acid_articulation'];ss=art['symbols'];f=W/'art-module.bin';f.write_bytes(e.uc.mem_read(art['code'],art['code_bytes']));e.emac.install(emac.disasm(str(f),art['code'],art['code'],art['code']+art['code_bytes']))
runs={}
for glide,legato in [(0,1),(1,1),(127,1),(1,0),(0,0)]:
 e.uc.mem_write(art['bss'],bytes(art['bss_end']-art['bss']))
 e.call(ss['aa_track_set'],0,glide,legato)
 for t in range(6):
  e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=13 if t==0 else 17,note=48,pitch=64,finetune=64,color=64,shape=80,sweep=100,contour=0,decay=64,punch=0,gate=1)
  e.uc.mem_write(E.PARAMS+14+66*t+46,struct.pack('>3H',0,127<<8,0));e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8));e.uc.mem_write(e.audit_symbols['gv_gain']+4*t,struct.pack('>I',16777216))
 e.emac.macsr=0xa0
 rows=[]
 for block in range(45):
  if block==12:e.set(0,note=60)
  e.uc.mem_write(0x800017b4,bytes(4))
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);audio=e.block(1 if block in (0,12) else 0)
  state=struct.unpack('>36i',e.uc.mem_read(ss['trk'],144));rows.append(dict(key=state[1],env=state[13],trig=state[26],peak=int(np.max(abs(audio)))))
 runs[(glide,legato)]=rows
 print('CASE',glide,legato,'keys',[x['key'] for x in rows[10:16]],'trigs',[x['trig'] for x in rows[10:16]],flush=True)
assert runs[(0,1)][12]['trig']==3
assert runs[(1,1)][12]['trig']==2
assert runs[(0,1)][13]['key']==60<<16
assert runs[(1,1)][13]['key']<60<<16
assert runs[(127,1)][20]['key']<runs[(1,1)][20]['key']
assert runs[(1,0)][13]['key']<60<<16
assert runs[(1,0)][13]['trig']==4
assert runs[(0,0)][13]['key']==60<<16
assert runs[(0,1)][13]['env']<runs[(1,0)][13]['env']
args.output.write_text(json.dumps(dict(native_dsp=True,glide_off_ties=True,legato_off_retriggers=True,slow_glide_slower=True,cases={str(k):v for k,v in runs.items()},hardware_tested=False),indent=2)+'\n');print('PASS native ACID articulation DSP',flush=True)

