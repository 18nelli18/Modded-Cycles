"""Noyau HALL identique, compile pour la vitesse dans le trou PUNCH reserve."""
import subprocess,re
CODE=0x468a6000
END=0x468ae000
def prepare(root,build):
 root=root.resolve();src=root/'tools/machines/fx_menu';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 # Les etats restent ceux du module FX ; reset et queues gardent leurs adresses.
 original=build/'fx.elf'
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(original)],text=True).splitlines() if len(v:=line.split())==3}
 names=('hall_w','hall_fill','hall_pos','hall_apfill','hall_decay','hall_tone','hall_low','hall_previous','hall_error','ps_comb','ps_ap')
 text=(src/'hall.c').read_text().replace('static u32 hall_', 'extern u32 hall_').replace('static s32 hall_', 'extern s32 hall_').replace('void fx_hall(', 'void fx_hall_hot(')
 source=build/'hall-hot145.c';source.write_text(text);obj=build/'hall-hot145.o';elf=build/'hall-hot145.elf';binary=build/'hall-hot145.bin';ld=build/'hall-hot145.ld'
 flags=['-mcpu=54418','-O3','-funroll-loops','-ffreestanding','-fno-builtin','-fno-pic','-ffunction-sections','-fdata-sections','-DFX_POLISH=1','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(src)]
 subprocess.run([cross+'gcc.exe',*flags,'-c',str(source),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} hall_hot_end = .; .data : {{ *(.data*) }} .bss (NOLOAD) : {{ *(.bss*) *(COMMON) }} }}\n'+''.join(f'{name} = {sy[name]:#x};\n' for name in names))
 subprocess.run([cross+'ld.exe','--gc-sections','-e','fx_hall_hot','-T',str(ld),'-o',str(elf),str(obj)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 hot={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert hot['hall_hot_end']<END
 return binary.read_bytes(),dict(code=CODE,end=hot['hall_hot_end'],entry=hot['fx_hall_hot'],old_entry=sy['fx_hall'],aliases={name:sy[name] for name in names})
