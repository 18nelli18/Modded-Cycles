"""200 : trois banques secondaires, une UI, quatre contributions natives."""
import struct,json,subprocess
CODE=0x46900000;BSS=0x46910000;END=0x46940000
def apply(root,build,prefix,rt,tail,meta,patch,lazy_start=False,count_option=False,wave_safe=False,compact_ram=False):
 from gen_governor_recovery_test import BASE,TAIL,RUNTIME
 CODE,BSS,END=(0x468f4000,0x468fc000,0x46900000) if compact_ram else (0x46900000,0x46910000,0x46940000)
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());native={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 src=root/'tools/machines/lfo168';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 aliases={k:v for k,v in native.items() if k.startswith('lf2')}
 aliases.update({k:v for k,v in meta['lfo_polarity']['symbols'].items() if k in ('lp_one','lp_two','lp_dirty','lp_hook')})
 aliases['fxp_crc']=meta['fx_project']['symbols']['fxp_crc']
 hooks=[('mx_old_dispatch',native['lf2_dispatch'],'mx_dispatch'),('mx_old_prepare',native['lf2_prepare'],'mx_prepare'),('mx_old_key',native['lf2p_menu_key'],'mx_key'),('mx_old_write',native['lf2n_write'],'mx_write'),('mx_old_pol_encoder',meta['lfo_polarity']['symbols']['lp2_encoder'],'mx_pol_encoder'),('mx_old_render',meta['lfo_polarity']['symbols']['lp2_render'],'mx_render'),('mx_old_frame',meta['braids_scale']['symbols']['bq_frame'],'mx_frame'),('mx_old_change',meta['fx_project']['symbols']['fxs_change'],'mx_change')]
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);tramp='.text\n';writes=[]
 for name,at,target in hooks:
  arr,base=(prefix,BASE) if at<TAIL else(tail,TAIL);raw=bytes(arr[at-base:at-base+32]);n=0
  if raw[:2]==bytes.fromhex('4ef9'):
   aliases[name]=int.from_bytes(raw[2:6],'big');writes.append((at,raw[:6],target));continue
  for ins in cs.disasm(raw,at):
   assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic);n+=ins.size
   if n>=6:break
  assert n>=6;tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';writes.append((at,raw[:n],target))
 (build/'mx_tramp.S').write_text(tramp)
 for source in (src/'control.c',src/'hook.S',build/'mx_tramp.S'):
  obj=build/('mx-'+source.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DMX_LAZY_START=1'] if lazy_start else []),*(['-DMX_COUNT_OPTION=1'] if count_option else []),*(['-DLFO_WAVE_SAFE=1'] if wave_safe else []),*(['-DMX_COMPACT_RAM=1'] if compact_ram else []),'-c',str(source),'-o',str(obj)],check=True)
 ld=build/'lfo168.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.mxentry) *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} mx_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss.mxcount) *(.bss*) *(COMMON) }} . = ALIGN(4); mx_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['mx_code_end']<BSS<sy['mx_end']<END
 if count_option:assert sy['mx_count']==BSS and sy['mx_count_entry']==CODE
 if compact_ram:
  assert meta['braids_scale']['symbols']['bq_code_end']<=CODE and sy['mx_code_end']<meta['braids_scale']['bss']
  assert meta['braids_scale']['end']<=BSS
  blob=binary.read_bytes();old=bytes(tail[CODE-TAIL:CODE-TAIL+len(blob)]);assert len(old)==len(blob) and not any(old)
  patch(CODE,old,blob,tail)
  tail.extend(bytes(max(0,sy['mx_end']-TAIL-len(tail))))
 else:
  assert TAIL+len(tail)<CODE;tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(binary.read_bytes().ljust(sy['mx_end']-CODE,b'\0'))
 for at,old,target in writes:patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target])+bytes.fromhex('4e71')*((len(old)-6)//2),prefix if at<TAIL else tail)
 # Seuls les huit lecteurs UI utilisent le contexte selectionne. Audio/storage restent LFO2.
 sites=[0x4016bcfc,0x40172c78,0x40178fdc,0x40179014,0x40184814,0x401848b0,0x40184cc2,0x4018f990]
 for at in sites:patch(at,struct.pack('>I',native['lf2_context']),struct.pack('>I',sy['mx_ui_context']),prefix)
 at=native['lf2_open_callback'];patch(at,struct.pack('>I',native['lf2_launch']),struct.pack('>I',sy['mx_launch']),prefix)
 at=meta['lfo_polarity']['symbols']['lp2_pol_value'];old=bytes(tail[at-TAIL:at-TAIL+6]);patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy['mx_pol_value']),tail)
 at=0x40091cda;patch(at,bytes.fromhex('4ef9')+struct.pack('>I',aliases['lp_hook']),bytes.fromhex('4ef9')+struct.pack('>I',sy['mx_wave']),prefix)
 return dict(compact_ram=compact_ram,pattern_storage_bytes=36928 if compact_ram else 0,count_option=count_option,wave_safe=wave_safe,count_menu="Mod Setup > Global > LFOs: 1/2/3/4" if count_option else None,default_count=2 if count_option else 4,code=CODE,bss=BSS,end=sy['mx_end'],symbols=sy,aliases=aliases,ui_context_reads=sites,lfos_per_audio_track=4,extra_controls='Same eight native controls, quick assign, speed knob and independent polarity',extra_storage='Separate per-project file, 96 patterns; stopped-only writes',lazy_start=lazy_start,extra_service_gate=('successful user LFO-page opening; IPL0; app ready; not loading' if lazy_start else 'automatic UI startup'),native_sound_export=False,extra_native_plocks=False,status='experimental',hardware_tested=False)
