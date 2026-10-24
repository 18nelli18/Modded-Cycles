"""Construction du chorus prive original, note141 ; seules des sources originales."""
import math,os,subprocess,struct,hashlib
CODE=0x467f1000
BSS=0x467f8000

def apply(root,build,prefix,rt,tail,meta,patch,slow_modes=False,format_fix=False):
 from gen_governor_recovery_test import BASE,TAIL
 src=root/'tools/machines/stereo_chorus'
 (src/'sine.h').write_text('/* Sinus mathematique Q15, genere par chorus_assets.py. */\nstatic const s16 CH_SINE[256]={'+','.join(str(round(math.sin(i*2*math.pi/256)*32767)) for i in range(256))+'};\n')
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objects=[]
 for name in ('chorus.c','control.c','hooks.S','popup.c'):
  obj=build/(name+'.o');objects.append(obj)
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DCH_SLOW_MODE_STEPS=2'] if slow_modes else []),*(['-DCH_FORMAT_FIX=1'] if format_fix else []),'-c',str(src/name),'-o',str(obj)],check=True)
 get=lambda at,n:bytes(tail[at-TAIL:at-TAIL+n])
 prev=int.from_bytes(prefix[0x400775fa-BASE:0x400775fe-BASE],'big');assert prev==0x467b0fb8
 popup=int.from_bytes(get(meta['dx_symbols']['dx_beat_api']+8,4),'big');assert 0x40000400<popup<0x46800000
 aliases=dict(ch_previous_popup=0x467c6000,ch_previous_encoder=prev,ch_previous_draw=meta['persist_symbols']['ms_draw'],menu=meta['symbols']['menu'],ch_notice=popup,ch_native=0x400579c4)
 ld=build/'chorus.ld';elf=build/'chorus.elf';binary=build/'chorus.bin'
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} . = ALIGN(4); ch_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); ch_end = .; }}\n'+'\n'.join(f'{k} = {v:#x};' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects)],check=True)
 subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 assert sy['ch_code_end']<BSS and sy['ch_end']<0x46800000
 blob=binary.read_bytes().ljust(sy['ch_end']-CODE,b'\0');assert TAIL+len(tail)<CODE
 tail.extend(bytes(CODE-TAIL-len(tail)));tail.extend(blob)
 patch(0x40056a2c,bytes.fromhex('4eb9400579c4'),b'\x4e\xb9'+struct.pack('>I',sy['ch_fx']),prefix)
 patch(0x400775f8,b'\x4e\xf9'+struct.pack('>I',prev)+b'\x4e\x71',b'\x4e\xf9'+struct.pack('>I',sy['ch_encoder_hook'])+b'\x4e\x71',prefix)
 needle=b'\x4e\xf9'+struct.pack('>I',aliases['ch_previous_draw']);hits=[i for i in range(0,CODE-TAIL-6,2) if tail[i:i+6]==needle];assert len(hits)==1,hits
 patch(TAIL+hits[0],needle,b'\x4e\xf9'+struct.pack('>I',sy['ch_draw']),tail)
 patch(0x401005bc,struct.pack('>I',aliases['ch_previous_popup']),struct.pack('>I',sy['ch_popup']),prefix)
 for at,text in [(0x40129946,b'Reverb Size\0'),(0x40129959,b'Reverb Tone\0')]:assert prefix[at-BASE:at-BASE+12]==text
 return dict(symbols=sy,aliases=aliases,code=CODE,bss=BSS,end=sy['ch_end'],code_bytes=binary.stat().st_size,sha256=hashlib.sha256(blob).hexdigest(),status='experimental',format_fix=format_fix,default='Reverb',mode_file='/Chorus.cfg',params='Native Reverb Size/Tone',hardware_tested=False)
