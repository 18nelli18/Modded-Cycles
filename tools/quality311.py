"""Comparaison qualite/cout : HALL3k et CHORD sans interpolation des tables.

Adresses et tailles verifiees contre les modules309 deja demarres ; aucun
nouveau buffer, detour audio, nombre de voix ou changement de frequence de note.
"""
from pathlib import Path
import hashlib,os,subprocess
ROOT=Path(__file__).resolve().parents[1]

def apply(meta,native,runtime,sram,out):
    base=0x46700000;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    result={}
    for key,capacity,src,flags,aliases,opt in [
        ('chord_second',0x1100,'tools/machines/chord_cpu/oscillator.S',['CHORD_SECOND_FAST','CHORD_ECO_LOOKUP'],{},'-Os'),
        ('hall_merged_gain',0x1000,'tools/machines/fx_menu/hall-eco305.c',['FX_POLISH','HALL_ECO_6K','HALL_ECO_3K','HALL_ECO_SPARSE','HALL_MERGED_GAIN'],{k:v for k,v in meta['fx_menu']['symbols'].items() if k.startswith('hall_') or k in ('ps_comb','ps_ap')},'-O3')]:
        d=meta[key];code=d['code'];before=bytes(runtime[code-base:code-base+d['code_bytes']])
        assert hashlib.sha256(before).hexdigest()==d['sha256']
        assert not any(runtime[code-base+d['code_bytes']:code-base+capacity])
        stem=out/key
        stem.with_suffix('.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
        run('gcc','-mcpu=54418',opt,'-ffreestanding','-fno-builtin','-fno-common','-fwrapv',*[f'-D{x}' for x in flags],'-c',ROOT/src,'-o',stem.with_suffix('.o'))
        run('ld','-T',stem.with_suffix('.ld'),'-o',stem.with_suffix('.elf'),stem.with_suffix('.o'));run('objcopy','-O','binary',stem.with_suffix('.elf'),stem.with_suffix('.bin'))
        blob=stem.with_suffix('.bin').read_bytes();assert len(blob)<=capacity
        symbols={v[2]:int(v[0],16) for line in run('nm',stem.with_suffix('.elf')).splitlines() if len(v:=line.split())==3}
        entry='chord_fast' if key=='chord_second' else 'fx_hall';assert symbols[entry]==d['symbols'][entry]
        runtime[code-base:code-base+capacity]=blob+bytes(capacity-len(blob))
        result[key]=dict(code=code,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),previous_sha256=d['sha256'],capacity=capacity,symbols=symbols)
    return dict(modules=result,hall_internal_rate=3000,chord_wavetable_interpolation=False,quality_changed=True,new_state_bytes=0,hardware_tested=False)
