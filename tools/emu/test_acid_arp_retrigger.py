"""ACID sous retrig natif : reproduire la liaison2.63 et verifier la relance2.64."""
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

patched='acid_arp' in meta or meta.get('acid_articulation',{}).get('arp_retrigger',False)
if patched:
 art=meta.get('acid_arp',meta.get('acid_articulation'));
 if 'acid_articulation' in meta:sy=dict(sy,trk=art['symbols']['trk'])
 f=W/'arp-module.bin';f.write_bytes(e.uc.mem_read(art['code'],art['code_bytes']));e.emac.install(emac.disasm(str(f),art['code'],art['code'],art['code']+art['code_bytes']))
runs={}
for mode,gate,repeat in [(0,1,0),(0,1,1),(1,0,1),(2,0,1)]:
 for t in range(6):
  e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=13 if t==0 else 17,note=48,pitch=64,finetune=64,color=64,shape=80,sweep=100,contour=0,decay=64,punch=0,gate=gate)
  e.uc.mem_write(E.PARAMS+14+66*t+46,struct.pack('>3H',0,127<<8,0));e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8));e.uc.mem_write(e.audit_symbols['gv_gain']+4*t,struct.pack('>I',16777216))
 e.uc.mem_write(0x40a78d58,bytes(168));e.uc.mem_write(sy['ae_mode'],struct.pack('>I',mode));e.emac.macsr=0xa0;rows=[]
 if repeat:
  e.uc.mem_write(0x40a78d58+4,struct.pack('>I',0xffffffff));e.uc.mem_write(0x40a78d58+20,struct.pack('>I',0x40600000))
 for block in range(30):
  if block in (10,20):e.set(0,note=60 if block==10 else 48)
  e.uc.mem_write(0x800017b4,bytes(24));e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);audio=e.block(1 if block in (0,10,20) else 0)
  state=struct.unpack('>35i',e.uc.mem_read(sy['trk'],140));rows.append(dict(env=state[13],trig=state[26],key=state[1],peak=int(np.max(abs(audio[0]))),amp=struct.unpack('>2i',e.uc.mem_read(E.VOICE0+0x230,8))))
 runs[str((mode,gate,repeat))]=rows;print('CASE',mode,gate,repeat,[(b,rows[b]['env'],rows[b]['trig']) for b in (1,9,10,11,19,20,21)],flush=True)
assert not e.unmapped
for key,rows in runs.items():
 active=key!='(0, 1, 0)'
 for b in (10,20):
  if active and patched:
   assert rows[b+1]['trig']==1 and rows[b+1]['env']==0x7fffffff,(key,b,'missing envelope restart')
   if key.startswith('(1,') or key.startswith('(2,'):assert rows[b]['amp']==(0,0) and rows[b+1]['amp']==rows[1]['amp'],(key,b,'amp not restarted')
  else:
   assert rows[b]['trig']==2 and rows[b+1]['env']<rows[b-1]['env'],(key,b,'slide changed')
print('PASS native ACID envelopes: '+('arp retriggers; ordinary ties preserved' if patched else '2.63 arp regression reproduced'),flush=True)
args.output.write_text(json.dumps(dict(patched=patched,runs=runs,hardware_tested=False),indent=2)+'\n')
