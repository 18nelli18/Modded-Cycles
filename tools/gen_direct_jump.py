"""Port prive PPPCCC Direct Jump dans Global, sur les quatre socles2.61 epingles.
Les instructions natives sont extraites de l'OS officiel ; aucune image publiee.
Note204. --check reconstruit et compare le resultat local.
"""
from pathlib import Path
import argparse,hashlib,json,os,struct,subprocess,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from gen_governor_recovery_test import read,BASE,START,RUNTIME,TAIL
from mtlib import aplib,container
from mtlib.syx import wrap,BYTES_PER_MSG
import aplib_grow
from bootstrap205_assets import pack
from machines.direct_jump import upstream as G,common
S=R/'tools/machines/direct_jump';CODE=0x46920000;BSS=0x46930000
PINS={'2eb4b07f45ee24b7d9f198b09094db358b1d995fa8111b80daf6e114f9fac5c6','7f000ba151c24b77e40d92fa8a640910e375ffd4eee2064f677eeb7697012c51','ff8eddcd16d6dcc30111d2064a905eb7c142818d52f27d653696636fefe607c0','6cde04f1ab8bb202799c3e96b7170fac47cc90707020ff356585eba80773d692'}
PINS.add('c803ffb0fec8e13cc437a5cb16a46266adcc54ada2bff8fb3f5622ee0ad1c4a6')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('source','metadata','cycles','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--cross',default='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');p.add_argument('--check',action='store_true');a=p.parse_args()
 sha=lambda b:hashlib.sha256(b).hexdigest();raw=a.source.read_bytes();assert sha(raw) in PINS
 m=json.loads(a.metadata.read_text());assert m['sha256']==sha(raw)
 assert sha(a.cycles.read_bytes())=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c'
 _,_,stock,stockops=read(a.cycles);common.IMAGE=stock
 info,pkg,image,ops=read(a.source);prefix=bytearray(image[:START]);oldend=int.from_bytes(prefix[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 compressed=image[START:oldend];rt,rtops=aplib.depack(struct.pack('>II',len(compressed),sum(compressed)&0xffffffff)+compressed);rt=bytearray(rt);tail=bytearray(image[oldend:]);originalrt=bytes(rt)
 native_tail=int.from_bytes(prefix[0x40195ad8-BASE:0x40195adc-BASE],'big')
 assert TAIL+native_tail<=CODE
 edits=[]
 def area(at):return (prefix,BASE) if at<RUNTIME else (rt,RUNTIME) if at<TAIL else (tail,TAIL)
 def patch(at,old,new):
  buf,base=area(at);assert bytes(buf[at-base:at-base+len(old)])==old,hex(at);assert len(old)==len(new);buf[at-base:at-base+len(old)]=new;edits.append(dict(at=at,old=old.hex(),new=new.hex()))
 aliases={}
 for k in ('symbols','capture_symbols','persist_symbols'):aliases.update(m.get(k,{}))
 for k in ('fx_menu','groove_strum','fx_project','lfo_reload','sidechain','mute_quant'):aliases.update(m[k].get('aliases',{}));aliases.update(m[k].get('symbols',{}))
 aliases.update(m['per_track_fx']['symbols']);aliases={k:v for k,v in aliases.items() if isinstance(v,int) and k.replace('_','').isalnum()}
 full='ae_mode' in m['per_track_fx']['symbols'];row=11 if full else 10
 aliases.update(jp_enabled=BSS,jp_request=CODE,jp_fix=CODE+4,jp_keep=CODE+14,jp_old_edit=aliases['ae_global_edit' if full else 'mf_tree_edit'])
 for kind in ('key','encoder','draw'):aliases['jp_old_'+kind]=aliases[('ae_' if full else 'mf_gc_')+kind]
 aliases['jp_old_frame']=aliases['ae_frame' if full else 'mf_frame']
 O=a.output;O.mkdir(parents=True,exist_ok=True);cross=a.cross;exe='.exe' if os.name=='nt' else '';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*v):return subprocess.check_output([cross+tool+exe,*map(str,v)],text=True)
 G.M_J1=CODE;G.M_J2=CODE+512;G.M_J3=CODE+1024;G.M_J4=CODE+1536;G.REQ=CODE;G.FIX=CODE+4;G.SAVE=CODE+8;G.KEEP=CODE+14
 parts,lab=G.build();core=''
 for at,b in parts.items():core+=f'.section .core{at-CODE},"ax"\n.balign 4\n'+'.byte '+','.join(map(str,b))+'\n'
 (O/'cores.S').write_text(core)
 hooks=[('DJK',G.K_HOOK,G.K_CK),('DJS',G.S_HOOK,G.S_CK),('DJF',G.F_HOOK,G.F_CK),('FK',G.FK_HOOK,G.FK_CK),('FO',G.FO_HOOK,G.FO_CK),('OT',G.OT_HOOK,G.OT_CK),('RL',G.RL_HOOK,G.RL_CK)]
 gates='.text\n'
 for name,at,(n,h) in hooks:
  orig=stock[at-BASE:at-BASE+n];assert sha(orig)==h
  # MOVEM et LEA ne changent pas CCR : chemin OFF strictement natif.
  restore=' move.l 8(%sp),%d0\n move.w %d0,%ccr\n movem.l (%sp),%d0-%d1\n lea 12(%sp),%sp\n'
  gates+=f'.globl jp_{name}\njp_{name}:\n lea -12(%sp),%sp\n movem.l %d0-%d1,(%sp)\n move.w %sr,%d0\n move.l %d0,8(%sp)\n tst.l jp_enabled\n beq .Loff_{name}\n'+restore+f' jmp {lab[name]:#x}\n.Loff_{name}:\n'+restore
  if name=='RL':gates+='.byte '+','.join(map(str,orig[:4]))+f'\n bne .Lrl_skip\n jmp {G.RL_OFF:#x}\n.Lrl_skip: jmp {G.RL_SKIP:#x}\n'
  else:gates+='.byte '+','.join(map(str,orig))+f'\n jmp {at+n:#x}\n'
 (O/'gates.S').write_text(gates)
 view=(S/'global.S').read_text().replace('mf_global_draw','jp_global_draw').replace('ae_global_edit','jp_edit')
 if not full:
  view=view.replace('    clrb %a0@(920)\n','').replace('.Lacid_label: .asciz "ACID"\n','').replace('.long 0,0,0,.Lacid_label,0,1,.Lts_label,0,0,0,0,0,0,1,ae_value,0,0,0,0,0,0\n','')
 view=view.replace('moveq #11,%d0',f'moveq #{row+1},%d0').replace('    jsr gc_tree_row',f'    clrb %a0@({80+84*row})\n    jsr gc_tree_row',1).replace('.Lallocator: .byte 0','.Ljump_label: .asciz "JUMP"\n.Lallocator: .byte 0')
 view+='\n.long 0,0,0,.Ljump_label,0,1,.Lts_label,0,0,0,0,0,0,1,jp_value,0,0,0,0,0,0\n';(O/'global.S').write_text(view)
 objs=[]
 for src in (O/'cores.S',O/'gates.S',O/'global.S',S/'control.c'):
  obj=O/(src.stem+'.o');run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-fwrapv',f'-DJP_ROW={row}','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj);objs.append(obj)
 ld='SECTIONS { '+''.join(f'.core{at-CODE} {at:#x} : {{ *(.core{at-CODE}) }} ' for at in parts)+f'.text {CODE+4096:#x} : {{ *(.text*) *(.rodata*) *(.data*) }} .bss {BSS+64:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) jp_bss_end = .; }} }}\n'+''.join(f'PROVIDE({k} = {v:#x});\n' for k,v in aliases.items())
 (O/'jump.ld').write_text(ld);run('ld','-T',O/'jump.ld','-e','jp_frame','-o',O/'jump.elf',*objs);run('objcopy','-O','binary',O/'jump.elf',O/'jump.bin')
 sy={v[2]:int(v[0],16) for line in run('nm',O/'jump.elf').splitlines() if len(v:=line.split())==3};blob=(O/'jump.bin').read_bytes();blob+=bytes((-len(blob))&3);assert CODE+len(blob)<=BSS and sy['jp_bss_end']<0x46940000
 for name,at,(n,h) in hooks:patch(at,stock[at-BASE:at-BASE+n],b'\x4e\xf9'+struct.pack('>I',sy['jp_'+name])+b'\x4e\x71'*((n-6)//2))
 for kind,target in [('key','jp_key'),('encoder','jp_encoder'),('draw','jp_draw')]:
  at=m['groove_strum']['symbols']['gc_'+kind];buf,base=area(at);old=bytes(buf[at-base:at-base+6]);assert old==b'\x4e\xf9'+struct.pack('>I',aliases['jp_old_'+kind]);patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy[target]))
 at=m['lfo_reload']['symbols']['xp_frame'];buf,base=area(at);old=bytes(buf[at-base:at-base+6]);assert old==b'\x4e\xf9'+struct.pack('>I',aliases['jp_old_frame']);patch(at,old,b'\x4e\xf9'+struct.pack('>I',sy['jp_frame']))
 # Le titre experimental suit la meme version2.62 que les moteurs MD locaux.
 from title204_assets import apply
 title=apply(Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo'),O,prefix,lambda at,old,new,buf:patch(at,old,new), '2.62',lite=not full,previous=m['title_screen'])
 packed=aplib.repack(bytes(rt),rtops,bytes(x!=y for x,y in zip(rt,originalrt)))
 # Un chargeur sparse deja present garde ses adresses absolues.
 if len(tail)>native_tail:assert START+len(packed)-8==oldend
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(packed)-8)
 main=prefix+packed[8:]+tail;oldentry=int.from_bytes(main[0x40195adc-BASE:0x40195ae0-BASE],'big');pad=(-len(main))&3;loader=BASE+len(main)+pad;src=loader+128
 load=f'''.text
.globl jp_load
jp_load:
 lea -12(%sp),%sp
 movem.l %d0/%a0-%a1,(%sp)
 lea {src:#x},%a0
 lea {CODE:#x},%a1
 move.l #{len(blob)//4},%d0
1: move.l (%a0)+,(%a1)+
 subq.l #1,%d0
 bne.s 1b
 lea {BSS:#x},%a0
 move.l #{(sy['jp_bss_end']-BSS+3)//4},%d0
2: clr.l (%a0)+
 subq.l #1,%d0
 bne.s 2b
 movem.l (%sp),%d0/%a0-%a1
 lea 12(%sp),%sp
 jmp {oldentry:#x}
'''
 (O/'load.S').write_text(load);run('gcc','-mcpu=54418','-c',O/'load.S','-o',O/'load.o');run('ld','-Ttext',hex(loader),'-e','jp_load','-o',O/'load.elf',O/'load.o');run('objcopy','-O','binary',O/'load.elf',O/'load.bin');stub=(O/'load.bin').read_bytes();assert len(stub)<=128
 struct.pack_into('>I',main,0x40195adc-BASE,loader);main+=bytes(pad)+stub+bytes(128-len(stub))+blob
 dirty=bytes(x!=y for x,y in zip(main[:START],stock))+b'\1'*(len(main)-START);packed=aplib_grow.repack_grow(bytes(main),stockops,dirty,START);packed,packing=pack(packed);assert aplib.depack(packed,bootstrap_gap=0x1ffc00)[0]==main
 plains=[]
 for s in pkg['sections']:
  try:plains.append(aplib.depack(pkg['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,pkg['blob'][:-32],pkg['blob'][-32:]);assert key;rebuilt=container.rebuild(pkg,{3:packed},key);assert len(rebuilt)<=0x1c0000
 result=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),info['product'],info['start_seq']);target=O/'Supermodel_2.62_Direct_Jump_Experimental.syx'
 if a.check:assert target.read_bytes()==result
 else:target.write_bytes(result)
 proof=dict(upstream='gialloinfuso/PPPCCC-M-S-Mods',revision='43b894bd14f55313cef6381af9a008acec3ed0f1',license='MIT',credit='PPPCCC/gialloinfuso',hardware_tested=False,code=CODE,code_bytes=len(blob),bss=BSS,bss_end=sy['jp_bss_end'],symbols=sy,aliases=aliases,core_symbols=lab,global_row=row,global_rows=row+1,default='OFF',storage='/DirectJump.cfg',hooks=edits,loader=loader,flash_bytes=len(rebuilt),margin=0x1c0000-len(rebuilt),source_sha256=sha(raw))
 m.update(sha256=sha(result),main_os_sha256=sha(main),release='2.62',title_screen=title,direct_jump=proof,hardware_tested=False);(O/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('PASS Direct Jump build',sha(result),'flash',len(rebuilt),'margin',proof['margin'],flush=True)
if __name__=='__main__':main()
