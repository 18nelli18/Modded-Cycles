"""Compiler Shadow dans le padding des anciennes metadonnees, jamais dans le DSP existant."""
from pathlib import Path
import math,subprocess
CODE=0x4678b200;BSS=0x4678ca00;END=0x4678d000

def prepare(root,build,punch_distortion=False):
 src=root/'tools/machines/shadow';inc=[round(2**32*440*2**((n-69)/12)/48000) for n in range(129)];sine=[round(32767*math.sin(2*math.pi*i/256)) for i in range(256)]
 (src/'shadow_tables.h').write_text('/* Tables mathematiques originales, 48kHz. */\nstatic const u32 SH_INC[129]={'+','.join(map(str,inc))+'};\nstatic const s16 SH_SINE[256]={'+','.join(map(str,sine))+'};\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');obj=build/'shadow.o';ld=build/'shadow.ld';elf=build/'shadow.elf';binary=build/'shadow.bin'
 subprocess.run([cross+'gcc.exe','-mcpu=54418',*(['-DSHADOW_PUNCH_DISTORTION=1'] if punch_distortion else []),'-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src/'shadow.c'),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} shadow_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} shadow_end = .; }}')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['shadow_code_end']<BSS and sy['shadow_end']<END
 return binary.read_bytes(),dict(code=CODE,bss=BSS,end=sy['shadow_end'],symbols=sy,code_bytes=binary.stat().st_size,machine=19,name='Shadow',inspiration='Opal Dust by Fors',implementation='original fixed-point pulsar prototype',oscillators=3,controls=['Grain','Density','Spread','Chaos'],punch_distortion=punch_distortion,punch_drive=(4 if punch_distortion else None),status='experimental',hardware_tested=False)
