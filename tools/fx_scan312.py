"""Scan veille deroule : memes32samples et meme seuil exact zero, garde SIL intact."""
from pathlib import Path
import hashlib,os,subprocess
ROOT=Path(__file__).resolve().parents[1]

def apply(meta,runtime,out):
 base=0x46700000;prior=meta['fx_energy'];code=prior['code'];end=meta['silent_commit_guard']['code'];out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert hashlib.sha256(runtime[code-base:code-base+prior['code_bytes']]).hexdigest()==prior['sha256']
 assert not any(runtime[code-base+prior['code_bytes']:end-base])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 (out/'scan.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in prior['aliases'].items()))
 run('gcc','-mcpu=54418','-O2','-DEI_SCAN_UNROLL','-ffreestanding','-fno-builtin','-fno-common','-c',ROOT/'tools/machines/track_fx/fx-energy309.c','-o',out/'scan.o');run('ld','-T',out/'scan.ld','-o',out/'scan.elf',out/'scan.o');run('objcopy','-O','binary',out/'scan.elf',out/'scan.bin')
 blob=(out/'scan.bin').read_bytes();assert code+len(blob)<=end
 sy={v[2]:int(v[0],16) for line in run('nm',out/'scan.elf').splitlines() if len(v:=line.split())==3};assert sy['ei_present']==prior['symbols']['ei_present']
 runtime[code-base:end-base]=blob+bytes(end-code-len(blob))
 return dict(code=code,code_bytes=len(blob),symbols=sy,sha256=hashlib.sha256(blob).hexdigest(),previous_sha256=prior['sha256'],aliases=prior['aliases'],new_state_bytes=0,all_32_samples_checked=True,threshold_unchanged=True,active_transport_unchanged=True,hardware_tested=False)
