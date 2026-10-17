"""Note116 : menus reels A/B, Oct0 sans transposition et stockage inchange."""
import argparse,pathlib,sys,struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,OBJ
import test_arp as A

def main():
 p=argparse.ArgumentParser();p.add_argument('--case',required=True);a=p.parse_args();img,memories,ts=boot_case(a.case)
 arp=next((t for t in ts if t['id']=='arp'),None)
 if arp:
  A.UI_CFG=int(arp['symbols']['ui_cfg'],16);A.RING=int(arp['symbols']['ring'],16)
  e,items,drawn,_,_=A.menu(img);assert len(items)==5
  fn=A.make_fn(e,items[4][2]);change=A.make_fn(e,items[4][3]);data=e.track.data+512
  for added in range(4):
   e.uc.mem_write(data,bytes([added<<3]));drawn.clear();e.call(items[4][2][1],fn,0,0x93700000,0x93710000,7);assert drawn[-1][6]==added
  e.uc.mem_write(data,b'\0');e.sel=A.SEL
  for delta,want in ((-1,0),(1,8),(1,16),(1,24),(1,24),(-20,0)):
   e.call(items[4][3][1],change,0,delta&0xffffffff);assert e.uc.mem_read(data,1)[0]==want
  A.repeat_tests(img);assert not A.FAIL
  print('PASS A : menu Oct0..3, bornes, changements ; suites reelles et sauvegardes identiques',flush=True)
 bank=next((t for t in ts if t['id']=='midi-out-bank'),None)
 if not bank:return
 owner=next(t for t in ts if 'octave_draw'in t.get('symbols',{}));sy={**bank['symbols'],**owner['symbols']};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in memories:u.mem_write(at,raw)
 assert r.call('ml_prepare')==1;r.call('mlp_retrigger_open');settings=r.r32(r.s['ml_repeat_edit_settings']);assert settings
 # Callback prive de rendu : retrouver son prologue avant le crochet garde.
 start=r.s['mlp_retrigger_render'];body=bytes(u.mem_read(start,4096));call=b'\x4e\xb9'+struct.pack('>I',r.s['octave_draw']);pos=body.index(call);begin=body.rfind(b'\x4f\xef\xff\xf0',0,pos);assert begin>=0
 values=[];r.stubs[0x40071a04]=lambda args:values.append(args[6]) or 0
 row=OBJ+0x1000;r.w32(row+80,5);r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_held'],0)
 for stored in range(1,5):
  u.mem_write(settings+5,bytes([stored]));values.clear();r.call(start+begin,0,row,0x93003000,0,0,0);assert values==[stored-1],values
  state=OBJ+0x2000;r.call('ml_arp_init',state)
  for note in (60,64,67):assert r.call('ml_arp_held',state,note,1)==1
  notes=[r.call('ml_arp_next',state,0,stored) for _ in range(24)]
  expected={note+12*octave for note in (60,64,67) for octave in range(stored)};assert set(notes)==expected,(stored,notes)
 print('PASS B : vrai callback Oct0..3 ; notes tenues seules a0 et extensions1..3 ; donnees1..4 inchangees',flush=True)
 print('LIMITES : menus et notes executes en emulation ; geste et son physiques a verifier')
if __name__=='__main__':main()
