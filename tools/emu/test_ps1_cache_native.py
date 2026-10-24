"""v76 : vrai mixeur PS1 six pistes, PCM exacts et modele cache DDR.
Sources mono ou mid/side. Aucun timer/cache materiel simule.
"""
import sys,struct,json
from test_fx_menu_audio import fixture
from test_fx_combo_cpu import prep
from test_delay_crush_sends import run
from test_ps1_cache import Cache
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from boot_candidate import ROOT
import mcengine as E

def main():
 stems=['staging/all-features-polivoks-cpu-trim-test-v75',sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v76'];rows=[]
 for side,pan in ((False,64),(True,21)):
  fs=[fixture(stem,0) for stem in stems];caches=[]
  for f in fs:
   s=prep(f,7,0,100,pan,side);e=f[0];e.uc.mem_write(0x40710000,struct.pack('>64i',*([500000000,-310000000]*32)))
   for _ in range(160):e.call(s['fx_ps1'],0x40710200,0x40710000,E.PARAMS+432)
   cache=Cache();caches.append(cache)
   def observe(u,access,a,size,value,data,cache=cache):
    for line in range(a//16,(a+size-1)//16+1):cache.touch(line*16,access==UC_MEM_WRITE)
   e.uc.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,observe,begin=0x40000000,end=0x47ffffff)
  for b in range(40):
   got=[run(f,1) for f in fs]
   assert all(got[0][k]==got[1][k] for k in ('post','wet','rev_wet')),('six-track mixer',side,b)
  row={'stereo_source':side,'pan':pan,'pcm_exact_blocks':40,'cache_access_miss_dirty':[[c.access,c.miss,c.dirty] for c in caches]};rows.append(row);print('PASS full six-track PS1 native mixer',row,flush=True)
 assert all(row['cache_access_miss_dirty'][1][1]<row['cache_access_miss_dirty'][0][1] for row in rows)
 (ROOT/('output/firmware/ps1-native-cache-proof-'+stems[1].rsplit('-',1)[-1]+'.json')).write_text(json.dumps({'candidate':stems[1],'sha256':fs[1][1]['sha256'],'rows':rows,'metric':'Idealized four-way LRU trace of cached DDR data, not hardware timing','hardware_tested':False},indent=2)+'\n')
if __name__=='__main__':main()
