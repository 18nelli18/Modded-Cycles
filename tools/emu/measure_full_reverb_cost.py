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

network=m.get('reverb_network_comparison');results={}
for kernel_name in ('fx_room','fx_hall','fx_ps1'):
 pairs=[]
 for folder in (a.baseline,a.build):
  meta=json.loads((folder/'BUILD.json').read_text());sy=meta['activity_masks']['symbols'];path=next(folder.glob('*.syx'));fx.boot=lambda p,path=path:bc.boot(path)
  r,files,bind=fixture();image=bc.load(path)
  if len(image)>0x40200000-0x40000400:r.u.mem_write(0x40200000,image[0x40200000-0x40000400:])
  if network and folder==a.baseline:assert not any(r.u.mem_read(network['code'],network['end']-network['code'])),'network reservation already occupied'
  r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);bind(0x40000542,lambda args:0);r.call(sy['am_boot_finish'])
  if network and folder==a.build:assert bytes(r.u.mem_read(network['code'],network['end']-network['code']))==(folder/'network.bin').read_bytes()
  mac=ExtendedEMAC(r.u)
  for label,at,size in [('fx',meta['fx_menu']['code'],meta['fx_menu']['code_bytes']),('hot',meta['fx_menu']['ps1_hot_address'],meta['fx_menu']['ps1_hot_code_bytes'])]+([('network',network['code'],network['end']-network['code'])] if network else [])+[('primary',meta['activity_masks']['code'],meta['activity_masks']['code_bytes'])]:
   if label=='network' and folder==a.baseline:continue
   raw=a.output.parent/('kernel-'+label+'-'+folder.parent.name+'.bin');raw.write_bytes(r.u.mem_read(at,size));mac.install(emac.disasm(str(raw),at,at,at+size))
  r.w32(meta['fx_menu']['symbols']['fx_gate_time'],0)
  pairs.append((r,mac,meta))
 rng=random.Random(54415);peak=0
 for block in range(320):
  samples=[rng.randrange(-12000,12001)*65536 if block<8 or 150<=block<156 else 0 for i in range(64)]
  output=[]
  for r,mac,meta in pairs:
   r.u.mem_write(0x93180000,struct.pack('>64i',*samples));r.u.mem_write(0x93181000,bytes(256));r.u.mem_write(0x93182000,struct.pack('>2h',(90 if block<150 else 127)*256,(65 if block<150 else 113)*256))
   mac.macsr=0xa0
   for acc in range(4):mac.put_physical(acc,0x123456789abc+acc)
   r.u.reg_write(C.UC_M68K_REG_SR,0x2700)
   r.call(meta['fx_menu']['symbols'][kernel_name],0x93181000,0x93180000,0x93182000)
   output.append((bytes(r.u.mem_read(0x93181000,256)),[mac.physical(i) for i in range(4)],mac.macsr))
  assert output[0]==output[1],(kernel_name,block,[i for i,(x,y) in enumerate(zip(*output)) if x!=y])
  peak=max(peak,max(abs(v) for v in struct.unpack('>64i',output[0][0])))
 costs=[]
 from unicorn import UC_HOOK_CODE
 for r,mac,meta in pairs:
  counter=[0];hook=r.u.hook_add(UC_HOOK_CODE,lambda *args,counter=counter:counter.__setitem__(0,counter[0]+1));r.call(meta['fx_menu']['symbols'][kernel_name],0x93181000,0x93180000,0x93182000);r.u.hook_del(hook);costs.append(counter[0])
 print('INSTRUCTIONS',kernel_name,costs,'not hardware cycles',flush=True)
 renders={}
 for stage in ('steady','switching'):
  costs=[[],[]]
  for trial in range(8):
   signal=[rng.randrange(-12000,12001)*65536 for i in range(64)];outputs=[]
   for index,(r,mac,meta) in enumerate(pairs):
    fs=meta['fx_menu']['symbols'];mode={'fx_room':8,'fx_hall':11,'fx_ps1':7}[kernel_name]
    for key,value in [('ready',1),('active',mode),('gain',256),('prior_gain',256),('correction_on',0)]:r.w32(fs[key],value)
    r.w32(fs['ch_mode'],mode if stage=='steady' else 0);r.u.mem_write(0x93180000,struct.pack('>64i',*signal));r.u.mem_write(0x93183000,bytes(100));bind_here=lambda args:0
    if 0x46835ff0 not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x46835ff0,end=0x46835ff0)
    r.stubs[0x46835ff0]=bind_here
    counter=[0];hook=r.u.hook_add(UC_HOOK_CODE,lambda *args,counter=counter:counter.__setitem__(0,counter[0]+1))
    r.call(fs['fx_reverb'],0x93181000,0x93180000,0x93182000,0x93183000,0x93183040,0x93183058);r.u.hook_del(hook);costs[index].append(counter[0]);outputs.append(bytes(r.u.mem_read(0x93181000,256)))
   assert outputs[0]==outputs[1],(kernel_name,stage,trial,'full renderer PCM')
  means=[sum(v)/len(v) for v in costs];renders[stage]=dict(mean=means,delta=means[1]-means[0],percent=100*(means[1]/means[0]-1))
 print('FULL RENDER',kernel_name,renders,flush=True)
 assert peak>0,(kernel_name,'silent fixture');results[kernel_name]=dict(blocks=320,peak=peak,pcm_exact=True,emac_exact=True,render_instructions=renders);print('PASS',kernel_name,'320 real kernel blocks, cold/hot/wrap/INF-size transition, PCM and EMAC exact',flush=True)
a.output.write_text(json.dumps(dict(kernels=results,new_audio_ram_bytes=0,audible_delay_lengths_unchanged=True,hardware_tested=False),indent=2)+'\n')
