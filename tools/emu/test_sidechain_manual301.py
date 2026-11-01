"""Sidechain301 : jeu live mute, sequence, solo, enveloppes et retours stereo."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
from unicorn import UC_HOOK_CODE
u=r.u;sy=m['sidechain']['symbols'];fixed='sidechain_manual301' in m
if not any(lo<=0x80000000<=hi for lo,hi,flags in u.mem_regions()):u.mem_map(0x80000000,0x20000)
side=0x931c0000;ons=side+1024
r.w32(sy['br_side'],side);r.w32(sy['br_side_on'],ons);u.mem_write(ons,struct.pack('>6I',*([1]*6)))
bind(sy['du_native_voice'],lambda args:0)
if fixed:
 for hook in m['sidechain_manual301']['hooks']:assert bytes(u.mem_read(hook['at'],6))==b'\x4e\xf9'+struct.pack('>I',hook['target'])
def setup(source,target,follow,mute,solo,playing=1):
 cfg=[0,9,0,0,6]*6;cfg[source*5:source*5+5]=[(1<<target)|(64 if follow else 0),15,0,1,0]
 u.mem_write(sy['du_config'],bytes(cfg));u.mem_write(sy['du_fx'],bytes(1 if t==source else 0 for t in range(6)));r.w32(sy['initialized'],0);r.call(sy['du_reset'])
 for at,value in [(0x800017ac,mute),(0x800017b0,solo),(0x40a78874,playing),(0x40a7883c,0)]:r.w32(at,value)
def fill():
 for t in range(6):u.mem_write(0x80001858+t*128,struct.pack('>32i',*([400000000]*32)));u.mem_write(side+t*128,struct.pack('>32i',*([-200000000]*32)))
def lane(t,base=0x80001858):return struct.unpack('>32i',bytes(u.mem_read(base+t*128,128)))
def note(source,kind):
 words=[0,1,source,kind]+[0]*20;words[10]=513;u.mem_write(EVENT,struct.pack('>24I',*words));r.call(sy['du_note'],EVENT)
def process():fill();r.call(sy['du_process'])
def live(source):r.call(sy['du_voice_hook'],0x80001858,0x8000100c,1<<source,0)
setup(4,5,True,16,0);live(4);process();assert (lane(5)[-1]<10000)==fixed
print('PASS reported T5 -> T6 reproduction:', 'corrected' if fixed else 'bug confirmed',flush=True)
if not fixed:
 a.output.write_text(json.dumps(dict(bug_reproduced=True,muted_live_suppressed=True,source=m['sha256']))+'\n');sys.exit(0)
cases=0
for source in range(6):
 target=(source+1)%6
 for follow in (False,True):
  for mute,solo,blocked in [(0,0,False),(1<<source,0,True),(0,1<<target,True),(1<<source,1<<source,False)]:
   for playing in (0,1):
    for kind in ('sequence','pad','live-note'):
     setup(source,target,follow,mute,solo,playing)
     if kind=='pad':live(source)
     else:note(source,1 if kind=='sequence' else 0)
     process();duck=kind!='sequence' or not(follow and blocked)
     assert (lane(target)[-1]<10000)==duck,(source,follow,mute,solo,playing,kind,lane(target)[-1])
     assert (lane(target,side)[-1]>-10000)==duck
     assert all(lane(t)==(400000000,)*32 for t in range(6) if t!=target)
     wet=0x80008000;u.mem_write(wet,struct.pack('>64i',*([400000000,-200000000]*32)));r.call(sy['du_return'],wet,0)
     assert (struct.unpack('>64i',bytes(u.mem_read(wet,256)))[-2]<10000)==duck
     cases+=1
# Une suite de pulses sequence mutes ne doit ni couper ni prolonger le live.
setup(4,5,True,16,0);live(4);process();curve=[]
for b in range(90):note(4,1);process();curve.append(lane(5)[-1])
assert min(curve[:20])<10000 and curve[25]<400000000 and curve[60:]==[400000000]*30
# Retrig live pendant une queue, puis effacement lors du changement de pattern.
live(4);process();assert lane(5)[-1]<10000
r.call(sy['du_reset']);process();assert lane(5)[-1]==400000000
# Note-off, event invalide : aucun pulse.
setup(4,5,True,16,0)
for words in ([0,0,4,0]+[0]*20,[0,1,6,0]+[0]*20,[0,1,4,0xffffffff]+[0]*20):
 u.mem_write(EVENT,struct.pack('>24I',*words));r.call(sy['du_note'],EVENT);process();assert lane(5)==(400000000,)*32
# Bypass desactive : PCM intact et cout borne.
u.mem_write(sy['du_config'],bytes([0,9,0,0,6]*6));u.mem_write(sy['du_fx'],bytes(6));r.w32(sy['initialized'],0);r.call(sy['du_reset']);fill();before=bytes(u.mem_read(0x80001858,768));count=[0]
hook=u.hook_add(UC_HOOK_CODE,lambda *args:count.__setitem__(0,count[0]+1));r.call(sy['du_process']);u.hook_del(hook)
assert bytes(u.mem_read(0x80001858,768))==before and count[0]<50,count
print('PASS',cases,'source/policy/mute/solo/transport/input cases; stereo+FX, complete live tail, no ghost retrigger, reset, disabled bypass',count[0],flush=True)
a.output.write_text(json.dumps(dict(cases=cases,real_native_voice_hook=True,stereo=True,fx_return=True,live_tail_survives_muted_sequence=True,muted_sequence_does_not_retrigger=True,pattern_reset_clears_live=True,disabled_instructions=count[0],source=m['sha256'],hardware_tested=False),indent=2)+'\n')
