"""LFO secondaires : comparer PCM-parametres, phases et etats natifs avec masques."""
from pathlib import Path
import argparse,json,os,random,struct,subprocess,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import Rig
import mcengine as E,emac
from emac_state import ExtendedEMAC
from test_tempo_max import lfo_params
from unicorn import UC_HOOK_CODE,m68k_const as C
bc.ROOT=a.output.parent/'cache';im,mem=bc.boot(next(a.build.glob('*.syx')));m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));sy=m['per_track_fx']['symbols'];aliases=m['four_lfos']['aliases'];mx=m['four_lfos']['symbols']
W=a.output.parent/'mask-build';W.mkdir(exist_ok=True);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
def run(t,*args):return subprocess.check_output([cross+t+'.exe',*map(str,args)],text=True)
original_run=subprocess.run
def cross_run(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[cross+'objdump.exe',*cmd[1:]]
 return original_run(cmd,*args,**kw)
subprocess.run=cross_run
pairs=[]
for candidate in (False,True):
 source=(R/'tools/machines/track_fx/lfo-direct.c').read_text(encoding='utf-8') if candidate else subprocess.check_output(['git','show','909e6a0:tools/machines/track_fx/lfo-direct.c'],cwd=R,text=True)
 source=source.replace('volatile u32 li_noapply,li_active_tracks[3];','extern volatile u32 li_noapply;volatile u32 li_active_tracks[3];').replace('volatile u32 li_noapply;','extern volatile u32 li_noapply;')
 source=source.replace('extern extern','extern')
 src=W/('new.c' if candidate else 'old.c');src.write_text(source);obj=src.with_suffix('.o');run('gcc','-mcpu=54418','-O3','-ffreestanding','-fno-builtin','-fwrapv','-c',src,'-o',obj)
 ld=W/'module.ld';ld.write_text('SECTIONS { .text 0x47000000 : { *(.text*) *(.rodata*) } .bss 0x47010000 (NOLOAD) : { *(.bss*) *(COMMON) } }\n'+''.join(f'PROVIDE({k} = {sy[k]:#x});\n' for k in ('li_context','li_count','li_extra','li_sync_fast','li_update','li_noapply')))
 elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');run('ld','-T',ld,'-e','li_dispatch','-o',elf,obj);run('objcopy','-O','binary',elf,binary);ns={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
 r=Rig(im,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,len(mem[0][1]));r.u.mem_write(*mem[0]);r.u.mem_map(0x47000000,0x20000);r.u.mem_write(0x47000000,binary.read_bytes());mac=ExtendedEMAC(r.u);mac.install(E._emac_instrs(im,[(0x4008f100,0x40091d50)]));mac.macsr=0x20
 r.stubs[0x40001fba]=lambda a:0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40001fba,end=0x40001fba)
 frame=bytearray(lfo_params([28672]*6,[4]*6).ljust(476,b'\0'));r.u.mem_write(0x931a0000,bytes(frame))
 for ctx in (0x93190000,0x93191000,0x93192000):r.call(aliases['lf2_init'],ctx,0x931a0000)
 r.w32(sy['li_context'],0x93190000);r.w32(sy['li_extra'],0x93191000);r.w32(sy['li_extra']+4,0x93192000);pairs.append((r,mac,ns))
rng=random.Random(265);cases=0
for n in range(1,5):
 for block in range(96):
  frame=bytearray(lfo_params([rng.randrange(32768) for t in range(6)],[rng.randrange(12) for t in range(6)]).ljust(476,b'\0'))
  for t in range(6):frame[22+66*t]=rng.choice([0,11,24,127])
  configs=[b''.join(struct.pack('>8H',rng.randrange(32768),4<<8,0,rng.choice([0,11,24,127])<<8,rng.randrange(7)<<8,0,0,16384) for t in range(6)) for z in range(3)]
  outputs=[];ticks=rng.choice([14400,30000,65520]);trigger=rng.randrange(64)
  for r,mac,ns in pairs:
   r.u.reg_write(C.UC_M68K_REG_SR,0x2700);r.w32(sy['li_count'],n);r.u.mem_write(0x931a0000,bytes(frame))
   for z in range(3):r.u.mem_write(0x93190000+4096*z+192,configs[z])
   r.call(ns['li_dispatch'],0x931a0000,ticks,trigger)
   outputs.append((bytes(r.u.mem_read(0x931a0000,476)),bytes(r.u.mem_read(0x40fde838,192)),*[bytes(r.u.mem_read(0x93190000+4096*z,288)) for z in range(3)],mac.macsr,[mac.physical(k) for k in range(4)]))
  assert outputs[0]==outputs[1],(n,block,[i for i,(x,y) in enumerate(zip(*outputs)) if x!=y]);cases+=1
 print('PASS LFO',n,'96 native state/frame comparisons',flush=True)
# PUNCH : le delegate recoit les sons stock intacts, y compris PUNCH ON.
src=W/'punch.c';src.write_text((R/'tools/machines/track_fx/voice-punch.c').read_text(encoding='utf-8'));obj=src.with_suffix('.o');run('gcc','-mcpu=54418','-O3','-ffreestanding','-fno-builtin','-fwrapv','-DPP_UNIQUE=1','-DPP_REMOVE_LEGACY=1','-c',src,'-o',obj)
ld=W/'punch.ld';ld.write_text('SECTIONS { .text 0x47000000 : { *(.text*) *(.rodata*) } .bss 0x47010000 (NOLOAD) : { *(.bss*) *(COMMON) } } PROVIDE(mf_old_voice_playability = 0x40002000);')
elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');run('ld','-T',ld,'-e','pp_voice_loop','-o',elf,obj);run('objcopy','-O','binary',elf,binary);ns={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
r=Rig(im,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x47000000,0x20000);r.u.mem_write(0x47000000,binary.read_bytes());observed=[]
r.stubs[0x40002000]=lambda a:observed.append(bytes(r.u.mem_read(a[1],476))) or 0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x40002000,end=0x40002000)
for machine in range(25):
 for punch in (0,256):
  frame=bytearray(476)
  for t in range(6):
   for slot in range(33):struct.pack_into('>H',frame,14+66*t+2*slot,64<<8)
   struct.pack_into('>H',frame,14+66*t+18,machine<<8);struct.pack_into('>H',frame,14+66*t+30,punch)
  r.u.mem_write(0x931a0000,bytes(frame));r.call(ns['pp_voice_loop'],0x931b0000,0x931a0000,63,0)
  assert bytes(r.u.mem_read(0x931a0000,476))==bytes(frame),('frame restore',machine,punch)
  if machine<6 or not punch and machine!=21:assert observed[-1]==bytes(frame),('native PUNCH parity',machine,punch)
  expected=63 if machine>=6 and machine not in (13,17,21) and punch else 0
  assert r.r32(ns['pp_custom_mask'])==expected,(machine,punch)
print('PASS stock PUNCH frame parity, 25 machines x ON/OFF, mask bounds and frame restoration',flush=True)
a.output.write_text(json.dumps(dict(cases=cases,punch_cases=50,native_states_and_frames_exact=True,hardware_tested=False),indent=2)+'\n')
