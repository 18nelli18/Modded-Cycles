"""v78 : PS1 chaud assemble, PCM/etats exacts et contrat EMAC physique.
Mesures instructions/empreinte code seulement, jamais des cycles materiels.
"""
import sys,struct,random,json,math
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_vinyl_dust import rig,IN,OUT
from test_fx_cpu import counted
from test_ps1_cache import state
from boot_candidate import ROOT
OLD='validation/all-features-polivoks-cpu-trim-test-v77';NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v78'

def main():
 fs=[rig(stem) for stem in (OLD,NEW)];rng=random.Random(780);cost=[[],[]];cold=[[],[]];hot=[[],[]];footprints=[set(),set()]
 for r,s,m in fs:r.call('fx_ps1_reset')
 for b in range(8192):
  if b in (1400,3600):
   for r,s,m in fs:r.call('fx_ps1_reset')
  raw=[rng.choice([-2147483648,2147483647,rng.randrange(-2147483648,2147483648)]) for _ in range(64)] if b%700<64 else [0]*64
  if b%19<9:raw=[raw[i//2*2] for i in range(64)]
  params=struct.pack('>hh',(-256,0,16384,32512,32767)[b//73%5],(-256,0,16384,32512,32767)[b//47%5]);got=[]
  for j,(r,s,m) in enumerate(fs):
   ready=r.r32(s['ps_filled'])==2048;r.u.mem_write(IN,struct.pack('>64i',*raw));r.u.mem_write(IN+1024,params);out=IN if b%61==0 else OUT
   if b%64==0:
    n=counted(r,'fx_ps1',out,IN,IN+1024);cost[j].append(n);(hot if ready else cold)[j].append(n)
   else:r.call('fx_ps1',out,IN,IN+1024)
   got.append(bytes(r.u.mem_read(out,256)))
  assert got[0]==got[1],('PCM',b)
  if b%31==0:assert state(fs[0][0],fs[0][1],2056)==state(fs[1][0],fs[1][1],2056),('state',b)
 assert sum(hot[1])<sum(hot[0])*.9,(hot[0],hot[1])
 print('PASS8192 PS1 blocks PCM/state exact: cold/hot/reset/ring wrap/mono/stereo/in-place/full-scale/controls/tails',flush=True)
 # Contexte EMAC et ABI, meme si le programme appelant utilise un autre mode.
 regs={getattr(C,'UC_M68K_REG_'+kind+str(i)):0x12340000+i for kind,ix in [('D',range(2,8)),('A',range(2,7))] for i in ix}
 for status in (0,0x20,0x30,0x40,0x60,0xa0,0xb0,0xe0):
  for case in range(8):
   physical=[rng.getrandbits(48) for _ in range(4)];got=[];signal=struct.pack('>64i',*[rng.randrange(-2147483648,2147483648) for _ in range(64)])
   for r,s,m in fs:
    r.mac.macsr=status
    for k,v in enumerate(physical):r.mac.put_physical(k,v)
    for reg,val in regs.items():r.u.reg_write(reg,val)
    r.u.mem_write(IN,signal);r.call('fx_ps1',OUT,IN,IN+1024);got.append(bytes(r.u.mem_read(OUT,256)))
    assert r.mac.macsr==status and [r.mac.physical(k) for k in range(4)]==physical,('EMAC48',status,case)
    assert all(r.u.reg_read(reg)==v for reg,v in regs.items()),('ABI',status,case)
   assert got[0]==got[1],('context PCM',status,case)
 print('PASS64 physical48bit ACC0..3/MACSR contexts and ABI exact',flush=True)
 # Profil etabli identique pour comparer l empreinte de code executee.
 steady=[[],[]]
 for j,(r,s,m) in enumerate(fs):
  r.u.mem_write(IN+1024,struct.pack('>hh',25600,16384));r.u.mem_write(IN,struct.pack('>64i',*([180000000,-110000000]*32)))
  for b in range(32):
   if b==31:
    h=r.u.hook_add(UC_HOOK_CODE,lambda u,pc,*a,j=j:footprints[j].add(pc//16));steady[j].append(counted(r,'fx_ps1',OUT,IN,IN+1024));r.u.hook_del(h)
   else:steady[j].append(counted(r,'fx_ps1',OUT,IN,IN+1024))
 report={'candidate':NEW,'sha256':fs[1][2]['sha256'],'exact_pcm_blocks':8192,'emac_contexts':64,'sampled_hot_instructions':hot,'hot_saving':1-sum(hot[1])/sum(hot[0]),'sampled_cold_instructions':cold,'steady_instructions':steady,'steady_executed_code_lines16':[len(x) for x in footprints],'hardware_tested':False,'metric':'Executed instructions and unique code lines, not actual timing/cache misses'}
 (ROOT/('output/firmware/ps1-fast-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS PS1 hot saving',round(report['hot_saving']*100,2),'percent; steady',steady[0][-1],steady[1][-1],'code lines',report['steady_executed_code_lines16'],flush=True)
if __name__=='__main__':main()
