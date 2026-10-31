"""Commit de machine : vrai DrumSelect, setMachine et reset sonore, sans audition."""
from pathlib import Path
import argparse,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
import boot_candidate as bc
import test_keep_machine_params as K
from unicorn import m68k_const as C
bc.ROOT=a.output.parent/'native-menu-cache';im,mem=bc.boot(next(a.build.glob('*.syx')));K.boot=lambda p:(im,mem);u,obj,snd=K.fixture('unused');m=json.loads((a.build/'BUILD.json').read_text(encoding='utf-8'));s=m['activity_masks']['symbols']
u.hooks[0x40000542]=('continue',0);u.call(s['am_boot_finish']);u.hooks[m['fx_menu']['symbols']['fx_notice']]=('notice',0);u.hooks[0x40076bee]=('redraw',0);u.hooks[0x4001e318]=('machine',0);u.hooks[0x4007240c]=('DATA',32)
for fn in (0x400f44c6,0x4001416c):del u.hooks[fn]
u.hooks[0x400802e0]=('alloc',0x93210000);u.hooks[0x400802ec]=('free',0)
view=0x93900000;event=0x93910000
for t in range(6):u.uc.mem_write(view+0x70+4*t,bytes(4))
u.uc.mem_write(snd,bytes(100));u.uc.mem_write(snd+38,b'\0\0');u.uc.reg_write(C.UC_M68K_REG_D2,0);u.call(m['keep_params']['symbols']['kr_snapshot'],obj);u.uc.mem_write(view+136,bytes(u.uc.mem_read(K.T.SCRATCH,12)))
before=bytes(u.uc.mem_read(snd,100));u.uc.mem_write(s['mb_silent'],struct.pack('>I',1))
for i in range(4):u.call(0x400a2712,view,1,0,0);assert bytes(u.uc.mem_read(snd,100))==before
assert u.u32(s['mb_candidate'])==4
# Meme dessinateur natif : comparer la liste integrale des commandes graphiques.
def draw(machine,pending):
 u.uc.mem_write(s['mb_pending'],struct.pack('>I',pending));u.calls.clear()
 for at,name in ((0x40071a04,'text'),(0x40071da4,'image'),(0x40070c4e,'mark'),(0x40070efc,'fill'),(0x93000000,'a5'),(0x93000010,'a4')):u.hooks[at]=(name,0)
 for at in (0x93000000,0x93000010):u.uc.mem_write(at,b'\x4e\x75')
 u.uc.mem_write(0x40fe32cc,struct.pack('>I',0x92000000));u.uc.mem_write(0x40fe384c,struct.pack('>I',0x92100000));u.uc.mem_write(view+108,struct.pack('>I',0x91002000))
 sp=K.T.STACK-0x800;u.uc.mem_write(sp,struct.pack('>I',K.T.STOP)*64)
 regs={C.UC_M68K_REG_D3:machine,C.UC_M68K_REG_D2:0x91000000,C.UC_M68K_REG_A2:view,C.UC_M68K_REG_A5:0x93000000,C.UC_M68K_REG_A4:0x93000010,C.UC_M68K_REG_A7:sp}
 for reg,value in regs.items():u.uc.reg_write(reg,value)
 u.uc.emu_start(0x400a25e0,K.T.STOP,count=1000000)
 return [(name,args[:7] if name=='text' else args[:6]) for name,args in u.calls if name in ('text','image','mark','fill')]
reference=draw(4,0);pending=draw(0,1)
assert reference and reference==pending,'pending browse changes native graphics';assert bytes(u.uc.mem_read(snd,100))==before
u.uc.mem_write(s['mb_pending'],struct.pack('>I',1))
u.uc.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,32,1,0));u.call(0x400a292c,view,event)
assert u.uc.mem_read(snd+38,1)[0]==4,('commit',bytes(u.uc.mem_read(snd+38,2)).hex());assert not u.bad
print('PASS actual native machine commit: Kick unchanged while browsing, DATA replaces it with Tone',flush=True)
a.output.write_text(json.dumps(dict(native_machine_commit=True,browse_keeps_raw_sound_exact=True,native_graphics_commands_exact=True,hardware_tested=False),indent=2)+'\n')
