"""Test130 : vrai build, chaine encodeur et coefficients ; pads natifs dans les deux modes.
Les getters UI et la derniere delegation encodeur sont instrumentes. Pas de preuve hardware.
"""
import argparse,pathlib,sys,struct
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig,STACK
from probe_chord_pads import Rig as Pads,official_image,BASE,CONTROLLER
from unicorn import UC_HOOK_CODE,m68k_const as C

def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='usb');a=p.parse_args();case='build/wizard-control/'+a.profile+'-after'
 img,mem,ts=boot_case(case);sy={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy});u=r.u
 for at,size in ((0x43000000,0x800000),(0x46700000,0x500000),(0x80000000,0x200000)):u.mem_map(at,size)
 for at,raw in mem:u.mem_write(at,raw)
 r.w16=lambda at,value:u.mem_write(at,struct.pack('>H',value&65535))
 r.r16=lambda at:int.from_bytes(u.mem_read(at,2),'big')
 r.w32(0x40fe4178,0)
 def bind(at,fn):
  if at not in r.stubs:u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 held={2,5};bind(0x4007faf4,lambda a:int(a[0] in held));event=0x93010000;base=0x93020000;frame=0x93030000;getter=0x93040000;delegate=getter+16
 def get_params(args):
  value=base+128*args[0];u.reg_write(C.UC_M68K_REG_A0,value);return value
 bind(getter,get_params);r.w32(r.s['wf_api']+12,getter)
 for lane in range(6):
  u.mem_write(base+128*lane,bytes(100));r.w16(base+128*lane+18,6<<8);r.w16(base+128*lane+26,32512);r.w16(base+128*lane+28,0)
 r.w32(r.s['wf_api'],delegate);selected=set(range(6))
 def turn(args):
  assert args[0]==0x1234 and args[1]==event,args[:2]
  index=r.r32(event+12)-6
  for lane in selected:r.w16(base+128*lane+26+2*index,0x2000+lane*256 if index==0 else 0x1000)
  return 0x12345678
 bind(delegate,turn)
 def encoder(index):u.mem_write(event,struct.pack('>6I',0x400fbebc,0,0,6+index,1,0));return r.call(0x400775f8,0x1234,event)
 # Sans geste : aucune prise de controle, meme si le delegue modifie les mots.
 held.clear();assert encoder(0)==0x12345678
 for lane in range(6):
  r.w16(frame+26,0x4000);r.w16(frame+28,0x0100)
  assert r.call('wf_value',frame,lane,0)==0x4000
 # Un vrai changement seulement sur les pistes incluses. Pas de fuite vers les exclues.
 for lane in range(6):r.w16(base+128*lane+26,32512)
 held.update((2,5));selected={0,2,5};assert encoder(0)==0x12345678
 for lane in range(6):
  expected=0x2000+lane*256 if lane in selected else 0x4000
  assert r.call('wf_value',frame,lane,0)==expected,(lane,hex(r.call('wf_value',frame,lane,0)),hex(expected),hex(r.r16(base+128*lane+26)))
  assert r.call('wf_value',frame,lane,1)==0x0100
 print('PASS vrai hook encodeur chaine, retour preserve ; Control All seulement, masque respecte, cutoff et resonance independants')
 # Deux sons verrouilles tres differents : la meme piste conserve sa coupure live.
 sampler=next(t for t in ts if t['id']=='sample-wizard');ws={k:int(v,16) for k,v in sampler['symbols'].items()}
 def coeff(lane,cut,res):
  r.w16(frame+26,cut);r.w16(frame+28,res);before=bytes(u.mem_read(frame,100))
  keep={C.UC_M68K_REG_D3:0x12345678,C.UC_M68K_REG_D5:0x33445566,C.UC_M68K_REG_D6:0x55667788,C.UC_M68K_REG_D7:0x77889900}
  for reg,value in keep.items():u.reg_write(reg,value)
  u.reg_write(C.UC_M68K_REG_D2,lane);u.reg_write(C.UC_M68K_REG_A2,frame);u.reg_write(C.UC_M68K_REG_A7,STACK)
  u.emu_start(ws['sp_flt_go'],ws['sp_flt_done'],count=100000)
  assert u.reg_read(C.UC_M68K_REG_PC)==ws['sp_flt_done']
  assert u.reg_read(C.UC_M68K_REG_A7)==STACK
  assert all(u.reg_read(reg)==value for reg,value in keep.items())
  assert bytes(u.mem_read(frame,100))==before,'frame audio/pool modifie'
  return tuple(r.r32(ws[name]+4*lane) for name in ('filt_f','filt_q','filt_mk'))
 for lane in selected:
  assert coeff(lane,0x1000,0)==coeff(lane,0x7000,0)
  assert coeff(lane,0x1000,0)!=coeff(lane,0x1000,0x1800),'resonance verrouillee doit rester native sans override res'
  idx=(0x2000+lane*256)>>8
  assert coeff(lane,32512,0)[0]==r.r16(ws['filt_coef']+2*idx)
 assert coeff(1,0x1000,0)!=coeff(1,0x7000,0)
 assert encoder(1)==0x12345678
 for lane in selected:assert coeff(lane,0x1000,0)==coeff(lane,0x7000,0x3000)
 # Sortie Wizard invalide le cache, sans jamais ecrire dans les sons du pool.
 r.w16(base+26,32512);assert r.call('wf_value',frame,0,0)==r.r16(frame+26)
 print('PASS vrai bloc coefficients Wizard : deux sample locks, cutoff/res override, autres champs/registres/pile conserves, exclues natives')
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
