"""Comparer le PCM des six machines natives : PUNCH ON, filtres/LFO ajoutes inactifs."""
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

meta=json.loads((args.build/'BUILD.json').read_text(encoding='utf-8'));path=next(args.build.glob('*.syx'));stem='staging/all-features-polivoks-cpu-trim-test-v215';current.update(path=path,source_name=Path(stem).name+'.syx',meta=meta)
e=tw.fixtures(False,127,0,[stem],native_chordkeys=False,audit_count=False)[0];configure(e,False)
fx=meta['per_track_fx'];sy=fx['symbols'];f=W/'env-module.bin';f.write_bytes(e.uc.mem_read(fx['code'],fx['code_bytes']));e.emac.install(emac.disasm(str(f),fx['code'],fx['code'],fx['code']+fx['code_bytes']))
e.emac.fast[0x400a82cc]=lambda:None;e.emac.next[0x400a82cc]=sy['dry_osc']

patched='acid_arp' in meta or meta.get('acid_articulation',{}).get('arp_retrigger',False)
if patched:
 art=meta.get('acid_arp',meta.get('acid_articulation'));
 if 'trk' in art['symbols']:sy=dict(sy,trk=art['symbols']['trk'])
 f=W/'arp-module.bin';f.write_bytes(e.uc.mem_read(art['code'],art['code_bytes']));e.emac.install(emac.disasm(str(f),art['code'],art['code'],art['code']+art['code_bytes']))

f=W/'native-extra.bin';f.write_bytes(e.uc.mem_read(0x468c2000,0x1000));e.emac.install(emac.disasm(str(f),0x468c2000,0x468c2000,0x468c3000))
if meta.get('stock_voice_protection',{}).get('enabled') or meta.get('idle_routing_fast_path') or meta.get('sram_mixer',{}).get('enabled') or meta.get('one_mod_osc') or meta.get('control_all_latch'):
 def native_continue(u,pc,size,data):
  sp=u.reg_read(C.UC_M68K_REG_A7);u.reg_write(C.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(C.UC_M68K_REG_A7,sp+4)
 from unicorn import UC_HOOK_CODE
 e.uc.hook_add(UC_HOOK_CODE,native_continue,begin=0x40000542,end=0x40000542);e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.uc.reg_write(C.UC_M68K_REG_A0,E.PARAMS+0x8000);e.call(meta['complete_irq_accounting']['boot_target'] if meta.get('complete_irq_accounting') else meta['control_all_latch']['boot_target'] if meta.get('control_all_latch') else meta['activity_masks']['symbols']['am_boot_finish'])
 if meta.get('stock_voice_protection',{}).get('enabled'):assert e.uc.mem_read(0x8000e8b6,1)==b'\x64'
if meta.get('one_mod_osc'):
 at=meta['activity_masks']['code'];n=meta['activity_masks']['code_bytes'];f=W/'one-mod-primary.bin';f.write_bytes(e.uc.mem_read(at,n));e.emac.install(emac.disasm(str(f),at,at,at+n));target=meta['activity_masks']['symbols']['om_osc'];assert bytes(e.uc.mem_read(0x400a82cc,6))==b'\x4e\xf9'+struct.pack('>I',target);e.emac.next[0x400a82cc]=target
if meta.get('static_gain_mixer'):
 d=meta['static_gain_mixer'];f=W/'static-gain-mixer.bin';f.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']));e.emac.install(emac.disasm(str(f),d['code'],d['code'],d['code']+d['code_bytes']))
if meta.get('native_second_mod'):
 d=meta['native_second_mod'];f=W/'native-second-mod.bin';f.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']));e.emac.install(emac.disasm(str(f),d['code'],d['code'],d['code']+d['code_bytes']));assert bytes(e.uc.mem_read(0x400a82cc,6))==b'\x4e\xf9'+struct.pack('>I',d['target']);e.emac.next[0x400a82cc]=d['target']
if meta.get('sparse_static_mixer'):
 d=meta['sparse_static_mixer'];f=W/'sparse-static.bin';f.write_bytes(e.uc.mem_read(d['code'],d['code_bytes']));e.emac.install(emac.disasm(str(f),d['code'],d['code'],d['code']+d['code_bytes']));assert bytes(e.uc.mem_read(d['hook'],6))==b'\x4e\xf9'+struct.pack('>I',d['target'])
stock=tw.engine(real_load(DEV/'firmware/model-cycles_OS1.13.syx'))
for eng in (stock,e):
 for t in range(6):
  eng.set(t,machine=t,note=60,pitch=64,finetune=64,color=64,shape=64,sweep=64,contour=64,decay=110,punch=1,gate=0)
  eng.uc.mem_write(E.PARAMS+14+66*t+46,struct.pack('>3H',0,32512,0))
  eng.uc.mem_write(0x40fe4cdc+2*t,struct.pack('>H',127<<8))
peaks=[0]*6
rows=[]
for b in range(40):
 outs=[]
 for label,eng in [('stock',stock),('mod',e)]:
  try:
   eng.uc.reg_write(C.UC_M68K_REG_SR,0x2700);outs.append(eng.block(63 if b==0 else 0))
  except Exception:
   print('FAULT',label,b,hex(eng.uc.reg_read(C.UC_M68K_REG_PC)),bytes(eng.uc.mem_read(eng.uc.reg_read(C.UC_M68K_REG_PC),16)).hex(),flush=True);raise
 peaks=[max(peaks[t],int(np.max(np.abs(outs[0][t].astype(np.int64))))) for t in range(6)]
 rows.append([int(np.max(np.abs(outs[0][t].astype(np.int64)-outs[1][t].astype(np.int64)))) for t in range(6)])
assert all(p>100000 for p in peaks);assert not any(any(row) for row in rows);print('PASS stock PUNCH PCM parity: six audible machines, 40 native blocks',flush=True)
args.output.write_text(json.dumps(dict(blocks=40,native_machines=6,punch=True,max_difference=max(max(row) for row in rows),peaks=peaks,hardware_tested=False),indent=2)+'\n')
