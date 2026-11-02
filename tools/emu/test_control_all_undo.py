"""Geste UI natif et TRACK virtuel borne a la delegation encodeur."""
from pathlib import Path
import argparse,inspect,json,struct,sys
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True)
import boot_candidate as bc
import test_fx_menu_control as fx
from test_seq_gen_menu import EVENT
from unicorn import m68k_const as C
m=json.loads((a.build/'BUILD.json').read_text());s=m['control_all_latch']['symbols'];al=m['direct_jump']['aliases']
bc.ROOT=a.output.parent/'ui-cache';fx.metadata=m;fx.boot=lambda path:bc.boot(next(a.build.glob('*.syx')))
src=inspect.getsource(fx.fixture).replace("m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())",'m=metadata');exec(src,fx.__dict__)
r,_,h,log,files,key,turn,data,bind=fx.fixture('unused')
if m.get('bounded_burst_policy') or m.get('governor_key_optimization'):
 r.u.mem_map(0x80000000,0x20000)
 if m.get('clean_layout'):r.u.mem_write(0x80000000,bc.clean_sram(bc.load(next(a.build.glob('*.syx')))))
 else:
  for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,bytes(r.u.mem_read(0x46700000+off,n)))
bind(0x40000542,lambda a:0);r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000)
if not m.get('clean_layout'):r.call(m['complete_irq_accounting']['boot_target'] if m.get('complete_irq_accounting') else s['cal_finish'])
for hook in m['control_all_latch']['late_hooks']:assert bytes(r.u.mem_read(hook['at'],6))==b'\x4e\xf9'+struct.pack('>I',hook['target'])
if m.get('cpu_monitor'):r.w32(m['fx_menu']['symbols']['dx_enabled'],0)
held=set();keys=[];knobs=[];notices=[];scopes=[]
bind(s['cal_old_held'],lambda args:int(args[0] in held));bind(s['fx_notice'],lambda args:notices.append(r.string(args[0])) or 0)
bind(s['cal_old_key'],lambda args:scopes.append(r.r32(s['cal_scope'])) or keys.append(tuple(int.from_bytes(r.u.mem_read(args[1]+i*4,4),'big') for i in range(6))) or 73)
# Delegue assemble de test : interroger le vrai getter patche dans le meme appel.
probe=0x931b1000
r.u.mem_write(probe,bytes.fromhex('2f3c000000024eb94007faf4588f23c0931b1100704f4e75'))
r.u.mem_write(s['cal_old_encoder'],b'\x4e\xf9'+struct.pack('>I',probe))
tick=100000000
entry=m['acid_articulation']['symbols']['aa_face_key'];encoder=m['acid_articulation']['symbols']['aa_face_encoder']
def event(code,flags=1,dt=1000000):
 global tick
 tick=(tick+dt)&0xffffffff;r.w32(0xfc07000c,tick)
 if flags&1:held.add(code)
 else:held.discard(code)
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbe5c,0,tick,code,flags,0));return r.call(entry,0,EVENT)
def tap(dt=1000000):event(2,1,dt);event(2,16)
def turn(knob=4,kind=0x400fbebc):
 r.u.mem_write(EVENT,struct.pack('>6I',kind,0,tick,knob,1,0));r.w32(0x931b1100,99);result=r.call(encoder,0,EVENT);assert result==79;return r.r32(0x931b1100)
def latch():
 tap();tap();assert r.r32(s['cal_latched'])==1

def back(dt=1000000):event(12,1,dt);event(12,16)
def active():assert r.r32(s['cal_latched'])==1 and not r.r32(s['cal_scope']) and r.call(0x4007faf4,2)==0
latch();active();assert turn()==1
n=len(keys);back();active();assert len(keys)==n+2 and scopes[-2:]==[1,1]
back();assert not r.r32(s['cal_latched']) and len(keys)==n+2
latch();back();back(60000000);active()
turn();back();active();turn();back();active()
event(12,1,60000000);event(12,16,60000000);back();active()
turn();event(12);event(12,9);event(12,16);back();active()
turn();back();event(16);event(16,16);back();active();assert scopes[-3]==0
turn();r.w32(m['fx_menu']['symbols']['menu'],1);back();back();active();assert scopes[-2:]==[0,0];r.w32(m['fx_menu']['symbols']['menu'],0)
held.add(5);back();back();active();assert scopes[-2:]==[0,0];held.remove(5)
turn();back();back();assert not r.r32(s['cal_latched'])
latch();n=len(keys);tap();assert not r.r32(s['cal_latched']) and len(keys)==n
latch();turn();tick=0xffe00000;back();back();assert not r.r32(s['cal_latched'])
a.output.write_text(json.dumps(dict(native_back_forwarded=True,back_scope_balanced=True,double_back_consumes_second_pair=True,menu_modifier_repeat_hold_timeout_knob_chord_wrap=True,hardware_tested=False),indent=2)+'\n')
print('PASS native BACK delegation, scoped CTRL-ALL, double-BACK exit, TRACK exit and gesture edge cases')
