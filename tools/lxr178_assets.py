"""ESTUS : voix LXR modifiees, huit modes ; caves disjointes, reservation inchangee."""
from pathlib import Path
import json,subprocess,hashlib,os
TEXT=0x468d2000;TRI=0x468c5000;SAW=0x468dc000;REC=0x468e4000;BSS=0x468e7000;END=0x468e8000

def prepare(root,build,named_controls=False,previous_popup=0,advanced=False,aliases=None,engine_read=False,copy_build=False,optimize=False,live_clear=False,plocks=False,filter_priority=False):
 src=root/'tools/machines/lxr178';up=json.loads((src/'UPSTREAM.json').read_text())
 for name,want in up['sha256'].items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==want,name
 cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH'];objs=[]
 for name in ('lxr.c','bridge178.c','reset178.S',*(['plocks191.c'] if plocks else [])):
  obj=build/(name+'.o');objs.append(obj)
  subprocess.run([cross+'gcc.exe','-mcpu=54418',*(['-DESTUS_CONTROLS=1'] if named_controls else []),*(['-DESTUS_ADVANCED=1'] if advanced else []),*(['-DESTUS_ENGINE_READ=1'] if engine_read else []),*(['-DESTUS_COPY_BUILD=1'] if copy_build else []),*(['-DESTUS_LIVE187=1'] if live_clear else []),*(['-DESTUS_PLOCK191=1'] if plocks else []),*(['-DESTUS_FILTER204=1'] if filter_priority else []),('-O3' if optimize and name=='lxr.c' else '-O2'),'-fomit-frame-pointer','-fwrapv','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fno-common','-fno-jump-tables','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I',str(src),'-c',str(src/name),'-o',str(obj)],check=True)
 ld=build/'lxr178.ld';elf=ld.with_suffix('.elf')
 ld.write_text(f'''SECTIONS {{
 .text {TEXT:#x} : {{ *(.text*) *(.rodata*) *(.lxr_sin) *(.data.lxrlabels) }} lxr178_code_end = .;
 .tri {TRI:#x} : {{ *(.lxr_tri) }}
 .saw {SAW:#x} : {{ *(.lxr_saw) }}
 .rec {REC:#x} : {{ *(.lxr_rec) }}
 /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }}
 .bss {BSS:#x} (NOLOAD) : {{ *(.bss*) *(.data*) *(.lxr_rw) *(COMMON) }} lxr178_end = .;
 }}
 ASSERT(lxr178_code_end <= 0x468d8000,"code ESTUS plein")
 ASSERT(SIZEOF(.tri)==11264 && SIZEOF(.saw)==11264 && SIZEOF(.rec)==11264,"tables ESTUS inattendues")
 ASSERT(lxr178_end < {END:#x},"BSS ESTUS pleine")
 ''')
 defs={k:0 for k in ('estus_menu','estus_fx_open','estus_wf_api','estus_notice')};defs.update(aliases or {})
 subprocess.run([cross+'ld.exe','--orphan-handling=error','-T',str(ld),'-o',str(elf),*map(str,objs),'--defsym',f'lxr178_previous_popup={previous_popup}',*[x for k,v in defs.items() for x in ('--defsym',f'{k}={v}')]],check=True)
 sy={v[2]:int(v[0],16) for line in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(v:=line.split())==3}
 segments=[]
 for name,at in (('text',TEXT),('tri',TRI),('saw',SAW),('rec',REC)):
  binary=build/('lxr178-'+name+'.bin');subprocess.run([cross+'objcopy.exe','-O','binary','-j','.'+name,str(elf),str(binary)],check=True);segments.append((at,binary.read_bytes()))
 segments.append((BSS,bytes(sy['lxr178_end']-BSS)))
 meta=dict(filter_combo_priority=filter_priority,advanced_native_plocks=plocks,name='ESTUS',machine=24,machines=[24],code=TEXT,code_end=sy['lxr178_code_end'],bss=BSS,end=sy['lxr178_end'],symbols=sy,defaults=[64,0,64,64,127] if named_controls else [64,64,64,8,127],optimized=optimize,engine_read=engine_read,advanced=advanced,named_controls=named_controls,engine_knob='SHAPE' if named_controls else 'CONTOUR',modes=['KICK','TOM','PERC','SNARE','CLAP','CL HAT','OP HAT','CYMBAL'],upstream=up,license='GPL-3.0-only',status='experimental',hardware_tested=False,segments=[dict(at=at,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for at,raw in segments])
 return segments,meta
