"""aPLib205 : decouper les matches et consommer des litteraux pour proteger
l'entree du bootstrap en place. Le MAIN decode reste strictement identique.
"""
from mtlib import aplib

def pack(section,gap=0x1ffc00):
 data,ops=aplib.depack(section);w=aplib._Writer();last=1;literals=0;splits=0
 for kind,pos,off,n in ops:
  if kind==aplib.LITERAL:w.literal(data[pos]);continue
  remaining=n
  while remaining:
   margin=gap+len(w.o)-pos-64
   chunk=min(remaining,margin)
   if chunk>=4:
    w.match(off,chunk,last);last=off;pos+=chunk;remaining-=chunk;splits+=remaining>0
   else:
    count=min(remaining,512)
    for i in range(count):w.literal(data[pos+i])
    pos+=count;remaining-=count;literals+=count
 w.end();w.o[:4]=(len(w.o)-8).to_bytes(4,'big');w.o[4:8]=(sum(w.o[8:])&0xffffffff).to_bytes(4,'big');out=bytes(w.o)
 assert aplib.depack(out)[0]==data
 return out,dict(original_bytes=len(section),stored_bytes=len(out),bootstrap_gap=gap,margin=64,added_literal_bytes=literals,split_matches=splits,main_unchanged=True)
