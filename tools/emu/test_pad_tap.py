"""Note130 : vrai sc_key, tap unique et maintien long, aucun SCRAMBLE sur hold.
Les actions terminales sc_run/edition des pas sont instrumentees ; leur dispatch est natif.
"""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig
from unicorn import UC_HOOK_CODE
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='usb');p.add_argument('--main',action='store_true');a=p.parse_args()
 img,mem,ts=boot_case(('build/midi-machine/all/main-' if a.main else 'build/pad-tap/')+a.profile);sy={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x500000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 r.w32(0x40fe4178,0);event=0x93010000;runs=[];steps=[];held_steps=[False]
 def bind(at,fn):
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 bind(r.s['sc_run'],lambda a:runs.append(1) or 0)
 bind(r.s['sc_steps_toggle'],lambda a:steps.append(1) or int(held_steps[0]))
 def key(code,flags):
  u.mem_write(event,struct.pack('>6I',0,0,100+len(runs)+len(steps),code,flags,127));return r.call('wf_key',event)
 def close():key(12,1)
 api=r.s['wf_api'];assert r.r32(api+24)==r.s['sc_key']
 # SETTINGS seul ne modifie ni son ni mode.
 assert key(13,1)==0 and key(13,0)==0 and not runs
 for reverse_release in (False,True):
  for repeated in (False,True):
   n=len(runs);s=len(steps);key(13,1);assert key(2,1)==1
   assert len(runs)==n and len(steps)==s
   if repeated:assert key(2,9)==1 and len(runs)==n
   if reverse_release:key(13,0);key(2,16)
   else:key(2,16);key(13,0)
   assert len(runs)==n+1 and len(steps)==s+1,(reverse_release,repeated,len(runs),n)
   key(2,16);assert len(runs)==n+1
   assert r.r32(r.s['sc_taken'])==0 and r.r32(r.r32(api+16))==0
 print('PASS vrai sc_key : aucun effet a l appui, un SCRAMBLE au relachement dans les deux ordres, repeat et doubles releases sans doublon')
 # Le SCRAMBLE des pas tenus garde sa route : pas de sc_run global.
 held_steps[0]=True;n=len(runs);s=len(steps);key(13,1);key(2,1);key(2,16);key(13,0)
 assert len(runs)==n and len(steps)==s+1;held_steps[0]=False
 for reverse_release in (False,True):
  n=len(runs);s=len(steps);key(13,1);key(2,1);key(2,9);assert len(runs)==n
  assert key(2,33)==1 and r.call('wf_menu_edit')==0
  assert key(32,16)==1 and r.call('wf_menu_edit')==1
  if reverse_release:key(13,0);key(2,16)
  else:key(2,16);key(13,0)
  assert len(runs)==n and len(steps)==s
  close();assert r.r32(r.r32(api+16))==0
 print('PASS maintien long natif : Pad Setup, DATA/BACK, releases dans les deux ordres, aucun SCRAMBLE ; route pas tenus intacte')
 assert not any(k in sy for k in ('wf_value','wf_before','wf_after'))
 print('PASS helper sans aucun hook ni routine audio/filtre')
 # Menu ferme : aucun appel au dessinateur natif, allocation ou repaint.
 pcs=[]
 hook=u.hook_add(UC_HOOK_CODE,lambda uc,pc,size,data:pcs.append(pc))
 for _ in range(100):assert r.call('wf_draw',0,0)==0
 u.hook_del(hook)
 assert r.s['wf_menu_draw'] not in pcs and 0x400802e0 not in pcs and 0x40076bee not in pcs
 print('PASS 100 dessins menu ferme : aucun MenuView, allocation ni repaint ; mesure fonctionnelle, pas chronometrage materiel')
if __name__=='__main__':main()
