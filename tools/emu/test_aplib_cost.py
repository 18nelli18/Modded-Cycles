#!/usr/bin/env python3
"""Roundtrip du compresseur compatible, motifs courts/longs et octets aléatoires."""
import random,struct
import aplib_cost
from mtlib import aplib

def main():
 rng=random.Random(6165)
 fixtures=[b'',b'a',b'aaa',bytes(range(256))*20,b'\0'*40000,b'abcde'*9000]
 fixtures += [bytes(rng.randrange(256) for _ in range(n)) for n in (2,3,4,31,257,1024,9000)]
 for data in fixtures:
  for lazy in (False,True):
   packed=aplib_cost.pack(data,32,lazy);decoded,_=aplib.depack(struct.pack('>II',len(packed),sum(packed)&0xffffffff)+packed);assert decoded==data
 print('ok : roundtrip compatible, deux stratégies, motifs/runs/offsets longs/aléatoire/vides')
if __name__=='__main__':main()
