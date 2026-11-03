"""Premiere frontiere du coeur audio : bus stereo6/7 vers noyau commun exact."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];BASE=0x46700000;NB=0x40000400
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);s=meta['per_track_fx']['symbols']
 code=s['mf_sum6'];seven=s['mf_sum7'];limit=s['mf_post'];assert s['mf_live']%4==0
 assert {k for k,v in s.items() if code<=v<limit}=={'mf_sum6','mf_sum7'}
 aliases={k:s[k] for k in ['native_sum','mf_mode','mf_audio_ready','mf_live','mf_sync_audio','sends','enabled']}
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
 (out/'routing-core.ld').write_text(f'SECTIONS {{ .six {code:#x} : {{ *(.text.ac_sum6) *(.text.routed6*) }} .seven {seven:#x} : {{ *(.text.ac_sum7) *(.text.routed7*) }} .forbidden 0 (NOLOAD) : {{ *(.text) *(.data*) *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\nASSERT(SIZEOF(.forbidden)==0,"etat non autorise")\nASSERT(ADDR(.six)+SIZEOF(.six)<={seven:#x},"routing six plein")\nASSERT(ADDR(.seven)+SIZEOF(.seven)<={limit:#x},"routing seven plein")\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 run('gcc','-mcpu=54418','-O3','-ffunction-sections','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-fno-pic','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/routing-core363.c','-o',out/'routing-core.o');run('ld','--orphan-handling=error','-T',out/'routing-core.ld','-o',out/'routing-core.elf',out/'routing-core.o');run('objcopy','-O','binary',out/'routing-core.elf',out/'routing-core.bin');blob=(out/'routing-core.bin').read_bytes();assert code+len(blob)<=limit
 sy={v[2]:int(v[0],16) for line in run('nm',out/'routing-core.elf').splitlines() if len(v:=line.split())==3};assert sy['ac_sum6']==code and sy['ac_sum7']==seven;patches=[]
 for at,key,target in [(0x40056716,'mf_sum6','ac_sum6'),(0x40056698,'mf_sum7','ac_sum7')]:
  old=b'\x4e\xf9'+struct.pack('>I',s[key]);assert native[at-NB:at-NB+6]==old;assert old==b'\x4e\xf9'+struct.pack('>I',sy[target])
 old=bytes(runtime[code-BASE:limit-BASE]);new=blob.ljust(limit-code,b'\0');runtime[code-BASE:limit-BASE]=new;patches.append(dict(at=code,old=old.hex(),new=new.hex()))
 return dict(code=code,code_bytes=len(blob),symbols=sy,aliases=aliases,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,PCM_exact=True,pattern_state_cache=False,sync_owner_unchanged=True,in_place=True,external_entries_unchanged=True,hardware_tested=False)
