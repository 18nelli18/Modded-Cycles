"""Preuve native des reglages ACID, navigation et sauvegarde globale."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));s=m['activity_masks']['symbols'];al=m['direct_jump']['aliases']
bc.ROOT=a.output.parent/'ui-cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
def fixture():
 r,_,h,log,files,key,turn,data,bind=fx.fixture('unused');bind(al['gc_input_quiet'],lambda a:1);bind(0x400423e4,lambda a:0);return r,files,bind


import random,subprocess,emac
from emac_state import ExtendedEMAC
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';original_run=subprocess.run
def cross_run(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[cross+'objdump.exe',*cmd[1:]]
 return original_run(cmd,*args,**kw)
subprocess.run=cross_run
pairs=[]
for folder in (a.baseline,a.build):
 meta=json.loads((folder/'BUILD.json').read_text());sy=meta['activity_masks']['symbols'];fx.boot=lambda path,folder=folder:bc.boot(next(folder.glob('*.syx')))
 r,files,bind=fixture();image=bc.load(next(folder.glob('*.syx')))
 if len(image)>0x40200000-0x40000400:r.u.mem_write(0x40200000,image[0x40200000-0x40000400:])
 r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);bind(0x40000542,lambda a:0);r.call(sy['am_boot_finish']);r.u.mem_map(0x80000000,0x20000)
 mac=ExtendedEMAC(r.u);raw=folder/'module.bin';mac.install(emac.disasm(str(raw),meta['activity_masks']['code'],meta['activity_masks']['code'],meta['activity_masks']['code']+meta['activity_masks']['code_bytes']))
 calls=[]
 def kernel(args,r=r,calls=calls,name=None):
  data=bytes(r.u.mem_read(args[1],256));r.u.mem_write(args[0],data);calls.append(('kernel',name,bytes(r.u.mem_read(args[2],4)) if name not in ('fx_ring',) else None,tuple(args[3:5]) if name=='ch_chorus' else None));return 0
 for name in ('ch_native','ch_chorus','fx_ps1','fx_room','fx_hall','fx_ring','fx_gated'):bind(meta['fx_menu']['symbols'][name],lambda args,name=name,kernel=kernel:kernel(args,name=name))
 bind(0x46835ff0,lambda args,r=r,calls=calls:calls.append(('sidechain',bytes(r.u.mem_read(args[0],256)))) or 0)
 pairs.append((r,mac,meta,calls))

from unicorn import UC_HOOK_CODE
rng=random.Random(265);report={}
for mode in (0,1,2,7,8,9,10,11):
 report[str(mode)]={}
 for stage in ('steady','switching'):
  costs=[[],[]]
  for trial in range(8):
   samples=[rng.randrange(-2147483648,2147483648) for i in range(64)];outputs=[]
   for index,(r,mac,meta,calls) in enumerate(pairs):
    fs=meta['fx_menu']['symbols']
    for k,v in [('ready',1),('active',mode),('gain',256),('prior_gain',256),('correction_on',0)]:r.w32(fs[k],v)
    r.w32(fs['ch_mode'],mode if stage=='steady' else (7 if mode==0 else 0));r.u.mem_write(0x93180000,struct.pack('>64i',*samples));r.u.mem_write(0x93181000,bytes(256));r.u.mem_write(0x93182000,bytes(476));r.u.mem_write(0x93183000,bytes(48));calls.clear();mac.macsr=0xa0;r.u.reg_write(C.UC_M68K_REG_SR,0x2700)
    counter=[0];hook=r.u.hook_add(UC_HOOK_CODE,lambda *args,counter=counter:counter.__setitem__(0,counter[0]+1))
    r.call(fs['fx_reverb'],0x93181000,0x93180000,0x93184000,0x93182000,0x93183000,0x93183018);r.u.hook_del(hook);costs[index].append(counter[0]);outputs.append(bytes(r.u.mem_read(0x93181000,256)))
   assert outputs[0]==outputs[1],(mode,stage,trial)
  means=[sum(v)/len(v) for v in costs];report[str(mode)][stage]=dict(mean=means,peak=[max(v) for v in costs],delta=means[1]-means[0],percent=100*(means[1]/means[0]-1))
 print('MODE',mode,report[str(mode)],flush=True)
report['files']=[dict(path=str(folder),sha256=json.loads((folder/'BUILD.json').read_text())['sha256']) for folder in (a.baseline,a.build)]
report['scope']='Executed ColdFire wrapper instructions; effect kernels intercepted identically; not hardware cycles or total CPU load.'
a.output.write_text(json.dumps(report,indent=2)+'\n')
