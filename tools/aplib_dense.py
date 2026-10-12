"""Compresseur aPLib compatible : recherche bornée de plusieurs antécédents.

Réservé aux prototypes à forte contrainte d'image ; aucun changement du
format ou du décompresseur embarqué. Choisit le plus petit flux vérifié.
"""
import struct
from mtlib import aplib
import aplib_grow

def pack(data,depth=32):
    writer=aplib._Writer();chains={};i=0;last=1;n=len(data)
    while i<n:
        best=0;offset=0
        if i+3<=n:
            key=data[i:i+3]
            candidates=list(reversed(chains.get(key,())))
            reuse=i-last
            if reuse>=0 and data[reuse:reuse+3]==key and reuse not in candidates:
                candidates.insert(0,reuse)
            for pos in candidates:
                off=i-pos
                if off<1 or off>aplib_grow.WINDOW:continue
                length=3;limit=min(n-i,aplib_grow.MAX_MATCH)
                while length<limit and data[pos+length]==data[i+length]:length+=1
                if length>best or (length==best and off==last):best,offset=length,off
        count=best if best>=3 else 1
        if best>=3:writer.match(offset,best,last);last=offset
        else:writer.literal(data[i])
        for pos in range(i,min(i+count,n-2)):
            key=data[pos:pos+3];history=chains.setdefault(key,[])
            history.append(pos)
            if len(history)>depth:del history[0]
        i+=count
    writer.end()
    dense=bytes(writer.o[aplib.SECT_HDR:]);baseline=aplib_grow.pack(data)
    result=min((baseline,dense),key=len)
    restored,_=aplib.depack(struct.pack('>II',len(result),sum(result)&0xffffffff)+result)
    assert bytes(restored)==bytes(data),'roundtrip aPLib dense incorrect'
    return result
