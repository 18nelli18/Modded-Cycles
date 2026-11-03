"""Frontiere postmix reconstruite sur place, noyaux et etat existants."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=0x46700000
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);s=meta['per_track_fx']['symbols'];code=s['mf_post'];limit=s['rt_render']
 assert {k for k,v in s.items() if code<=v<limit}=={'mf_post'}
 keys=['mf_mode','mf_audio_ready','mf_requested','mf_side','mf_side_on','mf_live','lt_active','enabled','sends','lt_source_mask','left','right','wet','mf_old_post','lt_run_slots'];aliases={k:s[k] for k in keys}
 (out/'routing-post.ld').write_text(f'SECTIONS {{ .text {code:#x} : SUBALIGN(2) {{ *(.text*) *(.rodata*) }} .forbidden 0 (NOLOAD) : {{ *(.data*) *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\nASSERT(SIZEOF(.forbidden)==0,"etat non autorise")\nASSERT(ADDR(.text)+SIZEOF(.text)<={limit:#x},"post plein")\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 run('gcc','-mcpu=54418','-O2','-falign-functions=2','-falign-jumps=2','-falign-loops=2','-fomit-frame-pointer','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-fno-pic','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/routing-post364.c','-o',out/'routing-post.o');run('ld','--orphan-handling=error','-T',out/'routing-post.ld','-o',out/'routing-post.elf',out/'routing-post.o');run('objcopy','-O','binary',out/'routing-post.elf',out/'routing-post.bin');blob=(out/'routing-post.bin').read_bytes();assert code+len(blob)<=limit
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'routing-post.elf').splitlines() if len(v:=line.split())==3};assert symbols['ac_post']==code
 old=bytes(runtime[code-BASE:limit-BASE]);new=blob.ljust(limit-code,b'\0');runtime[code-BASE:limit-BASE]=new
 return dict(code=code,code_bytes=len(blob),symbols=symbols,patches=[dict(at=code,old=old.hex(),new=new.hex())],sha256=hashlib.sha256(blob).hexdigest(),in_place=True,new_state_bytes=0,no_route_no_tail_bypass=True,tail_processing_retained=True,hardware_tested=False)
