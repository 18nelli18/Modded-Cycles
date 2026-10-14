#!/usr/bin/env python3
"""REC/LED B et sélection PadsView réelle, sans modifier le moteur audio.

Le clavier physique et les sorties LED/MIDI sont instrumentés ; les getters,
PadsView et callbacks propres restent exécutés. Essai matériel requis.
"""
import argparse,copy,json,pathlib,struct,sys,importlib.util
from unicorn import UC_HOOK_CODE
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'chord_keys_compat'))
from test_step_delete_reset import image
from test_sdvintage import main_os_from_syx
from test_seq_gen_menu import Rig
spec=importlib.util.spec_from_file_location('play_ui_chord',HERE/'chord_keys_compat/chord_ui_checks.py')
ck=importlib.util.module_from_spec(spec);spec.loader.exec_module(ck)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True);p.add_argument('--bank',required=True);a=p.parse_args()
 stock=main_os_from_syx(a.cycles);cat=json.loads(pathlib.Path(a.catalog).read_text())['tweaks'];bank=json.loads(pathlib.Path(a.bank).read_text())
 cat=copy.deepcopy(cat);cat=[bank if t['id']==bank['id'] else t for t in cat]
 chord=next(t for t in cat if t['id']=='chord-keys-supermodel')
 w=bank['play_ui']['chord_primary'];row=next(x for x in chord['writes'] if x['off']==w['off']);row['new']=w['new']
 blob=image(stock,cat);symbols={k:int(v,16) for k,v in chord['symbols'].items()}
 for secondary in (False,True):
  for pad in range(1,7):
   r,*_=ck._ui_rig(blob,symbols)
   ck._pad(r,pad,True,secondary=secondary)
   assert ('select',(pad-1,)) in r.calls,(pad,secondary,r.calls)
   assert any(name=='on' and args[0]==pad-1 for name,args in r.calls),r.calls
   ck._pad(r,pad,False,secondary=secondary)
   assert any(name=='off' and args[0]==pad-1 for name,args in r.calls),r.calls
  r,*_=ck._ui_rig(blob,symbols);ck._key(r,1,True)
  ck._pad(r,2,True,secondary=secondary)
  assert not any(name=='select' for name,args in r.calls),r.calls
  ck._key(r,1,False);ck._pad(r,2,False,secondary=secondary)
  assert bytes(r.uc.mem_read(symbols['held_pads'],6))==bytes(6)
 print('ok : six pads, deux vtables, sélection/note/off natifs ; TRIG tenu conserve HARMONY et son release',flush=True)
 r=Rig(blob,{'writes':[]},{'writes':[],'symbols':bank['symbols']});rec=0x930a0000
 reads=[];r.stubs[0x400cf9a8]=lambda args:reads.append(1) or rec
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400cf9a8,end=0x400cf9a8)
 phase=r.s['TG_slide_phase'];r.stubs[phase]=lambda args:0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=phase,end=phase)
 step=0x930b0000
 from unicorn import m68k_const as mk
 for active in (0,1):
  r.u.mem_write(rec+357,bytes((active,active)))
  for lane in range(6):
   r.w32(r.s['mlp_track'],lane);r.u.reg_write(mk.UC_M68K_REG_D0,13)
   assert r.call('mpu_led_begin')==lane
   assert r.u.reg_read(mk.UC_M68K_REG_D5)==13
   for flags in (0,1,2,3):
    r.u.mem_write(step,bytes((60,100,1,flags)));r.u.reg_write(mk.UC_M68K_REG_A2,step)
    r.call('mpu_led_state');actual=r.u.reg_read(mk.UC_M68K_REG_D4)
    expected=1 if not active or flags==0 else 260 if flags==2 else 3
    assert actual==expected,(active,lane,flags,actual)
 assert len(reads)==12
 print('ok : REC cache une lecture/frame, notes/locks/slide masqués hors REC ; curseur D5 conservé',flush=True)
 r.u.mem_write(rec+357,b'\0\0');r.u.reg_write(mk.UC_M68K_REG_D0,7);r.call('mpu_led_begin')
 for pressed in range(16):
  r.w32(r.s['mlp_live_held'],1<<pressed)
  for key in range(16):
   r.u.reg_write(mk.UC_M68K_REG_D2,key);r.u.mem_write(step,bytes((60,100,1,3)));r.u.reg_write(mk.UC_M68K_REG_A2,step)
   r.call('mpu_led_state');assert r.u.reg_read(mk.UC_M68K_REG_D4)==(3 if key==pressed else 1)
 r.w32(r.s['mlp_live_held'],0);r.call('mpu_led_state');assert r.u.reg_read(mk.UC_M68K_REG_D4)==1
 print('ok : 16 touches live tenues, seule touche correspondante visible ; release éteint, pattern enregistré masqué',flush=True)
if __name__=='__main__':main()
