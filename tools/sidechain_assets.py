"""Ducking122 : UI native et blocs six pistes ; aucun fichier annexe."""
import struct,subprocess
CODE=0x46833000;BSS=0x46835000;END=0x46836000
def apply(root,build,prefix,rt,tail,meta,patch,fx):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 assert fx['symbols']['fx_hot_end']<=CODE and END<=0x46840000
 sc=meta['scramble_mask'];sx=sc['symbols'];br=meta['beat_repeat_symbols'];aliases={**sc['aliases'],**{k:sx[k] for k in ('sx_submenu','sx_masks','sx_track','sx_subrow','sx_root_value')},**{k:br[k] for k in ('br_side','br_side_on')}}
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);cs.skipdata=False
 def read(at,n):return bytes((prefix if at<RUNTIME else tail)[at-(BASE if at<RUNTIME else TAIL):at-(BASE if at<RUNTIME else TAIL)+n])
 def change(at,old,new):patch(at,old,new,prefix if at<RUNTIME else tail)
 tramp='.text\n';entries=[]
 for name,at,target in [('key',sx['sx_key'],'du_key'),('encoder',sx['sx_encoder'],'du_encoder'),('draw',sx['sx_draw'],'du_draw')]:
  raw=read(at,24);n=0
  for ins in cs.disasm(raw,at):
   assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic)
   n+=ins.size
   if n>=6:break
  tramp+=f'.globl du_previous_{name}\ndu_previous_{name}:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';entries.append((at,raw[:n],target))
 # La boucle voix est appelee egalement pour le jeu live/retrig.
 at=0x400a7d4a;raw=read(at,24);n=0
 for ins in cs.disasm(raw,at):
  n+=ins.size
  if n>=6:break
 tramp+='.globl du_native_voice\ndu_native_voice:\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';entries.append((at,raw[:n],'du_voice_hook'))
 # Le JSR arp_filter existant garde son traitement puis publie le pulse.
 at=0x40058e28;old=read(at,6);assert old[:2]==b'\x4e\xb9';arp=int.from_bytes(old[2:],'big');arpcode=read(arp,32);assert arpcode[:2]==b'\x2f\x0a'
 # Le trampoline arp commence par push a2, jsr arp_filter.
 assert arpcode[2:4]==b'\x4e\xb9';aliases['du_previous_note']=int.from_bytes(arpcode[4:8],'big');entries.append((arp+2,arpcode[2:8],'du_note_filter'))
 gain=br['br_gain_hook'];raw=read(gain,64);needle=b'\x4e\xb9'+struct.pack('>I',br['br_audio']);i=raw.find(needle);assert i>=0
 aliases['du_previous_audio']=br['br_audio'];entries.append((gain+i,needle,'du_audio'))
 (build/'du_tramp.S').write_text(tramp)
 old=(root/'tools/machines/mod_diagnostic/menu.S').read_text();rootmenu=(build/'sx_root.S').read_text().replace('sx_root_draw','du_root_draw').replace('moveq #7,%d0','moveq #8,%d0').replace('    clrb %a0@(584)','    clrb %a0@(668)\n    clrb %a0@(584)')
 rootmenu=rootmenu.replace('.Lscramble:', '.Lduck: .asciz ""\n.Lscramble:')+'\n.long 0,0,0,.Lduck,0,1,.Lts_label,0,0,0,0,0,0,1,du_root_value,0,0,0,0,0,0\n';(build/'du_root.S').write_text(rootmenu)
 sub=old[:old.index('.Lchannel:')].replace('dx_menu_draw','du_sub_draw').replace('wf_menu_row','du_menu_row').replace('wf_menu_edit','du_menu_edit').replace('movel row,%d0','movel du_row,%d0').replace('moveq #6,%d0','moveq #9,%d0').replace('lea.l .Lts_subtitle_data,%a0','lea.l du_title_track+12,%a0').replace('.long 3,3,0','.long 4,4,0').replace('.asciz "Mod"','.asciz "Side"')
 sub=sub.replace('    jsr du_menu_row','    clrb %a0@(584)\n    clrb %a0@(668)\n    clrb %a0@(752)\n    jsr du_menu_row')
 labels=['']*9;sub+='\n'+''.join(f'.Lname{i}: .asciz "{label}"\n' for i,label in enumerate(labels))+'.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'+''.join(f'.long 0,0,0,.Lname{i},0,1,.Lts_label,0,0,0,0,0,0,1,du_value{i},0,0,0,0,0,0\n' for i in range(9));(build/'du_sub.S').write_text(sub)
 objects=[]
 for src in [root/'tools/machines/sidechain/duck.c',root/'tools/machines/sidechain/hooks.S',build/'du_tramp.S',build/'du_root.S',build/'du_sub.S']:
  obj=build/('du_'+src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'du.ld';elf=build/'du.elf';binary=build/'du.bin';ld.write_text(f'SECTIONS {{ .text {CODE:#x}: {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} du_code_end = .; .bss {BSS:#x} (NOLOAD): {{ *(.bss*) *(COMMON) }} du_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};code=binary.read_bytes();assert sy['du_code_end']<BSS and sy['du_end']<END
 if len(tail)<sy['du_end']-TAIL:tail.extend(bytes(sy['du_end']-TAIL-len(tail)))
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(code)]);patch(CODE,bytes(len(code)),code,tail)
 for at,old,target in entries:change(at,old,old[:2]+struct.pack('>I',sy[target]) if old[:2]==b'\x4e\xb9' else b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71'*((len(old)-6)//2))
 return dict(code=CODE,bss=BSS,end=sy['du_end'],code_bytes=len(code),symbols=sy,trigger_based=True,settings='per pattern',scramble_per_pattern=True,attack_ms=[0,2,5,10,20,40,80,160],hold_ms=[0,20,60,120],release_ms=[10,20,30,50,75,100,150,200,300,400,500,750,1000,1500,2000,3000],depth_steps=16,hooks=[dict(at=at,size=len(old),target=target) for at,old,target in entries],hardware_tested=False)
