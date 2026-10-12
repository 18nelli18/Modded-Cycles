#!/usr/bin/env python3
"""Shortcuts B compilés : copie, collage, clear/undo ; isolation audio/routage."""
import argparse,struct,json,pathlib
from unicorn import UC_HOOK_CODE
import build
from test_midi_lane_page import make,load,key
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import RAW

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');ap.add_argument('--retrigger',action='store_true');a=ap.parse_args()
 stock=main_os_from_syx(a.cycles);r=make(stock,repeat=a.retrigger);load(r,clipboard=True,repeat=a.retrigger)
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
 settings=0
 if a.retrigger:
  r.call('ml_repeat_prepare_ui');settings=r.r32(r.s['ml_repeat_edit_settings'])
  assert settings
  r.u.mem_write(settings,bytes((1,12,8,0,2,3,0,0)))
  r.u.mem_write(settings+8,bytes((1,9,4,0,1,2,63,0)))
  saved=bytes(r.u.mem_read(settings,520));dest=bytes(r.u.mem_read(settings+4*520,520))
 original=[lane(n) for n in range(6)]
 def chord(code):
  key(r,1,1);assert key(r,code,3)==1
  key(r,1,0);assert key(r,code,0)==1
 r.w32(r.s['mlp_track'],0)
 if settings:
  allocator=r.stubs[0x400802e0];r.stubs[0x400802e0]=lambda args:0
  chord(9);assert r.r32(r.s['mlp_clip_ready'])==0
  assert [lane(n) for n in range(6)]==original
  r.stubs[0x400802e0]=allocator
 chord(9)
 assert [lane(n) for n in range(6)]==original
 r.w32(r.s['mlp_track'],4);chord(11)
 pasted=lane(4)
 if settings:assert bytes(r.u.mem_read(settings+4*520,520))==saved
 assert pasted[:4]==original[4][:4] and pasted[6:8]==original[4][6:8]
 assert pasted[4:6]==original[0][4:6] and pasted[8:]==original[0][8:]
 assert all(lane(n)==original[n] for n in range(6) if n!=4)
 chord(11);assert lane(4)==original[4] # undo paste
 if settings:assert bytes(r.u.mem_read(settings+4*520,520))==dest
 if settings:
  rt=r.r32(r.s['ml_runtime']);state=r.s['ml_repeat_states']+4*20
  assert r.call('ml_repeat_arm',rt,state,4,100,0x9a3c6404,8,0xffffffff)==1
  assert r.call('ml_take',rt)==0x9a3c6404
 chord(10);cleared=lane(4)
 if settings:
  assert r.r32(state)==0 and r.call('ml_take',rt)==0x8a3c0004
 assert cleared[:8]==original[4][:8]
 assert cleared[8:]==struct.pack('>I',0x48640100)*64
 if settings:
  assert bytes(r.u.mem_read(settings+4*520,8))==dest[:8]
  assert bytes(r.u.mem_read(settings+4*520+8,512))==bytes((0,0,0,0,0,1,0,0))*64
 chord(10);assert lane(4)==original[4] # undo clear
 if settings:assert bytes(r.u.mem_read(settings+4*520,520))==dest
 # Appui long n'exécute pas deux fois ; libération FUNC avant STOP consommée.
 key(r,1,1);key(r,11,3);after=lane(4)
 key(r,11,35);assert lane(4)==after
 key(r,1,0);assert key(r,11,0)==1
 assert bytes(r.u.mem_read(RAW,722))==audio
 assert key(r,10,1)==0 and key(r,11,1)==0 # transport normal sans FUNC
 r.stubs[0x400cf9a8]=lambda args:0
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
 popups=[]
 def popup(args):
  from unicorn import m68k_const as mk
  assert r.u.reg_read(mk.UC_M68K_REG_SR)&0x700==0
  popups.append(r.string(args[0]));return 0
 address=r.s['TG_show_popup'];r.stubs[address]=popup
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
 # Clipboard par pas indépendant : tenir TRIG, REC copie, STOP colle.
 r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_step'],0)
 key(r,16,1);assert key(r,9,1)==1;key(r,9,0);key(r,16,0)
 assert lane(0)==original[0] and popups==['COPY']
 r.w32(r.s['mlp_track'],5);r.w32(r.s['mlp_step'],48)
 before=[lane(n) for n in range(6)]
 key(r,31,1);assert r.r32(r.s['mlp_step'])==63
 assert key(r,11,1)==1;key(r,11,0);key(r,31,0)
 assert popups==['COPY','PASTE']
 assert lane(5)[8+63*4:12+63*4]==original[0][8:12]
 assert lane(5)[:8+63*4]==before[5][:8+63*4]
 assert all(lane(n)==before[n] for n in range(5))
 if settings:
  assert bytes(r.u.mem_read(settings+5*520+8+63*8,8))==saved[8:16]
 assert bytes(r.u.mem_read(RAW,722))==audio
 print('ok : TRIG+REC/STOP copie un pas avec locks, page4/pas64, release sans suppression, A-side intact')
 print('ok : clavier B copy/paste/clear/undo,64pas, lane sélectionnée seule, routage/audio intacts, releases et transport')
if __name__=='__main__':main()
