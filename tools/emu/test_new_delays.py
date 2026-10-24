"""v59 : retours DMA modelises, DSP delay natif, octave dans la boucle et routes UI.
Pas de pourcentage CPU materiel deduit du compte d instructions.
"""
import sys,struct,json,math,wave,time
from pathlib import Path
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_vinyl_dust import rig,block,wav,IN,OUT
from test_fx_menu_audio import fixture,configure,run
from test_fx_menu_control import fixture as ui_fixture
from boot_candidate import ROOT
import mcengine as E
import emac
from emac_state import ExtendedEMAC
from collections import deque
from boot_candidate import load
from test_seq_gen_menu import STACK,STOP

def native_rig(stem):
 r,s,m=rig(stem);u=r.u;u.mem_map(0x80000000,0x20000);u.mem_map(0xfc040000,0x10000);u.mem_map(0x4a400000,0x400000)
 original=load(ROOT/'output/firmware'/(stem+'.syx'))
 for lo,hi,dst in ((0x4019b590,0x401a2a50,0x80000000),(0x401a2a50,0x401aa140,0x80008000)):u.mem_write(dst,original[lo-0x40000400:hi-0x40000400])
 mac=getattr(r,'mac',None) or ExtendedEMAC(u);mac.install(E._emac_instrs(original,[(0x40057260,0x4005770e)]));d=m['fx_menu']
 if not hasattr(r,'mac'):mac.install(emac.disasm(str(ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/fx.bin')),d['code'],d['code'],d['code']+d['code_bytes']))
 u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(C.UC_M68K_REG_A7,STACK);u.emu_start(0x40057260,STOP,count=5000000);assert u.reg_read(C.UC_M68K_REG_PC)==STOP;assert r.r32(0x8000b570)==0x8000b590;mac.macsr=0xa0
 return r,s,m,mac

def delay_render(stem,mode,feedback=12000,seconds=1.2):
 r,s,m,mac=native_rig(stem);u=r.u;param=IN+1024;u.mem_write(param,struct.pack('>hh',11000,feedback));r.w32(s['cr_mode'],mode)
 for name,val in [('nd_ready',1),('nd_active',mode),('nd_gain',256),('nd_prior',256)]:r.w32(s[name],val)
 # DMA modelise : transfert des seules donnees du ring, DSP natif inchange.
 ring=deque([bytes(256)]*150);output=[];returns=[];work=r.r32(0x8000b570)
 for b in range(int(seconds*1500)+64):
  raw=ring.popleft();bank=raw+raw[-8:]*2;u.mem_write(work,bank+bank);signal=[]
  for i in range(32):
   t=(b-64)*32+i;v=.12*math.sin(2*math.pi*375*t/48000)*math.sin(math.pi*t/2400)**2 if 0<=t<2400 else 0
   signal.extend([int(v*2147483647)]*2)
  u.mem_write(IN,struct.pack('>64i',*signal));r.call('fx_dfx',OUT,IN,param);ring.append(bytes(u.mem_read(work,256)))
  wet=struct.unpack('>64i',u.mem_read(OUT,256));returns.extend(wet)
  if b>=64:output.extend(max(-2147483648,min(2147483647,a+d)) for a,d in zip(signal,wet))
 y=np.array(returns,dtype=float).reshape(-1,2)/2147483648
 assert np.max(abs(y))<.5
 return output,y,r,s,mac

def main():
 stem=sys.argv[1];r,s,m=rig(stem);report={};zero=[0]*64;special=tuple(x for x in m['fx_menu']['delay_selector_order'] if x>=5)
 # +12 demi-tons : vrai C compile, une sinusoide deja dans le retour delay.
 r.call('fx_shift_reset');audio=[]
 for b in range(900):
  # Les deux canaux portent exactement le meme ton 375Hz.
  signal=[int(.15*2147483647*math.sin(2*math.pi*375*(b*32+i)/48000)) for i in range(32) for c in range(2)]
  r.u.mem_write(IN,struct.pack('>64i',*signal));r.call('fx_shift',IN);audio.extend(struct.unpack('>64i',r.u.mem_read(IN,256)))
 y=np.array(audio).reshape(-1,2)[4096:,0].astype(float);n=len(y);hz=np.fft.rfftfreq(n,1/48000);sp=abs(np.fft.rfft(y*np.hanning(n)))**2
 fundamental=sp[abs(hz-375)<5].sum();octave=sp[abs(hz-750)<5].sum();assert octave>fundamental*.5,(fundamental,octave);assert octave>sp[(hz>900)&(hz<1400)].sum()*8
 report['octave_power_ratio']=float(octave/fundamental)
 if m['fx_menu'].get('delay_return_hook'):assert octave>fundamental*5
 # Sorties du vrai delay et sa boucle, DMA seul modelise.
 renders={}
 for mode in special:
  sound,wet,rr,ss,mac=delay_render(stem,mode);wav(ROOT/'output/firmware/validation'/(('ping-pong-' if mode==5 else 'shimmer'+str(mode-5)+'-')+stem.rsplit('-',1)[-1]+'.wav'),sound);renders[mode]=wet
  if mode==5:
   energy=[]
   for k in range(1,5):
    segment=wet[(64+150*k)*32:(64+150*k)*32+3000];energy.append(np.sum(segment*segment,axis=0))
   assert energy[0][1]>100*energy[0][0] and energy[1][0]>100*energy[1][1],energy
   report['ping_pong_echo_energy']=[x.tolist() for x in energy]
  # ABI et cout : le hook entier, lecture ring + feedback natifs inclus.
  regs={getattr(C,'UC_M68K_REG_'+kind+str(i)):0x12340000+i for kind,ix in [('D',range(2,8)),('A',range(2,7))] for i in ix}
  for reg,val in regs.items():rr.u.reg_write(reg,val)
  count=[0];hook=rr.u.hook_add(UC_HOOK_CODE,lambda *a:count.__setitem__(0,count[0]+1));rr.call('fx_dfx',OUT,IN,IN+1024);rr.u.hook_del(hook);assert all(rr.u.reg_read(reg)==val for reg,val in regs.items());assert mac.macsr==0xa0 and all(mac.physical(i)==0 for i in range(4));report['instructions_'+str(mode)]=count[0]
  print('PASS native feedback loop/render/ABI for mode',mode,'instructions',count[0],flush=True)
 if 7 in special:
  _,preserved,*_=delay_render(stem.rsplit('-',1)[0]+'-v62',6)
  assert np.array_equal(renders[7],preserved),'Shimmer2 differs from preserved v62 audio'
  report['shimmer2_exact_v62']=True
  print('PASS Shimmer2 complete native feedback render bit exact v62',flush=True)
 # L octave monte dans les repetitions, pas uniquement sur un retour final.
 z=renders[6];segment=z[(64+300)*32:(64+300)*32+4096,0];hz=np.fft.rfftfreq(len(segment),1/48000);power=abs(np.fft.rfft(segment*np.hanning(len(segment))))**2
 assert power[abs(hz-750)<25].sum()>power[(hz>1000)&(hz<1200)].sum()*10

 print('PASS native two-head shifter: 375Hz -> 750Hz component, bounded stereo audio',flush=True)
 # En-tetes et controles : native Time/Feedback/Send, aucune page crusher.
 r,s,h,log,files,key,turn,data,bind=ui_fixture(stem)
 for mode in special:
  r.w32(s['cr_mode'],mode)
  for knob,mods,want in [(15,set(),(15,0,0)),(15,{1},(15,1,0)),(8,set(),(8,0,0)),(8,{1},(8,1,0))]:
   h.clear();h.update(mods);log.clear();turn(knob);assert log==[('native',*want)],(mode,knob,mods,log)
  r.w32(s['fx_dirty'],1);h.clear();r.call('fx_service');saved=files['/FxMix.cfg'];rr,ss,hh,ll,ff,*_=ui_fixture(stem);ff['/FxMix.cfg']=saved;rr.call('fx_service');assert rr.r32(ss['cr_mode'])==mode
 if m['fx_menu'].get('delay_return_hook'):
  forwarded=[]
  def native_zero(a):forwarded.append('native');return 0
  def legacy(a):forwarded.append('legacy');return 0
  bind(s['fx_native_encoder'],native_zero);bind(s['fx_previous_encoder'],legacy)
  for mode in (0,3,4)+special:
   r.w32(s['cr_mode'],mode)
   for knob,mods in [(15,set()),(15,{1}),(15,{13}),(8,set())]:
    if mode in (3,4) and mods=={1}:continue
    if mode==0 and mods=={13}:continue
    forwarded.clear();h.clear();h.update(mods);assert turn(knob)==1;assert forwarded==['native'],(mode,knob,mods,forwarded)
 print('PASS both modes native Time/Feedback/Send, persistent IDs5/6 and native0 ownership',flush=True)
 # Mixeur complet : legacy PCM exact v57, tous les cinq anciens modes.
 old=stem.rsplit('-',1)[0]+'-v57'
 for mode in range(5):
  fs=[fixture(old,0),fixture(stem,0)]
  for f in fs:configure(f,0,[0]*6,0,mode)
  for b in range(3):
   a,z=[run(f,1) for f in fs];assert a['post']==z['post'] and a['wet']==z['wet'],('legacy mixer',mode,b)
 print('PASS all five legacy Delay/Crush routes PCM exact v57 in native mixer',flush=True)
 # Nouveau chemin dans le vrai mixeur, registres a4/a5 et EMAC inclus.
 for mode in special:
  f=fixture(stem,0);configure(f,0,[0]*6,0,mode);e,m,cs,got=f;sy=m['fx_menu']['symbols']
  for name,val in [('nd_ready',1),('nd_active',mode),('nd_gain',256),('nd_prior',256)]:e.uc.mem_write(sy[name],struct.pack('>I',val))
  e.uc.mem_write(0x8000b570,struct.pack('>I',0x8000b590));e.uc.mem_write(E.PARAMS+54,struct.pack('>H',32512))
  result=run(f,3);assert not e.unmapped
  if mode==5:assert any(e.uc.mem_read(sy['nd_feed'],256)),'real native input rejected'

 print('PASS both new hook branches execute full native mixer with preserved ABI/EMAC',flush=True)
 # Poussiere : send0 sec, send actif avec source silencieuse ; volume et mute.
 for mode in (3,4):
  f=fixture(stem,0);configure(f,mode,[127 if mode==3 else 0,0,0,0,0,0],127);e,m,cs,g=f;sy=m['fx_menu']['symbols'];e.uc.mem_write(sy['fx_crackle'],struct.pack('>I',64));e.uc.mem_write(sy['fx_warble'],bytes(4));e.uc.mem_write(E.TRACK_BASE,bytes(768));run(f,3)
  gains=struct.unpack('>2I',e.uc.mem_read(sy['dust_target'],8));assert min(gains)>15000,('silent-source gain',mode,gains)
  e.uc.mem_write(0x404e9b53,b'\x01');run(f,2);assert not any(e.uc.mem_read(sy['dust_target'],8)),('mute',mode)
  e.uc.mem_write(0x404e9b53,b'\x00');e.uc.mem_write(E.PARAMS,bytes(2));run(f,2);assert not any(e.uc.mem_read(sy['dust_target'],8)),('track volume0',mode)
 print('PASS Vinyl and Vinyl+Rev dust targets survive silent source and obey mute/volume',flush=True)
 report.update(stem=stem,sha256=m['sha256'],legacy_mixer_exact=True,new_native_hooks=True,vinyl_silent_source=True,hardware_tested=False)
 (ROOT/'output/firmware'/('new-delays-proof-'+stem.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
