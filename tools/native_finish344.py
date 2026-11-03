"""Derouler gain et demi-niveau sans changer leur ordre ni le detecteur de queue.

Gain quatre samples en DDR; demi-niveau quatre samples dans les40octets
SRAM libres. Aucun etat ajoute, aucune modification des seuils du gouverneur.
"""
from pathlib import Path
import hashlib,os,struct,subprocess
BASE=0x40000400;AMP=0x400a9478;HALF=0x400a7e2a;CODE=0x46798700

def apply(meta,native,runtime,sram,stock,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert meta.get('voice_filter_unroll') and not meta.get('gain_fusion')
 assert not any(runtime[CODE-0x46700000:CODE-0x46700000+256])
 assert any(x['kind']=='remove' and x['address']<=CODE and CODE+256<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
 body=bytes(stock[AMP-BASE:AMP-BASE+14]);half=bytes(native[HALF-BASE:HALF-BASE+14])
 assert native[AMP-BASE:AMP-BASE+14]==body and body[-2:]==bytes.fromhex('24c2')
 assert half.hex()=='41e900802211e28122c1b3c866f6'
 layout=meta['sram_audio'];fast=(max(x['at']+x['bytes'] for x in layout['modules'])+3)&~3
 cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
 def raw(b):return '.byte '+','.join(map(str,b))+'\n'
 def assemble(name,source,at):
  (out/(name+'.S')).write_text(source)
  def run(tool,*args):subprocess.check_call([cross+tool+'.exe',*map(str,args)])
  run('gcc','-mcpu=54418','-c',out/(name+'.S'),'-o',out/(name+'.o'));run('ld','-Ttext',hex(at),'-e','entry','-o',out/(name+'.elf'),out/(name+'.o'));run('objcopy','-O','binary',out/(name+'.elf'),out/(name+'.bin'))
  return (out/(name+'.bin')).read_bytes()
 gain=assemble('finish-gain','.text\n.globl entry\nentry:\n moveq #8,%d0\nloop:\n.rept 4\n'+raw(body)+'.endr\n subq.l #1,%d0\n bne.w loop\n jmp 0x400a948a\n',CODE)
 halve=assemble('finish-half','.text\n.globl entry\nentry:\n'+raw(half[:4])+'loop:\n.rept 4\n'+raw(half[4:10])+'.endr\n cmpa.l %a0,%a1\n bne.w loop\n jmp 0x400a7e38\n',fast)
 assert len(halve)==40 and fast+len(halve)<=0x800062b4
 assert not any(sram[fast-0x80000000:fast-0x80000000+len(halve)])
 patches=[]
 for at,old,target in [(AMP,body[:6],CODE),(HALF,half,fast)]:
  new=b'\x4e\xf9'+struct.pack('>I',target)+b'\x4e\x71'*((len(old)-6)//2)
  native[at-BASE:at-BASE+len(old)]=new;patches.append(dict(at=at,old=old.hex(),new=new.hex()))
 runtime[CODE-0x46700000:CODE-0x46700000+len(gain)]=gain;sram[fast-0x80000000:fast-0x80000000+len(halve)]=halve
 module=dict(name='finish_half',at=fast,bytes=len(halve),sha256=hashlib.sha256(halve).hexdigest(),symbols={'entry':fast})
 layout['modules'].append(module);layout['patches'].extend(patches);layout['SRAM_used']=fast+len(halve)-0x80005268
 return dict(code=CODE,code_bytes=len(gain),sha256=hashlib.sha256(gain).hexdigest(),fast=fast,fast_bytes=len(halve),patches=patches,new_state_bytes=0,gain_instructions_saved=45,half_instructions_saved=46,hardware_tested=False)
