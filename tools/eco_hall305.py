"""Comparaison privee HALL6k : etat existant, durees conservees a un pas pres."""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
CODE=0x46702400

def apply(meta,runtime,out,sparse=False,merged=False):
    code_at=0x46703800 if merged else CODE
    base=0x46700000;fs=meta['fx_menu']['symbols'];out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert any(x['kind']=='remove' and x['address']<=code_at and code_at+4096<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    assert not any(runtime[code_at-base:code_at-base+4096])
    aliases={k:v for k,v in fs.items() if k.startswith('hall_') or k in ('ps_comb','ps_ap')}
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    (out/'eco-hall.ld').write_text(f'SECTIONS {{ .text {code_at:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
    run('gcc','-mcpu=54418','-O3','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DFX_POLISH','-DHALL_ECO_6K',*(['-DHALL_ECO_SPARSE'] if sparse else []),*(['-DHALL_MERGED_GAIN'] if merged else []),'-c',ROOT/'tools/machines/fx_menu/hall-eco305.c','-o',out/'eco-hall.o')
    run('ld','-T',out/'eco-hall.ld','-o',out/'eco-hall.elf',out/'eco-hall.o')
    run('objcopy','-O','binary',out/'eco-hall.elf',out/'eco-hall.bin')
    blob=(out/'eco-hall.bin').read_bytes();assert len(blob)<=4096
    symbols={v[2]:int(v[0],16) for line in run('nm',out/'eco-hall.elf').splitlines() if len(v:=line.split())==3}
    at=fs['fx_hall'];old=bytes(runtime[at-base:at-base+6]);new=b'\x4e\xf9'+struct.pack('>I',symbols['fx_hall'])
    assert old==b'\x4e\xf9'+struct.pack('>I',(meta['eco_hall']['symbols']['fx_hall'] if merged else meta['audio_headroom']['hall']['entry'])),old.hex()
    patches=[dict(at=at,old=old.hex(),new=new.hex())]
    if merged:
        lo=fs['fx_reverb'];hi=fs['fx_post'];pattern=bytes.fromhex('760bb6806700');chunk=bytes(runtime[lo-base:hi-base]);assert chunk.count(pattern)==1
        site=lo+chunk.index(pattern)+4;was=bytes(runtime[site-base:site-base+4]);replacement=b'\x4e\x71'*2
        patches.append(dict(at=site,old=was.hex(),new=replacement.hex()));runtime[site-base:site-base+4]=replacement
    runtime[at-base:at-base+6]=new;runtime[code_at-base:code_at-base+len(blob)]=blob
    return dict(code=code_at,code_bytes=len(blob),symbols=symbols,patches=patches,merged_output_gain=merged,sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,internal_rate=6000,previous_rate=6000 if merged else 12000,quality_unchanged=merged,combs_per_channel=2 if sparse else 4,allpass_per_channel=1 if sparse else 2,dry_unchanged=True,delay_unchanged=True,hardware_tested=False)
