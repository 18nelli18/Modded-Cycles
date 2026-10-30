"""Selection de trigs PPPCCC : TRACK + PAGE, conserve Genie, Page Len et slide.
Socles Direct Jump prives2.62 ; aucun changement du flasheur public. Note205.
"""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
import aplib_grow
from bootstrap205_assets import pack
from machines.trig_select import upstream as G
from machines.direct_jump import common
CODE=0x46924000;BSS=0x46930100;S=R/'tools/machines/trig_select'
PINS={'666ea8c01dba471bb12dccd47788a11db9d99ef40dbac7133ab25e03a2cf0181','9c8014519712c07ccae2de8a17c4bc79107460eeb6b5cd43b00ea85032c6c206','5853c22e4227ac5dc44971ebcf73c469c2cd52b91b80b939e0dfd5a6a9861d58','6e76e2a9128621bcd7051a85e4f5730adef8fd12d7dfae1e2b564509bfc2e06c','df8339eb91fa9fc56893961cd87f04b43f3098f80cc22848a7e05002d5527024'}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('source','metadata','cycles','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--cross',default='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');p.add_argument('--check',action='store_true');a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
 raw=a.source.read_bytes();m=json.loads(a.metadata.read_text());assert sha(raw) in PINS and m['sha256']==sha(raw)
 assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
 _,_,stock,stockops=read(a.cycles);common.IMAGE=stock;info,pkg,image,_=read(a.source);image=bytearray(image)
 assert m['direct_jump']['code']+m['direct_jump']['code_bytes']<=CODE and m['direct_jump']['bss_end']<=BSS
 O=a.output;O.mkdir(parents=True,exist_ok=True);cross=a.cross;exe='.exe' if os.name=='nt' else '';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*v):return subprocess.check_output([cross+tool+exe,*map(str,v)],text=True)
 aliases={**m['direct_jump']['aliases'],**m['direct_jump']['symbols'],**m['page_length']['symbols'], 'ts_on':BSS}
 aliases['ts_old_led']=int.from_bytes(image[0x40021f58-BASE:0x40021f5c-BASE],'big');assert image[0x40021f56-BASE:0x40021f60-BASE]==b'\x4e\xb9'+struct.pack('>I',aliases['ts_old_led'])+b'\x4e\x71'*2
 G.M_A=CODE;G.M_S=CODE+0x400;G.TS_ON=BSS
 # Le port conserve les seuls noyaux de selection. Les modifications Absolute
 # du patch Control Mode ne changent pas le comportement relatif de Supermodel.
 G.HAS=(CODE+0x1000,CODE+0x1006,CODE+0x100c)
 texts={};b=bytearray()
 for k,text in G.TXT.items():texts[k]=CODE+0xc00+len(b);b+=text.encode()+b'\0'
 cs,ls=G.build_s(texts);ca,la=G.build_a(texts,CODE+0x1012,CODE+0x1018,ls)
 core=''
 for name,at,data in [('keys',CODE,ca),('selection',CODE+0x400,cs),('strings',CODE+0xc00,b)]:
  assert len(data)<=0x400;core+=f'.section .{name},"ax"\n.byte '+','.join(map(str,data))+'\n'
 (O/'cores.S').write_text(core)
 entries='''.section .entries,"ax"
 jmp ts_has_note
 jmp ts_has_lock
 jmp ts_has_plock
 jmp ts_popup
 jmp ts_gest
.section .text
.globl ts_func_page
ts_func_page:
 movea.l (%sp)+,%a0
 move.l %d3,-(%sp)
 move.l %a0,-(%sp)
 move.l ts_on,%d0
 cmpi.l #0x5453454c,%d0
 beq 1f
 jmp 0x40072490
1: moveq #0,%d0
 rts
''';(O/'entries.S').write_text(entries);objs=[]
 for src in (O/'cores.S',O/'entries.S',S/'control.c',S/'bridge.S'):
  obj=O/(src.stem+'.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv','-Wall','-Wextra','-Werror','-c',src,'-o',obj);objs.append(obj)
 ld='SECTIONS { '+f'.keys {CODE:#x} : {{ *(.keys) }} .selection {CODE+0x400:#x} : {{ *(.selection) }} .strings {CODE+0xc00:#x} : {{ *(.strings) }} .entries {CODE+0x1000:#x} : {{ *(.entries) }} .text {CODE+0x1100:#x} : {{ *(.text*) *(.rodata*) *(.data*) }} .bss {BSS+32:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) ts_bss_end = .; }} }}\n'+''.join(f'PROVIDE({k}={v:#x});\n' for k,v in aliases.items())
 ld=ld.replace('=',' = ');(O/'trig.ld').write_text(ld);run('ld','-T',O/'trig.ld','-e','ts_led','-o',O/'trig.elf',*objs);run('objcopy','-O','binary',O/'trig.elf',O/'trig.bin');sy={v[2]:int(v[0],16) for line in run('nm',O/'trig.elf').splitlines() if len(v:=line.split())==3}
 blob=(O/'trig.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<0x46930000 and sy['ts_bss_end']<0x46940000
 edits=[]
 def put(at,old,new):
  assert bytes(image[at-BASE:at-BASE+len(old)])==old,hex(at);assert len(old)==len(new);image[at-BASE:at-BASE+len(new)]=new;edits.append(dict(at=at,old=old.hex(),new=new.hex()))
 put(G.GRID_VT,struct.pack('>I',G.GRID_KEY),struct.pack('>I',la['TSK']))
 n,h=G.TSF_ORIG;orig=stock[G.TSF_HOOK-BASE:G.TSF_HOOK-BASE+n];assert sha(orig)==h;put(G.TSF_HOOK,orig,b'\x4e\xb9'+struct.pack('>I',sy['ts_func_page'])+b'\x4e\x71')
 at=G.TSL_HOOK;put(at,bytes(image[at-BASE:at-BASE+10]),b'\x4e\xb9'+struct.pack('>I',sy['ts_led'])+b'\x4e\x71'*2)
 oldentry=int.from_bytes(image[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(image))&3;loader=BASE+len(image)+pad;src=loader+128
 load=f'''.text
.globl ts_load
ts_load:
 lea -12(%sp),%sp
 movem.l %d0/%a0-%a1,(%sp)
 lea {src:#x},%a0
 lea {CODE:#x},%a1
 move.l #{len(blob)//4},%d0
1: move.l (%a0)+,(%a1)+
 subq.l #1,%d0
 bne.s 1b
 lea {BSS:#x},%a0
 move.l #{(sy['ts_bss_end']-BSS+3)//4},%d0
2: clr.l (%a0)+
 subq.l #1,%d0
 bne.s 2b
 movem.l (%sp),%d0/%a0-%a1
 lea 12(%sp),%sp
 jmp {oldentry:#x}
'''
 (O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','ts_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=128
 struct.pack_into('>I',image,0x40195adc-BASE,loader);image+=bytes(pad)+stub+bytes(128-len(stub))+blob
 dirty=bytes(x!=y for x,y in zip(image[:START],stock))+b'\1'*(len(image)-START);packed=aplib_grow.repack_grow(bytes(image),stockops,dirty,START);packed,packing=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==image
 plains=[]
 for s in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000;raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.62_Direct_Jump_Trig_Select_Experimental.syx'
 if a.check:assert target.read_bytes()==raw
 else:target.write_bytes(raw)
 proof=dict(upstream='gialloinfuso/PPPCCC-M-S-Mods',revision='43b894bd14f55313cef6381af9a008acec3ed0f1',credit='PPPCCC/gialloinfuso',license='MIT',code=CODE,code_bytes=len(blob),bss=BSS,bss_end=sy['ts_bss_end'],symbols=sy,core_symbols={**ls,**la},default='OFF after boot',toggle='TRACK + PAGE',all_none='FUNC + PAGE while in selection mode',relative_editing_preserved=True,selected_LED_blink_hz=4,old_slide_LED_helper=aliases['ts_old_led'],hooks=edits,flash_bytes=len(rebuilt),margin=0x1c0000-len(rebuilt),hardware_tested=False,source_sha256=m['sha256'])
 m.update(sha256=sha(raw),main_os_sha256=sha(image),trig_select=proof,hardware_tested=False);(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS Trig Select build',sha(raw),'flash',len(rebuilt),'margin',proof['margin'],flush=True)
if __name__=='__main__':main()
