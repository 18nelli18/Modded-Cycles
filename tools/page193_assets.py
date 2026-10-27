"""Page Len1..16 dans ScaleMenuView, compteur natif, codec d'en-tete."""
import struct,subprocess
CODE=0x468f7000;END=0x468fa000
def apply(root,build,prefix,rt,tail,meta,patch,dark=False,warp=False,grid=False):
 from gen_governor_recovery_test import BASE,TAIL
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 entries=[('pl_old_decode',0x4005b3b4,8,'pl_decode','4feffff448d70c04'),('pl_old_init',0x40061526,6,'pl_init','206f00044a88'),('pl_old_led',0x4002fd38,8,'pl_led','4fefffcc48d73cfc')]
 if warp:entries += [('wp_old_insert',0x4009203c,8,'wp_insert','4fefffec48d70c1c'),('wp_old_schedule',0x40091f82,8,'wp_schedule','2f0a2f02202f000c'),('wp_old_cancel',0x40091fdc,8,'wp_cancel','4feffff448d70c04')]
 if grid:entries += [('pg_old_led',0x40021d22,8,'pg_led','4fefffac48d77cfc'),('pg_old_key',0x40022382,8,'pg_key','4e56ffa048d73cfc')]
 tramp='.text\n'
 for name,at,size,target,guard in entries:
  old=bytes(prefix[at-BASE:at-BASE+size]);assert old.hex()==guard
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,old))+f'\njmp {at+size:#x}\n'
 (build/'page193_tramp.S').write_text(tramp);objs=[]
 for src in [root/'tools/machines/page193/page193.c',root/'tools/machines/page193/page193.S',build/'page193_tramp.S']+([root/'tools/machines/page193/warp195.c',root/'tools/machines/page193/warp195.S'] if warp else []):
  obj=build/(src.name+'.o');subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra',*(['-DPAGE_DARK194=1'] if dark else []),*(['-DPAGE_WARP195=1'] if warp else []),*(['-DPAGE_GRID197=1'] if grid else []),'-c',str(src),'-o',str(obj)],check=True);objs.append(str(obj))
 ld=build/'page193.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 previous=int.from_bytes(prefix[0x4002f7da-BASE:0x4002f7de-BASE],'big');assert previous==0x401bb604
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); pl_code_end = .; .bss 0x468f9e00 (NOLOAD) : {{ *(.bss*) *(COMMON) }} pl_end = .; }}\npl_previous_menu = {previous:#x};' if warp else f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); pl_end = .; }}\npl_previous_menu = {previous:#x};')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*objs],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes();assert sy['pl_end']<END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]);patch(CODE,bytes(len(blob)),blob,tail)
 if warp:assert sy['pl_code_end']<=0x468f9e00 and not any(tail[0x468f9e00-TAIL:sy['pl_end']-TAIL])
 for _,at,size,target,guard in entries:
  patch(at,bytes.fromhex(guard),b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((size-6)//2),prefix)
 for at,guard,target in [(0x40055344,'528118814a2a77cb','pl_step_hook'),(0x40055442,'716a77c624331c00','pl_master_hook'),(0x4002f7d8,'4ef9401bb604','pl_menu_tail')]:
  old=bytes.fromhex(guard);patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((len(old)-6)//2),prefix)
 if warp:
  for at,guard,target in [(0x40054c8a,'4ab940a78630','wp_begin_hook'),(0x400558e2,'7001b0b940a78874','wp_finish_hook')]:
   old=bytes.fromhex(guard);patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((len(old)-6)//2),prefix)
 return dict(code=CODE,code_bytes=len(blob),symbols=sy,default=16,minimum=1,maximum=16,pattern_header_tag_offset=60,physical_page_stride=16,base='v191',inactive_steps_dark=dark,warp=warp,grid_inactive_dark=grid,hardware_tested=False)
