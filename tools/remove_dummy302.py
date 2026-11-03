"""Retire Dummy des machines permises et efface son rendu, nom et illustrations.

Le navigateur confirme partage ce module : ses fonctions restent en place.
Les trampolines d'icones deleguent aux anciens choix, y compris MD.
"""
from pathlib import Path
import os,struct,subprocess,hashlib
def apply(meta,native,runtime,out):
 if not meta.get('dummy300'):return {'already_absent':True}
 d=meta['dummy300'];s=d['symbols'];base=0x46700000;nb=0x40000400
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 code=0x467a6800;limit=0x467a7000
 assert not any(runtime[code-base:limit-base])
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)])
 source=Path(__file__).parent/'machines/track_fx/dummy300.c'
 run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-DDY_FULL=1','-DDY_OPTIONAL=1','-DDY_REMOVE','-c',source,'-o',out/'remove.o')
 (out/'remove.ld').write_text(f'SECTIONS {{ . = {code:#x}; .text : {{ KEEP(*(.text.dy_allowed)) KEEP(*(.text.dy_set)) *(.text*) *(.rodata*) }} /DISCARD/ : {{ *(.bss*) *(.comment) *(.eh_frame) }} }}\ndy_old_set = {s["dy_fallback_set"]:#x};\ndy_md_present = {s["dy_md_present"]:#x};\n')
 run('ld','--gc-sections','-T',out/'remove.ld','-o',out/'remove.elf',out/'remove.o');run('objcopy','-O','binary',out/'remove.elf',out/'remove.bin')
 sy={v[2]:int(v[0],16) for line in run('nm','--defined-only',out/'remove.elf').decode().splitlines() if len(v:=line.split())==3}
 blob=(out/'remove.bin').read_bytes();assert code+len(blob)<=limit
 runtime[code-base:code-base+len(blob)]=blob
 patches=[];erased=[]
 def patch(at,new):
  buf,off=(native,at-nb) if at<base else (runtime,at-base)
  old=bytes(buf[off:off+len(new)]);buf[off:off+len(new)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 def erase(lo,hi):
  assert d['code']<=lo<hi<=d['code']+d['code_bytes']
  raw=bytes(runtime[lo-base:hi-base]);runtime[lo-base:hi-base]=bytes(hi-lo);erased.append(dict(at=lo,bytes=hi-lo,sha256=hashlib.sha256(raw).hexdigest()))
 assert native[0x400a7d96-nb:0x400a7d9c-nb]==b'\x4e\xf9'+struct.pack('>I',s['dy_voice'])
 patch(0x400a7d96,bytes.fromhex('2005e4a07201'))
 erase(s['dy_voice'],s['dy_names'])
 for name,end in [('names','left'),('left','right'),('right','shown'),('shown','amp_gate'),('amp_gate','lfo_gate'),('lfo_gate','increment')]:
  at=s['dy_'+name];erase(at,s['dy_'+end]);patch(at,b'\x4e\xf9'+struct.pack('>I',s['dy_fallback_'+name]))
 for name,end in [('allowed','set'),('set','draw_marks')]:
  at=s['dy_'+name];erase(at,s['dy_'+end]);patch(at,b'\x4e\xf9'+struct.pack('>I',sy['dy_'+name]))
 erase(s['dy_icon_bitmap'],s['dy_stats_pixels']+384);erase(s['dy_name'],s['dy_name']+6)
 assert native[0x400147a4-nb:0x400147a6-nb]==bytes.fromhex('701c');patch(0x400147a4,bytes.fromhex('701b'))
 at=0x4683c800+41*56+12;assert runtime[at-base:at-base+4]==struct.pack('>I',28<<8);patch(at,struct.pack('>I',27<<8))
 at=s['dy_display_hook'];raw=bytes(runtime[at-base:at-base+80]);assert raw.count(bytes.fromhex('701c'))==1;patch(at+raw.index(bytes.fromhex('701c')),bytes.fromhex('701b'))
 meta['dummy_available']=False;meta['dummy_removed']=True;meta['dummy_selection_bit']=None
 return dict(code=code,code_bytes=len(blob),symbols=sy,patches=patches,erased=erased,shared_browser_retained=True,machine28_selectable=False)
