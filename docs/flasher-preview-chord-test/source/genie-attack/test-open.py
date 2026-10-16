"""Chemin complet sg_open : registres avant allocation, constructeur et échecs."""
exec(open('work/genie-attack-test/test-native.py').read().split('# Bypass exact')[0])
from test_seq_gen_menu import Rig
from unicorn import m68k_const as m,UC_HOOK_MEM_WRITE
r=Rig(img,{'writes':[]},{'writes':[],'symbols':sg['symbols']},real_ui=True);r.u.mem_write(int(w['append']['dest'],16),build.payload_runtime(w,stock,None));r.w32(0x40fe4178,1)
for fail in [0,1]:
 r.fail_new=fail;r.new_count=0;r.present.clear();r.w32(ss['sg_obj'],0);r.u.reg_write(m.UC_M68K_REG_A4,0x12345678)
 r.call('sg_open');obj=r.r32(ss['sg_obj'])
 if not fail:
  assert obj and r.r32(obj+0x2f00)==s['avg_led_vt']+8
  assert r.call(0x400f4cec,obj,0x401121c0,0x400ff970,0xfffffffe)==obj+0x2f00
  assert r.present
  r.call('sg_render',obj,0x93006000)
  clock=ws['blk_clk'];r.w32(clock,r.r32(clock)+1000)
  led=ws['led_hook'];r.stubs[led]=lambda a:0;r.u.hook_add(__import__('unicorn').UC_HOOK_CODE,r.stub,begin=led,end=led)
  r.call('sg_tick');assert not r.r32(ss['sg_intro']);r.call('sg_render',obj,0x93006000)
 else:assert not obj and not r.present
print('PASS full sg_open with invalid incoming A4, real private RTTI, native renderer, native constructor + intro/tick/menu transition / object allocation failure')
