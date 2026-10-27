"""195 : onde Uni/Bi apres fade natif, avant profondeur signee."""
import struct,subprocess,json
CODE=0x468e0000;BODY=0x468e1000;BSS=0x468e8000;END=0x468f0000
def apply(root,build,prefix,rt,tail,meta,patch,wave_safe=False,sound_polarity=False,sound_copy=False,copy_live=False,copy_track_lookup=False,copy_command=False,copy_four=False,clear_commit=False):
 from gen_governor_recovery_test import BASE,TAIL
 src=root/'tools/machines/polarity163';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());native={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 aliases={**{k:v for k,v in native.items() if k.startswith('lf2')},'lp1_old_count':0x40072514,'lp1_old_widget':0x4007292a,'lp1_old_key':int.from_bytes(prefix[0x401016c8-BASE:0x401016cc-BASE],'big'),'lp1_old_encoder':int.from_bytes(prefix[0x401016cc-BASE:0x401016d0-BASE],'big'),'sx_track':meta['scramble_mask']['symbols']['sx_track']}
 # Prologues sans branche, rejoues par des trampolines gardes.
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);tramp='.text\n';hooks=[]
 extra_hooks=[('lp_old_sound_write',native['lf2n_write'],'lp_sound_write'),('lp_old_sound_pack',native['lf2n_pack'],'lp_sound_pack_entry'),('lp_old_sound_unpack',native['lf2n_unpack'],'lp_sound_unpack_entry'),('lp_old_sound_init',native['lf2n_init'],'lp_sound_init_entry')] if sound_polarity else []
 if copy_command:extra_hooks += [('lp_old_copy_command',0x40014bd2,'lp_copy_command'),('lp_old_paste_command',0x40014c88,'lp_paste_command')]
 for name,at,target in [('lp2_old_encoder',native['lf2p_enc'],'lp2_encoder'),('lp_old_frame',meta['groove_strum']['symbols']['gc_frame'],'lp_ui_frame')]+extra_hooks:
  arr,base=(prefix,BASE) if at<TAIL else(tail,TAIL);raw=bytes(arr[at-base:at-base+24]);n=0
  if raw[:2]==bytes.fromhex('4ef9'):
   aliases[name]=int.from_bytes(raw[2:6],'big');hooks.append((at,raw[:6],target));continue
  for ins in cs.disasm(raw,at):
   assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic);n+=ins.size
   if n>=6:break
  assert n>=6;tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';hooks.append((at,raw[:n],target))
 (build/'lp_tramp.S').write_text(tramp)
 (build/'lp_entry.S').write_text('.section .lpentry,"ax"\n.globl lp_entry\nlp_entry: jmp lp_frame\n')
 for source in [src/'control.c',src/'hook.S',src/'state.S',src/'ui.c',src/'ui.S',src/'layout.S',*([src/'sound176.c',src/'sound176.S'] if sound_polarity else []),*([src/'sound_copy177.c'] if sound_copy else []),build/'lp_entry.S',build/'lp_tramp.S']:
  obj=build/(source.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DLFO_WAVE_SAFE=1'] if wave_safe else []),*(['-DLFO_SOUND_POL=1'] if sound_polarity else []),*(['-DLFO_COPY_LIVE=1'] if copy_live else []),*(['-DLFO_TRACK_LOOKUP=1'] if copy_track_lookup else []),*(['-DLFO_COPY_COMMAND=1'] if copy_command else []),*(['-DLFO_COPY_FOUR=1'] if copy_four else []),*(['-DLFO_CLEAR_COMMIT188=1'] if clear_commit else []),'-c',str(source),'-o',str(obj)],check=True)
 ld=build/'polarity163.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .lpentry {CODE:#x} : {{ *(.lpentry) }} .text {BODY:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} lp_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss.lpstate) *(.bss*) *(COMMON) }} . = ALIGN(4); lp_end = .; }}\nPROVIDE(lp_context = 0x40184808);\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.lpentry','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['lp_one']==BSS and sy['lp_two']==BSS+24 and sy['lp_dirty']==BSS+48 and sy['lp_code_end']<BSS<sy['lp_end']<END
 assert TAIL+len(tail)<=CODE
 tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(binary.read_bytes().ljust(sy['lp_end']-CODE,b'\0'))
 old=bytes.fromhex('75147a207342');at=0x40091cda
 patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy['lp_hook']),prefix)
 for at,target in [(0x40101650,'lp1_count'),(0x40101654,'lp1_widget_get'),(0x401016c8,'lp1_key'),(0x401016cc,'lp1_encoder'),(0x401016e4,'lp1_key_sub'),(0x40101730,'lp1_encoder_sub')]:
  off=at-BASE;patch(at,bytes(prefix[off:off+4]),struct.pack('>I',sy[target]),prefix)
 at=native['lf2p_render'];patch(at,bytes(prefix[at-BASE:at-BASE+6]),bytes.fromhex('4ef9')+struct.pack('>I',sy['lp2_render']),prefix)
 for at,old,target in hooks:patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target])+bytes.fromhex('4e71')*((len(old)-6)//2),prefix if at<TAIL else tail)
 if sound_copy:
  # Tous les constructeurs SoundCopy sont agrandis ; destructeurs natifs inchanges.
  for at in (0x40014a02,0x40014bfa,0x40014cb0,0x4006b208,0x4006b3dc,0x4008e172):
   patch(at,bytes.fromhex('48780068'),bytes.fromhex('487800a0' if copy_four else '48780080'),prefix)
  for at in (0x40014a86,0x40014c1e,0x40014cd4,0x4006b226,0x4006b3f8,0x4008e19a):
   patch(at,bytes.fromhex('4eb94008f1f0'),bytes.fromhex('4eb9')+struct.pack('>I',sy['lp_clip_capture']),prefix)
  for at in (0x40014b8e,0x40014d3c):
   patch(at,bytes.fromhex('4eb94008f1f0'),bytes.fromhex('4eb9')+struct.pack('>I',sy['lp_clip_restore']),prefix)
 return dict(copy_four=copy_four,copy_command=copy_command,copy_live=copy_live,sound_copy=sound_copy,sound_polarity=sound_polarity,sound_encoding="tagA0 in MULT2 low byte; mixed-radix record88..91; legacy fallback" if sound_polarity else None,wave_safe=wave_safe,code=CODE,end=sy['lp_end'],code_end=sy['lp_code_end'],symbols=sy,aliases=aliases,default='Bi',menu='Pol. in LFO1 and LFO2 menus',settings_file='/LfoPol.cfg',scope=('native sound for tagged/new sounds; previous global preference for untagged legacy sounds' if sound_polarity else 'global per track and LFO'),formula='unipolar wave before signed depth; fade-aware offset',status='experimental',hardware_tested=False)
