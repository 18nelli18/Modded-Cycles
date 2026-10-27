"""Commande native complete, publication des cinq champs puis prochain bloc audio."""
from pathlib import Path
import sys,struct
v=sys.argv[1] if len(sys.argv)>1 else 'v189'
if len(sys.argv)==1:sys.argv.append(v)
exec(Path(__file__).with_name('test_lfo_clear189_fixture.py').read_text().split('seedall();before=')[0])
frame=0x8000100c
events=[]
def notify_fields(args):
 track=(args[0]-handle(0))//68;event=args[1]
 if '--debug' in sys.argv:print('notify',track,hex(event),bytes(u.mem_read(event,8)).hex() if event else '-')
 if event and r.r32(event)==0x400fd0ac:
  slot=r.r32(event+4)
  if 28<=slot<=32:
   u.mem_write(frame+70+66*track+2*(slot-28),bytes(u.mem_read(raw(track)+20+2*slot,2)))
   events.append((track,slot))
 return 0
bind(notify,notify_fields)
u.mem_write(data+0x58000,b'CLEARED\0')
for track in range(6):
 seedall()
 for t in range(6):u.mem_write(frame+70+66*t,bytes(u.mem_read(raw(t)+76,10)))
 before=[allstate(t) for t in range(6)];events.clear()
 assert r.call(0x400149fa,handle(track),24,data+0x58000,1,0)==1
 assert allstate(track)==(primary,secondary,secondary,secondary,0,0,0,0)
 assert sorted(events)==[(track,i) for i in range(28,33)],events
 assert all(allstate(t)==before[t] for t in range(6) if t!=track)
 # Le vrai synchroniseur recharge les donnees de la frame, comme au bloc suivant.
 r.call(a['lf2n_sync'],ctx,frame)
 # La polarite est encodee dans l'octet bas du multiplicateur natif.
 expected=secondary[:3]+b'\xa0'+secondary[4:]
 assert bytes(u.mem_read(settings(track),16))==expected,bytes(u.mem_read(settings(track),16)).hex()
 assert r.call(0x40014b06,handle(track),track,1)==1
 restored=allstate(track)
 assert restored[:4]==before[track][:4] and restored[6:]==before[track][6:],('Undo',track,restored,before[track])
 assert [r.call(s['lp_sound_get'],track,b) for b in range(2)]==[1,1]
print('PASS full native sound-clear command on six tracks, five field notifications, next audio sync and four-bank native Undo',flush=True)
seedall();before=[allstate(t) for t in range(6)]
seen=[];bind(mx['mx_old_pattern_clear'],lambda args:seen.append(tuple(args[:6])) or 1)
assert r.call(mx['mx_clear_pattern'],root,0,1,0,1,1)==1
assert [allstate(t) for t in range(6)]==before
events.clear();assert r.call(mx['mx_clear_pattern'],root,0,1,1,1,1)==1
r.call(a['lf2n_sync'],ctx,frame)
for t in range(6):
 state=allstate(t);assert state[0]==primary and state[1]==expected and state[2:]==(secondary,secondary,0,0,0,0),(t,state)
assert len(events)==30
print('PASS active pattern clear publishes all six tracks; sequence-only clear preserves LFOs',flush=True)
assert bytes(u.mem_read(0x40014aa0,6))==bytes.fromhex('4eb940061866')
assert bytes(u.mem_read(0x400149fa,6))==bytes.fromhex('4ef9')+struct.pack('>I',mx['mx_clear_command'])
print('PASS generic initializer unchanged; post-command reset runs after native notifications',flush=True)
