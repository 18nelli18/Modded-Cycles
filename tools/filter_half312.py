"""Prototype LOW24k : entree moyennee, sortie interpolee, pole recalcule.

Occupe4400..4800 et remplace le module de coefficients4c00..5600.
Les autres modes et le bypass natif restent a48k.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]

def apply(meta,runtime,out):
 base=0x46700000;code=0x46704400;coeff=0x46704c00;bss=0x46705600;out=Path(out);out.mkdir(parents=True,exist_ok=True)
 hall=meta['hall_merged_gain'];old=meta['filter_single_div'];assert hall['code']+hall['code_bytes']<=code
 assert not any(runtime[code-base:0x46704800-base])
 assert old['code']==coeff and hashlib.sha256(runtime[coeff-base:coeff-base+old['code_bytes']]).hexdigest()==old['sha256']
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
 aliases=meta['filter_modes']['symbols'];(out/'coeff.ld').write_text(f'SECTIONS {{ .text {coeff:#x} : {{ *(.text*) *(.rodata*) }} .bss {bss:#x} (NOLOAD) : {{ *(.bss*) }} fh_end = .; }}\n'+''.join(f'{k} = {aliases[k]:#x};\n' for k in ['fc_type','fc_native_table']))
 objects=[]
 for name,flags in [('filter-low',['-DPF_HALF_RATE']),('filter-modes',[])]:
  obj=out/(name+'.o');run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-DPF_SINGLE_DIV',*flags,'-c',ROOT/('tools/machines/track_fx/'+name+'.c'),'-o',obj);objects.append(obj)
 run('ld','-T',out/'coeff.ld','-o',out/'coeff.elf',*objects);run('objcopy','-O','binary',out/'coeff.elf',out/'coeff.bin')
 sy={v[2]:int(v[0],16) for line in run('nm',out/'coeff.elf').splitlines() if len(v:=line.split())==3};blob=(out/'coeff.bin').read_bytes();assert coeff+len(blob)<=bss and sy['fh_end']<=0x46705858
 (out/'kernel.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) }} }}\npf_coeff = {sy["fast_pf_coeff"]:#x};\n')
 run('gcc','-mcpu=54418','-DPF_HALF_RATE','-c',ROOT/'tools/machines/polivoks_lite/filter.S','-o',out/'kernel.o');run('ld','-T',out/'kernel.ld','-o',out/'kernel.elf',out/'kernel.o');run('objcopy','-O','binary',out/'kernel.elf',out/'kernel.bin');kernel=(out/'kernel.bin').read_bytes();assert code+len(kernel)<=0x46704800
 patches=[]
 def patch(at,new,expected):
  was=bytes(runtime[at-base:at-base+6]);assert was==expected,(hex(at),was.hex(),expected.hex());runtime[at-base:at-base+6]=new;patches.append(dict(at=at,old=was.hex(),new=new.hex()))
 for name in ['fast_pf_coeff','fast_fc_coeff']:
  patch(meta['filter_pattern300']['symbols'][name],b'\x4e\xf9'+struct.pack('>I',sy[name]),b'\x4e\xf9'+struct.pack('>I',old['symbols'][name]))
 at=meta['recovery_symbols']['pf_run'];patch(at,b'\x4e\xf9'+struct.pack('>I',code),bytes.fromhex('202f000841f9'))
 runtime[coeff-base:bss-base]=blob+bytes(bss-coeff-len(blob));runtime[code-base:code-base+len(kernel)]=kernel
 return dict(code=code,code_bytes=len(kernel),coeff=coeff,coeff_bytes=len(blob),bss=bss,bss_bytes=sy['fh_end']-bss,symbols=sy,patches=patches,rate=24000,output_rate=48000,new_state_bytes=0,quality_changed=True,hardware_tested=False)
