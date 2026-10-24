"""Verrou UI privev42 au-dessus du test Tone/crusherv41, DSP conserve."""
import subprocess,struct,hashlib
CODE=0x467ff000;BSS=0x467ffe00
def apply(root,build,tail,meta,patch,advanced=False):
 from gen_governor_recovery_test import TAIL
 sy=meta['beat_repeat_symbols'];at=sy['br_key'];old=bytes(tail[at-TAIL:at-TAIL+8]);assert old.hex()=='4feffff4206f0010'
 tramp=build/'bl_tramp.S';tramp.write_text('.text\n.globl bl_native\nbl_native:\n.byte '+','.join(map(str,old))+f'\njmp {at+8:#x}\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in (root/'tools/machines/repeat_latch/latch.c',tramp):
  obj=build/(src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror',*(['-DFX_TEMP_SHORTCUTS=1'] if advanced else []),'-c',str(src),'-o',str(obj)],check=True)
 track_at=sy['br_old_track_keys'];track_old=bytes(tail[track_at-TAIL:track_at-TAIL+4]);aliases={k:sy[k] for k in ('br_keys','br_cancel','br_popup')};aliases['bl_previous_track']=int.from_bytes(track_old,'big');ld=build/'latch.ld';elf=build/'latch.elf';binary=build/'latch.bin'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); bl_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); bl_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 symbols={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 assert symbols['bl_code_end']<BSS and symbols['bl_end']<0x46800000 and TAIL+len(tail)<CODE
 blob=binary.read_bytes().ljust(symbols['bl_end']-CODE,b'\0');tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(blob)
 patch(at,old,b'\x4e\xf9'+struct.pack('>I',symbols['bl_key'])+b'\x4e\x71',tail)
 patch(track_at,track_old,struct.pack('>I',symbols['bl_track_keys']),tail)
 return dict(symbols=symbols,code=CODE,bss=BSS,end=symbols['bl_end'],code_bytes=binary.stat().st_size,sha256=hashlib.sha256(blob).hexdigest(),status='experimental',hardware_tested=False,momentary_steps=True,double_tap_ms=350,exit='BACK',edit_shortcuts_blocked=True,plain_transport_retained=True)
