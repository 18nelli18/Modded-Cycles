"""Horodater l'entree applicative avant les menus qui consomment DATA."""
import struct,subprocess
CODE=0x468d0180
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,TAIL
 fx=meta['fx_menu']['symbols'];at=0x400775f8;old=bytes(prefix[at-BASE:at-BASE+6]);assert old[:2]==b'\x4e\xf9';previous=int.from_bytes(old[2:6],'big')
 text=f'''.text
.globl ui210_encoder
ui210_encoder:
 move.l %d0,-(%sp)
 move.l 0xfc07000c,%d0
 move.l %d0,{fx['last_input']:#x}
 moveq #1,%d0
 move.l %d0,{fx['input_seen']:#x}
 move.l (%sp)+,%d0
 jmp {previous:#x}
'''
 p=build/'ui_idle210.S';p.write_text(text);obj=p.with_suffix('.o');elf=p.with_suffix('.elf');binary=p.with_suffix('.bin');cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(p),'-o',str(obj)],check=True);subprocess.run([cross+'ld.exe','-e','ui210_encoder','-Ttext',hex(CODE),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 code=binary.read_bytes();assert CODE+len(code)<=0x468d0200 and not any(tail[CODE-TAIL:CODE-TAIL+len(code)])
 patch(CODE,bytes(len(code)),code,tail);patch(at,old,b'\x4e\xf9'+struct.pack('>I',CODE),prefix)
 return dict(encoder=CODE,encoder_bytes=len(code),previous_encoder=previous,idle_ticks=135168000,idle_seconds=1,preserves_audio=True,settings_remain_dirty_until_saved=True,scope=['Filter','LFO polarity','LFO count','LFO3/4','Groove'])
