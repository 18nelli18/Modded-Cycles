"""Cache LOW identique : quotients DIVU et restes mul/sub, aucune quantification."""
from pathlib import Path
import os,subprocess,struct,hashlib
ROOT=Path(__file__).resolve().parents[1];CODE=0x46704c00;BSS=0x46705600;END=0x46705858
def apply(meta,runtime,out,full_cache=False):
    base=0x46700000;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert any(x['kind']=='remove' and x['address']<=CODE and END<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    assert not any(runtime[CODE-base:END-base])
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    aliases=meta['filter_modes']['symbols']
    (out/'filter-div.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} fd_end = .; }}\n'+''.join(f'{k} = {aliases[k]:#x};\n' for k in ['fc_type','fc_native_table']))
    cache_flags=['-DPF_FULL_CACHE'] if full_cache else []
    run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-DPF_SINGLE_DIV',*cache_flags,'-c',ROOT/'tools/machines/track_fx/filter-low.c','-o',out/'filter-div.o')
    run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DPF_SINGLE_DIV',*cache_flags,'-c',ROOT/'tools/machines/track_fx/filter-modes.c','-o',out/'filter-modes.o')
    run('ld','-T',out/'filter-div.ld','-o',out/'filter-div.elf',out/'filter-div.o',out/'filter-modes.o');run('objcopy','-O','binary',out/'filter-div.elf',out/'filter-div.bin')
    blob=(out/'filter-div.bin').read_bytes();symbols={v[2]:int(v[0],16) for line in run('nm',out/'filter-div.elf').splitlines() if len(v:=line.split())==3}
    assert CODE+len(blob)<=BSS and symbols['fd_end']<=END
    patches=[]
    for name in ['fast_pf_coeff','fast_fc_coeff']:
        at=meta['filter_pattern300']['symbols'][name];old=bytes(runtime[at-base:at-base+6]);assert old[:2]==bytes.fromhex('4fef')
        new=b'\x4e\xf9'+struct.pack('>I',symbols[name]);runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
    runtime[CODE-base:CODE-base+len(blob)]=blob
    return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=symbols['fd_end']-BSS,symbols=symbols,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),quality_unchanged=True,coefficients_exact=True,full_coefficient_cache=full_cache,hardware_tested=False)
