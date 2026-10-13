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
 names=('knob_cc','knob_cc_ui','knob_cc_scroll','knob_cc_locks','knob_cc_lock_patterns','knob_cc_lock_edit','knob_cc_lock_queue','knob_cc_lock_clip','lfo_cc_names')
 defs={k:0x9306a000+i*4 for i,k in enumerate(('TG_set_held','TG_mod_used','TG_blk_clk','mlp_track','mlp_step','mlp_held','mlp_changed','ml_pattern','ml_play_pattern','ml_clock_state','mlp_obj'))}
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
 pat,event,clock=0x93070000,0x93074000,0x93076000
 for lane in range(6):r.u.mem_write(pat+lane*264,bytes((1,0,6+lane,4,64,2,0,0))+bytes(256))
 for name,value in (('ml_pattern',pat),('ml_play_pattern',pat),('ml_clock_state',clock),('mlp_track',0),('mlp_step',19),('mlp_held',8)):
  r.w32(defs[name],value)
 r.w32(clock,1);r.w32(0x40fe4228,1);r.w32(event+12,2)
 sent=[]
 def send(args):sent.append(bytes(r.u.mem_read(args[1],3)));assert args[0]==3 and args[2]==4;return 0
 r.stubs[0x400826b0]=send;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
 r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 r.delta=5;assert r.call('mlkc_enc',event)==1 and not sent
 assert r.u.mem_read(syms['mlkc_state'],2)==bytes((74,64))
 locks=r.call('mlkc_locks_for',pat,0);assert locks
 assert r.call('mlkc_lock_get',locks,0,19,0)==0x4a45
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2700);r.call('mlkcq_step',pat,0,19);assert not sent
 r.u.reg_write(mk.UC_M68K_REG_SR,0x2000);assert r.call('mlkcq_ready')==1
 r.call('mlkcq_worker');assert sent==[b'\xb6\x4a\x45']
 r.u.mem_write(syms['mlkc_state'],bytes((71,64)))
 r.call('mlkcq_step',pat,0,19);r.call('mlkcq_worker');assert sent[-1]==b'\xb6\x4a\x45' and len(sent)==2
 r.call('mlkcq_step',pat,0,19);r.u.mem_write(pat+1,b'\x01');r.call('mlkcq_worker');assert len(sent)==2
 r.u.mem_write(pat+1,b'\x00');r.call('mlkcq_step',pat,0,19);r.u.mem_write(pat+2,b'\x00');r.call('mlkcq_worker');assert len(sent)==2
 r.u.mem_write(pat+2,b'\x06');r.u.mem_write(syms['mlkc_state'],bytes((74,64)))
 r.w32(defs['mlp_held'],8|128);r.delta=5;r.call('mlkc_enc',event)
 assert r.call('mlkc_lock_get',locks,0,19,0)==0x4a4a and r.call('mlkc_lock_get',locks,0,23,0)==0x4a4a
 r.call('mlkc_clear_selected');assert r.call('mlkc_lock_get',locks,0,19,0)==65535
 assert r.call('mlkc_lock_get',locks,0,23,0)==0x4a4a
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
 r.call('mlkcq_reset');sent.clear()
 for knob in range(12):assert r.call('mlkc_lock_set',locks,0,7,knob,knob,100)==1
 r.call('mlkcq_step',pat,0,7);r.call('mlkcq_worker');assert len(sent)==8
 r.call('mlkcq_worker');assert len(sent)==12
 r.call('mlkcq_step',pat,0,7);r.w32(clock,0);r.call('mlkcq_worker');assert len(sent)==12 and r.call('mlkcq_ready')==0
 freed=[];r.stubs[0x400802ec]=lambda args:freed.append(args[0]) or 0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
 r.call('mlkc_locks_reset');assert r.call('mlkc_locks_for',pat,0)==0 and locks in freed
 print('ok : TRIG+potard verrouille sans émission/base modifiée, douze CC, destination figée, même valeur réémise à chaque passage')
 print('ok : queue IRQ sans port physique, huit CC/retrait, mute/canal/Stop invalides filtrés, projet reset libéré')
 print('ok : multi-TRIG, clear, step copy/paste, lane copy/paste/clear/undo ; aucune donnée A modifiée')
 print('Limite : extensions CC RAM uniquement ; non incluses dans les sauvegardes MIDI actuelles')
if __name__=='__main__':main()
