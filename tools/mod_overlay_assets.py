"""Mod Setup132 : overlay global, encodeurs audio et retour a la page intacte."""
import struct,subprocess
CODE=0x46899000;BSS=0x4689e000;END=0x468a0000
def apply(root,build,prefix,rt,tail,meta,patch,popup_return=False,direct_popup=False,held_popup=False,nested_popup=False,popup_labels=False):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 sy=meta['symbols'];fx=meta['fx_menu']['symbols'];aliases={'mo_menu':sy['menu'],'mo_menu_encoder':meta['dx_symbols']['dx_encoder']};hooks=[]
 def read(at,n):
  a,b=(prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
  return bytes(a[at-b:at-b+n])
 def write(at,old,new):patch(at,old,new,prefix if at<RUNTIME else rt if at<TAIL else tail)
 tramp='.text\n';cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 for name,at in [('encoder',0x400775f8),('key',sy['wf_key']),('draw',sy['wf_draw']),('stack',fx['fx_stack_overlay'])]+([('popup',meta['fundamentals']['symbols']['bf_popup'])] if popup_return else [])+([('parameter_encoder',0x4001f4f0),('fx_bind',fx['fx_popup_bind'])] if direct_popup else []):
  raw=read(at,32)
  if raw[:2]==b'\x4e\xf9':n=6;aliases['mo_previous_'+name]=int.from_bytes(raw[2:6],'big')
  else:
   n=0
   for ins in cs.disasm(raw,at):
    assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic);n+=ins.size
    if n>=6:break
   assert n>=6 and n%2==0
   tramp+='\n.globl mo_previous_'+name+'\nmo_previous_'+name+':\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n'
  hooks.append((at,raw[:n],'mo_'+name))
 frame=meta['fx_project']['frame_hook'];raw=read(frame,6);assert raw[:2]==b'\x4e\xb9'
 if direct_popup:aliases['mo_fx_render']=fx['fx_popup_render']
 aliases['mo_previous_frame']=int.from_bytes(raw[2:],'big');assert aliases['mo_previous_frame']==meta['fx_project']['symbols']['fxp_frame']
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 ts=build/'mod-overlay-tramp.S';ts.write_text(tramp)
 for src in (root/('tools/machines/sidechain/mod-overlay159.c' if popup_labels else 'tools/machines/sidechain/mod-overlay137.c' if nested_popup else 'tools/machines/sidechain/mod-overlay135.c' if held_popup else 'tools/machines/sidechain/mod-overlay134.c' if direct_popup else 'tools/machines/sidechain/mod-overlay133.c' if popup_return else 'tools/machines/sidechain/mod-overlay132.c'),ts):
  obj=build/(src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'mod-overlay.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); mo_code_end = .; .data : {{ *(.data*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); mo_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};code=binary.read_bytes()
 assert meta['legacy']['end']<CODE and symbols['mo_code_end']<BSS and symbols['mo_end']<meta['punch']['code']
 assert len(tail)>=END-TAIL and not any(tail[CODE-TAIL:END-TAIL]);write(CODE,bytes(len(code)),code)
 for at,old,target in hooks:write(at,old,b'\x4e\xf9'+struct.pack('>I',symbols[target])+b'\x4e\x71'*((len(old)-6)//2))
 write(frame,raw,b'\x4e\xb9'+struct.pack('>I',symbols['mo_frame']))
 return dict(code=CODE,code_bytes=len(code),bss=BSS,end=symbols['mo_end'],symbols=symbols,aliases=aliases,ui_only=True,audio_unchanged=True,preview_ms=(2000 if popup_return else 1000),popup_above_machine_selector=popup_return,capture_after_native_edit=direct_popup,cached_popup_pixels=held_popup,nested_draw_guard=nested_popup,back_release_owned=popup_return,hooks=[dict(at=at,size=len(old),target=target) for at,old,target in hooks],frame_hook=frame,hardware_tested=False)
