"""v77 : six voix reelles, filtres partages et reverb PS1 dans le mixeur natif.
Banc de rendu sans sequenceur/USB/temps materiel ; PCM exacts contre v76.
"""
import sys,struct,json
from unicorn import UC_HOOK_CODE
from test_fx_menu_audio import fixture
from test_fx_combo_cpu import prep
from test_delay_crush_sends import run
from profile_all_machines_cpu import DEFAULT
from test_polivoks_lite import RUN,F,Q,Y
from boot_candidate import ROOT
import mcengine as E
OLD=sys.argv[2] if len(sys.argv)>2 and not sys.argv[2].startswith('--') else 'validation/all-features-polivoks-cpu-trim-test-v76';NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v77';CLOSED='--closed' in sys.argv

def main():
 fs=[fixture(stem,0) for stem in (OLD,NEW)];rows=[]
 for f in fs:
  s=prep(f,7,0,100,64,False);e=f[0]
  for lane,machine in enumerate((0,1,2,3,11,4)):
   e.set(lane,machine=machine,**dict(zip(('color','shape','sweep','contour'),DEFAULT[machine])),decay=100)
  e.uc.mem_write(0x40710000,struct.pack('>64i',*([180000000,-110000000]*32)))
  for _ in range(160):e.call(s['fx_ps1'],0x40710200,0x40710000,E.PARAMS+432)
 total=[0,0];peaks=[0,0]
 for b in range(64):
  pcm=[];voice=[];hist=[]
  for j,f in enumerate(fs):
   e,m,sy,g=f;n=[0];hits=[0]
   h=e.uc.hook_add(UC_HOOK_CODE,lambda *a:n.__setitem__(0,n[0]+1))
   hf=e.uc.hook_add(UC_HOOK_CODE,lambda *a:hits.__setitem__(0,hits[0]+1),begin=RUN,end=RUN)
   raw=e.block(63 if b%8==0 else 0,63 if b%24==22 else 0)
   for lane in range(6):
    e.uc.mem_write(F+lane*4,struct.pack('>I',64 if CLOSED else (256,2048,3072,4095)[b//16%4]));e.uc.mem_write(Q+lane*4,struct.pack('>I',4096 if CLOSED else (0,4096,8191)[b//8%3]))
   assert not CLOSED or bytes(e.uc.mem_read(F,24))==struct.pack('>6I',*([64]*6))
   # Le banc voix n execute pas le dispatch du mixeur : appliquer une fois
   # les filtres partages comme le chemin audio, avant les sends.
   assert hits[0]==0,('fixture already filters',b,j,hits)
   for lane in range(6):e.call(RUN,E.TRACK_BASE+lane*128,lane)
   assert hits[0]==6
   g=run(f,1);e.uc.hook_del(h);e.uc.hook_del(hf);total[j]+=n[0];peaks[j]=max(peaks[j],n[0]);pcm.append((g['post'],g['wet'],g['rev_wet']));voice.append(bytes(e.uc.mem_read(E.VOICE0,E.VSTRIDE*6)));hist.append(bytes(e.uc.mem_read(Y,112)))
  assert pcm[0]==pcm[1] and voice[0]==voice[1] and hist[0]==hist[1],('combined PCM/state',b)
 assert total[1]<total[0],total
 report={'candidate':NEW,'baseline':OLD,'closed_static':CLOSED,'sha256':fs[1][1]['sha256'],'pcm_exact_blocks':64,'lineup':['Kick','Snare','Metal','Perc','Swarm','Tone'],'filter_calls_each_build':384,'instructions':total,'peak_instructions':peaks,'saving':1-total[1]/total[0],'hardware_tested':False,'limits':'Native voices + filters + mixer/PS1; no sequencer/UI/USB timing or real cycle simulation'}
 (ROOT/('output/firmware/filter-ps1-mix-proof-'+NEW.rsplit('-',1)[-1]+('-closed' if CLOSED else '')+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS six real voices + six filters + PS1 native mix PCM/state exact',report,flush=True)
if __name__=='__main__':main()
