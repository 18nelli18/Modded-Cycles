#!/usr/bin/env python3
"""Suppression UI des trigs B : reset complet, locks et isolation audio."""
import argparse,struct,json,pathlib
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,key,PAT
from test_seq_gen_menu import RAW
from test_sdvintage import main_os_from_syx


def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 r=make(main_os_from_syx(a.cycles),repeat=True,conditions=True,live_record=True)
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text())
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  for w in t['writes']:
   at=0x40000400+w['off']
   if 0x40100000<=at<0x401ab750:r.u.mem_write(at,bytes.fromhex(w['new']))
  r.s.update({k:int(v,16) for k,v in t['symbols'].items()})
  assert r.call('ml_prepare')==1
  r.w32(r.s['ml_pattern'],PAT);r.call('ml_init',PAT)
 assert r.call('mlp_open')==1;r.call('ml_repeat_prepare_ui')
 locks=r.r32(r.s['ml_repeat_edit_settings']);assert locks
 rec=0x930a0000;r.u.mem_write(rec+357,b'\x01\x01')
 r.stubs[0x400cf9a8]=lambda args:rec;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
 audio=bytes(r.u.mem_read(RAW,722));default=bytes((60,100,1,0));lock_default=bytes((0,0,0,0,0,1,0,0))
 for lane in range(6):
  r.w32(r.s['mlp_track'],lane)
  for step in range(64):
   r.w32(r.s['mlp_step'],step)
   at=PAT+264*lane+8+4*step;lock=locks+520*lane+8+8*step
   r.u.mem_write(at,bytes((91,3,64,255)))
   r.u.mem_write(lock,bytes((1,15,8,127,2,4,255,165)))
   before=bytes(r.u.mem_read(PAT,1584));before_locks=bytes(r.u.mem_read(locks,3120))
   assert key(r,16+step%16)==1;assert key(r,16+step%16,0)==1
   assert bytes(r.u.mem_read(at,4))==default,(lane,step)
   assert bytes(r.u.mem_read(lock,8))==lock_default,(lane,step)
   expected=bytearray(before);off=at-PAT;expected[off:off+4]=default
   assert bytes(r.u.mem_read(PAT,1584))==expected
   expected=bytearray(before_locks);off=lock-locks;expected[off:off+8]=lock_default
   assert bytes(r.u.mem_read(locks,3120))==expected
   assert key(r,16+step%16)==1;assert key(r,16+step%16,0)==1
   assert bytes(r.u.mem_read(at,4))==bytes((72,100,1,1))
 assert bytes(r.u.mem_read(RAW,722))==audio
 print('ok : six voies ×64 pas, suppression/recréation C5/100/1, locks chance/retrigger/arp et slide/timing effacés')
 print('ok : pas voisins, réglages de voie et données audio inchangés')


if __name__=='__main__':main()
