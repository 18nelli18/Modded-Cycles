"""Extraire Feral du .syx utilisateur epingle, jamais de binaire dans les sources.
Replacer seulement le moteur et ses constantes/etats ; pas les hooks OS Feral.
"""
import hashlib,struct
from pathlib import Path
SHA='990d93714c19721bdc7afcb1dcb029a76a7718c3859da72d8dafff828e15d6ac'
CODE=0x467d0000;AUX=0x467e4000
RANGES=[(0x43000000,0x4301394c,CODE),(0x43033000,0x43036ed4,AUX)]

def address(value):
 for lo,hi,dst in RANGES:
  if lo<=value<hi:return dst+value-lo
 return value

def native_image(root):
 from mtlib import aplib,container
 from mtlib.syx import unwrap
 source=root/'firmware/model-cycles_OS1.13_feral.syx'
 assert hashlib.sha256(source.read_bytes()).hexdigest()==SHA
 pkg=container.parse(unwrap(source.read_bytes())[0]);sec=next(s for s in pkg['sections'] if s['id']==3)
 im=aplib.depack(pkg['blob'][sec['off']:sec['off']+sec['size']])[0];rt=bytearray(0x40000);off=0x1a9d40
 for i in range(12):
  at,words=struct.unpack_from('>II',im,0x4016cb28-0x40000400+8*i)
  if not words:break
  rt[at-0x43000000:at-0x43000000+words*4]=im[off:off+words*4];off+=words*4
 assert off==len(im)
 return im,bytes(rt)

def prepare(root,build):
 im,rt=native_image(root)
 blob=bytearray(AUX+0x3ed4-CODE);relocs=[]
 for lo,hi,dst in RANGES:
  raw=rt[lo-0x43000000:hi-0x43000000];base=dst-CODE;blob[base:base+len(raw)]=raw
  for i in range(0,len(raw)-3,2):
   old=struct.unpack_from('>I',raw,i)[0];new=address(old)
   if new!=old:struct.pack_into('>I',blob,base+i,new);relocs.append((hex(lo+i),hex(old),hex(new)))
 assert CODE+len(blob)<0x46800000
 (build/'feral-code.bin').write_bytes(blob[:0x1394c])
 return bytes(blob),dict(source_sha256=SHA,code=CODE,code_bytes=0x1394c,aux=AUX,end=CODE+len(blob),update=CODE,render=CODE+0x2ba,state=address(0x43036000),global_model=address(0x43036ed0),name=address(0x43033878),relocations=relocs,ranges=RANGES,models=10)
