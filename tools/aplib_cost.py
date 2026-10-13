"""Prototype aPLib compatible : choisir les matchs selon leur coût en bits.

Recherche bornée, regard d'un octet, format et décompresseur inchangés.
Chaque flux est relu intégralement avant d'être proposé au générateur.
"""
import struct
from mtlib import aplib
import aplib_grow

def pack(data,depth=128,lazy=True):
 w=aplib._Writer();chains={};n=len(data);i=0;last=1
 def gamma(v):return 2*(v.bit_length()-1)
 def match(at,last):
  if at+3>n:return 0,0,0
  key=data[at:at+3];positions=list(reversed(chains.get(key,())))
  reuse=at-last
  if reuse>=0 and data[reuse:reuse+3]==key and reuse not in positions:positions.insert(0,reuse)
  best=(0,0,0)
  for pos in positions:
   off=at-pos
   if not 1<=off<=aplib_grow.WINDOW:continue
   length=3;limit=min(n-at,aplib_grow.MAX_MATCH)
   while length<limit and data[pos+length]==data[at+length]:length+=1
   base=length-1-int(off>aplib.FAR_THRESHOLD)
   bits=1+(gamma(aplib.REUSE_GAMMA) if off==last else gamma((off+aplib.OFFSET_BIAS)>>8)+8)+2+(gamma(base-2) if base>3 else 0)
   score=9*length-bits
   if score>best[0] or (score==best[0] and off==last):best=(score,off,length)
  return best
 while i<n:
  score,off,length=match(i,last)
  if lazy and length and i+1<n and match(i+1,last)[0]>score+9:score=0
  if score>0:w.match(off,length,last);last=off;count=length
  else:w.literal(data[i]);count=1
  for pos in range(i,min(i+count,n-2)):
   key=data[pos:pos+3];history=chains.setdefault(key,[]);history.append(pos)
   if len(history)>depth:del history[0]
  i+=count
 w.end();packed=bytes(w.o[aplib.SECT_HDR:]);restored,_=aplib.depack(struct.pack('>II',len(packed),sum(packed)&0xffffffff)+packed)
 assert bytes(restored)==bytes(data),'roundtrip aPLib coût incorrect'
 return packed
