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
 for off,at,n in ((0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)):r.u.mem_write(at,bytes(r.u.mem_read(0x46700000+off,n)))
bind(0x40000542,lambda a:0);r.u.reg_write(C.UC_M68K_REG_A0,0x931b0000);r.call(m['complete_irq_accounting']['boot_target'] if m.get('complete_irq_accounting') else s['cal_finish'])
for hook in m['control_all_latch']['late_hooks']:assert bytes(r.u.mem_read(hook['at'],6))==b'\x4e\xf9'+struct.pack('>I',hook['target'])
held=set();keys=[];knobs=[];notices=[]
bind(s['cal_old_held'],lambda args:int(args[0] in held));bind(s['fx_notice'],lambda args:notices.append(r.string(args[0])) or 0)
bind(s['cal_old_key'],lambda args:keys.append(tuple(int.from_bytes(r.u.mem_read(args[1]+i*4,4),'big') for i in range(6))) or 73)
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
assert r.call(0x4007faf4,2)==0
# Simple tap : aucun verrou ; les deux evenements natifs sont transmis.
tap();assert not r.r32(s['cal_latched']);assert keys[-2][3:5]==(2,1) and keys[-1][3:5]==(2,16)
# Deuxieme tap ferme aussi la vue native avant activation.
tap();assert r.r32(s['cal_latched']);assert keys[-1][3:5]==(2,16);assert r.call(0x4007faf4,2)==0
assert turn(4)==1;assert r.call(0x4007faf4,2)==0;assert not r.r32(s['cal_scope'])
for knob in (1,14,15):assert turn(knob)==0
r.w32(m['fx_menu']['symbols']['menu'],1);assert turn()==0;r.w32(m['fx_menu']['symbols']['menu'],0)
for mod in (5,13):held.add(mod);assert turn()==0;held.remove(mod)
# Pas de TRACK virtuel lors d'un trig, transport ou BACK ; BACK consomme sa paire.
n=len(keys);event(16);event(16,16);assert len(keys)==n+2 and not held;assert r.call(0x4007faf4,2)==0
n=len(keys);event(12);assert not r.r32(s['cal_latched']);event(12,16);assert len(keys)==n
latch();n=len(keys);event(2);event(2,16);assert not r.r32(s['cal_latched']) and len(keys)==n
# Interruption par autre touche ou encodeur, taps longs/lents, repeats.
tap();event(3);event(3,16);tap();assert not r.r32(s['cal_latched']);event(12);event(12,16)
tap(60000000);tap(60000000);assert not r.r32(s['cal_latched'])
event(2,1,60000000);event(2,16,60000000);tap();assert not r.r32(s['cal_latched'])
event(2,1,60000000);turn();event(2,16);tap();assert not r.r32(s['cal_latched'])
event(2,1,60000000);event(2,9);event(2,16);assert not r.r32(s['cal_latched'])
tap(60000000);event(2);event(2,9);event(2,16);assert not r.r32(s['cal_latched'])
# TRACK+PAGE reste un accord physique transmis et ne peut armer le double tap.
event(2,1,60000000);event(8);event(8,16);event(2,16);tap();assert not r.r32(s['cal_latched'])
# Comparaison non signee du timer autour du wrap.
event(3);event(3,16);tick=0xffe00000;tap();tap();assert r.r32(s['cal_latched']);event(12);event(12,16)
print('PASS native installed latch hooks: clean taps, exits, physical releases, encoder-only TRACK, menus/modifiers, chords, repeats and timer wrap',flush=True)
a.output.write_text(json.dumps(dict(ui_only=True,physical_track_releases_preserved=True,encoder_scope_only=True,hardware_tested=False,notices=notices),indent=2)+'\n',encoding='utf-8')
