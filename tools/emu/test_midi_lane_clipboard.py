#!/usr/bin/env python3
"""Shortcuts B compilés : copie, collage, clear/undo ; isolation audio/routage."""
import argparse,struct,json,pathlib
import build
from test_midi_lane_page import make,load,key
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 stock=main_os_from_syx(a.cycles);r=make(stock);load(r,clipboard=True)
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text());cat=build.load_catalog()['model-cycles_OS1.13'][1]
  chosen=sorted([cat[x] for x in t['requires']],key=lambda x:x['order'])
  image,_=build.apply_writes(stock,chosen+[t]);r.u.mem_write(build.BASE,image)
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  r.s.update({k:int(v,16) for k,v in t['symbols'].items()})
 assert r.call('ml_prepare')==1 and r.call('mlp_open')==1
 pat=r.r32(r.s['ml_pattern']);audio=bytes(r.u.mem_read(RAW,722))
 def lane(n):return bytes(r.u.mem_read(pat+264*n,264))
 r.u.mem_write(pat+8,struct.pack('>I',0x3c640101));r.u.mem_write(pat+4,b'\x20\x01')
 original=[lane(n) for n in range(6)]
 def chord(code):
  key(r,1,1);assert key(r,code,3)==1
  key(r,1,0);assert key(r,code,0)==1
 r.w32(r.s['mlp_track'],0);chord(9)
 assert [lane(n) for n in range(6)]==original
 r.w32(r.s['mlp_track'],4);chord(11)
 pasted=lane(4)
 assert pasted[:4]==original[4][:4] and pasted[6:8]==original[4][6:8]
 assert pasted[4:6]==original[0][4:6] and pasted[8:]==original[0][8:]
 assert all(lane(n)==original[n] for n in range(6) if n!=4)
 chord(11);assert lane(4)==original[4] # undo paste
 chord(10);cleared=lane(4)
 assert cleared[:8]==original[4][:8]
 assert cleared[8:]==struct.pack('>I',0x48640100)*64
 chord(10);assert lane(4)==original[4] # undo clear
 # Appui long n'exécute pas deux fois ; libération FUNC avant STOP consommée.
 key(r,1,1);key(r,11,3);after=lane(4)
 key(r,11,35);assert lane(4)==after
 key(r,1,0);assert key(r,11,0)==1
 assert bytes(r.u.mem_read(RAW,722))==audio
 assert key(r,10,1)==0 and key(r,11,1)==0 # transport normal sans FUNC
 print('ok : clavier B copy/paste/clear/undo,64pas, lane sélectionnée seule, routage/audio intacts, releases et transport')
if __name__=='__main__':main()
