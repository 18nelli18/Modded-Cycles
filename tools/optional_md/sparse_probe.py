"""Chargement separe MD : pas de padding physique entre POTS et WAVE."""
from pathlib import Path
import struct,sys,json,hashlib,subprocess,os
W=Path(os.environ['MD_WORK']);R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools')]
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
import aplib_grow
from bootstrap205_assets import pack
source=Path(os.environ['MD_BASE_FILE'])
raw=source.read_bytes();info=unwrap(raw)[1];pkg=container.parse(unwrap(raw)[0]);sec=next(s for s in pkg['sections'] if s['id']==3)
original,ops=aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']]);image=bytearray(original)
BASE=0x40000400;m=json.loads((W/'probe/BUILD.json').read_text());module=(W/'probe/md.bin').read_bytes()
old_entry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');assert old_entry
from integrate_catalogue import apply
image=apply(image,m)
base_map=json.loads((R/'tools/machines/md/base-map.json').read_text())
for edit in base_map['title_edits']:
 at=edit['at']-BASE;old=bytes.fromhex(edit['old']);assert image[at:at+len(old)]==old;image[at:at+len(old)]=bytes.fromhex(edit['new'])
alignment=(-len(image))&3;loader=BASE+len(image)+alignment;src=loader+192;assert len(module)%4==0
sine_at=m['symbols']['trx_b2_sine'];sine_offset=sine_at-m['code']
assert sine_offset+32768*4<=len(module)
sines=struct.unpack('>32768i',module[sine_offset:sine_offset+32768*4]);deltas=[sines[0]]+[b-a for a,b in zip(sines,sines[1:])]
assert all(-32768<=x<32768 for x in deltas)
body=module[:sine_offset];suffix=module[sine_offset+32768*4:];delta_bytes=struct.pack('>32768h',*deltas);delta_src=src+len(body)+len(suffix)
copy_suffix=f''' adda.l #131072,%a1
 move.l #{len(suffix)//4},%d0
4: move.l (%a0)+,(%a1)+
 subq.l #1,%d0
 bne.s 4b
''' if suffix else ''
text=f'''.text
.globl md_load
md_load:
 lea -20(%sp),%sp
 movem.l %d0-%d2/%a0-%a1,(%sp)
 lea {src:#x},%a0
 lea {m['code']:#x},%a1
 move.l #{len(body)//4},%d0
1: move.l (%a0)+,(%a1)+
 subq.l #1,%d0
 bne.s 1b
{copy_suffix}
 lea {delta_src:#x},%a0
 lea {sine_at:#x},%a1
 move.l #32768,%d0
 moveq #0,%d1
3: move.w (%a0)+,%d2
 ext.l %d2
 add.l %d2,%d1
 move.l %d1,(%a1)+
 subq.l #1,%d0
 bne.s 3b
 lea {m['bss']:#x},%a0
 move.l #{m['bss_bytes']//4},%d0
2: clr.l (%a0)+
 subq.l #1,%d0
 bne.s 2b
 movem.l (%sp),%d0-%d2/%a0-%a1
 lea 20(%sp),%sp
 jmp {old_entry:#x}
'''
B=W/'probe';s=B/'load.S';s.write_text(text);cross=os.environ['M68K_CROSS'];os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
subprocess.run([cross+'gcc'+os.environ.get('MD_EXE',''),'-mcpu=54418','-c',str(s),'-o',str(B/'load.o')],check=True)
subprocess.run([cross+'ld'+os.environ.get('MD_EXE',''),'-e','md_load','-Ttext',hex(loader),'-o',str(B/'load.elf'),str(B/'load.o')],check=True)
subprocess.run([cross+'objcopy'+os.environ.get('MD_EXE',''),'-O','binary','-j','.text',str(B/'load.elf'),str(B/'load.bin')],check=True)
stub=(B/'load.bin').read_bytes();assert len(stub)<=192
struct.pack_into('>I',image,0x40195adc-BASE,loader)
image+=bytes(alignment)+stub+bytes(192-len(stub))+body+suffix+delta_bytes
official=Path(os.environ['MD_CYCLES'])
stockpkg=container.parse(unwrap(official.read_bytes())[0]);stocksec=next(s for s in stockpkg['sections'] if s['id']==3)
stock,stockops=aplib.depack(stockpkg['blob'][stocksec['off']:stocksec['off']+stocksec['size']]);start=0x401aa140-BASE;assert len(stock)==start
dirty=bytes(a!=b for a,b in zip(image[:start],stock))+b'\1'*(len(image)-start)
packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,start);packed,packing=pack(packed)
assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
plains=[]
for s in pkg['sections']:
 try:plains.append(aplib.depack(pkg['blob'][s['off']:s['off']+s['size']])[0])
 except Exception:pass
key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key
rebuilt=container.rebuild(pkg,{3:packed},key)
report=dict(source_sha256=hashlib.sha256(raw).hexdigest(),flash_bytes=len(rebuilt),flash_limit=0x1c0000,remaining_flash_bytes=0x1c0000-len(rebuilt),fits_flash=len(rebuilt)<=0x1c0000,loader=loader,source=src,code=m['code'],code_bytes=len(module),bss=m['bss'],bss_bytes=m['bss_bytes'],packing=packing,native_catalogue_installed=True,hardware_tested=False)
assert report['fits_flash'],report
syx=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq'])
(B/'SPARSE-BOOT-PROBE.syx').write_bytes(syx);report['sha256']=hashlib.sha256(syx).hexdigest()
(B/'SPARSE-BUDGET.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
