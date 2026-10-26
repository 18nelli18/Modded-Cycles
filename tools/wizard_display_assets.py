"""191 : accueil Sample Wizard, reserve UI independante et detour draw seulement."""
import json,struct,subprocess
CODE=0x468b8000;BSS=0x468ba800;END=0x468bb000
def apply(root,build,prefix,rt,tail,meta,patch,volume=False):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
 profile=json.loads((root/'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text());sy={k:int(v,16) for t in profile['composedTweaks'] for k,v in t.get('symbols',{}).items()}
 aliases={'sx_track':meta['scramble_mask']['symbols']['sx_track'],'ws_params':meta['playability_symbols']['mm_params']}
 aliases.update({a:sy[b] for a,b in [('ws_slot_base','slot_base'),('ws_slot_count','slot_count'),('ws_slot_size','slot_size'),('ws_slot_hash','slot_hash'),('ws_slot_side','slot_soff'),('ws_track_slot','track_slot'),('ws_names','NAME_BASE'),('ws_pcm_top','PCM_TOP'),('ws_mode','loop_mode')]})
 def read(at,n):
  area,base=(prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL);return bytes(area[at-base:at-base+n])
 at=sy['mm_draw'];raw=read(at,32);tramp='.text\n.globl ws_previous_draw\nws_previous_draw:\n';n=0
 for ins in Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040).disasm(raw,at):
  assert not ins.mnemonic.startswith(('b','j')),(hex(at),ins.mnemonic);n+=ins.size
  if n>=6:break
 assert n>=6 and n%2==0
 tramp+='.byte '+','.join(map(str,raw[:n]))+f'\njmp {at+n:#x}\n';(build/'wizard-display-tramp.S').write_text(tramp)
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');objs=[]
 for src in [root/'tools/machines/wizard_display/display158.c',build/'wizard-display-tramp.S']:
  obj=build/(src.name+'.o');objs.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror','-Wno-misleading-indentation',*(['-DWS_VOLUME159=1'] if volume else []),'-c',str(src),'-o',str(obj)],check=True)
 ld=build/'wizard-display.ld';elf=ld.with_suffix('.elf');binary=ld.with_suffix('.bin')
 ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} ws_code_end = .; .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); ws_end = .; }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items()))
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objs)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 symbols={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3};blob=binary.read_bytes()
 assert meta['groove_strum']['symbols']['gc_code_end']<CODE and symbols['ws_code_end']<0x468ba000 and meta['groove_strum']['end']<BSS<symbols['ws_end']<END
 assert not any(tail[CODE-TAIL:CODE-TAIL+len(blob)]) and not any(tail[BSS-TAIL:symbols['ws_end']-TAIL])
 patch(CODE,bytes(len(blob)),blob,tail);patch(at,raw[:n],b'\x4e\xf9'+struct.pack('>I',symbols['ws_draw'])+b'\x4e\x71'*((n-6)//2),rt)
 return dict(code=CODE,bss=BSS,end=symbols['ws_end'],code_end=symbols['ws_code_end'],symbols=symbols,aliases=aliases,hook=at,old=raw[:n].hex(),layout='Wide waveform',scope='Sample Wizard idle home only',browser_changed=False,popups='native',note_entry='native',scan_reads_per_column_per_channel=32,cached=True,volume_bar=volume,status='experimental',hardware_tested=False)
