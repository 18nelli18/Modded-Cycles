"""PM natif : deux invariants en registres et boucle deroulee quatre fois.

D5 est constant avant/apres le noyau; A2 est recharge apres celui-ci.
Les produits, interpolations et avancees de phase restent dans le meme ordre.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
BASE=0x40000400;SITE=0x400a8bb6;END=0x400a8c00;CODE=0x467a6200

def apply(meta,native,runtime,stock,out,sram=None):
 assert meta.get('native_finish') and not meta.get('phase_loop')
 body=bytes(stock[SITE-BASE:END-BASE]);assert native[SITE-BASE:END-BASE]==body
 assert native[END-BASE:END-BASE+6]==bytes.fromhex('53806600ffb2')
 assert stock[SITE-BASE-24:SITE-BASE-18]==bytes.fromhex('2a3c6487ed51')
 assert not any(runtime[CODE-0x46700000:CODE-0x46700000+512])
 assert any(x['kind']=='remove' and x['address']<=CODE and CODE+512<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 a=bytes.fromhex('d3ef0048');b=bytes.fromhex('deaf0054');assert body.count(a)==body.count(b)==1
 first,rest=body.split(a);middle,last=rest.split(b);assert not first
 raw=lambda v:'.byte '+','.join(map(str,v))+'\n'
 pairs=2 if sram is not None else 4
 code=CODE
 low_edit=None
 if sram is not None:
  low=next(x for x in meta['sram_audio']['modules'] if x['name']=='low');lo=low['at'];old_low=bytes(sram[lo-0x80000000:lo-0x80000000+low['bytes']]);assert len(old_low)==556 and hashlib.sha256(old_low).hexdigest()==low['sha256']
  assert old_low[20:548]==old_low[20:152]*4
  code=lo+292
 source='.text\n.globl entry\nentry:\n move.l 72(%sp),%d5\n movea.l 84(%sp),%a2\n moveq #'+str(32//pairs)+',%d0\nloop:\n.rept '+str(pairs)+'\n adda.l %d5,%a1\n'+raw(middle)+' add.l %a2,%d7\n'+raw(last)+'.endr\n subq.l #1,%d0\n bne.w loop\n move.l #0x6487ed51,%d5\n tst.l %d0\n jmp 0x400a8c06\n'
 out=Path(out);out.mkdir(parents=True,exist_ok=True);(out/'phase-loop.S').write_text(source)
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def run(tool,*args):subprocess.check_call([cross+tool+'.exe',*map(str,args)])
 run('gcc','-mcpu=54418','-c',out/'phase-loop.S','-o',out/'phase-loop.o');run('ld','-Ttext',hex(code),'-e','entry','-o',out/'phase-loop.elf',out/'phase-loop.o');run('objcopy','-O','binary',out/'phase-loop.elf',out/'phase-loop.bin')
 blob=(out/'phase-loop.bin').read_bytes();assert len(blob)<=512
 if sram is not None:
  low_source='.text\n.globl entry\nentry:\n'+raw(old_low[:20])+'loop:\n.rept 2\n'+raw(old_low[20:152])+'.endr\n cmpa.l %a2,%a1\n bne.w loop\n jmp (%a5)\n'
  (out/'phase-low.S').write_text(low_source);run('gcc','-mcpu=54418','-c',out/'phase-low.S','-o',out/'phase-low.o');run('ld','-Ttext',hex(lo),'-e','entry','-o',out/'phase-low.elf',out/'phase-low.o');run('objcopy','-O','binary',out/'phase-low.elf',out/'phase-low.bin')
  compact=(out/'phase-low.bin').read_bytes();assert len(compact)==292 and len(compact)+len(blob)<=556
  replacement=(compact+blob).ljust(556,b'\0');sram[lo-0x80000000:lo-0x80000000+556]=replacement
  low_edit=dict(at=lo,old=old_low.hex(),new=replacement.hex());low.update(bytes=292,sha256=hashlib.sha256(compact).hexdigest());meta['sram_audio']['filter_pairs_per_iteration']=2
  meta['sram_audio']['modules'].append(dict(name='phase_loop',at=code,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),symbols={'entry':code}))
 old=bytes(native[SITE-BASE:SITE-BASE+6]);new=b'\x4e\xf9'+struct.pack('>I',code)
 native[SITE-BASE:SITE-BASE+6]=new
 if sram is None:runtime[CODE-0x46700000:CODE-0x46700000+len(blob)]=blob
 return dict(code=code,in_SRAM=sram is not None,low_edit=low_edit,code_bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),patches=[dict(at=SITE,old=old.hex(),new=new.hex())],new_state_bytes=0,stack_reads_removed_per_call=62,hardware_tested=False)
