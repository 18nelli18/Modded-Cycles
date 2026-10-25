"""QntM : menu natif9lignes, sous-menu2lignes et copie mute/solo quantifiee."""
import struct,subprocess
CODE=0x4689b000;BSS=0x4689f000;END=0x468a0000
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 du=meta['sidechain']['symbols'];sy=meta['symbols'];sc=meta['scramble_mask']['symbols'];mo=meta['mod_overlay']['symbols']
 aliases={**sy,**meta['dx_symbols'],**sc,**du};aliases.update(menu=sy['menu'],row=sy['row'],sx_submenu=sc['sx_submenu'],du_page=du['du_page'])
 def read(at,n):
  arr,base=(prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
  return bytes(arr[at-base:at-base+n])
 def change(at,old,new):patch(at,old,new,prefix if at<RUNTIME else rt if at<TAIL else tail)
 hooks=[];tramp='.text\n';cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 for name,at,target in [('set',0x400594f0,'mq_set'),('key',du['du_key'],'mq_key'),('encoder',du['du_encoder'],'mq_encoder'),('draw',du['du_draw'],'mq_draw'),('frame',mo['mo_frame'],'mq_frame')]:
  raw=read(at,32);n=0;alias='mq_native_set' if name=='set' else 'mq_previous_'+name
  if raw[:2]==b'\x4e\xf9':n=6;aliases[alias]=int.from_bytes(raw[2:6],'big')
  else:
   for ins in cs.disasm(raw,at):
    assert not ins.mnemonic.startswith(('b','j')),(name,ins.mnemonic);n+=ins.size
    if n>=6:break
   assert n>=6 and n%2==0
   tramp+='\n.globl '+alias+'\n'+alias+':\n.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n'
  hooks.append((at,raw[:n],target))
 rootmenu=(build/'du_root.S').read_text().replace('du_root_draw','mq_root_draw').replace('moveq #8,%d0','moveq #9,%d0').replace('    jsr wf_menu_row','    clrb %a0@(752)\n    jsr wf_menu_row')
 rootmenu=rootmenu.replace('.Lduck:', '.Lquant: .asciz "QntM"\n.Lduck:')+'\n.long 0,0,0,.Lquant,0,1,.Lts_label,0,0,0,0,0,0,1,mq_root_value,0,0,0,0,0,0\n'
 sub=(root/'tools/machines/mod_diagnostic/menu.S').read_text().split('.Lchannel:')[0]
 sub=sub.replace('dx_menu_draw','mq_sub_draw').replace('wf_menu_row','mq_menu_row').replace('wf_menu_edit','mq_menu_edit').replace('movel row,%d0','movel mq_row,%d0').replace('moveq #6,%d0','moveq #2,%d0').replace('.long 3,3,0','.long 4,4,0').replace('.asciz "Mod"','.asciz "Mute"').replace('.asciz "Setup"','.asciz "Quant"')
 for offset in (248,332,416,500):sub=sub.replace(f'    clrb %a0@({offset})\n','')
 sub+='\n.Lon: .asciz "On"\n.Ldiv: .asciz "Div"\n.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'
 for i,label in enumerate(('on','div')):sub+=f'.long 0,0,0,.L{label},0,1,.Lts_label,0,0,0,0,0,0,1,mq_value{i},0,0,0,0,0,0\n'
 irq='''.text
.globl mq_irq
mq_irq:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 jsr mq_tick
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 move.l 0x800017ac,%d1
 rts
'''
 for name,text in [('mq_root.S',rootmenu),('mq_sub.S',sub),('mq_tramp.S',tramp),('mq_irq.S',irq)]: (build/name).write_text(text)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in [root/'tools/machines/sidechain/mute-quant142.c',*[build/n for n in ('mq_root.S','mq_sub.S','mq_tramp.S','mq_irq.S')]]:
  obj=build/(src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'mute-quant.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x}: {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} mq_code_end = .; .bss {BSS:#x} (NOLOAD): {{ *(.bss*) *(COMMON) }} mq_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes()
 assert meta['mod_overlay']['code']+meta['mod_overlay']['code_bytes']<=CODE and symbols['mq_code_end']<meta['mod_overlay']['bss'] and meta['mod_overlay']['end']<BSS and symbols['mq_end']<END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]) and not any(tail[BSS-TAIL:symbols['mq_end']-TAIL]);change(CODE,bytes(len(blob)),blob)
 for at,old,target in hooks:change(at,old,b'\x4e\xf9'+struct.pack('>I',symbols[target])+b'\x4e\x71'*((len(old)-6)//2))
 at=du['du_root_draw'];change(at,read(at,6),b'\x4e\xf9'+struct.pack('>I',symbols['mq_root_draw']))
 at=0x40058ca6;change(at,bytes.fromhex('2239800017ac'),b'\x4e\xb9'+struct.pack('>I',symbols['mq_irq']))
 return dict(code=CODE,bss=BSS,end=symbols['mq_end'],code_bytes=len(blob),symbols=symbols,aliases=aliases,label='QntM',enabled_default=False,division_default='1/4',divisions=['1/16','1/8','1/4','1/2','1'],units='fraction of active pattern length',applies=['mute','solo'],settings_file='/MuteQuant.cfg',save='stopped only',hardware_tested=False,status='experimental')
