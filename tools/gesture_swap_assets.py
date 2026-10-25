"""Gestes123 : remplacement du seul controleur UI, trampoline garde."""
import struct,subprocess
CODE=0x4684d000;END=0x4684f000
def apply(root,build,prefix,rt,tail,meta,patch,once=False,menu_handoff=False):
 code=0x4684f000 if meta.get('sidechain',{}).get('fx_returns') else CODE
 end=0x46850000 if meta.get('sidechain',{}).get('fx_returns') else END
 from gen_governor_recovery_test import TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 sy=meta['symbols'];sc=meta['scramble_mask'];at=sc['symbols']['sx_previous_key']
 raw=bytes(tail[at-TAIL:at-TAIL+24]);cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);n=0
 for ins in cs.disasm(raw,at):
  assert not ins.mnemonic.startswith(('b','j'));n+=ins.size
  if n>=6:break
 assert meta['fx_project']['code']+meta['fx_project']['code_bytes']<=code
 aliases={'wm_'+a:sy[b] for a,b in [('menu','menu'),('editing','editing'),('settings','settings'),('used','menu_used'),('owned','track_owned'),('pending','pending'),('api','wf_api')]};aliases['wm_steps']=sc['original']['sc_steps_toggle']
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');obj=build/'gesture123.o';elf=build/'gesture123.elf';binary=build/'gesture123.bin';ld=build/'gesture123.ld'
 subprocess.run([cross+'gcc.exe','-mcpu=54418',*(['-DWM_ONCE=1'] if once else []),*(['-DWM_MACHINE_EXIT=1'] if menu_handoff else []),'-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(root/'tools/machines/sidechain/gesture123.c'),'-o',str(obj)],check=True)
 ld.write_text(f'SECTIONS {{ .text {code:#x}: {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} wm_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};data=binary.read_bytes();assert symbols['wm_end']<end and not any(tail[code-TAIL:code-TAIL+len(data)])
 patch(code,bytes(len(data)),data,tail);patch(at,raw[:n],b'\x4e\xf9'+struct.pack('>I',symbols['wm_key'])+b'\x4e\x71'*((n-6)//2),tail)
 return dict(code=code,end=symbols['wm_end'],symbols=symbols,aliases=aliases,previous_key=at,machines_closes_menu=menu_handoff,short='Mod Setup; held steps toggle Scramble only',hold='Scramble once',hardware_tested=False)
