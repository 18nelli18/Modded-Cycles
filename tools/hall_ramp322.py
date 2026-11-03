"""HALL3k identique : rampe incrementale et branche de gain hors boucle."""
from pathlib import Path
import os,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];LIMIT=0x46704400
def apply(meta,runtime,out,opt='-O3',fractional=False):
 assert opt in ('-O3','-O2','-Os')
 base=0x46700000;out=Path(out);out.mkdir(parents=True,exist_ok=True);d=meta['hall_merged_gain'];code=d['code'];assert code==0x46703800 and meta['quality_economy']['hall_internal_rate']==3000
 assert hashlib.sha256(bytes(runtime[code-base:code-base+d['code_bytes']])).hexdigest()==d['sha256'];assert not any(runtime[code-base+d['code_bytes']:LIMIT-base])
 aliases={k:v for k,v in meta['fx_menu']['symbols'].items() if k.startswith('hall_') or k in ('ps_comb','ps_ap')};cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*args):return subprocess.check_output([cross+t+'.exe',*map(str,args)],text=True)
 (out/'hall-ramp.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
 flags=['FX_POLISH','HALL_ECO_6K','HALL_ECO_3K','HALL_ECO_SPARSE','HALL_MERGED_GAIN','HALL_LINEAR_WET' if fractional else 'HALL_RAMP_FAST']
 run('gcc','-mcpu=54418',opt,'-fwrapv','-ffreestanding','-fno-builtin','-fno-common',*[f'-D{x}' for x in flags],'-c',ROOT/'tools/machines/fx_menu/hall-eco305.c','-o',out/'hall-ramp.o');run('ld','-T',out/'hall-ramp.ld','-o',out/'hall-ramp.elf',out/'hall-ramp.o');run('objcopy','-O','binary',out/'hall-ramp.elf',out/'hall-ramp.bin');blob=(out/'hall-ramp.bin').read_bytes();assert code+len(blob)<=LIMIT,len(blob)
 symbols={v[2]:int(v[0],16) for line in run('nm',out/'hall-ramp.elf').splitlines() if len(v:=line.split())==3};assert symbols['fx_hall']==d['symbols']['fx_hall']
 runtime[code-base:LIMIT-base]=blob+bytes(LIMIT-code-len(blob))
 return dict(code=code,code_bytes=len(blob),symbols=symbols,sha256=hashlib.sha256(blob).hexdigest(),previous_sha256=d['sha256'],quality_unchanged=not fractional,fractional_wet_ramp=fractional,wet_error_bound_Q31=122880 if fractional else 0,network_history_unchanged=True,new_state_bytes=0,hardware_tested=False,compiler_optimization=opt)
