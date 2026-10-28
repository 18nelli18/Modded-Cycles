"""TINY GATE tenu et attaque PUNCH, wrapper entier du moteur resident."""
import struct,subprocess
CODE=0x468f6000;BSS=0x468f6f00;END=0x468f7000

def apply(root,build,rt,tail,patch,meta):
 from gen_governor_recovery_test import RUNTIME,TAIL
 assert meta['four_lfos']['symbols']['mx_code_end']<=CODE and meta['page_length']['code']>=END
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 old=bytes(rt[0x4677c000-RUNTIME:0x4677c008-RUNTIME]);assert old.hex()=='4e56ffdc206e000c'
 tramp=build/'tiny212_tramp.S';tramp.write_text('.text\n.globl tn_old_update\ntn_old_update:\n.byte '+','.join(map(str,old))+'\njmp 0x4677c008\n')
 objs=[]
 for src in (root/'tools/machines/tiny212/tiny212.c',tramp):
  obj=build/(src.name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-Werror','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-c',str(src),'-o',str(obj)],check=True);objs.append(str(obj))
 ld=build/'tiny212.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} tn_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} tn_end = .; }}')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*objs],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert sy['tn_code_end']<BSS and sy['tn_end']<=END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]) and not any(tail[BSS-TAIL:sy['tn_end']-TAIL])
 patch(CODE,bytes(len(blob)),blob,tail);patch(0x4677c000,old,b'\x4e\xf9'+struct.pack('>I',sy['tn_update'])+b'\x4e\x71',rt)
 return dict(code=CODE,code_bytes=len(blob),symbols=sy,gate_sustain=True,state_stride=16,restore_native_decay=True,native_physical_envelopes_preserved=True,punch='12-semitone pitch snap, exponential 7/8 per32-frame block',hardware_tested=False)

