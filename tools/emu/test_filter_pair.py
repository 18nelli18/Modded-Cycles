"""v77 : filtre six pistes, paires exactes, saturation/historiques/EMAC/ABI.
Cout en instructions seulement, pas cycles du DSP ni marge materielle.
"""
import sys,struct,random,json
from unicorn import m68k_const as C
from test_polivoks_lite import RUN,F,Q,Y,ROOT
from test_governor_recovery import load,call,BUF
from emac_state import ExtendedEMAC
import emac
OLD='validation/all-features-polivoks-cpu-trim-test-v76'
NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v77'

def main():
 fs=[load(stem) for stem in (OLD,NEW)];rng=random.Random(770);totals=[0,0];hot=[0,0]
 for (r,m),stem in zip(fs,(OLD,NEW)):
  r.mac=ExtendedEMAC(r.u);at=0x467c7000;path=ROOT/('output/firmware/governor-recovery-'+stem.rsplit('-',1)[-1]+'/module.bin');raw=path.read_bytes();r.mac.install(emac.disasm(str(path),at,at,at+len(raw)))
 for b in range(4096):
  lane=b%6;f=(0,1,17,64,512,2048,3072,4095,6000)[b//6%9];q=(0,4096,8191,10000)[b//54%4]
  signal=[rng.choice([-2147483648,2147483647,rng.randrange(-2147483648,2147483648)]) for _ in range(32)] if b%9 else [0]*32
  initial=[rng.randrange(-134217728,134217728) for _ in range(4)] if b%19==0 else [1000]*4 if b%9==0 else None
  status=(0,0x20,0x30,0x40,0x60,0xa0,0xb0,0xe0)[b%8];acc=[rng.getrandbits(48) for _ in range(4)];out=[]
  for j,(r,m) in enumerate(fs):
   r.w32(F+lane*4,f);r.w32(Q+lane*4,q)
   if initial is not None:
    for k,v in enumerate(initial):r.w32(Y+28*k+4*lane,v)
   r.u.mem_write(BUF,struct.pack('>32i',*signal));r.mac.macsr=status
   for k,v in enumerate(acc):r.mac.put_physical(k,v)
   r.count=0;call(r,RUN,BUF,lane);totals[j]+=r.count
   out.append((bytes(r.u.mem_read(BUF,128)),bytes(r.u.mem_read(Y,112)),r.mac.macsr,[r.mac.physical(k) for k in range(4)]))
   assert r.mac.macsr==status and [r.mac.physical(k) for k in range(1,4)]==acc[1:],('EMAC preserved',b,j)
  assert out[0]==out[1],('PCM/state/EMAC',b)
 # Cout chaud avec tous les filtres actifs, coeff deja calcules.
 for b in range(192):
  lane=b%6;f=(1,17,256,1024,3072,4095)[lane];q=(0,4096,8191)[b%3];signal=[rng.randrange(-2147483648,2147483648) for _ in range(32)]
  out=[]
  for j,(r,m) in enumerate(fs):
   r.w32(F+4*lane,f);r.w32(Q+4*lane,q);r.call(m['recovery_symbols']['pf_coeff'],lane)
   r.u.mem_write(BUF,struct.pack('>32i',*signal));r.mac.macsr=0xa0;r.mac.acc[:]=[0]*4;r.count=0;call(r,RUN,BUF,lane);hot[j]+=r.count;out.append(bytes(r.u.mem_read(BUF,128))+bytes(r.u.mem_read(Y,112)))
  assert out[0]==out[1],('hot state',b)
 saving=1-hot[1]/hot[0];assert saving>.12,hot
 report={'candidate':NEW,'sha256':fs[1][1]['sha256'],'pcm_exact_blocks':4288,'all_six_tracks':True,'emac_abi_exact':True,'all_calls_instructions':totals,'hot_instructions':hot,'hot_saving':saving,'hardware_tested':False,'metric':'Executed instructions for filter only; not cycles or full audio callback'}
 (ROOT/('output/firmware/filter-pair-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS4288 filter blocks exact, six lanes, cutoff/resonance/clipping/bypass/quiet/history/EMAC48/ABI;',report,flush=True)
if __name__=='__main__':main()
