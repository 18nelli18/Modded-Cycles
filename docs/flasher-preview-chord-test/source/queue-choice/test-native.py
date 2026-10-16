"""Menu réel et commit natif page/boucle, sans API UI dans l'interruption."""
import json,struct
from unicorn import m68k_const as m
from test_seq_gen_queue import setup,boundary,PAT
from test_seq_gen_menu import Rig,RAW
from chord_keys_pr87 import load_stock
import build
stock=load_stock('firmware/model-cycles_OS1.13.syx');sg=json.load(open('work/genie-queue-choice/recipes.json'))['wizard'];base=json.load(open('work/sample-wizard-options/case-pair-scale-gen.json'))['tweaks'][0]
r=Rig(stock,base,sg);r.call('sg_open');r.w32(r.s['sg_intro'],0)
order=[20,19]+list(range(19))+[21]
for row,val in enumerate(order):
 r.u.reg_write(m.UC_M68K_REG_D0,row);assert r.call('sg_map_row')==val
 r.u.reg_write(m.UC_M68K_REG_D0,val);assert r.call('sg_unmap_row')==row
r.w32(r.s['sg_row'],1);r.call('sg_render',r.r32(r.s['sg_obj']),0x93006000);print('MENU',r.texts)
assert any(t[2]=='Queue at' for t in r.texts);assert any(t[2]=='Loop' for t in r.texts)
r.click();r.knob(1);assert r.r32(r.s['avq_mode'])==1;r.texts.clear();r.call('sg_render',r.r32(r.s['sg_obj']),0x93006000);assert any(t[2]=='Page' for t in r.texts)
r.knob(1);assert r.r32(r.s['avq_mode'])==1;r.knob(-1);assert r.r32(r.s['avq_mode'])==0;r.click()
for length in [16,20,32,48,64]:
 for mode in [0,1]:
  for step in [0,1,15,16,17,31,32,47,48,63]:
   if step>=length:continue
   r=setup(stock,base,sg,length=length);r.call('sg_open');r.w32(r.s['avq_mode'],mode);r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1
   boundary(r,step=step,phase=1);assert r.r32(r.s['sg_q_state'])==1
   boundary(r,step=step,phase=0);expected=2 if step==0 or mode==1 and step%16==0 else 1
   assert r.r32(r.s['sg_q_state'])==expected,(length,mode,step,r.r32(r.s['sg_q_state']))
print('PASS 22 menu rows, Generate first / Queue at second, Loop default, DATA bounds and labels; 16/20/32/48/64-step playback page/loop boundaries, prefetch phases, registers/SR preserved.')
