"""Page Len1..16 dans ScaleMenuView, compteur natif, codec d'en-tete."""
import struct,subprocess
CODE=0x468f7000;END=0x468fa000
def apply(root,build,prefix,rt,tail,meta,patch,dark=False):
 from gen_governor_recovery_test import BASE,TAIL
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 entries=[('pl_old_decode',0x4005b3b4,8,'pl_decode','4feffff448d70c04'),('pl_old_init',0x40061526,6,'pl_init','206f00044a88'),('pl_old_led',0x4002fd38,8,'pl_led','4fefffcc48d73cfc')]
 tramp='.text\n'
 for name,at,size,target,guard in entries:
  old=bytes(prefix[at-BASE:at-BASE+size]);assert old.hex()==guard
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,old))+f'\njmp {at+size:#x}\n'
 (build/'page193_tramp.S').write_text(tramp);objs=[]
 for src in [root/'tools/machines/page193/page193.c',root/'tools/machines/page193/page193.S',build/'page193_tramp.S']:
  obj=build/(src.name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra',*(['-DPAGE_DARK194=1'] if dark else []),'-c',str(src),'-o',str(obj)],check=True);objs.append(str(obj))
 ld=build/'page193.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 previous=int.from_bytes(prefix[0x4002f7da-BASE:0x4002f7de-BASE],'big');assert previous==0x401bb604
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); pl_end = .; }}\npl_previous_menu = {previous:#x};')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*objs],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert sy['pl_end']<END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]);patch(CODE,bytes(len(blob)),blob,tail)
 for _,at,size,target,guard in entries:
  patch(at,bytes.fromhex(guard),b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((size-6)//2),prefix)
 for at,guard,target in [(0x40055344,'528118814a2a77cb','pl_step_hook'),(0x40055442,'716a77c624331c00','pl_master_hook'),(0x4002f7d8,'4ef9401bb604','pl_menu_tail')]:
  old=bytes.fromhex(guard);patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((len(old)-6)//2),prefix)
 return dict(code=CODE,code_bytes=len(blob),symbols=sy,default=16,minimum=1,maximum=16,pattern_header_tag_offset=60,physical_page_stride=16,base='v191',inactive_steps_dark=dark,hardware_tested=False)
