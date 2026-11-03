"""DATA distant prive, uniquement confirmation OS ; aucune modification DSP315."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1];CODE=0x4679a400;BSS=0x4679b800;END=BSS+64
def apply(meta,runtime,out):
 base=0x46700000;out=Path(out);out.mkdir(parents=True,exist_ok=True);assert not any(runtime[CODE-base:END-base]);assert not meta.get('output_monitor_fast')
 sy=meta['diagnostic_midi']['symbols'];aliases=dict(uk_old_request=sy['dx_request'],uk_old_send=sy['dx_send'])
 (out/'upgrade-key.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} uk_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/upgrade-key317.c','-o',out/'upgrade-key.o');run('ld','-T',out/'upgrade-key.ld','-o',out/'upgrade-key.elf',out/'upgrade-key.o');run('objcopy','-O','binary',out/'upgrade-key.elf',out/'upgrade-key.bin');raw=(out/'upgrade-key.bin').read_bytes()
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'upgrade-key.elf').splitlines() if len(v:=line.split())==3};assert CODE+len(raw)<=BSS and symbols['uk_end']<=END
 patches=[]
 for oldfn,newfn in [('dx_request','uk_request'),('dx_send','uk_send')]:
  expected=b'\x4e\xb9'+struct.pack('>I',sy[oldfn]);candidates=[p for p in meta['diagnostic_midi']['patches'] if p['new']==expected.hex()];assert len(candidates)==1
  at=candidates[0]['at'];assert runtime[at-base:at-base+6]==expected
  new=b'\x4e\xb9'+struct.pack('>I',symbols[newfn]);runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=expected.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(raw)]=raw
 return dict(code=CODE,code_bytes=len(raw),bss=BSS,bss_bytes=symbols['uk_end']-BSS,symbols=symbols,patches=patches,sha256=hashlib.sha256(raw).hexdigest(),audio_hooks=False,hardware_tested=False,request='SMUK317!',upgrade_confirmation_only=True)
