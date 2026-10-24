"""Construction du slot delay/bitcrusher prive, note142 ; sources originales."""
import math,subprocess,struct,hashlib
CODE=0x467fb000;BSS=0x467fe000

def apply(root,build,prefix,tail,meta,patch,wet=False,split_sends=False,center_delay=False,cpu_opt=False,lean_fx=False):
 from gen_governor_recovery_test import BASE,TAIL
 src=root/('tools/machines/delay_crush_send' if split_sends else 'tools/machines/delay_crush_wet' if wet else 'tools/machines/delay_crush')
 rates=[round(65536*2**(-6*(127-i)/127)) for i in range(128)]
 (src/'rates.h').write_text('/* Increment Q16 a48kHz :750Hz..48kHz, generation mathematique. */\nstatic const u32 CR_RATE[128]={'+','.join(map(str,rates))+'};\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for name in ('crush.c','control.c','popup.c','hooks.S','show.S'):
  obj=build/('cr_'+name+'.o');objects.append(obj)
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DCR_CENTER_DELAY=1'] if center_delay and name=='control.c' else []),*(['-DCR_CPU_OPT=1'] if cpu_opt else []),*(['-DCR_LEAN_FX=1'] if lean_fx else []),'-c',str(src/name),'-o',str(obj)],check=True)
 ch=meta['stereo_chorus'];sy=ch['symbols'];aliases=dict(cr_previous_encoder=sy['ch_encoder_hook'],cr_previous_draw=sy['ch_draw'],cr_native_popup=sy['ch_popup'],cr_native=0x40057488,cr_notice=ch['aliases']['ch_notice'],menu=ch['aliases']['menu'])
 if split_sends:aliases.update(cr_side=meta['beat_repeat_symbols']['br_side'],cr_side_on=meta['beat_repeat_symbols']['br_side_on'])
 ld=build/'crush.ld';elf=build/'crush.elf';binary=build/'crush.bin'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); cr_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); cr_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 assert sy['cr_code_end']<BSS and sy['cr_end']<0x46800000
 blob=binary.read_bytes().ljust(sy['cr_end']-CODE,b'\0');assert TAIL+len(tail)<CODE
 tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(blob)
 if wet:patch(0x40056b38,bytes.fromhex('4878000448798000b990'),b'\x4e\xf9'+struct.pack('>I',sy['cr_mix_hook'])+b'\x4e\x71'*2,prefix)
 patch(0x4005699c,bytes.fromhex('4eb940057488'),b'\x4e\xb9'+struct.pack('>I',sy['cr_fx']),prefix)
 patch(0x400775f8,b'\x4e\xf9'+struct.pack('>I',aliases['cr_previous_encoder'])+b'\x4e\x71',b'\x4e\xf9'+struct.pack('>I',sy['cr_encoder_hook'])+b'\x4e\x71',prefix)
 needle=b'\x4e\xf9'+struct.pack('>I',aliases['cr_previous_draw']);hits=[i for i in range(0,ch['code']-TAIL-6,2) if tail[i:i+6]==needle];assert len(hits)==1,hits
 patch(TAIL+hits[0],needle,b'\x4e\xf9'+struct.pack('>I',sy['cr_draw']),tail)
 return dict(symbols=sy,aliases=aliases,code=CODE,bss=BSS,end=sy['cr_end'],code_bytes=binary.stat().st_size,sha256=hashlib.sha256(blob).hexdigest(),status='experimental',default='Delay',mode_file='/Crush.cfg',routing_version=(3 if split_sends else 2 if wet else 1),split_sends=split_sends,cpu_opt=cpu_opt,lean_fx=lean_fx,selector_order=([2,1,0] if lean_fx else [2,1,0,3,4] if center_delay else [0,1,2,3,4]),send_file=('/CrushSend.cfg' if split_sends else None),echo_crusher_position=('before native delay' if split_sends else 'after native delay'),params='Independent global Rate0..127 and Bits2..16; native delay time/feedback retained',hardware_tested=False)
