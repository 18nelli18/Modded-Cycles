"""v80 : DSP conserves exacts face a v78, mixeur natif et vrais retours Ping Pong."""
import sys,json,struct
import numpy as np
from boot_candidate import ROOT
from test_fx_menu_audio import fixture
from test_fx_combo_cpu import prep
from test_delay_crush_sends import run
from test_new_delays import delay_render
import mcengine as E
OLD='validation/all-features-polivoks-cpu-trim-test-v78'
NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v80'

def main():
 rows=[]
 cases=[(r,0,p,side) for r in (0,1,2,3,7) for p,side in ((64,False),(21,True))]+[(0,c,64,False) for c in (1,2)]+[(7,5,21,True)]
 for rev,delay,pan,side in cases:
  fs=[fixture(stem,0) for stem in (OLD,NEW)]
  for f in fs:
   s=prep(f,rev,0 if delay==5 else delay,100,pan,side);e=f[0]
   if delay==5:
    e.uc.mem_write(f[2]['cr_mode'],struct.pack('>I',5))
    for name,value in [('nd_active',5),('nd_ready',1),('nd_gain',256),('nd_prior',256)]:e.uc.mem_write(s[name],struct.pack('>I',value))
   e.uc.mem_write(0x40710000,struct.pack('>64i',*([180000000,-110000000]*32)))
   if rev==7:
    for _ in range(160):e.call(s['fx_ps1'],0x40710200,0x40710000,E.PARAMS+432)
   if rev in (1,2):
    for _ in range(32):e.call(s['fx_reverb'],0x40710200,0x40710000,E.PARAMS+432,E.PARAMS,0x40708000,0x40708020)
  for b in range(32):
   got=[]
   for f in fs:
    e,m,cs,g=f;s=m['fx_menu']['symbols']
    if b==16:
     for t in range(6):
      e.uc.mem_write(E.PARAMS+54+66*t,bytes(2));e.uc.mem_write(E.PARAMS+56+66*t,bytes(2))
     e.uc.mem_write(s['fx_aux_ch'],bytes(24));e.uc.mem_write(s['fx_aux_vi'],bytes(24));e.uc.mem_write(cs['cr_send'],bytes(24))
    g=run(f,1);got.append(tuple(g[k] for k in ('post','wet','rev_wet','send','rev_input')))
   assert got[0]==got[1],('PCM',rev,delay,pan,side,b)
  rows.append(dict(reverb=rev,delay=delay,pan=pan,mid_side=side,blocks=32))
  print('PASS retained native mixer PCM exact',rows[-1],flush=True)
 # Les vrais retours Delay sont non nuls avec le DMA modelise : quatre echos.
 rendered=[delay_render(stem,5,feedback=12000,seconds=.65)[1] for stem in (OLD,NEW)]
 assert np.array_equal(*rendered),'Ping Pong feedback PCM'
 energy=[]
 for k in range(1,5):
  seg=rendered[1][(64+150*k)*32:(64+150*k)*32+3000];energy.append(np.sum(seg*seg,axis=0))
 assert energy[0][1]>100*energy[0][0] and energy[1][0]>100*energy[1][1],energy
 print('PASS Ping Pong real native feedback PCM exact v78; alternate stereo echo energy',energy,flush=True)
 # Aller-retour Ping/Delay, y compris fondu de32blocs, aucune histoire pitch.
 fs=[fixture(stem,0) for stem in (OLD,NEW)]
 for f in fs:prep(f,0,0,100)
 for mode in (5,0,5,2,1,0):
  for f in fs:f[0].uc.mem_write(f[2]['cr_mode'],struct.pack('>I',mode))
  for b in range(70):
   a,z=[run(f,1) for f in fs]
   assert all(a[k]==z[k] for k in ('post','wet','rev_wet')),('transition',mode,b)
 print('PASS retained Delay/Ping/Crush transitions and fades PCM exact v78',flush=True)
 m=fs[1][1]
 (ROOT/('output/firmware/lean-audio-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(dict(candidate=NEW,baseline=OLD,sha256=m['sha256'],mixer_cases=rows,native_ping_exact=True,transitions_exact=True,hardware_tested=False),indent=2)+'\n')
if __name__=='__main__':main()
