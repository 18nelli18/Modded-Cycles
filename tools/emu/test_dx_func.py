"""v72 : scan natif reproduisant le defaut v71, toggle DX et verrou retrig."""
import sys,struct
from test_fx_menu_control import fixture
STEM=sys.argv[1] if len(sys.argv)>1 else 'validation/all-features-polivoks-cpu-trim-test-v72'

def setup(enabled=1,stem=STEM):
 f=fixture(stem);r,s,h,log,files,key,turn,data,bind=f;notes=[]
 bind(s['fx_notice'],lambda a:notes.append(r.string(a[0])) or 0)
 r.w32(s['dx_enabled'],enabled)
 for name,v in [('gr_diag_blocks',4),('gr_diag_sum',1024),('dx_peak',90100),('dx_over',2),('dx_new',3)]:r.w32(s[name],v)
 return f,notes

def gesture(f,hold=500,gap=100,tap=60):
 key=f[5];key(1);key(1,0,tap);key(1,5,gap);key(1,0,hold)

def native_trace(hold=1000):
 from test_trig_hold import Rig,GRID_KEY
 from test_fx_menu_control import boot,ROOT
 from unicorn import UC_HOOK_CODE
 image,_=boot(ROOT/'output/firmware'/(STEM+'.syx'));panel=Rig(image)
 panel.uc.hook_add(UC_HOOK_CODE,panel._stub(lambda a:0),begin=GRID_KEY,end=GRID_KEY)
 log=panel.run({10:[(1,True)],70:[(1,False)],170:[(1,True)],170+hold:[(1,False)]},hold+250)
 return [(t,code,flags) for t,kind,code,flags in log if code==1]

def replay_native(stem,trace,enabled=1):
 f,notes=setup(enabled,stem);last=0
 for now,code,flags in trace:f[5](code,flags,now-last);last=now
 return notes

def main():
 trace=native_trace();assert any(flags&32 for _,_,flags in trace),trace
 n=replay_native('validation/all-features-polivoks-cpu-trim-test-v71',trace)
 assert not [x for x in n if x.startswith('A')],('v71 should reproduce failure',n)
 print('PASS reproduced v71 cancellation with native panel/hold flags',[(t,hex(flags)) for t,_,flags in trace],flush=True)
 if STEM.endswith('v71'):return
 assert replay_native(STEM,trace)==['A100 P100 O2 N3']
 assert not replay_native(STEM,trace,0)
 for duration in (550,750,1500,3000):assert replay_native(STEM,native_trace(duration))==['A100 P100 O2 N3'],duration
 print('PASS native debounce, event constructor and long-hold repeats: 550ms..3s; DX toggle respected',flush=True)
 for enabled in (0,1):
  f,notes=setup(enabled);gesture(f);assert notes==(['A100 P100 O2 N3'] if enabled else []),notes
  r,s,*_=f
  assert r.r32(s['dx_enabled'])==enabled
  for name,v in [('gr_diag_blocks',4),('gr_diag_sum',1024),('dx_peak',90100),('dx_over',2),('dx_new',3)]:assert r.r32(s[name])==(0 if enabled else v),(name,enabled)
 print('PASS FUNC tap/hold: existing DX toggle gates popup and counter reset; Off preserves counters',flush=True)
 for tap,gap,hold in [(251,100,500),(60,351,500),(60,100,499)]:
  f,n=setup();gesture(f,hold,gap,tap);assert not n,(tap,gap,hold,n)
 for code in [2,4,5,8,9,10,11,12,13,14,15,16,31]:
  f,n=setup();k=f[5];k(1);k(1,0,60);k(1,5,100);k(code);k(code,0,600);k(1,0);assert not [x for x in n if x.startswith('A')],(code,n)
 f,n=setup();k=f[5];k(1);k(1,0,60);k(1,5,100);f[6](14);k(1,0,600);assert not [x for x in n if x.startswith('A')],n
 f,n=setup();k=f[5];k(1);k(1,0,600);assert not n
 f,n=setup();gesture(f,60);assert not n
 f,n=setup();k=f[5];k(1);k(1,0,60);k(1,5,100);k(1,9,600);assert not n;k(1,0);assert n==['A100 P100 O2 N3'],n
 f,n=setup();r,s,*_=f;r.w32(0xfc07000c,0xfffffff0)
 # Le fixture a sa propre horloge ; passer pres du wrap par un grand delai.
 f[5](1,1,31700);f[5](1,0,60);f[5](1,5,100);f[5](1,0,600);assert n==['A100 P100 O2 N3'],n
 print('PASS short/late/single gestures, held-event repeat and cancellation by other buttons/encoders',flush=True)
 for enabled in (0,1):
  f,n=setup(enabled);k=f[5];k(2);k(4);k(4,0,600);k(2,0);assert not [x for x in n if x.startswith('A')],n
 f,n=setup();r,s,h,l,files,k,*_=f;k(2);k(4);k(4,0,80);k(4,1,100);k(4,0);k(2,0);assert r.r32(s['bl_latched']);gesture(f,600);assert r.r32(s['bl_latched']) and n[-1]=='A100 P100 O2 N3',n
 f,n=setup();r,s,*_=f;k=f[5];k(1);k(1,0,60);k(1,5,100);r.w32(s['dx_enabled'],0);k(1,0,600);assert not n and r.r32(s['gr_diag_blocks'])==4
 for code in (2,4,13,16):
  f,n=setup();k=f[5];k(code);gesture(f,600);k(code,0);assert not [x for x in n if x.startswith('A')],(code,n)
 print('PASS old TRACK+RETRIG gesture removed; FUNC diagnostic works without leaving latched retrig; toggle Off mid-gesture cancels',flush=True)
if __name__=='__main__':main()
