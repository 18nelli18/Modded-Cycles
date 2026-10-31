"""Commit de machine : vrai DrumSelect, setMachine et reset sonore, sans audition."""
from pathlib import Path
import argparse,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_keep_machine_params as K
from unicorn import m68k_const as C
bc.ROOT=a.output.parent/'native-menu-cache';im,mem=bc.boot(next(a.build.glob('*.syx')));K.boot=lambda p:(im,mem);u,obj,snd=K.fixture('unused');m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));s=m['activity_masks']['symbols']
u.hooks[0x40000542]=('continue',0);u.call(s['am_boot_finish']);u.hooks[s['fx_notice']]=('notice',0);u.hooks[0x40076bee]=('redraw',0);u.hooks[0x4001e318]=('machine',0);u.hooks[0x4007240c]=('DATA',32)
for fn in (0x400f44c6,0x4001416c):del u.hooks[fn]
u.hooks[0x400802e0]=('alloc',0x93210000);u.hooks[0x400802ec]=('free',0)
view=0x93900000;event=0x93910000
for t in range(6):u.uc.mem_write(view+0x70+4*t,bytes(4))
u.uc.mem_write(snd,bytes(100));u.uc.mem_write(snd+38,b'\0\0');u.uc.reg_write(C.UC_M68K_REG_D2,0);u.call(m['keep_params']['symbols']['kr_snapshot'],obj);u.uc.mem_write(view+136,bytes(u.uc.mem_read(K.T.SCRATCH,12)))
before=bytes(u.uc.mem_read(snd,100));u.uc.mem_write(s['mb_silent'],struct.pack('>I',1))
for i in range(4):u.call(0x400a2712,view,1,0,0);assert bytes(u.uc.mem_read(snd,100))==before
assert u.u32(s['mb_candidate'])==4
u.uc.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,32,1,0));u.call(0x400a292c,view,event)
assert u.uc.mem_read(snd+38,1)[0]==4,('commit',bytes(u.uc.mem_read(snd+38,2)).hex());assert not u.bad
print('PASS actual native machine commit: Kick unchanged while browsing, DATA replaces it with Tone',flush=True)
a.output.write_text(json.dumps(dict(native_machine_commit=True,browse_keeps_raw_sound_exact=True,hardware_tested=False),indent=2)+'\n')
