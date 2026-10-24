"""SPEAK : lexique128, controles independants, rendu ColdFire et six voix natives."""
import sys,json,struct,hashlib,wave
import numpy as np
from boot_candidate import ROOT
from test_vinyl_dust import rig,IN,OUT
from test_fx_cpu import counted
from test_keep_machine_params import fixture,T
from test_wizard_playback import fixtures
from unicorn import UC_HOOK_CODE,m68k_const as C
import mcengine as E
NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v82'

def core():
 r,unused,m=rig(NEW);s=m['speak']['symbols'];r.s.update(s);state=IN+2048;inp=IN+3072;size=r.r32(s['speak_state_bytes']);rows=[];samples={}
 def render(word,note=60,voice=64,speed=64,artic=80,punch=0):
  r.u.mem_write(state,bytes(size));r.u.mem_write(inp,struct.pack('>7i',note<<16,voice,word,speed,artic,punch,1));audio=[]
  for b in range(5000):
   r.call('speak_block',state,inp,OUT);audio.extend(struct.unpack('>32i',r.u.mem_read(OUT,128)))
   if b==0:r.w32(inp+24,0)
   if r.r32(state+24) and b>3:break
  else:raise AssertionError(('word did not end',word))
  assert max(map(abs,audio))<(2147483648 if m['speak'].get('level_calibrated') else 536870912) and any(audio),('bounds/silent',word)
  return audio,b+1
 for word in range(128):
  audio,n=render(word);rows.append(dict(word=m['speak']['words'][word],blocks=n,peak=max(map(abs,audio))));samples[word]=audio
 assert len({hashlib.sha256(struct.pack('>'+str(len(a))+'i',*a)).hexdigest() for a in samples.values()})>100
 print('PASS128 words render nonzero, bounded and complete in ColdFire',flush=True)
 base,n=render(31)
 for name,args in [('pitch',dict(note=72)),('voice',dict(voice=0)),('speed',dict(speed=127)),('artic',dict(artic=0)),('punch',dict(punch=1))]:
  audio,length=render(31,**args);assert audio!=base,name
  if name in ('pitch','voice','artic','punch'):assert length==n,(name,length,n)
 slow,ns=render(31,speed=0);fast,nf=render(31,speed=127);assert ns>nf*5
 again,_=render(31);assert again==base,'deterministic retrigger'
 # Limites de toutes les commandes et notes, sous gardes memoire.
 for note in (0,36,60,96,127):
  for voice,art,speed in ((0,0,0),(127,127,127)):render(45,note,voice,speed,art,1)
 costs=[]
 r.u.mem_write(state,bytes(size));r.u.mem_write(inp,struct.pack('>7i',60<<16,64,31,64,80,0,1))
 for b in range(200):
  if b in (30,60,100,160):costs.append(counted(r,'speak_block',state,inp,OUT))
  else:r.call('speak_block',state,inp,OUT)
  r.w32(inp+24,0)
 print('PASS independent pitch/speed, voice/articulation/punch, deterministic retrigger and extremes; block instructions',costs,flush=True)
 phrase=[]
 for word,note in ((0,60),(48,60),(28,60),(35,64),(19,60),(112,67),(127,60)):
  audio,_=render(word,note);phrase+=audio+[0]*2400
 path=ROOT/('output/firmware/validation/speak-phrase-'+NEW.rsplit('-',1)[-1]+'.wav')
 with wave.open(str(path),'wb') as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(struct.pack('<'+str(len(phrase))+'h',*[max(-32768,min(32767,x>>(16 if m['speak'].get('level_calibrated') else 13))) for x in phrase]))
 return dict(words=rows,core_instructions=costs,pitch_independent_of_speed=True,speed_duration_blocks=[ns,nf],preview=str(path))

def ui():
 m=json.loads((ROOT/'output/firmware'/(NEW+'.json')).read_text());u,obj,snd=fixture(NEW);t=m['tiny_extra'];assert u.u32(T.ROW_COUNT)==21;assert t['menu_order'][-4:]==[18,19,20,17]
 for i,label in enumerate(('Voice','Word','Speed','Artic','Decay')):
  desc=u.call(0x4005a692,18 if i==4 else 11+i,20);assert desc==141+i
  ptr=u.call(0x4000b22a,0,desc);assert bytes(u.uc.mem_read(ptr,len(label)+1))==label.encode()+b'\0'
  cc=u.call(0x4005a7f8,desc);assert cc<=127 and (i==4 or u.call(0x4005a8ce,0,20,cc)==desc),(i,cc)
 # Deux rangees :21reperes tous dans la moitie droite.
 u.hooks.update({0x40070c4e:'outline',0x40070efc:'filled'});stop=0x400a26f2
 h=u.uc.hook_add(UC_HOOK_CODE,lambda uc,*a:uc.emu_stop(),begin=stop,end=stop)
 for machine in range(21):
  u.uc.reg_write(C.UC_M68K_REG_A7,T.STACK-1024);u.uc.reg_write(C.UC_M68K_REG_D2,T.SCRATCH);u.uc.reg_write(C.UC_M68K_REG_D3,machine);u.calls.clear();u.uc.emu_start(t['symbols']['marks'],T.STOP,count=100000)
  rs=[(n,a) for n,a in u.calls if n in ('outline','filled')];assert len(rs)==21 and [i for i,(n,a) in enumerate(rs) if n=='filled']==[t['menu_order'].index(machine)];assert all(64<=a[1]<=a[3]<=127 and 0<=a[2]<=a[4]<=15 for n,a in rs)
 u.uc.hook_del(h);assert not u.bad
 print('PASS21 machines, SPEAK before MIDI Out, five native lock/CC/LFO descriptors and21 bounded markers',flush=True)
 # Dessin natif avec les vrais bitmaps et registres de l ecran MACHINES.
 source=(ROOT/'tools/emu/test_machine_identity.py').read_text();ns={'__file__':str(ROOT/'tools/emu/test_machine_identity.py')};exec(source[:source.index("stem=__import__('sys')")],ns)
 texts,images,raw=ns['render'](NEW,20);assert texts[0][0]=='SPEAK' and any(a[1]==m['speak']['stats_descriptor'] for a in images) and any(a[1]==m['speak']['icon_descriptor'] for a in images)
 from render_midi_bank import png
 pixels=[0 if struct.unpack_from('>I',raw,(x*2+(63-y)//32)*4)[0]&(1<<(31-(63-y)%32)) else 255 for y in range(64) for x in range(128)];png(ROOT/'output/firmware'/('speak-card-'+NEW.rsplit('-',1)[-1]+'.png'),pixels)
 print('PASS native SPEAK stats/microphone card and ABI',flush=True)

def main():
 ui();report=core();report.update(candidate=NEW,hardware_tested=False)
 (ROOT/'output/firmware'/('speak-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
