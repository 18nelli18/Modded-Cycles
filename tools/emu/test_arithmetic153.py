"""185 : calculs LEGACY/ACID exacts et cout en instructions, sans mesure appareil."""
from pathlib import Path
import sys,subprocess,os,re,struct,random
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
import emac
from unicorn import m68k_const as C
build=R/'output/firmware/governor-recovery-v153';cross=str(R.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH'];helper=re.search(r'static inline s32 mod_mul24\(.*?\n\}',(R/'tools/machines/dx7/port.cc').read_text(),re.S).group()
src=build/'arithmetic153.c';src.write_text('#define ACID_FAST153 1\n#include "acid_dsp.h"\n'+helper+'\ns32 test_mod(s32 a,s32 b){return mod_mul24(a,b);}\ns32 ref_twice(s32 a,s32 b){return qmac2(a,b,a,b);}\ns32 fast_twice(s32 a,s32 b){return qmul_twice(a,b);}\n')
obj=src.with_suffix('.o');elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-ffunction-sections','-fdata-sections','-I'+str(R/'tools/machines/fundamentals'),'-c',str(src),'-o',str(obj)],check=True);subprocess.run([cross+'ld.exe','--gc-sections','-e','test_mod','-u','ref_twice','-u','fast_twice','-Ttext','0x40a73000','-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};e=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-v153'],audit_count=False)[0];e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.uc.mem_write(0x40a73000,binary.read_bytes());e.emac.install(emac.disasm(str(binary),0x40a73000,0x40a73000,0x40a73000+binary.stat().st_size));rng=random.Random(153)
cases=[(a,b) for a in [-(17<<24),-1,0,1,1<<24,17<<24] for b in [0,1,(1<<24)-1,1<<24]]+[(rng.randrange(-(17<<24),(17<<24)+1),rng.randrange((1<<24)+1)) for i in range(1000)]
for a,b in cases:
 e.emac.macsr=0x20;e.emac.put_physical(0,0);assert e.call(sy['test_mod'],a,b)==((a*b)>>24)&0xffffffff,(a,b)
print('PASS exact LEGACY Q24 product',len(cases),'boundary/random cases',flush=True)
cases=[(a,b) for a in [-2147483648,-1,0,1,2147483647] for b in [-2147483648,-1,0,1,2147483647]]+[(rng.randrange(-(1<<31),1<<31),rng.randrange(-(1<<31),1<<31)) for i in range(1000)]
for a,b in cases:
 out=[]
 for name in ['ref_twice','fast_twice']:
  e.emac.macsr=0xa0;e.emac.put_physical(0,0);out.append(e.call(sy[name],a,b))
 expected=max(-(1<<31),min((1<<31)-1,(a*b)>>30))&0xffffffff;assert out==[expected,expected],(a,b,out,expected)
print('PASS exact ACID repeated-product folding, signed truncation and saturation',len(cases),'boundary/random cases',flush=True)
