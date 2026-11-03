"""CHORD : poids nul symetrique, interpolation intacte, ancien HALL devenu mort."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
def apply(meta,native,runtime,sram,out):
    base=0x46700000;prior=meta['eco_hall'];retired_at=prior['code'];retired_size=prior['code_bytes'];code_at=0x46702100;capacity=0x46703200-code_at
    assert meta['hall_merged_gain']['code']!=code_at
    assert runtime[meta['fx_menu']['symbols']['fx_hall']-base:meta['fx_menu']['symbols']['fx_hall']-base+6]==b'\x4e\xf9'+struct.pack('>I',meta['hall_merged_gain']['symbols']['fx_hall'])
    assert hashlib.sha256(runtime[retired_at-base:retired_at-base+retired_size]).hexdigest()==prior['sha256']
    assert not any(runtime[code_at-base:retired_at-base]) and not any(runtime[retired_at-base+retired_size:code_at-base+capacity])
    assert any(x['kind']=='remove' and x['address']<=code_at and code_at+capacity<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    needle=struct.pack('>I',retired_at)
    # Les tables MD peuvent contenir ces quatre octets a une adresse impaire.
    # Un operande de saut ColdFire ou pointeur aligne doit rester absent.
    for bank in (runtime,native,sram):
        assert not any(bank[i:i+4]==needle for i in range(0,len(bank)-3,2))
    out=Path(out);out.mkdir(parents=True,exist_ok=True);cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    run('gcc','-mcpu=54418','-DCHORD_SECOND_FAST','-c',ROOT/'tools/machines/chord_cpu/oscillator.S','-o',out/'chord-second.o');run('ld','-Ttext',hex(code_at),'-e','chord_fast','-o',out/'chord-second.elf',out/'chord-second.o');run('objcopy','-O','binary',out/'chord-second.elf',out/'chord-second.bin')
    blob=(out/'chord-second.bin').read_bytes();assert len(blob)<=capacity
    sy={v[2]:int(v[0],16) for line in run('nm',out/'chord-second.elf').splitlines() if len(v:=line.split())==3 and v[2].startswith('chord_')}
    site=0x400a8906;old=bytes(native[site-0x40000400:site-0x40000400+6]);assert old==b'\x4e\xf9'+struct.pack('>I',meta['recovery_symbols']['chord_fast'])
    new=b'\x4e\xf9'+struct.pack('>I',sy['chord_fast']);native[site-0x40000400:site-0x40000400+6]=new;runtime[code_at-base:code_at-base+capacity]=blob+bytes(capacity-len(blob))
    return dict(code=code_at,code_bytes=len(blob),reclaimed_bytes=capacity,symbols=sy,sha256=hashlib.sha256(blob).hexdigest(),patches=[dict(at=site,old=old.hex(),new=new.hex())],new_state_bytes=0,quality_unchanged=True,oscillator_count_unchanged=True,PM_constant_weights_fast=True,PM_weight_ramps_fast=True,hardware_tested=False)
