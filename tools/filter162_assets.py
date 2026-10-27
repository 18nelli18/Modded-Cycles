"""194 : filtre partage a quatre types et popup TRACK+SWEEP."""
import struct,subprocess,json
CODE=0x468d0000;BODY=0x468d1000;BSS=0x468d8000;END=0x468e0000
def apply(root,build,prefix,rt,tail,meta,patch,center=False,gesture=False,key_guard=False,native_keys=False,defaults=False,ui_idle=False):
 from gen_governor_recovery_test import TAIL,RUNTIME
 src=root/'tools/machines/filter162';cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());native={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 aliases=dict(fc_low=meta['recovery_symbols']['pf_run'],sx_track=meta['scramble_mask']['symbols']['sx_track'],fc_native_table=native['filt_coef'],fc_track_used=meta['fx_menu']['symbols']['track_used'],menu=meta['symbols']['menu'],fc_params=meta['playability_symbols']['mm_params'],fc_native_draw={**meta['groove_strum']['aliases'],**meta['groove_strum']['symbols']}['gc_previous_draw'])
 if gesture:aliases['fc_wf_api']=meta['symbols']['wf_api']
 if native_keys:
  aliases['fc_previous_early_key']=meta['fx_menu']['symbols']['fx_key_hook']
 if ui_idle:aliases['fc_input_quiet']=meta['fx_menu']['symbols']['fx_input_quiet']
 objects=[]
 for name in (('control162b.c' if center else 'control.c'),'coeff.c','fc_high.S','fc_band.S','fc_lohi_low.S','entry.S','dispatch.S'):
  obj=build/('fc-'+name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418',*(['-DUI_IDLE210=1'] if ui_idle else []),'-O2','-fwrapv','-DPF_PAIR_OPT=1',*(['-DFILTER_GESTURE200=1'] if gesture else []),*(['-DFILTER_KEYS202=1'] if key_guard else []),*(['-DFILTER_NATIVE_KEYS203=1'] if native_keys else []),*(['-DFILTER_DEFAULTS208=1'] if defaults else []),'-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src/name),'-o',str(obj)],check=True)
 ld=build/'filter162.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin');ld.write_text(f'SECTIONS {{ .fcentry {CODE:#x} : {{ *(.fcentry) }} .fcextra {CODE+0x200:#x} : {{ *(.fcextra) }} fc_extra_end = .; .text {BODY:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} fc_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); fc_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data','-j','.fcentry','-j','.fcextra',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert sy['fc_extra_end']<=BODY and sy['fc_code_end']<0x468d2000<BSS<sy['fc_end']<END
 assert sy['fc_turn']==CODE and sy['fc_draw']==CODE+16 and sy['fc_frame']==CODE+32 and meta['click_repair']['end']<CODE
 at=0x467a539a;old=bytes.fromhex('4ef9')+struct.pack('>I',aliases['fc_low']);patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy['fc_dispatch']),rt)
 assert TAIL+len(tail)<CODE;tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(binary.read_bytes().ljust(sy['fc_end']-CODE,b'\0'))
 if native_keys:
  at=meta['beat_repeat_symbols']['br_key_hook'];old=b'\x4e\xf9'+struct.pack('>I',aliases['fc_previous_early_key']);assert bytes(tail[at-TAIL:at-TAIL+6])==old
  patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy['fc_prekey']),tail)
 if defaults:
  at=0x400141da;old=bytes.fromhex('4eb9400618f2');patch(at,old,bytes.fromhex('4eb9')+struct.pack('>I',sy['fc_new_sound']),prefix)
 return dict(code=CODE,bss=BSS,end=sy['fc_end'],code_end=sy['fc_code_end'],symbols=sy,aliases=aliases,types=['HIGH','LOW','BAND','LO/HI'],default='LOW',reset_new_clear=defaults,reset_cutoff=127 if defaults else None,gesture='SETTINGS + MACHINES + SWEEP' if gesture else 'TRACK + SWEEP',lohi_center=64,settings='global per track /Filter.cfg',wizard_internal_unchanged=True,center_on_select=center,machines_key_owned=key_guard,native_key_type_guard=native_keys,early_global_key_guard=native_keys,status='experimental',hardware_tested=False)
