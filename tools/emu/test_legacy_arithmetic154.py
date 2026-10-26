"""186 : LEGACY exact, Hagedisk original et bornes arithmetiques."""
from pathlib import Path
import sys,subprocess,os,re,random
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
import emac
from unicorn import m68k_const as C
build=R/'output/firmware/governor-recovery-v154';cross=str(R.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
helper=re.search(r'static inline s32 pitch_mul154\(.*?\n\}',(R/'tools/machines/dx7/port.cc').read_text(),re.S).group();src=build/'arithmetic154.c';src.write_text('typedef unsigned int u32;typedef int s32;\n'+helper+'\ns32 test_pitch(u32 u,s32 s){return pitch_mul154(u,s);}\n')
obj=src.with_suffix('.o');elf=src.with_suffix('.elf');binary=src.with_suffix('.bin');subprocess.run([cross+'gcc.exe','-mcpu=54418','-O3','-fwrapv','-c',str(src),'-o',str(obj)],check=True);subprocess.run([cross+'ld.exe','-e','test_pitch','-Ttext','0x40a73000','-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};e=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-v154'],audit_count=False)[0];e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.uc.mem_write(0x40a73000,binary.read_bytes());e.emac.install(emac.disasm(str(binary),0x40a73000,0x40a73000,0x40a73000+binary.stat().st_size));rng=random.Random(154)
cases=[(a,b) for a in [0,1,127,255,0x7fffffff,0x80000000,0xffffff00,0xffffffff] for b in [-0x7f800000,-0x7f7fffff,-129,-128,-127,-1,0,1,127,128,129,0x7f800000]]+[(rng.randrange(1<<32),rng.randrange(-(255<<23),(255<<23)+1)) for i in range(8192)]
for u,s in cases:
 e.emac.macsr=0x20;e.emac.put_physical(0,0);assert e.call(sy['test_pitch'],u,s)==((u*s)>>39)&0xffffffff,(u,s)
print('PASS exact LEGACY pitch product',len(cases),'bounded signed/full unsigned boundary/random cases, both high-bit branches')
