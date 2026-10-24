"""Menus FX prives v55 : relais gardes, aucun firmware public modifie."""
import subprocess,struct,hashlib
CODE=0x46800000;BSS=0x46808000

def apply(root,build,prefix,tail,meta,patch,settings_shortcuts=False,overlay=False,dust=False,new_delays=False,delay_repair=False,delay_quality=False,shimmer_clean=False,octave_delay=False,octave_polish=False,cloud=False,cloud_repair=False,ps1=False,cpu_opt=False,dx_func_fix=False,idle_opt=False,voice_opt=False,active_opt=False,ps1_cache_opt=False,ps1_fast_opt=False,lean_fx=False,no_shimmer=False,speak=False,cheap_fx=False,dub_distinct=False):
 from gen_governor_recovery_test import BASE,TAIL
 ch=meta['stereo_chorus'];cr=meta['delay_crush'];bl=meta['repeat_latch'];br=meta['beat_repeat_symbols']
 aliases={k:cr['symbols'][k] for k in ('cr_mode','cr_rate','cr_bits','cr_send','cr_post')}
 if lean_fx:aliases['cr_service']=cr['symbols']['cr_service']
 aliases.update({k:ch['symbols'][k] for k in ('ch_mode','ch_state','ch_chorus')})
 aliases.update({k:bl['symbols'][k] for k in ('bl_latched','bl_physical','bl_function')})
 aliases.update({k:meta['dx_symbols'][k] for k in ('dx_enabled','dx_peak','dx_over','dx_new','dx_beat_api')})
 aliases.update({k:meta['recovery_symbols'][k] for k in ('gr_diag_sum','gr_diag_blocks')})
 aliases.update({k:br[k] for k in ('br_keys','br_cancel')})
 aliases.update(fx_side=br['br_side'],fx_side_on=br['br_side_on'],ch_native=0x400579c4,
  fx_previous_encoder=cr['symbols']['cr_encoder_hook'],fx_native_encoder=ch['aliases']['ch_previous_encoder'],
  fx_previous_draw=cr['symbols']['cr_draw'],fx_previous_popup=ch['aliases']['ch_previous_popup'],
  fx_native_keys=bl['symbols']['bl_native'],fx_notice=cr['aliases']['cr_notice'],menu=ch['aliases']['menu'])
 if new_delays:aliases.update(fx_delay_previous=cr['symbols']['cr_fx'],fx_delay_state=cr['symbols']['cr_state'],fx_legacy_split=cr['symbols']['cr_split'])
 if settings_shortcuts:aliases['fx_wf_api']=meta['symbols']['wf_api']
 tramp='.text\n'
 entries=[('fx_query_original',0x4007faf4,6,prefix,'2f02202f0008'),('fx_key_original',br['br_key_hook'],8,tail,'4feffff048d70302')]
 for name,at,n,area,expected in entries:
  offset=at-(BASE if area is prefix else TAIL);old=bytes(area[offset:offset+n]);assert old.hex()==expected,(name,old.hex())
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,old))+f'\njmp {at+n:#x}\n'
 ts=build/'fx_tramp.S';ts.write_text(tramp)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in [root/'tools/machines/fx_menu'/n for n in ('dsp.c',('ping.c' if no_shimmer else 'delays.c'),'control.c','popup.c','keys.c','hooks.S','show.S')]+([root/'tools/machines/fx_menu/cloud.c'] if cloud else [])+([root/'tools/machines/fx_menu/ps1.c'] if ps1 else [])+([root/'tools/machines/fx_menu/ps1_fast.c',root/'tools/machines/fx_menu/ps1_hot.S'] if ps1_fast_opt else [])+([root/'tools/machines/fx_menu/room.c',root/'tools/machines/fx_menu/dub.S'] if cheap_fx else [])+[ts]:
  obj=build/('fx_'+src.name+'.o');objects.append(obj)
  opt=['-O3','-fno-unroll-loops'] if active_opt and src.name=='dsp.c' else ['-O3','-funroll-loops'] if cpu_opt and src.name in ('delays.c','ps1.c','ps1_fast.c','room.c') else ['-O2']
  subprocess.run([cross+'gcc.exe','-mcpu=54418',*opt,'-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DFX_SETTINGS_SHORTCUTS=1'] if settings_shortcuts else []),*(['-DFX_OVERLAY_MENU=1'] if overlay else []),*(['-DFX_DUST=1'] if dust else []),*(['-DFX_NEW_DELAYS=1'] if new_delays else []),*(['-DFX_DELAY_REPAIR=1'] if delay_repair else []),*(['-DFX_DELAY_QUALITY=1'] if delay_quality else []),*(['-DFX_SHIMMER_CLEAN=1'] if shimmer_clean else []),*(['-DFX_OCTAVE_DELAY=1'] if octave_delay else []),*(['-DFX_OCTAVE_POLISH=1'] if octave_polish else []),*(['-DFX_CLOUD=1'] if cloud else []),*(['-DFX_CLOUD_REPAIR=1'] if cloud_repair else []),*(['-DFX_PS1=1'] if ps1 else []),*(['-DFX_CPU_OPT=1'] if cpu_opt else []),*(['-DFX_DX_FUNC_FIX=1'] if dx_func_fix else []),*(['-DFX_IDLE_OPT=1'] if idle_opt else []),*(['-DFX_VOICE_OPT=1'] if voice_opt else []),*(['-DFX_PS1_CACHE_OPT=1'] if ps1_cache_opt else []),*(['-DFX_LEAN_FX=1'] if lean_fx else []),*(['-DFX_NO_SHIMMER=1'] if no_shimmer else []),*(['-DFX_SPEAK=1'] if speak else []),*(['-DFX_CHEAP=1'] if cheap_fx else []),*(['-DFX_DUB_DISTINCT=1'] if dub_distinct else []),*(['-Dfx_ps1=fx_ps1_cold'] if ps1_fast_opt and src.name=='ps1.c' else []),'-c',str(src),'-o',str(obj)],check=True)
  if ps1_fast_opt and src.name=='ps1.c':
   subprocess.run([cross+'objcopy.exe',*['--globalize-symbol='+n for n in ('ps_comb','ps_ap','ps_low','ps_filter','ps_previous','ps_w','ps_filled','ps_pos','ps_fill','ps_decay','ps_tone')],str(obj)],check=True)
 ld=build/'fx.ld';elf=build/'fx.elf';binary=build/'fx.bin'
 text_inputs='EXCLUDE_FILE (*fx_ps1_fast.c.o *fx_ps1_hot.S.o) *(.text* .rodata*)' if ps1_fast_opt else '*(.text*) *(.rodata*)'
 hot_section=' .ps1hot 0x46830000 : { *fx_ps1_fast.c.o(.text* .rodata*) *fx_ps1_hot.S.o(.text* .rodata*) } . = ALIGN(4); fx_hot_end = .; fx_end = .;' if ps1_fast_opt else ' fx_end = .;'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ {text_inputs} }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); fx_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); fx_bss_end = .; {hot_section} }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 assert sy['fx_code_end']<BSS and sy['fx_end']<(0x46840000 if ps1 else 0x46830000 if cloud else 0x46820000 if delay_quality else 0x46818000 if new_delays else 0x46810000)
 blob=binary.read_bytes().ljust(sy['fx_end']-CODE,b'\0')
 hot_size=0
 if ps1_fast_opt:
  assert ps1_cache_opt and not cloud and sy['fx_bss_end']<=0x46830000
  hot_binary=build/'ps1-hot.bin';subprocess.run([cross+'objcopy.exe','-O','binary','-j','.ps1hot',str(elf),str(hot_binary)],check=True)
  hot_raw=hot_binary.read_bytes();hot_size=len(hot_raw);offset=0x46830000-CODE
  blob=blob[:offset]+hot_raw+blob[offset+hot_size:];assert len(blob)==sy['fx_end']-CODE
 assert TAIL+len(tail)<CODE
 tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(blob)
 def j(addr):return b'\x4e\xf9'+struct.pack('>I',addr)
 if cheap_fx:
  assert speak and no_shimmer and ps1_fast_opt
  assert sy['fx_bss_end']<=0x46818000, 'FX BSS overlaps SPEAK'
  patch(0x400574bc,bytes.fromhex('4bf94013ff84'),j(sy['fx_dub_low_hook']),prefix)
  patch(0x400574d6,bytes.fromhex('41f94013fb84'),j(sy['fx_dub_high_hook']),prefix)
 if delay_repair:patch(0x40057638,bytes.fromhex('22798000b570'),j(sy['fx_delay_read_hook']),prefix)
 if new_delays:patch(0x4005699c,b'\x4e\xb9'+struct.pack('>I',cr['symbols']['cr_fx']),b'\x4e\xb9'+struct.pack('>I',sy['fx_dfx']),prefix)
 patch(0x400775f8,j(aliases['fx_previous_encoder'])+b'\x4e\x71',j(sy['fx_encoder_hook'])+b'\x4e\x71',prefix)
 needle=j(aliases['fx_previous_draw']);hits=[i for i in range(0,ch['code']-TAIL-6,2) if tail[i:i+6]==needle];assert len(hits)==1,hits
 patch(TAIL+hits[0],needle,j(sy['fx_draw']),tail)
 patch(0x40056a2c,b'\x4e\xb9'+struct.pack('>I',ch['symbols']['ch_fx']),b'\x4e\xb9'+struct.pack('>I',sy['fx_rfx']),prefix)
 patch(0x40056b38,j(cr['symbols']['cr_mix_hook'])+b'\x4e\x71'*2,j(sy['fx_mix_hook'])+b'\x4e\x71'*2,prefix)
 patch(0x401005bc,struct.pack('>I',ch['symbols']['ch_popup']),struct.pack('>I',sy['fx_popup']),prefix)
 for name,at,n,area,expected in entries:patch(at,bytes.fromhex(expected),j(sy['fx_query' if name=='fx_query_original' else 'fx_key_hook'])+b'\x4e\x71'*((n-6)//2),area)
 at=meta['recovery_symbols']['gr_beat_key'];old=bytes(tail[at-TAIL:at-TAIL+8]);assert old==bytes.fromhex('4fefffcc48d7001c'),old.hex()
 patch(at,old,j(sy['fx_diag_key'])+b'\x4e\x71',tail)
 at=0x400148aa;old=bytes(prefix[at-BASE:at-BASE+18]);assert old==j(meta['tiny_extra']['symbols']['tiny_menu_increment'])+b'\x4e\x71'*6,old.hex()
 patch(at,old,j(sy['fx_machine_hook'])+b'\x4e\x71'*6,prefix)
 return dict(symbols=sy,aliases=aliases,code=CODE,bss=BSS,end=sy['fx_end'],code_bytes=binary.stat().st_size,sha256=hashlib.sha256(blob).hexdigest(),status='experimental',hardware_tested=False,base_features=('v55' if settings_shortcuts else 'v54'),settings_shortcuts=settings_shortcuts,overlay=overlay,independent_vinyl_dust=dust,new_delays=new_delays,delay_return_hook=delay_repair,delay_quality=delay_quality,shimmer_feedback_branch=shimmer_clean,full_octave_return=octave_delay,octave_polish=octave_polish,cloud=cloud,cloud_repair=cloud_repair,ps1=ps1,cpu_opt=cpu_opt,dx_func_fix=dx_func_fix,idle_opt=idle_opt,voice_opt=voice_opt,active_opt=active_opt,ps1_cache_opt=ps1_cache_opt,ps1_fast_opt=ps1_fast_opt,lean_fx=lean_fx,no_shimmer=no_shimmer,speak=speak,cheap_fx=cheap_fx,room_rate=(12000 if cheap_fx else None),dub_native_filters=cheap_fx,dub_distinct=dub_distinct,ps1_hot_address=(0x46830000 if ps1_fast_opt else None),ps1_hot_code_bytes=hot_size,ps1_comb_stride=(2056 if ps1_cache_opt else 2048),dx_func_gesture=('FUNC tap, second press within350ms, hold500ms, release; DX toggle required; other controls cancel' if cpu_opt else None),reverb_selector_order=([8,7,3,0,1,2] if cheap_fx else [7,3,0,1,2] if lean_fx else [7,4,3,0,1,2,5,6] if ps1 else [4,3,0,1,2,5,6]),ps1_rate=(24000 if ps1 else None),cloud_pitch_range=([-12,12] if cloud else None),cloud_settings_file=('/Cloud.cfg' if cloud else None),shimmer_modes=({} if no_shimmer else {6: 'Shimmer 1: full octave, filtered/aligned'} if lean_fx else {6: 'Shimmer 1: full octave, filtered/aligned',7: 'Shimmer 2: preserved v62 mixed/diffused'} if octave_polish else None),native_delay_buffer=(0x8000b590 if delay_quality else None),delay_selector_order=([9,5,0,1,2] if cheap_fx else [5,0,1,2] if no_shimmer else [6,5,2,1,0] if lean_fx else [8,7,6,5,2,1,0,3,4] if cloud else [7,6,5,2,1,0,3,4] if octave_polish else [6,5,2,1,0,3,4] if new_delays else [2,1,0,3,4]),apply='TRACK release only',cancel='BACK',settings_file='/FxMix.cfg')
