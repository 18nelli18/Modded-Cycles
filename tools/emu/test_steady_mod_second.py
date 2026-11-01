"""Deuxieme operateur stable installe : PCM/etat/EMAC/ABI natifs, ramps et alias."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.first=False
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
cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';original=subprocess.run
def cross_run(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[cross+'objdump.exe',*cmd[1:]]
 return original(cmd,*args,**kw)
subprocess.run=cross_run
a.output.parent.mkdir(parents=True,exist_ok=True)
import os
os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
run('gcc','-mcpu=54418','-c',R/'tools/machines/track_fx/steady-mod-second.S','-o',a.output.parent/'second.o')
from gen_governor_recovery_test import read,BASE
image=read(next(a.build.glob('*.syx')))[2];tail=int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE;at=m['per_track_fx']['symbols']['dry_osc'];offset=tail+at-0x467ab360;body=image[offset:offset+512];dry=bytes.fromhex('246f0054226f00587020');native8=original_native8=read(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx'))[2][0x400a82cc-BASE:0x400a82d4-BASE]+bytes.fromhex('4ef9400a82d4');assert body.count(dry)==body.count(native8)==1
(a.output.parent/'second.ld').write_text('SECTIONS { .text 0x47000000 : { *(.text*) } }\n om_dry = '+hex(at+body.index(dry))+';\n om_native = '+hex(at+body.index(native8))+';\n')
run('ld','-T',a.output.parent/'second.ld','-o',a.output.parent/'second.elf',a.output.parent/'second.o');run('objcopy','-O','binary',a.output.parent/'second.elf',a.output.parent/'second.bin');prototype=(a.output.parent/'second.bin').read_bytes()
pairs=[];original_image=bc.load(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx'));lo,hi=(0x400a80e6,0x400a8204) if a.first else (0x400a8204,0x400a835e)
native=original_image[lo-0x40000400:hi-0x40000400];f=a.output.parent/'om-native.bin';f.write_bytes(native)
for variant in (0,1):
 meta=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));fx.metadata=meta;fx.boot=lambda p:bc.boot(next(a.build.glob('*.syx')))
 r,files,bind=fixture();r.u.mem_write(lo,native);mac=ExtendedEMAC(r.u);mac.install(emac.disasm(str(f),lo,lo,hi))
 for key,at,size in [('primary',meta['activity_masks']['code'],meta['activity_masks']['code_bytes']),('old',meta['per_track_fx']['symbols']['dry_osc'],512)]:
  raw=a.output.parent/('om-'+key+'.bin');raw.write_bytes(r.u.mem_read(at,size));mac.install(emac.disasm(str(raw),at,at,at+size))
 if variant:
  if meta.get('native_second_mod',{}).get('steady_mod_depth_with_amp_ramp'):
   d=meta['native_second_mod'];target=d['target'];installed=bytes(r.u.mem_read(target,len(prototype)));assert installed==prototype
   actual=a.output.parent/'installed-second.bin';actual.write_bytes(installed);mac.install(emac.disasm(str(actual),target,target,target+len(installed)))
  else:
   r.u.mem_map(0x47000000,0x10000);r.u.mem_write(0x47000000,prototype);mac.install(emac.disasm(str(a.output.parent/'second.bin'),0x47000000,0x47000000,0x47000000+len(prototype)));target=0x47000000
  entry=0x400a82cc;r.u.mem_write(entry,b'\x4e\xf9'+struct.pack('>I',target));mac.fast[entry]=lambda:None;mac.next[entry]=target
 if not variant:
  entry=0x400a82cc;target=meta['per_track_fx']['symbols']['dry_osc'];r.u.mem_write(entry,b'\x4e\xf9'+struct.pack('>I',target));mac.fast[entry]=lambda:None;mac.next[entry]=target
 pairs.append((r,mac))
from unicorn import UC_HOOK_CODE
rng=random.Random(273);costs={};regs=[getattr(C,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(C,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
for mode in ('a','b','a_ramp','b_ramp','both','dry','ramp_a','ramp_b','a_start','b_start','both_start','a_negative','b_negative','a_max','b_min','a_stable','b_stable','dry_stable'):
 total=[0,0]
 for case in range(32):
  state=bytearray(rng.randbytes(208));source_a=rng.randbytes(132);source_b=rng.randbytes(132);table=rng.randbytes(1028)
  for offset,address in [(148,0x93180000),(152,0x93181000),(168,0x93182000),(192,0x93183000),(196,0x93184000)]:struct.pack_into('>I',state,offset,address)
  if case>=8:struct.pack_into('>I',state,148 if case%2 else 152,(0x93183000 if case%4<2 else 0x93184000)+(-4,0,4)[case%3])
  wa=0 if mode in ('a','a_stable','a_ramp','dry','dry_stable','a_start','b_start','both_start','a_negative','a_max') else rng.randrange(1,0x10000000);wb=0 if mode in ('b','b_stable','b_ramp','dry','dry_stable','a_start','b_start','both_start','b_negative','b_min') else rng.randrange(1,0x10000000)
  if mode=='a_negative':wb=(-rng.randrange(1,0x10000000))&0xffffffff
  if mode=='b_negative':wa=(-rng.randrange(1,0x10000000))&0xffffffff
  if mode=='a_max':wb=0x7fffffff
  if mode=='b_min':wa=0x80000000
  for offset,value in [(132,wa),(140,wa),(136,wb),(144,wb)]:struct.pack_into('>I',state,offset,value)
  if mode in ('ramp_a','b_ramp'):struct.pack_into('>I',state,132,wa+4096)
  if mode in ('ramp_b','a_ramp'):struct.pack_into('>I',state,136,wb+8192)
  if mode in ('b_start','both_start'):struct.pack_into('>I',state,140,4096)
  if mode in ('a_start','both_start'):struct.pack_into('>I',state,144,8192)
  if mode.endswith('stable'):state[116:120]=state[120:124]
  status=0xa0 if case%2 else 0x20;acc=[rng.getrandbits(48) for i in range(4)];seed=[rng.getrandbits(32) for i in regs];outputs=[]
  for index,(r,mac) in enumerate(pairs):
   for at,raw in [(0x93170000,bytes(state)),(0x93180000,source_a),(0x93181000,source_b),(0x93182000,table),(0x93183000,b'\x5a'*128),(0x93184000,b'\xa5'*128)]:r.u.mem_write(at,raw)
   mac.macsr=status
   for i,v in enumerate(acc):mac.put_physical(i,v)
   for reg,v in zip(regs,seed):r.u.reg_write(reg,v)
   n=[0];hook=r.u.hook_add(UC_HOOK_CODE,lambda *args:n.__setitem__(0,n[0]+1));
   try:r.call(lo,0,0x93170000)
   except Exception:print('FAULT',mode,case,index,hex(r.u.reg_read(C.UC_M68K_REG_PC)),flush=True);raise
   r.u.hook_del(hook);total[index]+=n[0]
   assert [r.u.reg_read(reg) for reg in regs]==seed
   outputs.append((bytes(r.u.mem_read(0x93170000,208)),bytes(r.u.mem_read(0x93183000,128)),bytes(r.u.mem_read(0x93184000,128)),mac.macsr,[mac.physical(i) for i in range(4)]))
  assert outputs[0]==outputs[1],(mode,case,[i for i,(x,y) in enumerate(zip(*outputs)) if x!=y])
 costs[mode]=total
 if mode in ('a','b','a_ramp','b_ramp','a_start','b_start','a_negative','b_negative','a_max','b_min','a_stable','b_stable','dry_stable'):assert total[1]<total[0],(mode,total)
 print('PASS native oscillator',('first' if a.first else 'second'),mode,'32 cases exact PCM/state/EMAC/ABI; instructions',total,flush=True)
a.output.write_text(json.dumps(dict(cases=len(costs)*32,pcm_state_emac_abi_exact=True,instructions=costs,hardware_tested=False),indent=2)+'\n',encoding='utf-8')
