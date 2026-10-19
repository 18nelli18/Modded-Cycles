"""Note130 : pad mode seul ; comparaison octet pour octet du DSP avec principal1.96."""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig
from probe_chord_pads import Rig as Pads,official_image,BASE,CONTROLLER
from unicorn import UC_HOOK_CODE

def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='usb');a=p.parse_args()
 before,bmem,bt=boot_case('build/pad-mode/'+a.profile+'-before')
 img,mem,ts=boot_case('build/midi-machine/all/main-'+a.profile)
 q=next(t for t in ts if t['id']=='pad-selection')
 assert not any(t['id'] in ('wizard-control-test','audio-load-diagnostic') for t in ts)
 assert not any(k in q['symbols'] for k in ('wf_before','wf_after','wf_value','wf_cut','wf_res'))
 # Les charges preexistantes, y compris sampler/DSP/moteurs/MACRO, restent exactes.
 lookup=dict(mem)
 for at,raw in bmem:assert lookup[at][:len(raw)]==raw,('ancien runtime modifie',hex(at))
 # Le sampler resident et toutes ses tables sont aussi identiques apres bootstrap.
 wizard=next(t for t in ts if t['id']=='sample-wizard')
 lo=0x401aa140;hi=0x401c0000
 assert img[lo-BASE:hi-BASE]==before[lo-BASE:hi-BASE],'code/table sampler modifie'
 print('PASS tous les runtimes precedents et sampler resident identiques a1.96 ; aucun hook filtre, capture ou diagnostic')
 sy={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x500000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 r.w32(0x40fe4178,0);event=0x93010000
 def bind(at,fn):
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 # Hors menu : delegation directe avec valeur de retour conservee.
 delegate=event+512;r.w32(r.s['wf_api'],delegate);bind(delegate,lambda a:0x12345678)
 u.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,6,1,0));assert r.call(0x400775f8,0,event)==0x12345678
 # Le menu choisit le mode global, ne touche pas aux parametres de son.
 keyevent=event+128
 def key(code,flags):u.mem_write(keyevent,struct.pack('>6I',0,0,0,code,flags,0));return r.call('wf_key',keyevent)
 assert key(13,1)==0 and key(2,1)==1 and key(2,0)==1 and key(13,0)==0
 assert r.call('wf_menu_edit')==0
 bind(0x4006f73a,lambda a:1);u.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,1,1,0))
 assert r.call('wf_menu_encoder',event)==1 and r.r32(r.s['wf_stock'])==0
 assert key(32,16)==1 and r.call('wf_menu_edit')==1
 assert r.call('wf_menu_encoder',event)==1 and r.r32(r.s['wf_stock'])==1
 assert key(12,1)==1 and r.call('wf_menu_encoder',event)==0
 print('PASS menu : SETTINGS+TRACK, DATA obligatoire avant edition, choix Stock, BACK, aucune mutation de son')
 # Le vrai PadsView porte le nouveau branchement, sans ecriture de code a chaud.
 stock=official_image('firmware/model-cycles_OS1.13.syx');pads_image=bytearray(img)
 for lo,hi in ((0x4001d05e,0x4001d180),(0x4001d25e,0x4001d264)):pads_image[lo-BASE:hi-BASE]=stock[lo-BASE:hi-BASE]
 for mode in (0,1):
  for browser in (False,True):
   for lane in range(6):
    for track in (False,True):
     pr=Pads(bytes(pads_image));pr.uc.mem_map(0x46700000,0x500000)
     for at,raw in mem:
      if 0x46700000<=at<0x46c00000:pr.uc.mem_write(at,raw)
     pr.w32(r.s['wf_stock'],mode);pr.pressed={2} if track else set()
     if browser:
      node=0x93200000;view=0x93200100;pr.w32(CONTROLLER+20,node);pr.w32(node,CONTROLLER+20);pr.w32(node+8,view);pr.w32(node+12,0)
      pr.uc.hook_add(UC_HOOK_CODE,pr._stub(lambda a:view),begin=0x400f4cec,end=0x400f4cec)
     pr.event(lane+1,True,81+lane);plays=(browser or track) if not mode else not track
     assert any(kind=='on' for kind,args in pr.calls)==plays,(mode,browser,lane,track,pr.calls)
     pr.pressed.clear();pr.event(lane+1,False)
     assert [kind for kind,args in pr.calls]==(['off'] if plays else []),pr.calls
 print('PASS vrai PadsView : Silent/Stock x6pads xTRACK xpreecoute, note-off memorise, aucune reecriture executable')
if __name__=='__main__':main()
