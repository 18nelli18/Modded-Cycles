"""ACID filtre/Accent et SY BITS fin ; cave libre46840000, IDs conserves."""
import struct,subprocess
CODE=0x46840000;BSS=0x46848000;END=0x46850000
def apply(root,build,prefix,rt,tail,meta,patch,fx,tiny,shadow_gain=False,shadow_extra=False,punch=None,acid_fast=False,acid_hot=False):
 from gen_governor_recovery_test import TAIL,RUNTIME
 src=root/'tools/machines/fundamentals';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 def target(buf,base,at):
  assert buf[at-base:at-base+2]==b'\x4e\xb9';return int.from_bytes(buf[at-base+2:at-base+6],'big')
 stub=target(prefix,0x40000400,0x4000b82a)
 editbuf,editbase=(tail,TAIL) if stub>=TAIL else (rt,RUNTIME)
 off=stub-editbase;call=editbuf.find(b'\x4e\xb9',off,off+48);assert call>=off
 original=target(editbuf,editbase,call+editbase)
 old_popup=int.from_bytes(prefix[0x401005bc-0x40000400:0x401005bc-0x40000400+4],'big')
 frame=fx['symbols']['fx_frame_begin'];fc=tail.find(b'\x4e\xb9',frame-TAIL,frame-TAIL+48);assert fc>=frame-TAIL
 assert target(tail,TAIL,fc+TAIL)==fx['symbols']['fx_frame_prepare']
 objects=[]
 for name in ['acid.c','bits.c','bits.S','gain.S','elder-gain.S']:
  obj=build/('fund-'+name.replace('.','-')+'.o');objects.append(obj)
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2',*(['-O3','-funroll-loops','-fwrapv','-DACID_FAST153=1'] if acid_fast and name=='acid.c' else []),*(['-DACID_HOT155=1'] if acid_hot and name=='acid.c' else []),*(['-Delder_gain_render=shadow_gain_render','-Delder_render_original=shadow_render_original'] if shadow_gain and name=='elder-gain.S' else []),*(['-DSHADOW_GAIN4=1'] if shadow_extra and name=='elder-gain.S' else []),*(['-DPUNCH_SWEEP=1'] if punch else []),'-DGOV_SKIP','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-c',str(src/name),'-o',str(obj)],check=True)
 ld=build/'fundamentals.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 nm=tiny['machine_count'];table=tiny['data'];elder_original=int.from_bytes(tail[table+4*(nm*2+16)-TAIL:table+4*(nm*2+16)-TAIL+4],'big')
 level_machine=19 if shadow_gain else 16;level_original=int.from_bytes(tail[table+4*(nm*2+level_machine)-TAIL:table+4*(nm*2+level_machine)-TAIL+4],'big');level_symbol='shadow_gain_render' if shadow_gain else 'elder_gain_render'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} . = ALIGN(4); fund_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); fund_end = .; }}\n'+f'PROVIDE(bf_native_edit = {original:#x});\nPROVIDE(bf_native_frame = {fx["symbols"]["fx_frame_prepare"]:#x});\nPROVIDE(bf_native_popup = {old_popup:#x});\nPROVIDE(acid_render_original = acid_render);\nPROVIDE({'shadow_render_original' if shadow_gain else 'elder_render_original'} = {level_original:#x});')
 if punch:ld.write_text(ld.read_text()+f'\nPROVIDE(punch_turn = {punch["symbols"]["punch_turn"]:#x});\n')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['fund_code_end']<BSS and sy['fund_end']<END
 blob=binary.read_bytes().ljust(sy['fund_end']-CODE,b'\0');assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]);patch(CODE,bytes(len(blob)),blob,tail)
 patch(call+editbase+2,struct.pack('>I',original),struct.pack('>I',sy['bf_edit']),editbuf)
 patch(fc+TAIL+2,struct.pack('>I',fx['symbols']['fx_frame_prepare']),struct.pack('>I',sy['bf_prepare']),tail)
 patch(0x401005bc,struct.pack('>I',old_popup),struct.pack('>I',sy['bf_popup']),prefix)
 nm=tiny['machine_count'];table=tiny['data']
 for row,machine,sym in [(1,13,'acid_update'),(2,13,'acid_gain_render'),(2,level_machine,level_symbol)]:
  at=table+4*(nm*row+machine);old=bytes(tail[at-TAIL:at-TAIL+4]);assert int.from_bytes(old,'big')!=0;patch(at,old,struct.pack('>I',sy[sym]),tail)
 return dict(code=CODE,bss=BSS,end=sy['fund_end'],code_bytes=binary.stat().st_size,symbols=sy,acid_velocity_accent=[97,127],elder_gain_db=(0 if shadow_gain else 6.0206),shadow_gain_db=(12.0412 if shadow_extra else 6.0206 if shadow_gain else 0),elder_render_original=elder_original,level_render_original=level_original,bits_fine='FUNC + COLOR',bits_resolution='0.01 semitone (native Q8 quantization)',hardware_tested=False)
