"""Panic explicite : quiescence stock par le fondu natif, jamais le STOP simple."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]

def apply(meta,runtime,out):
 base=0x46700000;code=0x46704600;limit=0x46704800;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if 'filter_half_rate' in meta:assert meta['filter_half_rate']['code']+meta['filter_half_rate']['code_bytes']<=code
 assert not any(runtime[code-base:limit-base])
 old=meta['fx_energy'];scan=old['code'];scan_end=meta['silent_commit_guard']['code'];assert hashlib.sha256(runtime[scan-base:scan-base+old['code_bytes']]).hexdigest()==old['sha256']
 ps=meta['per_track_fx']['symbols'];aliases=dict(panic_pending=ps['mf_fx_panic_pending'],panic_previous=ps['mf_fx_begin'],panic_woken=ps['idle_woken'],panic_started=ps['idle_started'])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 (out/'panic-stock.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 run('gcc','-mcpu=54418','-c',ROOT/'tools/machines/track_fx/panic-stock313.S','-o',out/'panic-stock.o');run('ld','-T',out/'panic-stock.ld','-o',out/'panic-stock.elf',out/'panic-stock.o');run('objcopy','-O','binary',out/'panic-stock.elf',out/'panic-stock.bin');blob=(out/'panic-stock.bin').read_bytes();assert code+len(blob)<=limit
 (out/'panic-scan.ld').write_text(f'SECTIONS {{ .text {scan:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in old['aliases'].items()))
 run('gcc','-mcpu=54418','-O2','-DEI_SCAN_UNROLL','-DEI_PANIC_STOCK','-ffreestanding','-fno-builtin','-fno-common','-c',ROOT/'tools/machines/track_fx/fx-energy309.c','-o',out/'panic-scan.o');run('ld','-T',out/'panic-scan.ld','-o',out/'panic-scan.elf',out/'panic-scan.o');run('objcopy','-O','binary',out/'panic-scan.elf',out/'panic-scan.bin');body=(out/'panic-scan.bin').read_bytes();assert scan+len(body)<=scan_end
 site=ps['idle_voice_begin'];was=b'\x4e\xb9'+struct.pack('>I',ps['mf_fx_begin']);chunk=bytes(runtime[site-base:site-base+32]);assert chunk.count(was)==1
 at=site+chunk.index(was);new=b'\x4e\xb9'+struct.pack('>I',code);runtime[at-base:at-base+6]=new;runtime[code-base:code-base+len(blob)]=blob;runtime[scan-base:scan_end-base]=body+bytes(scan_end-scan-len(body))
 scan_sy={v[2]:int(v[0],16) for line in run('nm',out/'panic-scan.elf').splitlines() if len(v:=line.split())==3}
 return dict(code=code,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),scan_code=scan,scan_bytes=len(body),scan_sha256=hashlib.sha256(body).hexdigest(),scan_symbols=scan_sy,aliases=aliases,patches=[dict(at=at,old=was.hex(),new=new.hex())],new_state_bytes=0,ordinary_stop_unchanged=True,parameters_unchanged=True,native_block_fade_retained=True,stock_only_amp_quiescence=True,hardware_tested=False)
