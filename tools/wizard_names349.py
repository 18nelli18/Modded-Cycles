"""UI3.49 : corrige les vrais popups et noms LFO de Wizard, sans hook audio."""
from pathlib import Path
import os,struct,subprocess,hashlib
CODE=0x467a6200
LIMIT=0x467a7000
ENTRIES={'ld_short':(0x467ae7b2,8),'ld_long':(0x467ae7c8,8),'ld_first':(0x467ae924,6),'ld_second':(0x467ae99c,6)}
def apply(meta,native,runtime,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert not meta.get('wizard_names349')
 assert not any(runtime[CODE-0x46700000:LIMIT-0x46700000])
 assert any(x['kind']=='remove' and x['address']<=CODE and LIMIT<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
 os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)])
 source=Path(__file__).parent/'machines/lfo_destinations/ui.c'
 run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-DLD_EXTERNAL_API','-c',source,'-o',out/'names.o')
 script='SECTIONS { . = '+hex(CODE)+'; .text : { '+''.join('KEEP(*(.text.'+name+')) ' for name in ENTRIES)+'*(.text*) *(.rodata*) } /DISCARD/ : { *(.comment) *(.eh_frame) } }\nld_api = 0x467aeb74;\n'
 (out/'names.ld').write_text(script)
 run('ld','--gc-sections','-T',out/'names.ld','-o',out/'names.elf',out/'names.o')
 run('objcopy','-O','binary',out/'names.elf',out/'names.bin')
 sy={line.split()[2]:int(line.split()[0],16) for line in run('nm','--defined-only',out/'names.elf').decode().splitlines() if len(line.split())==3}
 blob=(out/'names.bin').read_bytes();assert CODE+len(blob)<=LIMIT
 patches=[]
 for name,(at,size) in ENTRIES.items():
  off=at-0x46700000;old=bytes(runtime[off:off+size])
  expected={'ld_short':'487800342f2f000c','ld_long':'4878002c2f2f000c','ld_first':'598f2f032f02','ld_second':'2f02242f0008'}[name]
  assert old.hex()==expected,(name,old.hex())
  new=b'\x4e\xf9'+struct.pack('>I',sy[name])+b'\x4e\x71'*((size-6)//2)
  runtime[off:off+size]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 runtime[CODE-0x46700000:CODE-0x46700000+len(blob)]=blob
 return dict(code=CODE,code_bytes=len(blob),symbols={k:v for k,v in sy.items() if k in ENTRIES},patches=patches,sha256=hashlib.sha256(blob).hexdigest(),UI_only=True,audio_hooks=False,new_state_bytes=0)
