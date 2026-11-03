"""Veille privee : garder le chemin DAC natif et reveiller avant les notes.

Pas de veille automatique de production : la commande SMDS seule arme le
test. L interruption conserve registres/CCR et le masque Song d origine.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
CODE=0x467a0200;BSS=0x467a0f00;END=0x467a1000

def apply(meta,native,runtime,out,automatic_stop=False):
 base=0x46700000;nb=0x40000400;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if meta.get('stage_profile'):
  from stage_profile320 import remove
  remove(meta,native,runtime);del meta['stage_profile']
 if meta.get('deep_idle_wake'):
  previous=meta['deep_idle_wake'];assert hashlib.sha256(runtime[CODE-base:CODE-base+previous['code_bytes']]).hexdigest()==previous['sha256']
  for patch in previous['patches']:
   offset=patch['at']-nb;new=bytes.fromhex(patch['new']);assert native[offset:offset+len(new)]==new
   native[offset:offset+len(new)]=bytes.fromhex(patch['old'])
  runtime[CODE-base:END-base]=bytes(END-CODE)
 assert not any(runtime[CODE-base:END-base])
 assert any(e['kind']=='remove' and e['address']<=CODE and END<=e['address']+e['bytes'] for e in meta['clean_layout']['retirement']['edits'])
 at=0x40058ca6;expected=b'\x4e\xb9'+struct.pack('>I',meta['acid_articulation']['symbols']['sg_mute_irq'])
 assert native[at-nb:at-nb+6]==expected
 audio_at=0x40059382;audio_old=bytes(native[audio_at-nb:audio_at-nb+6]);assert audio_old==bytes.fromhex('4eb9467886d0')
 note_at=0x4008171e;note_old=bytes(native[note_at-nb:note_at-nb+6]);assert note_old==bytes.fromhex('4ef940185968')
 aliases=dict(rw_panic_transport=0x40059692,rw_old_mute=meta['acid_articulation']['symbols']['sg_mute_irq'],rw_old_audio=0x467886d0,rw_old_note=0x40185968)
 if automatic_stop:aliases['rw_old_sound_off']=meta['per_track_fx']['symbols']['mf_panic_set']
 assembly='''.text
.globl rw_mute_irq
rw_mute_irq:
 lea -20(%sp),%sp
 movem.l %d0-%d1/%a0-%a1,(%sp)
 move.w %sr,%d0
 move.l %d0,16(%sp)
 jsr rw_check
 move.l 16(%sp),%d0
 move.w %d0,%sr
 movem.l (%sp),%d0-%d1/%a0-%a1
 lea 20(%sp),%sp
 jmp rw_old_mute
'''
 (out/'deep-idle.S').write_text(assembly)
 (out/'deep-idle.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} rw_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 run('gcc','-mcpu=54418','-O2',*(['-DRW_DOUBLE_STOP'] if automatic_stop else []),'-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/deep-idle329.c','-o',out/'deep-idle.o')
 run('gcc','-mcpu=54418','-c',out/'deep-idle.S','-o',out/'deep-idle-irq.o')
 run('ld','-T',out/'deep-idle.ld','-o',out/'deep-idle.elf',out/'deep-idle.o',out/'deep-idle-irq.o')
 run('objcopy','-O','binary',out/'deep-idle.elf',out/'deep-idle.bin');blob=(out/'deep-idle.bin').read_bytes()
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'deep-idle.elf').splitlines() if len(v:=line.split())==3}
 assert CODE+len(blob)<=BSS and symbols['rw_end']<=END
 new=b'\x4e\xb9'+struct.pack('>I',symbols['rw_mute_irq']);native[at-nb:at-nb+6]=new;runtime[CODE-base:CODE-base+len(blob)]=blob
 audio_new=b'\x4e\xb9'+struct.pack('>I',symbols['rw_audio']);native[audio_at-nb:audio_at-nb+6]=audio_new
 note_new=b'\x4e\xf9'+struct.pack('>I',symbols['rw_note']);native[note_at-nb:note_at-nb+6]=note_new
 patches=[dict(at=at,old=expected.hex(),new=new.hex()),dict(at=audio_at,old=audio_old.hex(),new=audio_new.hex()),dict(at=note_at,old=note_old.hex(),new=note_new.hex())]
 if automatic_stop:
  stop_at=0x40058c04;stop_old=b'\x4e\xf9'+struct.pack('>I',aliases['rw_old_sound_off']);assert native[stop_at-nb:stop_at-nb+6]==stop_old
  stop_new=b'\x4e\xf9'+struct.pack('>I',symbols['rw_stop']);native[stop_at-nb:stop_at-nb+6]=stop_new;patches.append(dict(at=stop_at,old=stop_old.hex(),new=stop_new.hex()))
 return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=symbols['rw_end']-BSS,symbols=symbols,aliases=aliases,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),private_command_only=not automatic_stop,automatic_stop_sleep=automatic_stop,ordinary_stop_unchanged=True,hardware_tested=False)
