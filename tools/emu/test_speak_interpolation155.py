"""188 : preuves natives exactes et cout en instructions, pas de CPU physique."""
from pathlib import Path
import sys,subprocess,os,re
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
B=R/'output/firmware/governor-recovery-v155';cross=str(R.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH'];helper=re.search(r'static inline s32 interp155\([^\n]+',(R/'tools/machines/speak/speak.c').read_text()).group();src=B/'interp155.c';src.write_text('typedef int s32;typedef unsigned int u32;\n'+helper+'\nint test_interp(void){volatile int divisor=6;for(int x=-40950;x<=40950;x++)if(interp155(x)!=x/divisor)return x+40951;return 0;}\n');obj=src.with_suffix('.o');elf=src.with_suffix('.elf');binary=src.with_suffix('.bin')
subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-c',str(src),'-o',str(obj)],check=True);subprocess.run([cross+'ld.exe','-e','test_interp','-Ttext','0x40a73000','-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True);e=fixtures(False,127,0,['staging/all-features-polivoks-cpu-trim-test-v155'],audit_count=False)[0];e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.uc.mem_write(0x40a73000,binary.read_bytes());assert e.call(0x40a73000)==0
print('PASS exhaustive81901 native SPEAK interpolation values, exact signed divide-by6 including both endpoints',flush=True)
