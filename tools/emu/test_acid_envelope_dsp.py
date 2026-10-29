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
runs={}
for mode in (0,1,2):
 for gate in (0,1):
  e.uc.mem_write(fx['bss'],bytes(fx['bss_bytes']))
  e.uc.mem_write(sy['ae_mode'],struct.pack('>I',mode))
  for t in range(6):
   e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE)
   e.set(t,machine=13 if t==0 else 17,note=48,pitch=64,finetune=64,color=64,shape=80,sweep=100,contour=0,decay=15,punch=0,gate=gate)
   e.uc.mem_write(E.PARAMS+14+66*t+46,struct.pack('>3H',0,127<<8,0));e.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',100<<8));e.uc.mem_write(e.audit_symbols['gv_gain']+4*t,struct.pack('>I',16777216))
  e.emac.macsr=0xa0
  for k in range(4):e.emac.put_physical(k,0)
  pcm=[];coef=[];amp=[];gate_flags=[];decay_coeff=[]
  for block in range(100):
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);a=e.block(1 if block==0 else 0,1 if block==75 else 0)
   pcm.append(a[0].copy());coef.append(int.from_bytes(e.uc.mem_read(sy['trk']+40,4),'big'));amp.append(int.from_bytes(e.uc.mem_read(E.VOICE0+0x230,4),'big',signed=True));gate_flags.append(int.from_bytes(e.uc.mem_read(E.VOICE0+0x24c,4),'big'));decay_coeff.append(int.from_bytes(e.uc.mem_read(E.VOICE0+0x250,4),'big'))
  a=np.stack(pcm);runs[(mode,gate)]=dict(pcm=a,filter_coeff=coef,amp=amp,gate=gate_flags,decay=decay_coeff)
  print('MODE',mode,'GATE',gate,'filter range',min(coef[2:70]),max(coef[2:70]),'amp',amp[5],amp[70],'peak',int(np.max(abs(a))),flush=True)
# Le filtre A reste constant ; F et AF partagent exactement sa trajectoire.
for gate in (0,1):
 a=runs[(1,gate)];f=runs[(0,gate)];af=runs[(2,gate)]
 assert len(set(a['filter_coeff'][2:70]))==1
 assert len(set(f['filter_coeff'][2:70]))>10
 assert f['filter_coeff'][:70]==af['filter_coeff'][:70]
 assert all(v==1 for v in f['gate'][2:70])
 assert all(v==gate for v in a['gate'][2:70]) and all(v==gate for v in af['gate'][2:70])
 assert a['decay']==af['decay']
 assert not np.array_equal(f['pcm'],af['pcm']) if gate==0 else True
assert abs(runs[(2,0)]['amp'][70])<abs(runs[(0,0)]['amp'][70])
assert runs[(2,1)]['amp'][70]==runs[(0,1)]['amp'][70]
# Une seule ecriture du mode pilote les six voix ACID au bloc suivant.
for t in range(6):e.set(t,machine=13,gate=0)
for mode in (2,0,1):
 e.uc.mem_write(sy['ae_mode'],struct.pack('>I',mode))
 for block in range(3):e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.block(63 if block==0 else 0)
 flags=[int.from_bytes(e.uc.mem_read(E.VOICE0+t*E.VSTRIDE+0x24c,4),'big') for t in range(6)]
 assert flags==[int(mode==0)]*6,(mode,flags)
report=dict(sha256=meta['sha256'],modes=['F','A','AF'],gate_settings=[0,1],blocks_each=100,A_filter_constant=True,F_AF_filter_trajectory_equal=True,single_setting_controls_six_tracks=True,amp_decay_restored=True,gate_sustain_preserved=True,hardware_tested=False)
args.output.write_text(json.dumps(report,indent=2)+'\n');np.savez_compressed(W/'envelope-pcm.npz',**{str(k):v['pcm'] for k,v in runs.items()});print('PASS',report,flush=True)
