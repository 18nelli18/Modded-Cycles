"""DX3.00 : historique des six pistes, trois pages, DATA et cout IRQ borne."""
from pathlib import Path
src=Path(__file__).with_name('test_cpu_monitor.py').read_text()
exec(compile(src,__file__,'exec'))
s=m['cpu_monitor']['symbols'];al=m['cpu_monitor']['aliases'];dx=al['dx_enabled'];r.w32(dx,1);chord();assert r.r32(s['cpu_page'])==0
for expected in (1,2,0):tap(15);assert r.r32(s['cpu_page'])==expected
r.call(s['cpu_reset']);pending=[0];native_calls=[]
def govern(args):
 native_calls.append(1);r.u.mem_write(0x46732058,bytes(int(bool(pending[0]&(1<<t))) for t in range(6)));return 0
bind(al['cpu_govern'],govern)
tracks=[0,3,1,5,4,2,0,3]
for i,t in enumerate(tracks):
 r.u.mem_write(0x46732058,bytes(6));pending[0]=1<<t;r.w32(0x46732f10,(200+i*3)*8);r.w32(0x46732f14,(210+i*2)*256);r.w32(0x4673207c,240+i);r.call(s['cpu_audio_end'])
assert r.r32(s['cut_count'])==6
r.call(s['cpu_snapshot']);history=[r.r32(s['cut_snap']+12*i) for i in range(6)];assert history==[t+1 for t in reversed(tracks[-6:])],history
assert [r.r32(al['dt_cuts']+4*t) for t in range(6)]==[2,1,1,2,1,1]
texts=[];formatter=r.stubs[0x40000e6e]
def observe(args):
 v=formatter(args);texts.append(r.string(args[0]));return v
bind(0x40000e6e,observe)
for page in range(3):
 r.w32(s['cpu_page'],page);r.call(s['cpu_snapshot']);r.call(s['cpu_stack'],0,canvas)
 if page==0:assert any(x.startswith('LAST T4 ') for x in texts),texts
 if page==1:assert len([x for x in texts if x.startswith('T') and '  S' in x])==5,texts
from render_midi_bank import png
# Une derniere coupe surT1 reste loggee meme si son total est deja99.
r.w32(al['dt_cuts'],99);r.u.mem_write(0x46732058,bytes(6));pending[0]=1;r.call(s['cpu_audio_end']);r.call(s['cpu_snapshot']);assert r.r32(s['cut_snap'])==1 and r.r32(al['dt_cuts'])==99
for page,label in [(0,'cpu-load'),(1,'recent-cuts'),(2,'track-totals')]:
 r.w32(s['cpu_page'],page);r.call(s['cpu_snapshot']);r.call(s['cpu_stack'],0,canvas);raw=bytes(r.u.mem_read(fb,1024));pixels=[0 if int.from_bytes(raw[(x*2+(63-y)//32)*4:(x*2+(63-y)//32)*4+4],'big')&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];png(a.output.parent/(label+'.png'),pixels)
n=len(native_calls);r.w32(dx,0);r.u.mem_write(0x46732058,bytes(6));pending[0]=2;count=r.r32(s['cut_count']);r.call(s['cpu_audio_end']);assert len(native_calls)==n+1 and r.r32(s['cut_count'])==count
r.w32(dx,1);tap(32);assert r.r32(s['cut_count'])==r.r32(s['cut_snap_count'])==0 and not any(r.u.mem_read(al['dt_cuts'],24))
a.output.write_text(json.dumps(dict(native_controls=True,global_dx_gated=True,pages=['CPU Load','Recent Cuts','Track Totals'],all_tracks_recorded=True,history_capacity=6,newest_first=True,saturated_totals_still_log=True,data_clears_history_and_totals=True,screen_width_checked=True,hardware_tested=False),indent=2)+'\n')
print('PASS generic cut history, all six tracks, wrap/order, three pages, saturated counters, DX gate and DATA clear')
