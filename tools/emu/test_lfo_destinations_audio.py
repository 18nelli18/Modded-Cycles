"""Note121 : deux vrais moteurs LFO, cibles 23..25, sorties et cout identiques avant/apres.
Execution sous Linux avec binutils m68k et Unicorn ; aucun fichier audio distribue.
"""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_tempo_max import Rig,LFO,LFO_PHASE,OBJ,lfo_params
from unicorn import UC_HOOK_CODE

def main():
 p=argparse.ArgumentParser();p.add_argument('--prefix',default='build/lfo-destinations/0');a=p.parse_args();results=[]
 for suffix in ('before','after'):
  img,mem,ts=boot_case(a.prefix+'-'+suffix);r=Rig(img[:0x41000000-0x40000400]);u=r.uc
  for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
  for at,raw in mem:u.mem_write(at,raw)
  sy={k:int(v,16) for t in ts for k,v in t.get('symbols',{}).items()};second=0x93010000;other=0x93011000;out=0x93012000;baseptr=0x93013000;seen=set();answer=[];counter=[0]
  u.hook_add(UC_HOOK_CODE,lambda *args:counter.__setitem__(0,counter[0]+1));r.emac.macsr=0x20
  for dest1,dest2 in ((23,23),(24,24),(25,25),(23,24),(24,25),(25,23)):
   u.mem_write(LFO_PHASE,bytes(192));u.mem_write(second,bytes(192));case=[]
   for tick in range(24):
    frames=[]
    for dest,speed in ((dest1,22000),(dest2,24000)):
     frame=bytearray(lfo_params([speed]*6,[9]*6)).ljust(476,b'\0')
     for track in range(6):
      struct.pack_into('>H',frame,track*66+30,28000);frame[track*66+22]=dest
      for k in (23,24,25):struct.pack_into('>H',frame,track*66+14+2*k,16384)
     frames.append(bytes(frame))
    u.mem_write(OBJ,frames[0]);u.mem_write(other,frames[1]);u.mem_write(baseptr,frames[0]);r.call(LFO,OBJ,14400,0);r.call(sy['lf2_update'],other,14400,0,second);r.call(sy['lf2_mix'],out,baseptr,238,LFO_PHASE,second)
    blob=bytes(u.mem_read(out,476));case.append(blob+bytes(u.mem_read(LFO_PHASE,192))+bytes(u.mem_read(second,192)))
    values=tuple(struct.unpack_from('>H',blob,track*66+14+2*k)[0] for track in range(6) for k in (23,24,25));assert all(0<=x<=32512 for x in values);seen.add(values)
   answer.append(case)
  assert len(seen)>6;results.append((answer,counter[0]));print('PASS',suffix,'two native LFO banks and bounded attack/cutoff/resonance modulation',counter[0],'instructions',flush=True)
 assert results[0]==results[1];print('PASS exact modulation/phase output and executed-instruction equality before/after UI hooks',flush=True)
if __name__=='__main__':main()
