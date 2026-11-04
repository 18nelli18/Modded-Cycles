"""Upper slices sur le clavier normal, construction native des note-on/off."""
from pathlib import Path
import hashlib
import os
import struct
import subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE=0x46700000;CODE=0x4679f400;LIMIT=0x4679f800;SITE=0x4001a236
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert meta.get('song_cursor367') and meta['song_cursor367']['code']+meta['song_cursor367']['code_bytes']<=CODE
 assert not any(runtime[CODE-BASE:LIMIT-BASE])
 old=bytes.fromhex('4872e8342f03');assert native[SITE-0x40000400:SITE-0x40000400+6]==old
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 objects=[]
 for name in ('slice-bank368.c','slice-bank368.S'):
  obj=out/(name+'.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/song'/name,'-o',obj);objects.append(obj)
 (out/'slice.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .forbidden 0 (NOLOAD) : {{ *(.data*) *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\nASSERT(SIZEOF(.forbidden)==0,"etat interdit")\nASSERT(ADDR(.text)+SIZEOF(.text)<={LIMIT:#x},"slice plein")\nsn_modes = {meta["wizard_display"]["symbols"]["ws_mode"]:#x};\n')
 run('ld','--orphan-handling=error','-T',out/'slice.ld','-e','sn_push368','-o',out/'slice.elf',*objects);run('objcopy','-O','binary',out/'slice.elf',out/'slice.bin');blob=(out/'slice.bin').read_bytes();symbols={p[2]:int(p[0],16) for line in run('nm',out/'slice.elf').splitlines() if len(p:=line.split())==3}
 new=b'\x4e\xb9'+struct.pack('>I',symbols['sn_push368']);native[SITE-0x40000400:SITE-0x40000400+6]=new;runtime[CODE-BASE:CODE-BASE+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),symbols=symbols,patches=[dict(at=SITE,region='native',old=old.hex(),new=new.hex()),dict(at=CODE,region='runtime',old=bytes(len(blob)).hex(),new=blob.hex())],sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,added_audio_hooks=0,native_release_ownership=True,hardware_tested=False)
