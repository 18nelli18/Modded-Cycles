"""Delay natif : matrice stable specialisee, memes valeurs et aucune nouvelle BSS."""
from pathlib import Path
import os,subprocess,struct,hashlib
ROOT=Path(__file__).resolve().parents[1];CODE=0x46704800;SITE=0x400576cc
def apply(meta,native,runtime,out):
    base=0x46700000;offset=CODE-base;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert any(x['kind']=='remove' and x['address']<=CODE and CODE+1024<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    assert not any(runtime[offset:offset+1024])
    old=bytes(native[SITE-0x40000400:SITE-0x40000400+6]);assert old[:2]==b'\x4e\xf9'
    target=int.from_bytes(old[2:],'big');assert 0x46700000<=target<0x46700600
    assert runtime[target-base:target-base+4]==bytes.fromhex('ac9c5808')
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    (out/'delay-static.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) }} }}\nds_old = {target:#x};\n')
    run('gcc','-mcpu=54418','-c',ROOT/'tools/machines/track_fx/delay-static307.S','-o',out/'delay-static.o');run('ld','-T',out/'delay-static.ld','-o',out/'delay-static.elf',out/'delay-static.o');run('objcopy','-O','binary',out/'delay-static.elf',out/'delay-static.bin')
    blob=(out/'delay-static.bin').read_bytes();assert len(blob)<=1024
    new=b'\x4e\xf9'+struct.pack('>I',CODE);native[SITE-0x40000400:SITE-0x40000400+6]=new;runtime[offset:offset+len(blob)]=blob
    return dict(code=CODE,code_bytes=len(blob),patches=[dict(at=SITE,old=old.hex(),new=new.hex())],sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,quality_unchanged=True,delay_lengths_unchanged=True,hardware_tested=False)
