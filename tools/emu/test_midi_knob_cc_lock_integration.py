#!/usr/bin/env python3
"""Intégration CC RAM : édition tenue, queue bornée, routage, clear et clipboard."""
import argparse,pathlib,subprocess,tempfile,json
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--tweak');a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
 names=('knob_cc','knob_cc_ui','knob_cc_scroll','knob_cc_assignment','knob_cc_scramble','knob_cc_locks','knob_cc_lock_patterns','knob_cc_lock_edit','knob_cc_lock_queue','settings_present','runtime','service','knob_cc_lock_clip','lfo_cc_names')
 defs={k:0x9306a000+i*4 for i,k in enumerate(('TG_set_held','TG_mod_used','TG_blk_clk','mlp_track','mlp_step','mlp_held','mlp_changed','ml_pattern','ml_play_pattern','ml_clock_state','mlp_obj','ml_runtime'))}
 defs['ml_runtime']=0x9307a000
 defs['SG_random']=0x9306b000
 defs['TG_show_popup']=0x9306b004
 with tempfile.TemporaryDirectory() as tmp:
  p=pathlib.Path(tmp);objs=[]
  for name in names:
   obj=p/(name+'.o');objs.append(str(obj));subprocess.run([cross+'as','-march=cfv4e','--defsym','ML_KNOB_LOCKS=1','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
  (p/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .text 0x93050000 : { *(.text*) *(.rodata*) *(.data*) } }')
  subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlkc_enc','-o',str(p/'k.elf'),*objs],check=True)
  subprocess.run([cross+'objcopy','-O','binary',str(p/'k.elf'),str(p/'k.bin')],check=True)
  code=(p/'k.bin').read_bytes();syms=symbols(cross,p/'k.elf')
 r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
 if a.tweak:
  t=json.loads(pathlib.Path(a.tweak).read_text());syms={k:int(v,16) for k,v in t['symbols'].items()};r.s=syms
  for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
  defs={k:syms[k] for k in defs}
 r.w32(defs['ml_runtime'],0x9307b000)
 pat,event,clock=0x93070000,0x93074000,0x93076000
 for lane in range(6):r.u.mem_write(pat+lane*264,bytes((1,0,6+lane,4,64,2,0,0))+bytes(256))
 for name,value in (('ml_pattern',pat),('ml_play_pattern',pat),('ml_clock_state',clock),('mlp_track',0),('mlp_step',19),('mlp_held',8)):
  r.w32(defs[name],value)
 r.w32(clock,1);r.w32(0x40fe4228,1);r.w32(event+12,2)
 sent=[]
 def send(args):sent.append(bytes(r.u.mem_read(args[1],3)));assert args[0]==3 and args[2]==4;return 0
 r.stubs[0x400826b0]=send;router_hook=r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
 r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 # Assignation pendant lecture : aucun CC intermédiaire, même après release
 # sans lock. Un delta nul doit tout de même consommer SETTINGS.
 r.w32(defs['TG_set_held'],1);r.delta=0
 assert r.call('mlkc_enc',event)==1 and r.r32(defs['TG_mod_used'])==1
 r.delta=1;assert r.call('mlkc_enc',event)==1
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker')
 assert not sent and r.call('mlkcq_ready')==0
 r.w32(defs['TG_set_held'],0);r.call('mlkc_assign_sync')
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker')
 assert not sent and r.call('mlkcq_ready')==0
 r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 r.w32(defs['mlp_held'],0);r.delta=5
 assert r.call('mlkc_enc',event)==1
 assert sent==[b'\xb6\x4a\x45'],sent
 sent.clear();r.u.mem_write(syms['mlkc_state'],bytes((74,64)));r.w32(defs['mlp_held'],8)
 r.delta=5;assert r.call('mlkc_enc',event)==1 and not sent
 assert r.u.mem_read(syms['mlkc_state'],2)==bytes((74,64))
 locks=r.call('mlkc_locks_for',pat,0);assert locks
 assert r.call('mlkc_lock_get',locks,0,19,0)==0x4a45
 r.w32(0x9307b000+272,0x86480004)
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2700);r.call('mlkcq_step',pat,0,19);assert not sent
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);assert r.call('mlkcq_ready')==1
 r.call('mlkcq_worker');assert sent==[b'\xb6\x4a\x45']
 # Pendant assignation, les locks figés continuent, même déjà en file.
 r.call('mlkcq_step',pat,0,19);r.w32(defs['TG_set_held'],1);r.delta=1
 assert r.call('mlkc_enc',event)==1
 r.call('mlkcq_worker');assert sent[-1]==b'\xb6\x4a\x45' and len(sent)==2
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker')
 assert sent[-1]==b'\xb6\x4a\x45' and len(sent)==3
 # Pas sans lock : aucune destination provisoire ne part pendant/après scroll.
 r.u.mem_write(pat+8+20*4,bytes((72,100,1,1)))
 r.call('mlkcq_step',pat,0,20);r.call('mlkcq_worker');assert len(sent)==4
 assert len(sent)==4 and sent[-1]==b'\xb6\x4a\x40'
 r.w32(defs['TG_set_held'],0);r.call('mlkc_assign_sync');r.call('mlkcq_step',pat,0,20);r.call('mlkcq_worker');assert len(sent)==4
 sent[:]=[b'\xb6\x4a\x45']

 r.u.mem_write(syms['mlkc_state'],bytes((71,64)))
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker');assert sent[-1]==b'\xb6\x4a\x45' and len(sent)==2
 r.call('mlkcq_step',pat,0,19);r.u.mem_write(pat+1,b'\x01');r.call('mlkcq_worker');assert len(sent)==2
 r.u.mem_write(pat+1,b'\x00');r.call('mlkcq_step',pat,0,19);r.u.mem_write(pat+2,b'\x00');r.call('mlkcq_worker');assert len(sent)==2
 r.u.mem_write(pat+2,b'\x06');r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 r.w32(defs['mlp_held'],8|128);r.delta=5;r.call('mlkc_enc',event)
 assert r.call('mlkc_lock_get',locks,0,19,0)==0x4a4a and r.call('mlkc_lock_get',locks,0,23,0)==0x4a4a
 r.call('mlkc_clear_selected');assert r.call('mlkc_lock_get',locks,0,19,0)==65535
 assert r.call('mlkc_lock_get',locks,0,23,0)==0x4a4a
 r.u.mem_write(pat+8+19*4,bytes((72,100,1,1)))
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker');assert sent[-1]==b'\xb6\x4a\x40'
 r.call('mlkc_step_clip',0,pat,0,23);r.call('mlkc_step_clip',2,pat,1,45)
 assert r.call('mlkc_lock_get',locks,1,45,0)==0x4a4a
 r.w32(defs['mlp_track'],0);r.call('mlkc_lane_clip',0)
 r.w32(defs['mlp_track'],2);r.call('mlkc_lane_clip',3);assert r.call('mlkc_lock_get',locks,2,23,0)==0x4a4a
 r.call('mlkc_lane_clip',1);r.call('mlkc_lane_clip',4);assert r.call('mlkc_lock_get',locks,2,23,0)==65535
 r.call('mlkc_lane_clip',2);assert r.call('mlkc_lock_get',locks,2,23,0)==0x4a4a
 if a.tweak:
  # Contrat du raccordement : seules les notes acceptées déclenchent la queue.
  addr=syms['ml_repeat_locked_step'];allowed=[1]
  r.stubs[addr]=lambda args:allowed[0]
  r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
  r.u.mem_write(pat+8+23*4,bytes((72,100,1,1)))
  r.call('mlkcq_reset');sent.clear()
  assert r.call('ml_pattern_tick',0x93078000,pat,0,23)==1
  assert r.call('mlkcq_ready')==1
  r.call('mlkcq_worker');assert sent==[b'\xb6\x4a\x4a']
  allowed[0]=0;r.call('mlkcq_reset')
  assert r.call('ml_pattern_tick',0x93078000,pat,0,23)==0 and r.call('mlkcq_ready')==0
  print('ok : tick placé conserve retour note et ne publie CC que sur trig accepté')
  # Un trig de paramètres passe un paquet nul au séquenceur de notes.
  allowed[0]=1;packets=[]
  r.stubs[addr]=lambda args:packets.append(args[2]) or 1
  r.u.mem_write(pat+8+23*4,bytes((72,100,1,2)))
  r.call('mlkcq_reset');sent.clear()
  assert r.call('ml_pattern_tick',0x9307b000,pat,0,23)==1
  assert packets==[0] and r.call('mlkcq_ready')==1
  r.call('mlkcq_worker');assert sent==[b'\xb6\x4a\x4a']
  r.u.mem_write(pat+8+23*4,bytes((72,100,1,0)))
  r.call('mlkcq_reset');sent.clear()
  r.call('ml_pattern_tick',0x9307b000,pat,0,23)
  assert r.call('mlkcq_ready')==0 and not sent
  # Saisie réelle de la page B : FUNC+TRIG, maintien/édition puis suppression.
  for name in ('ml_bank_ui_sync','mlp_keyboard','mlp_clip_key','ml_repeat_delete_selected'):
   entry=syms[name];r.stubs[entry]=lambda args,name=name:1 if name=='ml_bank_ui_sync' else 0
   r.u.hook_add(UC_HOOK_CODE,r.stub,begin=entry,end=entry)
  r.w32(syms['ml_store_load_ready'],1)
  r.w32(syms['mlp_track'],0)
  r.w32(syms['mlp_func'],1);r.w32(syms['mlp_held'],0)
  r.w32(syms['mlp_remove'],0);r.w32(syms['mlp_changed'],0);r.w32(syms['mlp_step'],0)
  r.u.mem_write(pat+8,bytes((72,100,1,0)))
  r.w32(event+12,16);r.w32(event+16,1)
  r.call('mlp_menu_key',0x9307f000,event)
  assert r.u.mem_read(pat+11,1)==b'\x02', (bytes(r.u.mem_read(pat+8,4)).hex(),r.r32(syms['mlp_step']),r.r32(syms['mlp_held']),r.r32(syms['mlp_func']),r.r32(syms['mlp_track']))
  r.w32(event+16,0);r.call('mlp_menu_key',0x9307f000,event)
  assert r.u.mem_read(pat+11,1)==b'\x02'
  r.w32(syms['mlp_func'],0);r.w32(event+16,1)
  r.call('mlp_menu_key',0x9307f000,event)
  assert r.u.mem_read(pat+11,1)==b'\x02'
  r.w32(event+16,0);r.call('mlp_menu_key',0x9307f000,event)
  assert r.u.mem_read(pat+11,1)==b'\x00'
  print('ok : FUNC+TRIG crée un lock trigless, maintien ne crée pas de note, release sans édition efface')
  # Le writer natif doit recevoir l'état PWM260 et non une simple couleur.
  obj,claims,led=0x9307f000,0x9307f600,0x9307f700
  r.w32(syms['mlp_obj'],obj);r.w32(syms['mlp_track'],0);r.w32(syms['mlp_step'],0)
  r.u.mem_write(pat+8,bytes((72,100,1,2)));ledstates=[]
  ledstubs=((0x400cfaf4,lambda args:led),(0x4000608c,lambda args:args[0]+1),(0x400060bc,lambda args:args[0]+20),(0x40005f86,lambda args:ledstates.append((args[1],args[2])) or 0))
  for entry,fn in ledstubs:
   r.stubs[entry]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=entry,end=entry)
  entry=syms['mlp_cursor'];r.stubs[entry]=lambda args:0xffffffff
  r.u.hook_add(UC_HOOK_CODE,r.stub,begin=entry,end=entry)
  r.call('mlp_led',obj+0x500,0,claims)
  assert (1,260) in ledstates,ledstates
  print('ok : trigless B transmis au writer avec état PWM260 du mod dim')


 r.call('mlkcq_reset');sent.clear()
 for knob in range(12):assert r.call('mlkc_lock_set',locks,0,7,knob,knob,100)==1
 r.call('mlkcq_step',pat,0,7);r.call('mlkcq_worker');assert len(sent)==8
 r.call('mlkcq_worker');assert len(sent)==12
 r.call('mlkcq_step',pat,0,7);r.w32(clock,0);r.call('mlkcq_worker');assert len(sent)==12 and r.call('mlkcq_ready')==0
 freed=[];r.stubs[0x400802ec]=lambda args:freed.append(args[0]) or 0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
 r.call('mlkc_locks_reset');assert r.call('mlkc_locks_for',pat,0)==0 and locks in freed
 # Reproduction signalée : potard2 parcourant tous les CC en lecture.
 r.call('mlkcq_reset');sent.clear();r.w32(clock,1)
 r.w32(defs['mlp_track'],0);r.w32(defs['mlp_held'],0);r.w32(defs['TG_set_held'],1);r.w32(event+12,3)
 r.u.mem_write(syms['mlkc_state']+2,bytes((255,64)));r.delta=1
 for cc in range(128):
  assert r.call('mlkc_enc',event)==1
  assert r.u.mem_read(syms['mlkc_draft']+2,1)[0]==cc
  assert r.u.mem_read(syms['mlkc_state']+2,1)[0]==255
  r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker');assert not sent
 r.w32(defs['TG_set_held'],0);r.call('mlkc_assign_sync');r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker');assert not sent
 # Une note sans lock restaure la base ; pas de restauration sur repos.
 r.w32(defs['TG_set_held'],0);r.w32(clock,1)
 r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 locks=r.call('mlkc_locks_for',pat,1)
 assert r.call('mlkc_lock_set',locks,0,19,0,74,90)==1
 sent.clear();r.call('mlkcq_reset')
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker')
 assert sent==[b'\xb6\x4a\x5a']
 r.u.mem_write(pat+8+20*4,bytes((72,100,1,0)))
 r.call('mlkcq_step',pat,0,20);r.call('mlkcq_worker');assert len(sent)==1
 r.u.mem_write(pat+8+20*4,bytes((72,100,1,2)))
 r.call('mlkcq_step',pat,0,20);r.call('mlkcq_worker');assert len(sent)==1
 r.u.mem_write(pat+8+20*4,bytes((72,100,1,1)))
 r.call('mlkcq_step',pat,0,20);r.call('mlkcq_worker')
 assert sent[-1]==b'\xb6\x4a\x40' and len(sent)==2
 print('ok : prochaine note sans lock restaure la base ; repos et trigless ne restaurent pas')
 # Scramble ne modifie que les valeurs assignées de la voie sélectionnée.
 r.u.mem_write(syms['mlkc_state'],bytes((255,64))*72)
 r.u.mem_write(syms['mlkc_state']+24*2,bytes((74,30,1,40)))
 r.w32(defs['mlp_track'],2);sent.clear()
 before=bytes(r.u.mem_read(pat,1584));popups=[]
 r.stubs[defs['SG_random']]=lambda args:0x123456e5
 r.stubs[defs['TG_show_popup']]=lambda args:popups.append(r.string(args[0])) or 0
 for addr in (defs['SG_random'],defs['TG_show_popup']):r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.call('mlkc_scramble')
 assert sent==[b'\xb8\x4a\x65',b'\xb8\x01\x65'],sent
 assert bytes(r.u.mem_read(syms['mlkc_state']+48,4))==bytes((74,101,1,101))
 assert before==bytes(r.u.mem_read(pat,1584)) and popups==['SCRAMBLE']
 if a.tweak:
  r.w32(defs['mlp_obj'],0x9307f000);r.w32(syms['mlp_func'],0)
  r.w32(defs['TG_set_held'],1);r.w32(event+12,2)
  r.w32(event+8,101);r.w32(event+16,1)
  sent.clear();assert r.call('ml_key',event)==0
  assert sent==[b'\xb8\x4a\x65',b'\xb8\x01\x65'],sent
  assert r.r32(event+16)&8 and r.r32(defs['TG_mod_used'])==1
  r.w32(event+8,102);r.w32(event+16,0)
  assert r.call('ml_key',event)==0 and len(sent)==2
  r.w32(defs['TG_set_held'],0)
  r.w32(syms['ml_genie_settings'],1)
  r.w32(event+12,2);r.w32(event+16,1);sent.clear()
  r.call('mlp_menu_key',0x9307f000,event)
  assert sent==[b'\xb8\x4a\x65',b'\xb8\x01\x65'],sent
  toggles=[];entry=syms['ml_toggle'];r.stubs[entry]=lambda args:toggles.append(1) or 0
  r.u.hook_add(UC_HOOK_CODE,r.stub,begin=entry,end=entry)
  r.w32(syms['mlp_func'],1);r.w32(event+16,1)
  r.call('mlp_menu_key',0x9307f000,event);assert toggles==[1] and len(sent)==2
  r.w32(syms['mlp_func'],0);r.w32(syms['ml_genie_settings'],0)
 r.w32(defs['mlp_track'],0)
 print('ok : SCRAMBLE B envoie seulement les CC assignés sur le canal de la voie, données audio/notes inchangées')
 # SETTINGS doit conserver B seulement pour sa vue native spécifique.
 view,ref=0x9307d000,0x9307e000
 r.w32(ref,view);r.w32(view,0x40107a20)
 r.w32(view+28,0x9307d100);r.w32(view+32,0x9307d108)
 presentations=[]
 def present_settings(args):
  presentations.append(r.r32(view+32));return 37
 addr=syms['ml_settings_native'];r.stubs[addr]=present_settings
 r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(defs['mlp_obj'],0x9307f000)
 assert r.call('ml_settings_present',0x9307f100,ref,0)==37
 assert presentations[-1]==0x9307d100 and r.r32(view+32)==0x9307d108
 r.w32(defs['mlp_obj'],0)
 r.call('ml_settings_present',0x9307f100,ref,0)
 assert presentations[-1]==0x9307d108
 r.w32(defs['mlp_obj'],0x9307f000);r.w32(view,0x40107a24)
 r.call('ml_settings_present',0x9307f100,ref,0)
 assert presentations[-1]==0x9307d108
 # Le vrai chemin SETTINGS utilise toggle et non present : tester les deux sorties.
 manager,node=0x9307f100,0x9307f200
 sentinel=manager+20;r.w32(sentinel,sentinel);r.w32(view,0x40107a20)
 r.w32(defs['mlp_obj'],0x9307f000)
 def push_settings(args):
  assert args[0]==manager and args[2]==0
  assert r.r32(view+32)==r.r32(view+28)
  r.w32(node,sentinel);r.w32(node+8,view);r.w32(sentinel,node)
  return 1
 r.stubs[syms['ml_settings_native']]=push_settings
 close=r.r32(0x40107a20+40)
 def close_settings(args):
  assert args[0]==view;r.w32(sentinel,sentinel);return 1
 r.stubs[close]=close_settings;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=close,end=close)
 r.call('ml_settings_toggle',manager,ref,1)
 assert r.r32(sentinel)==node and r.r32(defs['mlp_obj'])==0x9307f000
 r.call('ml_settings_toggle',manager,ref,1)
 assert r.r32(sentinel)==sentinel and r.r32(defs['mlp_obj'])==0x9307f000
 r.call('ml_settings_toggle',manager,ref,1);r.call(close,view)
 assert r.r32(sentinel)==sentinel and r.r32(defs['mlp_obj'])==0x9307f000
 r.call('ml_settings_toggle',manager,ref,1)
 assert r.r32(sentinel)==node
 print('ok : chemin toggle SETTINGS empile sans replace ; SETTINGS/Back ferment seulement le menu, B reste actif')
 print('ok : SETTINGS natif conserve B, vecteur restauré ; A et autres menus inchangés')
 # Exécuter maintenant le vrai routeur OS jusqu'à la frontière DIN/USB.
 r.u.hook_del(router_hook);din=[];usb=[]
 for addr,fn in ((0x40001584,lambda args:din.append(bytes(r.u.mem_read(args[1],args[0]))) or 0),(0x40003396,lambda args:usb.append(bytes(r.u.mem_read(args[1],args[0]))) or 0),(0x400032ca,lambda args:0),(0x400032da,lambda args:0)):
  r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
 r.w32(event+12,3)
 r.u.mem_write(syms['mlkc_state']+2,bytes((74,64)));r.delta=1
 for port in (2,3,4):
  din.clear();usb.clear();r.u.mem_write(pat+3,bytes((port,)))
  assert r.call('mlkc_enc',event)==1
  expected=bytes((0xb6,74,64+port-1))
  assert din==([expected] if port in (3,4) else []),(port,din)
  assert usb==([expected] if port in (2,4) else []),(port,usb)
 print('ok : locks existants et déjà en file continuent pendant SETTINGS ; bases provisoires silencieuses')
 print('ok : tour normal potard2 passe le vrai routeur OS vers DIN/USB/BOTH, canal7/CC74/valeur exacts')
 print('ok : potard2 CC0..127 pendant lecture et après release, aucune émission avant usage ; SETTINGS delta0 consommé')
 print('ok : TRIG+potard verrouille sans émission/base modifiée, douze CC, destination figée, même valeur réémise à chaque passage')
 print('ok : queue IRQ sans port physique, huit CC/retrait, mute/canal/Stop invalides filtrés, projet reset libéré')
 print('ok : multi-TRIG, clear, step copy/paste, lane copy/paste/clear/undo ; aucune donnée A modifiée')
 print('Limite : extensions CC RAM uniquement ; non incluses dans les sauvegardes MIDI actuelles')
if __name__=='__main__':main()
