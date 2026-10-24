"""FXP120 : lookup non constructeur, application codec/frame, DSP inchange."""
import struct,subprocess,hashlib
CODE=0x4684b000;BSS=0x4684f000;END=0x46850000
def apply(root,build,prefix,rt,tail,meta,patch,fx,patterns=False,tiny=None,retro=None):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 sy0=fx['symbols'];al=fx['aliases'];fields=[];names=[]
 for name,count in [('ch_mode',1),('fx_speed',1),('fx_depth',1),('fx_crackle',1),('fx_warble',1),('fx_wspeed',1),('fx_aux_ch',6),('fx_aux_vi',6),('cr_mode',1),('cr_rate',1),('cr_bits',1),('cr_send',6),('fx_duck_amount',1),('fx_duck_release',1),('fx_ring_freq',1),('fx_ring_depth',1),('fx_phase_rate',1),('fx_phase_depth',1),('fx_phase_feedback',1),('fx_gate_time',1),('fx_gate_predelay',1)]:
  at=sy0.get(name,al.get(name));assert at
  for i in range(count):fields.append(at+4*i);names.append(name+(f'[{i}]' if count>1 else ''))
 assert len(fields)==36 and names[18]=='cr_mode' and names[20]=='cr_bits'
 def data(at,n):return bytes((tail if at>=TAIL else rt)[at-(TAIL if at>=TAIL else RUNTIME):at-(TAIL if at>=TAIL else RUNTIME)+n])
 defaults=[int.from_bytes(data(at,4),'big') for at in fields];assert max(defaults)<128 and defaults[0]==defaults[18]==0 and 2<=defaults[20]<=16
 rev=sum(1<<i for i in fx['reverb_selector_order']);delay=sum(1<<i for i in fx['delay_selector_order'])
 (build/'fields.h').write_text('#define FXP_FIELDS 36\n#define FXP_MENU_ADDRESS '+hex(sy0['fx_menu_open'])+'u\n#define FXP_REV_MASK '+str(rev)+'u\n#define FXP_DEL_MASK '+str(delay)+'u\nstatic const u32 fxp_fields[36]={'+','.join(hex(i) for i in fields)+'};\nstatic const u8 fxp_defaults[36]={'+','.join(map(str,defaults))+'};\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040)
 # GCC appelle directement part.0 depuis fx_draw ; accrocher les deux entrees
 # effectives plutot que le symbole public fx_service ignore dans ce chemin.
 service=sy0['fx_service.part.0'];draw=sy0['fx_draw']
 entries=[('fxp_native_encode',0x4005d18a,8,prefix,bytes.fromhex('4fefffd448d77cfc'),'fxp_encode'),('fxp_native_decode',0x4005d3dc,8,prefix,bytes.fromhex('4fefffdc48d77c3c'),'fxp_decode')]
 if patterns:
  assert tiny and retro and retro['end']<=0x468bd000
  for name,at,old,target in [('fxs_native_encode',0x4005ba0a,'4fefffe848d73c0c','fxs_encode'),('fxs_native_decode',0x4005b894,'4fefffe048d77c1c','fxs_decode'),('fxs_native_init',0x400615e8,'4fefffe448d70c7c','fxs_init'),('fxs_native_load',0x4000fb06,'4e56ffbc48d70c3c','fxs_load'),('fxs_native_new_project',0x4000f872,'4e56ffb848d70c3c','fxs_new_project')]:entries.append((name,at,8,prefix,bytes.fromhex(old),target))
 for name,at,target in [('fxp_native_service',service,'fxp_service'),('fxp_native_draw',draw,'fxp_draw')]:
  pro=data(at,24);n=0
  for ins in cs.disasm(pro,at):
   n+=ins.size
   if n>=6:break
  assert n>=6 and n%2==0
  entries.append((name,at,n,tail,pro[:n],target))
 frame=sy0['fx_frame_begin'];fc=tail.find(b'\x4e\xb9',frame-TAIL,frame-TAIL+48);assert fc>=frame-TAIL
 frame_target=int.from_bytes(tail[fc+2:fc+6],'big');assert frame_target==meta['fundamentals']['symbols']['bf_prepare']
 tramp='.text\n'
 for name,at,size,area,old,new in entries:
  off=at-(BASE if area is prefix else TAIL);assert bytes(area[off:off+size])==old
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(map(str,old))+f'\njmp {at+size:#x}\n'
 (build/'fxp_tramp.S').write_text(tramp);objects=[]
 for src in [root/'tools/machines/fx_project/project.c',build/'fxp_tramp.S']+([root/'tools/machines/fx_project/patterns.c',root/'tools/machines/fx_project/pattern-switch.S'] if patterns else []):
  obj=build/('fxp_'+src.name+'.o');objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DFX_PATTERN=1'] if patterns else []),'-I'+str(build),'-c',str(src),'-o',str(obj)],check=True)
 bss=0x468bd000 if patterns else BSS;limit=0x468c0000 if patterns else END
 ld=build/'fxp.ld';elf=build/'fxp.elf';binary=build/'fxp.bin';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); fxp_code_end = .; .bss {bss:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} fxp_end = .; }}\nfxp_native_new = 0x40061738;\nfxp_native_frame = {frame_target:#x};\nfxs_native_copy = 0x4008f1f0;\nwave_render_original = 0x467796fc;')
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(elf),str(binary)],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe',str(elf)],text=True).splitlines() if len(v:=line.split())==3};code=binary.read_bytes();assert CODE+len(code)<BSS and sy['fxp_end']<limit
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(code)]),'FXP code reservation occupied'
 if len(tail)<sy['fxp_end']-TAIL:tail.extend(bytes(sy['fxp_end']-TAIL-len(tail)))
 assert not any(tail[bss-TAIL:sy['fxp_end']-TAIL]),'FXP BSS reservation occupied'
 patch(CODE,bytes(len(code)),code,tail)
 for name,at,size,area,old,new in entries:patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[new])+b'\x4e\x71'*((size-6)//2),area)
 patch(0x4000f906,bytes.fromhex('4eb940061738'),b'\x4e\xb9'+struct.pack('>I',sy['fxp_new']),prefix)
 patch(TAIL+fc+2,struct.pack('>I',frame_target),struct.pack('>I',sy['fxp_frame']),tail)
 if patterns:
  patch(0x40055c5c,bytes.fromhex('23ca40a7887c'),b'\x4e\xf9'+struct.pack('>I',sy['fxs_switch_hook']),prefix)
  patch(0x4000ec48,bytes.fromhex('4eb94008f1f0'),b'\x4e\xb9'+struct.pack('>I',sy['fxs_copy']),prefix)
  for at,op in [(0x40010af8,'4bf9'),(0x40010d10,'4bf9'),(0x4001199a,'49f9'),(0x40011b18,'43f9')]:patch(at,bytes.fromhex(op+'4008f1f0'),bytes.fromhex(op)+struct.pack('>I',sy['fxs_copy']),prefix)
  row=tiny['data']+4*(2*tiny['machine_count']+14)
  patch(row,struct.pack('>I',0x467796fc),struct.pack('>I',sy['wave_gain_render']),tail)
 return dict(code=CODE,code_bytes=len(code),bss=bss,end=sy['fxp_end'],symbols=sy,fields=names,field_addresses=fields,defaults=defaults,menu_address=sy0['fx_menu_open'],frame_hook=TAIL+fc,frame_previous=frame_target,immediate_active_load=True,project_slot=0x40fe4228,never_construct_project=True,ui_hooks=[dict(at=at,size=size,target=new) for name,at,size,area,old,new in entries if area is tail],record_offset=0x1c0,record_size=64,format='FXP1',native_project=True,extra_file_io=False,per_pattern=patterns,pattern_record_offset=(0x39d0 if patterns else None),pattern_record_size=(48 if patterns else None),pattern_activation_hook=(0x40055c5c if patterns else None),wave_gain_db=(6.0206 if patterns else 0),hardware_tested=False)
