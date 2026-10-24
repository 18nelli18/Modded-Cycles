"""RETROSYN additionnel prive22 : moteur historique et IDs existants conserves."""
import subprocess,struct,json,os
from pathlib import Path
CODE=0x468b0000;ART=0x468bb000;BSS=0x468bc000;END=0x468c0000
def prepare(root,build):
 root=root.resolve();src=root/'tools/machines/retrosyn';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 c=build/'retrosyn-private.c';c.write_text('#include "'+str(src/'retrosyn.c').replace('\\','/')+'"\nconst char retrosyn_name[]="RETROSYN";\nconst char retrosyn_labels[5][8]={"Color","Shape","Sweep","Contour","Decay"};\nconst char retrosyn_short_labels[5][8]={"COLR","SHAP","SWEP","CONT","DEC"};\n')
 obj=build/'retrosyn-private.o';elf=build/'retrosyn-private.elf';binary=build/'retrosyn-private.bin';ld=build/'retrosyn-private.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(c),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); retrosyn_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); retrosyn_end = .; }}')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 s={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert s['retrosyn_code_end']<ART and s['retrosyn_end']<END
 from build_machine_identity_test import stats,icon,encode
 profile=dict(machine=22,name='RETROSYN',icon='R',**{'class':'SYNTH'},style='CHIP',str=3,dex=5,mag=4)
 blob=bytearray(binary.read_bytes().ljust(s['retrosyn_end']-CODE,b'\0'));pos=ART+56
 for desc,pixels,w,h in [(ART,stats(profile),48,33),(ART+28,icon(profile),34,34)]:
  mask=encode([[1]*w for _ in range(h)]);ptr=pos;blob[pos-CODE:pos-CODE+len(pixels)]=pixels;pos+=len(pixels);mp=pos;blob[pos-CODE:pos-CODE+len(mask)]=mask;pos+=len(mask);blob[desc-CODE:desc-CODE+28]=struct.pack('>7I',0x401117c8,w,h,2,ptr,mp,0)
 assert pos<BSS
 return bytes(blob),dict(code=CODE,bss=BSS,end=s['retrosyn_end'],code_bytes=binary.stat().st_size,symbols=s,profile=profile,machine=22,private_only=True)
