"""Candidat prive : veille des voix stock uniquement apres silence entier exact."""
from pathlib import Path
import os,subprocess,struct,hashlib
ROOT=Path(__file__).resolve().parents[1];CODE=0x46702000
def prepare(meta,runtime,sram,out):
    ps=meta['stock_voice_admin']['symbols'];out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not any(runtime[CODE-0x46700000:CODE-0x46700000+512])
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    (out/'zero.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) }} }}\nqt_engines = {ps["qt_engines"]:#x};\n')
    run('gcc','-mcpu=54418','-c',ROOT/'tools/machines/track_fx/exact-zero-voice304.S','-o',out/'zero.o');run('ld','-T',out/'zero.ld','-o',out/'zero.elf',out/'zero.o');run('objcopy','-O','binary',out/'zero.elf',out/'zero.bin')
    sy={v[2]:int(v[0],16) for line in run('nm',out/'zero.elf').splitlines() if len(v:=line.split())==3};code=(out/'zero.bin').read_bytes();assert len(code)<=512
    patches=[]
    for at,old,new in [(0x8000e91e,ps['qt_cached_gate'],sy['zz_gate']),(0x8000734c,ps['qt_scan_gate'],sy['zz_scan'])]:
        expected=b'\x4e\xf9'+struct.pack('>I',old);assert sram[at-0x80000000:at-0x80000000+6]==expected
        patches.append(dict(at=at,old=expected.hex(),new=(b'\x4e\xf9'+struct.pack('>I',new)).hex()))
    return dict(code=CODE,code_bytes=len(code),symbols=sy,patches=patches,sha256=hashlib.sha256(code).hexdigest(),new_state_bytes=0,exact_zero_only=True,finished_native_amp_required=True,amp_current_offset=0x230,amp_previous_offset=0x234,amp_stage_offset=0x23c,terminal_stage=1,machine_change_clears_counter=True,hardware_tested=False)

def apply(meta,runtime,sram,out):
    d=prepare(meta,runtime,sram,out)
    runtime[CODE-0x46700000:CODE-0x46700000+d['code_bytes']]=(Path(out)/'zero.bin').read_bytes()
    for p in d['patches']:sram[p['at']-0x80000000:p['at']-0x80000000+6]=bytes.fromhex(p['new'])
    return d
