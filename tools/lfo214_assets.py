"""Menus LFO jouables et generation des banques des projets sans UUID."""
import struct,subprocess
CODE=0x468f6800;BSS=0x468f6e80;END=0x468f6f00

def apply(root,build,prefix,tail,meta,patch):
 from gen_governor_recovery_test import BASE,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 mx=meta['four_lfos']['symbols'];fx=meta['fx_project']['symbols'];aliases={};writes=[];tramp='.text\n'
 assert meta.get('tiny_sustain',{}).get('symbols',{}).get('tn_code_end',CODE)<=CODE
 hooks=[('wf_old_key',mx['mx_key'],'wf_key'),('wf_old_encoder',mx['mx_pol_encoder'],'wf_encoder'),('wf_old_new',fx['fxs_project_new'],'wf_new'),('wf_old_decode_end',fx['fxs_project_decode_end'],'wf_decode_end')]
 for name,at,target in hooks:
  arr,base=(prefix,BASE) if at<TAIL else(tail,TAIL);raw=bytes(arr[at-base:at-base+32]);n=0
  if raw[:2]==bytes.fromhex('4ef9'):
   aliases[name]=int.from_bytes(raw[2:6],'big');writes.append((at,raw[:6],target));continue
  body=[]
  for ins in cs.disasm(raw,at):
   part=raw[n:n+ins.size]
   if part[:2]==bytes.fromhex('4eba'):
    assert ins.size==4;dest=ins.address+2+int.from_bytes(part[2:4],'big',signed=True);body.append(f'jsr {dest:#x}\n')
   else:
    assert not ins.mnemonic.startswith(('b','j')) and 'pc' not in ins.op_str,(name,ins.mnemonic,ins.op_str)
    body.append('.byte '+','.join(map(str,part))+'\n')
   n+=ins.size
   if n>=6:break
  assert n>=6;tramp+=f'.globl {name}\n{name}:\n'+''.join(body)+f'jmp {at+n:#x}\n';writes.append((at,raw[:n],target))
 (build/'wf_tramp.S').write_text(tramp)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for src in (root/'tools/machines/lfo214/workflow.c',build/'wf_tramp.S'):
  obj=build/('wf-'+src.name+'.o');objects.append(str(obj));subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',str(src),'-o',str(obj)],check=True)
 ld=build/'lfo214.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} wf_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} wf_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*objects],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 assert sy['wf_generation']==BSS and sy['wf_code_end']<=BSS and sy['wf_end']<=END
 blob=binary.read_bytes();assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]) and not any(tail[BSS-TAIL:sy['wf_end']-TAIL]);patch(CODE,bytes(len(blob)),blob,tail)
 for at,old,target in writes:patch(at,old,bytes.fromhex('4ef9')+struct.pack('>I',sy[target])+bytes.fromhex('4e71')*((len(old)-6)//2),prefix if at<TAIL else tail)
 return dict(code=CODE,bss=BSS,symbols=sy,aliases=aliases,unsaved_project_ram=True,preserve_first_project_save=True,musical_key_events_pass=True,trig_edit_encoders_pass=True,hardware_tested=False)
