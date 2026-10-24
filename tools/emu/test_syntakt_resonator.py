"""Resonateur SRAM : recurrence/saturation/EMAC/registres exacts face a v73.
Prototype --ram avant conteneur ; pas de cycles CPU materiels revendiques.
"""
import sys,argparse,random,struct,json
from unicorn import m68k_const as C
from test_wizard_playback import fixtures,ROOT
FN=0x80003470;N=62;STATE=0x42110000;BUF=0x48810000
BASE='validation/all-features-polivoks-cpu-trim-test-v73'

def main():
 p=argparse.ArgumentParser();p.add_argument('--ram',action='store_true');p.add_argument('--candidate',default='validation/all-features-polivoks-cpu-trim-test-v74');a=p.parse_args()
 raw=(ROOT/'output/firmware/resonator-test.bin').read_bytes()
 assert len(raw)==N
 def transform(rt):
  rt=bytearray(rt);off=FN-0x80001c5c;rt[off:off+N]=raw;return bytes(rt)
 es=[fixtures(False,127,0,[BASE],native_chordkeys=True)[0],fixtures(False,127,0,[BASE if a.ram else a.candidate],native_chordkeys=True,runtime_transform=transform if a.ram else None)[0]]
 rng=random.Random(740);cost=[0,0];cases=0
 for count in (-2,-1,0,1,2,16,31,32,64):
  for case in range(32):
   state=struct.pack('>4I',*[rng.getrandbits(32) for _ in range(4)]);buffer=rng.randbytes(512);phys=[rng.getrandbits(48) for _ in range(4)];outs=[]
   for j,e in enumerate(es):
    e.uc.mem_write(STATE,state);e.uc.mem_write(BUF,buffer);e.emac.macsr=0xa0
    for k,v in enumerate(phys):e.emac.put_physical(k,v)
    for kind,indices in [('D',range(8)),('A',range(7))]:
     for k in indices:e.uc.reg_write(getattr(C,'UC_M68K_REG_'+kind+str(k)),0x12340000+k)
    e.count=0;e.call(FN,BUF,count,STATE);cost[j]+=e.count
    outs.append((bytes(e.uc.mem_read(STATE,16)),bytes(e.uc.mem_read(BUF,512)),e.emac.macsr,[e.emac.physical(k) for k in range(4)],[e.uc.reg_read(getattr(C,'UC_M68K_REG_'+kind+str(k))) for kind,indices in [('D',range(8)),('A',range(7))] for k in indices]))
   assert outs[0]==outs[1],(count,case,[k for k,(x,y) in enumerate(zip(*outs)) if x!=y]);cases+=1
 print('PASS',cases,'resonator calls: signed counts, extreme states/coefs, PCM/state, all registers and EMAC48 exact; instructions',cost,flush=True)
 assert cost[1]<cost[0]
 (ROOT/'output/firmware/resonator-proof.json').write_text(json.dumps(dict(cases=cases,instructions=cost,hardware_tested=False,ram=a.ram,candidate=a.candidate),indent=2)+'\n')
if __name__=='__main__':main()
