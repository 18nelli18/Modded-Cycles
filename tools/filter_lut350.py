"""LOW/HP/BP exacts a resonance nulle : tables de quotients, restes reconstitues.

Deux tables de16KiB dans le staging retire. Code UI348/349 et SRAM inchanges.
Les autres resonances gardent les divisions exactes de302, sans quantification.
"""
from pathlib import Path
import hashlib,struct,subprocess,os
CODE=0x467a4200;BSS=0x467a5800;END=0x467a6000
F=0x46794700;R=0x467a7000
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);base=0x46700000
 for lo,hi in [(CODE,END),(F,F+16384),(R,R+16384)]:
  assert not any(runtime[lo-base:hi-base]),hex(lo)
  assert any(x['kind']=='remove' and x['address']<=lo and hi<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 columns=[[],[]]
 for f in range(4096):
  c=4096-f;ff=f*f;feedback=(362*(f*c))>>8;den=ff+c*c+feedback
  columns[0].append((ff<<30)//den);columns[1].append((feedback<<30)//den)
 for at,data in zip([F,R],columns):runtime[at-base:at-base+16384]=struct.pack('>4096I',*data)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)])
 root=Path(__file__).resolve().parents[1]
 objects=[]
 for name in ['filter-low','filter-modes']:
  obj=out/(name+'.o');run('gcc','-mcpu=54418','-O2','-fwrapv','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-DPF_SINGLE_DIV','-DPF_FULL_CACHE','-DPF_ZERO_LUT','-c',root/'tools/machines/track_fx'/(name+'.c'),'-o',obj);objects.append(obj)
 aliases={k:meta['filter_modes']['symbols'][k] for k in ['fc_type','fc_native_table']};aliases.update(pf_zero_f=F,pf_zero_r=R)
 script=f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) }} fl_end = .; }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items())
 (out/'filter-lut.ld').write_text(script);run('ld','-T',out/'filter-lut.ld','-o',out/'filter-lut.elf',*objects);run('objcopy','-O','binary',out/'filter-lut.elf',out/'filter-lut.bin')
 blob=(out/'filter-lut.bin').read_bytes();sy={v[2]:int(v[0],16) for line in run('nm',out/'filter-lut.elf').decode().splitlines() if len(v:=line.split())==3}
 assert CODE+len(blob)<=BSS and sy['fl_end']<=END
 prior=meta['filter_single_div'];patches=[]
 for name in ['fast_pf_coeff','fast_fc_coeff']:
  at=prior['symbols'][name];off=at-base;old=bytes(runtime[off:off+6]);assert old[:2]==bytes.fromhex('4fef'),(name,old.hex())
  new=b'\x4e\xf9'+struct.pack('>I',sy[name]);runtime[off:off+6]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 runtime[CODE-base:CODE-base+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),bss=BSS,bss_bytes=sy['fl_end']-BSS,symbols=sy,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),table_bytes=32768,coefficients_exact=True,sample_rate=48000,resonance_fallback_exact=True,audio_kernel_unchanged=True)
