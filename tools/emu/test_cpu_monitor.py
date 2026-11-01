"""Moniteur DX : controles natifs, gate global, reset/page et BACK non colle."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
d=m['cpu_monitor'];s=d['symbols'];al=d['aliases'];dx=al['dx_enabled'];cal=m['control_all_latch']['symbols']
for h in d['late_hooks']:assert bytes(r.u.mem_read(h['at'],6))==b'\x4e\xf9'+struct.pack('>I',h['target']),(h,bytes(r.u.mem_read(h['at'],6)).hex())
r.w32(0x40fe4178,0x931b7000)
held=set();keys=[];knobs=[];frames=[];stacks=[];paints=[]
bind(cal['cal_old_held'],lambda args:int(args[0] in held))
bind(al['cpu_old_key'],lambda args:keys.append(tuple(struct.unpack('>6I',r.u.mem_read(args[1],24)))) or 73)
bind(al['cpu_old_encoder'],lambda args:knobs.append(tuple(struct.unpack('>6I',r.u.mem_read(args[1],24)))) or 79)
bind(al['cpu_old_frame'],lambda args:frames.append(1) or 0);bind(al['cpu_old_stack'],lambda args:stacks.append(1) or 88)
bind(0x40076bee,lambda args:paints.append(1) or 0)
entry=m['acid_articulation']['symbols']['aa_face_key'];encoder=m['acid_articulation']['symbols']['aa_face_encoder'];tick=100000000
used=0x931b1800;r.w32(al['wf_api']+20,used);r.w32(used,0)
def event(code,flags=1,dt=1000000):
 global tick
 tick=(tick+dt)&0xffffffff;r.w32(0xfc07000c,tick)
 if flags&1:held.add(code)
 else:held.discard(code)
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbe5c,0,tick,code,flags,0));return r.call(entry,0,EVENT)
def tap(code,dt=1000000):event(code,1,dt);event(code,16)
def chord():event(13);tap(12);event(13,16)
def turn(knob):
 r.u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,tick,knob,1,0));return r.call(encoder,0,EVENT)
# DX off : accord entier natif, aucun changement de permission globale.
r.w32(dx,0);chord();assert not r.r32(s['cpu_open']) and not r.r32(dx);assert [x[3] for x in keys[-4:]]==[13,12,12,13]
r.w32(dx,1);chord();assert r.r32(s['cpu_open']) and r.r32(used)==1 and not held
# Toutes les rotations et le transport sont transmis sans transformation.
for knob in range(1,16):assert turn(knob)==79 and knobs[-1][3]==knob
for code in (10,11,16,21,2,13):
 n=len(keys);tap(code);assert len(keys)==n+2 and [x[3] for x in keys[-2:]]==[code,code]
assert r.r32(s['cpu_open'])
# Snapshot et deux pages : tout tient sur le vrai framebuffer.
import re
from render_midi_bank import png
def formatter(args):
 dest,fmt=args[:2];fmt=r.string(fmt);vals=[]
 for index,match in enumerate(re.finditer(r'%[-0-9]*([usdx])',fmt)):
  raw=args[index+2];vals.append(r.string(raw) if match[1]=='s' else raw)
 text=fmt%tuple(vals);assert len(text)<=21,(fmt,text);r.u.mem_write(dest,text.encode()+b'\0');return len(text)
bind(0x40000e6e,formatter)
for k,v in dict(gb_last_total=90112,gb_peak=97321,gb_over=4,gb_sum=21500,gb_blocks=100,dx_new=11,dt_t5_s=215,dt_t5_l=256).items():r.w32(al[k],v)
r.w32(0x46732f10,215*8);r.w32(0x46732f14,215*256)
for t,n in enumerate((1,0,2,7,1,0)):r.w32(al['dt_cuts']+t*4,n)
r.call(s['cpu_snapshot']);canvas,fb=0x931d0000,0x931d1000;r.w32(canvas+16,fb)
for page in (0,1):
 assert r.r32(s['cpu_page'])==page;r.call(s['cpu_stack'],0,canvas)
 raw=bytes(r.u.mem_read(fb,1024));pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)]
 png(a.output.parent/('load.png' if not page else 'tracks.png'),pixels)
 if not page:
  n=len(keys);tap(15);assert len(keys)==n
# Un popup/encodeur natif ne remplace pas l overlay ; cache conserve entre polls.
raw=bytes(r.u.mem_read(fb,1024));r.u.mem_write(fb,b'\xff'*1024);turn(4);r.call(s['cpu_stack'],0,canvas);assert bytes(r.u.mem_read(fb,1024))==raw
# DATA seul efface les compteurs ; les rotations DATA restent natives.
old_s=bytes(r.u.mem_read(0x46732f10,8));n=len(keys);tap(32);assert len(keys)==n and not r.r32(al['gb_over']) and not r.r32(al['dx_new']) and not any(r.u.mem_read(al['dt_cuts'],24));assert bytes(r.u.mem_read(0x46732f10,8))==old_s
assert turn(1)==79
# Repaint4Hz : ne poller qu apres250ms ; un frame passe toujours au parent.
base=len(paints);r.w32(s['stamp'],100);r.w32(0xfc07000c,101);r.call(s['cpu_frame']);assert len(paints)==base
r.w32(0xfc07000c,33792100);r.call(s['cpu_frame']);assert len(paints)==base+1 and len(frames)==2,(base,len(paints),len(frames),r.r32(0x40fe4178),r.r32(s['cpu_open']),r.r32(s['stamp']))
# BACK simple natif, second tap consomme et ferme seulement le moniteur.
n=len(keys);tap(12);assert r.r32(s['cpu_open']) and len(keys)==n+2
r.w32(al['cal_back_armed'],1);tap(12);assert not r.r32(s['cpu_open']) and len(keys)==n+2 and not r.r32(al['cal_back_armed'])
chord();tap(12);turn(4);tap(12);assert r.r32(s['cpu_open'])
# Hold/repeat/accord/timeout ne ferment pas par double tap.
turn(1);event(12,1,60000000);event(12,16,60000000);tap(12);assert r.r32(s['cpu_open'])
turn(1);event(12);event(12,9);event(12,16);tap(12);assert r.r32(s['cpu_open'])
turn(1);tap(12);tap(12,60000000);assert r.r32(s['cpu_open'])
turn(1);tap(12);tap(16);tap(12);assert r.r32(s['cpu_open'])
# Wrap timer non signe ; le chord d acces ferme egalement.
turn(1);tick=0xffe00000;tap(12);tap(12);assert not r.r32(s['cpu_open'])
chord();assert r.r32(s['cpu_open']);chord();assert not r.r32(s['cpu_open']) and not held
# DX off ferme la page et rend toutes les touches au natif.
chord();assert r.r32(s['cpu_open']);r.w32(dx,0);r.call(s['cpu_frame']);assert not r.r32(s['cpu_open']);n=len(keys);tap(15);tap(32);assert len(keys)==n+4
assert r.call(s['cpu_stack'],0,canvas)==88
# Ancien geste FUNC devenu no-op, aucune notification residuelle.
for flags in (1,16,1,16):r.u.mem_write(EVENT,struct.pack('>6I',0,0,0,1,flags,0));r.call(m['fx_menu']['symbols']['fx_diag_gesture'],EVENT)
a.output.write_text(json.dumps(dict(native_controls=True,global_dx_gated=True,legacy_popup_removed=True,page_reset_and_release_pairs=True,back_undo_double_exit=True,screen_width_checked=True,refresh_hz=4,hardware_tested=False),indent=2)+'\n')
print('PASS CPU monitor: DX gating, native knobs/transport, DATA clear/PAGE switch, BACK undo/double exit, ownership, wrap, polling and LCD cache')
