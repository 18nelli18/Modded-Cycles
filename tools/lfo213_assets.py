"""LFO2 complet au reload : fichier annexe par projet, 96 patterns x6 pistes."""
import struct,subprocess
CODE=0x468fb000;BSS=0x468fbf00;END=0x468fc000

def apply(root,build,prefix,tail,meta,patch,workflow=False,full_bank=False):
 from gen_governor_recovery_test import BASE,TAIL
 CODE,BSS,END=(0x468fd000,0x468fff00,0x46900000) if full_bank else (0x468fb000,0x468fbf00,0x468fc000)
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 mx=meta['four_lfos'];aliases={k:v for k,v in mx['aliases'].items() if k in ('lf2_context','lf2n_epoch','lf2n_seen')}
 aliases.update(xp_quiet=meta['fx_menu']['symbols']['fx_input_quiet'],xp_crc=meta['fx_project']['symbols']['fxp_crc'])
 aliases.update(memcpy=0x4008f1f0,memset=0x4008f238)
 aliases.update(xp_copy_prepare=mx['symbols']['mx_copy_prepare'],xp_pattern=mx['symbols']['mx_pattern'])
 aliases['xp_polarity']=mx['symbols']['mx_polarity']
 assert (mx['end']<=CODE) if full_bank else (meta['braids_scale']['end']<=CODE and END<=mx['bss'])
 if full_bank:tail.extend(bytes(max(0,END-TAIL-len(tail))))
 # SoundCopy contient un en-tete4 puis160 octets de donnees depuis208.
 # Le tag filtre a data+156 doit tenir aussi dans les six allocations.
 for at in (0x40014a02,0x40014bfa,0x40014cb0,0x4006b208,0x4006b3dc,0x4008e172):
  patch(at,bytes.fromhex('487800a0'),bytes.fromhex('487800a4'),prefix)
 hooks=[('xp_old_sync',mx['aliases']['lf2n_sync'],'xp_sync'),('xp_old_frame',mx['symbols']['mx_frame'],'xp_frame'),('xp_old_change',mx['symbols']['mx_change'],'xp_change'),('xp_old_clear',mx['symbols']['mx_clear_pattern'],'xp_clear')]
 hooks.extend([('xp_old_open',mx['symbols']['mx_launch'],'xp_open'),('xp_old_dispatch',mx['symbols']['mx_dispatch'],'xp_dispatch')])
 hooks.append(('xp_old_redraw',mx['symbols']['mx_copy_redraw'],'xp_redraw'))
 hooks.append(('xp_old_command',mx['symbols']['mx_clear_command'],'xp_command'))
 if full_bank:
  hooks.extend([('xp_old_edit',mx['aliases']['lf2_edit'],'xp_edit'),('xp_old_unpack',meta['lfo_polarity']['symbols']['lp_sound_unpack'],'xp_unpack'),('xp_old_pol_set',meta['lfo_polarity']['symbols']['lp_sound_set'],'xp_pol_set'),('xp_old_clip',meta['lfo_polarity']['symbols']['lp_clip_capture'],'xp_clip')])
  aliases.update(xp_lp_one=meta['lfo_polarity']['symbols']['lp_one'],xp_lp_two=meta['lfo_polarity']['symbols']['lp_two'],xp_project_decoding=meta['fx_project']['symbols']['decoding'])
 tramp='.text\n';writes=[]
 for name,at,target in hooks:
  arr,base=(prefix,BASE) if at<TAIL else(tail,TAIL);raw=bytes(arr[at-base:at-base+32]);n=0
  if raw[:2]==bytes.fromhex('4ef9'):
   aliases[name]=int.from_bytes(raw[2:6],'big');writes.append((at,raw[:6],target));continue
  for ins in cs.disasm(raw,at):
   assert not ins.mnemonic.startswith(('b','j')) and 'pc' not in ins.op_str,(name,ins.mnemonic,ins.op_str)
   n+=ins.size
   if n>=6:break
  assert n>=6;tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';writes.append((at,raw[:n],target))
 (build/'xp_tramp.S').write_text(tramp)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in (root/('tools/machines/lfo215/persist.c' if full_bank else 'tools/machines/lfo214/persist.c' if workflow else 'tools/machines/lfo213/persist.c'),build/'xp_tramp.S'):
  obj=build/('xp-'+src.name+'.o');objects.append(str(obj));subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'lfo213.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} xp_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} xp_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*objects],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['xp_code_end']<=BSS and sy['xp_end']<=END
 blob=binary.read_bytes();assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]) and not any(tail[BSS-TAIL:sy['xp_end']-TAIL]);patch(CODE,bytes(len(blob)),blob,tail)
 for at,old,target in writes:patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target])+bytes.fromhex('4e71')*((len(old)-6)//2),prefix if at<TAIL else tail)
 return dict(code=CODE,bss=BSS,end=sy['xp_end'],symbols=sy,aliases=aliases,clipboard_allocation_bytes=164,full_bank=full_bank,heap_bytes=22288 if full_bank else 9232,file='/L2p_<project>.cfg' if full_bank else '/L2x_<project>.cfg',scope='96 patterns x6 tracks: LFO2 fade/start/mode and LFO3/4 polarity; explicit menu/audio pattern synchronization',native_sound_export=False,hardware_tested=False)
