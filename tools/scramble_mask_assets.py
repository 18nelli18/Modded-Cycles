"""SCRAMBLE : six cases par piste, menu natif et stockage UI (note148)."""
import json,struct,subprocess
CODE=0x467c9000;BSS=0x467cf000;END=0x467d0000

def apply(root,build,prefix,rt,tail,meta,patch,short_labels=False,decay_fix=False,native_decay=False,delete_reset=False,per_pattern=False):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());allsy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()};sy=meta['symbols'];dx=meta['dx_symbols'];sc={k:v for k,v in allsy.items() if k.startswith('sc_')}
 def read(at,n):
  area,off=(prefix,at-BASE) if at<RUNTIME else (rt,at-RUNTIME) if at<TAIL else (tail,at-TAIL)
  return bytes(area[off:off+n])
 def write(at,old,new):patch(at,old,new,prefix if at<RUNTIME else rt if at<TAIL else tail)
 aliases={k:dx.get(k,sy.get(k,allsy.get(k))) for k in ('wf_menu_row','wf_menu_edit','wf_menu_value','wf_usb_menu_value','vp_menu_value','lm_menu_value','dl_menu_value','dx_menu_value','menu','row')};assert all(v is not None for v in aliases.values()),aliases
 aliases.update(sc_result=sc['sc_result'],sx_random=sc['sc_random'],sx_notice=allsy['show_popup'])
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);tramp='.text\n';hooks=[]
 for name,at in [('key',sy['wf_key']),('encoder',dx['dx_encoder']),('draw',sy['wf_draw']),('run',sc['sc_run'])]:
  raw=read(at,24);n=0
  for ins in cs.disasm(raw,at):
   assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic)
   n+=ins.size
   if n>=6:break
  assert n>=6
  tramp+=f'.globl sx_previous_{name}\nsx_previous_{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';hooks.append((at,raw[:n],'sx_'+name))
 (build/'sx_tramp.S').write_text(tramp)
 old=(root/'tools/machines/mod_diagnostic/menu.S').read_text()
 rootmenu=old.replace('dx_menu_draw','sx_root_draw').replace('moveq #6,%d0','moveq #7,%d0').replace('    jsr wf_menu_row','    clrb %a0@(584)\n    jsr wf_menu_row').replace('.asciz "Md"','.asciz "SIL"').replace('.asciz "Mute"','.asciz "LTC"').replace('.Lallocator: .byte 0','.Lscramble: .asciz "Scramble"\n.Lallocator: .byte 0')
 if short_labels:rootmenu=rootmenu.replace('.asciz "Scramble"','.asciz "SCRM"')
 rootmenu+='\n.long 0,0,0,.Lscramble,0,1,.Lts_label,0,0,0,0,0,0,1,sx_root_value,0,0,0,0,0,0\n';(build/'sx_root.S').write_text(rootmenu)
 # Meme MenuView, six cases et titre de piste dynamique, aucune police copiee.
 sub=old[:old.index('.Lchannel:')].replace('dx_menu_draw','sx_sub_draw').replace('wf_menu_row','sx_menu_row').replace('wf_menu_edit','sx_menu_edit').replace('movel row,%d0','movel sx_subrow,%d0').replace('lea.l .Lts_subtitle_data,%a0','lea.l sx_track_string+12,%a0').replace('.long 3,3,0','.long 4,4,0' if short_labels else '.long 8,8,0').replace('.asciz "Mod"','.asciz "SCRM"' if short_labels else '.asciz "Scramble"')
 labels=['Pitch','Decay','Color','Shape','Sweep','Contour'];callbacks=['sx_'+v.lower()+'_value' for v in labels]
 sub+='\n'+''.join(f'.Lname{i}: .asciz "{"Cnt" if short_labels and label=="Contour" else label}"\n' for i,label in enumerate(labels))+'.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'+''.join(f'.long 0,0,0,.Lname{i},0,1,.Lts_label,0,0,0,0,0,0,1,{cb},0,0,0,0,0,0\n' for i,cb in enumerate(callbacks));(build/'sx_sub.S').write_text(sub)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in (root/'tools/machines/scramble_mask/mask.c',root/'tools/machines/scramble_mask/hooks.S',build/'sx_tramp.S',build/'sx_root.S',build/'sx_sub.S',*([root/'tools/machines/scramble/step_delete.s'] if delete_reset else [])):
  obj=build/(src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DSX_PATTERN=1'] if per_pattern else []),*(['-DSX_DECAY_FIX=1'] if decay_fix else []),*(['-DSX_DECAY_NATIVE=1'] if native_decay else []),'-c',str(src),'-o',str(obj)],check=True)
 ld=build/'scramble_mask.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x}: {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); sx_code_end = .; .bss {BSS:#x} (NOLOAD): {{ *(.bss*) *(COMMON) }} . = ALIGN(4); sx_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};assert symbols['sx_code_end']<BSS and symbols['sx_end']<END
 blob=binary.read_bytes().ljust(symbols['sx_end']-CODE,b'\0');assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]);write(CODE,bytes(len(blob)),blob)
 hooks.append((sc['sc_steps_event'],bytes.fromhex('254e0048200a'),'sx_step_hook'))
 for at,old,label in hooks:write(at,old,b'\x4e\xf9'+struct.pack('>I',symbols[label])+b'\x4e\x71'*((len(old)-6)//2))
 if delete_reset:write(0x40022dd0,bytes.fromhex('4eb940017c4e'),b'\x4e\xb9'+struct.pack('>I',symbols['sc_step_delete']))
 return dict(delete_resets_flags=delete_reset,short_labels=short_labels,code=CODE,bss=BSS,end=symbols['sx_end'],code_bytes=binary.stat().st_size,symbols=symbols,aliases=aliases,original=sc,hooks=[dict(at=at,size=len(old),target=label) for at,old,label in hooks],parameters=labels,decay_slot_fixed=decay_fix,native_decay_resolved=native_decay,slots=[10,18 if native_decay else 15 if decay_fix else 18,11,12,13,14],default_mask=60,track_count=6,preferences_file='/Scramble.cfg',per_track=True,persist_scope='six track preferences across projects/power cycles',status='experimental',hardware_tested=False)
