#!/usr/bin/env python3
"""Réserve sept blocs : vraie initialisation native des listes cache OS1.13.

Ne prouve pas la performance disque ni les opérations de stockage complètes.
"""
import argparse,struct
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
 stock=main_os_from_syx(a.cycles)
 for reserved in (0,6,7):
  r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}})
  base=0x401eb750;r.u.mem_write(base,bytes(0x160))
  r.w32(0x400792f2,base+20*reserved)
  r.w32(0x400792bc,base+20*(reserved+1)+16)
  protected=0x401ab750;end=protected+reserved*16384
  if reserved:r.u.mem_write(protected,b'\xa5'*(end-protected))
  r.call(0x4007929c)
  head=r.r32(0x401eb894);tail=r.r32(0x401eb890)
  assert head==base+20*reserved and tail==base+20*15
  nodes=[];node=head;previous=0
  while node:
   assert node not in nodes and base<=node<base+320
   assert (node-base)%20==0 and r.r32(node+16)==previous
   nodes.append(node);previous=node;node=r.r32(node+12)
  assert nodes==[base+20*i for i in range(reserved,16)]
  assert previous==tail
  for i in range(reserved):assert r.r32(base+20*i+8)==0
  if reserved:assert bytes(r.u.mem_read(protected,end-protected))==b'\xa5'*(end-protected)
  print('ok : réserve',reserved,'blocs ; liste native',len(nodes),'blocs ; avant/arrière cohérents ; code préservé')
if __name__=='__main__':main()
