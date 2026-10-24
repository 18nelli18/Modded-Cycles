"""Reverb PS1 inspiree : vrai C ColdFire, bus natif, popups et sauvegarde."""
import json,struct,math,sys,hashlib
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_vinyl_dust import rig,IN,OUT,wav
from test_fx_menu_control import fixture as ui_fixture
from test_fx_menu_audio import fixture,configure,run
from boot_candidate import ROOT
from test_junior_integration import parts
STEM=sys.argv[1] if len(sys.argv)>1 else 'validation/all-features-polivoks-cpu-trim-test-v70'
VERSION=STEM.rsplit('-',1)[-1]
META=json.loads((ROOT/'output/firmware'/(STEM+'.json')).read_text())
OLD='v68' if META['fx_menu']['cloud'] else 'v66'

def render(size,tone,blocks=6000):
 r,s,m=rig(STEM);r.call('fx_ps1_reset');r.u.mem_write(IN+1024,struct.pack('>hh',size*256,tone*256));audio=[]
 for b in range(blocks):
  sig=[]
  for i in range(32):
   t=(b*32+i)/48000;v=.10*sum(math.sin(2*math.pi*f*t) for f in (220,277.18,329.63))*max(0,1-t/.08) if t<.08 else 0
   sig.extend([int(v*2147483647)]*2)
  r.u.mem_write(IN,struct.pack('>64i',*sig));r.call('fx_ps1',OUT,IN,IN+1024);audio.extend(struct.unpack('>64i',r.u.mem_read(OUT,256)))
 return np.array(audio).reshape(-1,2).astype(float)/2147483648,audio,r,s

def main():
 report={};renders={}
 for size,tone in ((20,64),(100,64),(100,0),(100,127)):
  y,a,r,s=render(size,tone);renders[size,tone]=y
  assert .0001<np.max(abs(y))<.5 and np.any(y[10000:])
  assert not np.array_equal(y[:,0],y[:,1]);assert abs(y.mean())<.001
  if (size,tone)==(100,64):
   wav(ROOT/'output/firmware/validation/ps1-v69-chord-wet.wav',a)
   r.call('fx_ps1_reset');r.u.mem_write(IN,bytes(256))
   for _ in range(150):r.call('fx_ps1',OUT,IN,IN+1024);assert not any(r.u.mem_read(OUT,256))
  print('PASS PS1 bounded stereo decay',size,'tone',tone,flush=True)
 late=lambda y:float(np.sum(y[48000:96000]**2))
 assert late(renders[100,64])>late(renders[20,64])*3
 spectra={}
 for tone in (0,127):
  y=renders[100,tone][8000:,0];p=abs(np.fft.rfft(y))**2;hz=np.fft.rfftfreq(len(y),1/48000);spectra[tone]=float(p[hz>1000].sum()/p.sum())
 assert spectra[127]>spectra[0],spectra
 # Le DSP complet execute le vrai mixeur et les vrais sends. Send0 = dry exact.
 old=STEM.rsplit('-',1)[0]+'-'+OLD
 for rev in range(7):
  fs=[fixture(old,0),fixture(STEM,0)]
  for f in fs:configure(f,rev,[100,0,0,0,0,0],70,0)
  for _ in range(3):
   x,y=[run(f,1) for f in fs];assert x['post']==y['post'],('legacy reverb',rev)
 for send in (0,127):
  a,b=fixture(STEM,0),fixture(STEM,1);configure(a,0,[0]*6);configure(b,7,[send,0,0,0,0,0]);x,y=[run(f,3) for f in (a,b)]
  if not send:assert x['post']==y['post'] and not any(y['rev_wet'])
  else:
   e,m,cs,g=b;sy=m['fx_menu']['symbols'];e.uc.mem_write(0x40710000,y['rev_input'])
   for _ in range(140):e.call(sy['fx_ps1'],0x40710200,0x40710000,__import__('mcengine').PARAMS+432)
   assert any(e.uc.mem_read(0x40710200,256))
   result=run(b,1);assert any(result['rev_wet'])
 print('PASS native mixer PS1 send0 exact dry, active send audible, old Reverb/Chorus/Vinyl routes exact v68',flush=True)
 r,s,m=rig(STEM);r.call('fx_ps1_reset');r.u.mem_write(IN,bytes(256));r.u.mem_write(IN+1024,struct.pack('>hh',32512,32512));costs=[]
 for _ in range(140):r.call('fx_ps1',OUT,IN,IN+1024)
 regs={getattr(C,'UC_M68K_REG_'+kind+str(i)):0x12340000+i for kind,ix in [('D',range(2,8)),('A',range(2,7))] for i in ix}
 for reg,val in regs.items():r.u.reg_write(reg,val)
 count=[0];h=r.u.hook_add(UC_HOOK_CODE,lambda *a:count.__setitem__(0,count[0]+1));r.call('fx_ps1',OUT,IN,IN+1024);r.u.hook_del(h)
 assert all(r.u.reg_read(reg)==val for reg,val in regs.items()) and count[0]<22000,count
 # Menu applique au relachement, pas pendant le parcours ; controles natifs.
 r,s,h,log,files,key,turn,data,bind=ui_fixture(STEM);r.w32(s['ch_mode'],3);key(2)
 for _ in range(4):turn(14,-1)
 assert r.r32(s['ch_mode'])==3 and r.r32(s['fx_menu_cursor'])==0
 key(2,0);assert r.r32(s['ch_mode'])==7
 for knob,mods,want in ((14,set(),(14,0,0)),(14,{1},(14,1,0)),(14,{13},(14,1,0)),(9,set(),(9,0,0))):
  h.clear();h.update(mods);log.clear();turn(knob);assert log==[('native',*want)],(mods,log)
 h.clear();r.w32(s['fx_dirty'],1);r.call('fx_service');saved=dict(files);rr,ss,hh,ll,ff,*_=ui_fixture(STEM);ff.update(saved);rr.call('fx_service');assert rr.r32(ss['ch_mode'])==7
 print('PASS PS1 menu release, native Send/Decay/Tone, SETTINGS guard and saved mode',flush=True)
 # Les voix/SCRAMBLE et le CLOUD compile sont conserves ; pas de changement hors MAIN.
 a,b=parts(old),parts(STEM);assert a[2]==b[2]
 for sec in a[0]['sections']:
  if sec['id']==3:continue
  z=next(z for z in b[0]['sections'] if z['id']==sec['id']);assert a[0]['blob'][sec['off']:sec['off']+sec['size']]==b[0]['blob'][z['off']:z['off']+z['size']]
 for name in (('fx_cloud.c.o',) if META['fx_menu']['cloud'] else ())+('fx_delays.c.o','module.bin','chorus.bin','crush.bin','latch.bin','scramble_mask.bin','keep_params.bin'):
  assert (ROOT/('output/firmware/governor-recovery-'+OLD)/name).read_bytes()==(ROOT/('output/firmware/governor-recovery-'+VERSION)/name).read_bytes(),name
 report.update(hardware_tested=False,ps1_inspired_rate=24000,pcm16=True,instructions=count[0],tone_band_ratio=spectra,late_energy={str(k):late(v) for k,v in renders.items()},native_dry_exact=True,old_fx_exact=True,cloud_excluded=not META['fx_menu']['cloud'],base_modules_exact=True)
 (ROOT/('output/firmware/ps1-proof-'+VERSION+'.json')).write_text(json.dumps(report,indent=2)+'\n')
 print('PASS PS1 ABI/instructions',count[0],'base DSP/runtime exact',OLD,'recovery sections unchanged',flush=True)
if __name__=='__main__':main()
