"""Filtre prive : vrai noyau ColdFire vs modele entier, cout et stabilite.

Le son change volontairement ; comparaison de cout seulement avec l'ancien
ladder. Instructions emulees, pas pourcentage CPU materiel.
"""
import json,pathlib,random,struct,subprocess,sys
from unicorn import m68k_const as C
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_governor_recovery import load,call,BUF
from boot_candidate import ROOT
import emac
RUN=0x401badda;F=0x401bbd60;Q=0x401bbd7c;Y=0x401bbdb4;LIMIT=134213632
original=subprocess.run

def cross(cmd,*args,**kw):
 if isinstance(cmd,list) and cmd[0]=='m68k-linux-gnu-objdump':cmd=[str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe'),*cmd[1:]]
 return original(cmd,*args,**kw)
subprocess.run=cross

def coeff(f,q):
 f=min(f,4095);q=min(q,8191);c=4096-f;ff=f*f;cc=c*c;fb=((362-(q*346>>13))*f*c)>>8;d=ff+cc+fb
 b=(ff<<30)//d;diff=ff-cc;a1=((abs(diff)<<30)//d)*2*(1 if diff>=0 else -1);a2=((ff+cc-fb)<<30)//d
 return b,a1,a2

def reference(data,state,co):
 x1,x2,y1,y2=state;b,a1,a2=co;out=[]
 for raw in data:
  x=raw>>4;acc=((b*(x+2*x1+x2)>>23)<<23)-((a1*y1>>23)<<23)-((a2*y2>>23)<<23);y=(acc>>31)*2;y=max(-LIMIT,min(LIMIT,y));out.append(y<<4);x2=x1;x1=x;y2=y1;y1=y
 return out,[x1,x2,y1,y2]

def setup(stem='all-features-polivoks-cpu-test-v20'):
 version=stem.rsplit('-',1)[-1];module=ROOT/('output/firmware/governor-recovery-'+version)
 rigs=[load('all-features-macro-names-test-v17'),load(stem)]
 for i,(r,m) in enumerate(rigs):
  if i==0:
   at=RUN;raw=bytes(r.u.mem_read(RUN,678));path=module/'reference-filter.bin'
  else:
   at=0x467c7000;raw=(module/'module.bin').read_bytes();path=module/'module.bin'
  if i==0:path.write_bytes(raw)
  r.emac=emac.EMAC(r.u);r.emac.install(emac.disasm(str(path),at,at,at+len(raw)))
 return rigs

def main():
 rigs=setup(sys.argv[1] if len(sys.argv)>1 else 'all-features-polivoks-cpu-test-v20');r,m=rigs[1];sy=m['recovery_symbols']
 for f in range(1,4096):
  for q in (0,8191):
   lane=f%6;r.w32(F+4*lane,f);r.w32(Q+4*lane,q);ptr=r.call(sy['pf_coeff'],lane);got=struct.unpack('>3i',r.u.mem_read(ptr+8,12));expected=coeff(f,q);assert got==expected,(f,q,got,expected)
   b,a1,a2=got;assert a2<(1<<30) and (1<<30)+a1+a2>0 and (1<<30)-a1+a2>0,(f,q,'Jury stability')
 print('PASS 8190 real coefficient updates : Q30 exacts, chaque cutoff1..4095, resonance min/max, stabilite lineaire Jury',flush=True)
 rng=random.Random(20261022);totals={0:[0,0],1:[0,0]};changes=[0,0]
 for case in range(144):
  f=(1,17,64,256,1024,2048,3072,4095)[case%8];q=(0,4096,8191)[(case//8)%3];lane=case%6
  data=[rng.choice([0x7fffffff,-0x80000000,rng.randrange(-0x10000000,0x10000000)]) for _ in range(32)]
  state=[0,0,0,0];out,after=reference(data,state,coeff(f,q))
  for j,(r,m) in enumerate(rigs):
   r.w32(F+4*lane,f);r.w32(Q+4*lane,q)
   for pole in range(4):r.w32(Y+28*pole+4*lane,0)
   r.u.mem_write(BUF,struct.pack('>32i',*data));r.emac.macsr=0xa0;r.emac.acc[:]=[0,111,222,333];r.count=0;call(r,RUN,BUF,lane);changes[j]+=r.count
   assert r.emac.macsr==0xa0 and r.emac.acc==[0,111,222,333],('EMAC state',j)
   if j==1:
    got=struct.unpack('>32i',r.u.mem_read(BUF,128));assert list(got)==out,(case,'samples',got,out)
    assert [struct.unpack('>i',r.u.mem_read(Y+28*pole+4*lane,4))[0] for pole in range(4)]==after
   # Deuxieme bloc au meme reglage : cout du chemin chaud, sans recalcul coeff.
   r.u.mem_write(BUF,struct.pack('>32i',*data));r.count=0;call(r,RUN,BUF,lane);totals[bool(q)][j]+=r.count
 print('PASS 144 blocs reels : extremes signes, tous les six tracks, etats et samples exacts au modele entier, MACSR/ACC1..3 preserves',flush=True)
 for res,counts in totals.items():
  saving=100*(1-counts[1]/counts[0]);print('FILTER INSTRUCTIONS resonance',res,'old/new',counts,'saving',round(saving,1),'percent',flush=True);assert saving>10,counts
 print('FILTER CHANGING COEFFICIENTS old/new totals',changes,'includes cold/update cost',flush=True)
 assert changes[1]<changes[0]
 # Silence, contournement et isolation des six historiques.
 for lane in range(6):
  r,m=rigs[1];r.w32(F+lane*4,0);data=struct.pack('>32i',*[rng.randrange(-0x80000000,0x80000000) for _ in range(32)]);r.u.mem_write(BUF,data);before=bytes(r.u.mem_read(Y,112));call(r,RUN,BUF,lane);assert bytes(r.u.mem_read(BUF,128))==data and bytes(r.u.mem_read(Y,112))==before
  r.w32(F+lane*4,2048);r.w32(Q+lane*4,8191)
  for pole in range(4):r.w32(Y+28*pole+4*lane,1000)
  r.u.mem_write(BUF,bytes(128));call(r,RUN,BUF,lane);assert bytes(r.u.mem_read(BUF,128))==bytes(128)
  assert all(r.r32(Y+28*pole+4*lane)==0 for pole in range(4))
 print('PASS bypass exact, repos remis a zero, six pistes ; aucune sortie HP/BP ajoutee',flush=True)
 # Le modele entier reste borne apres changements brusques de coefficient.
 state=[0]*4
 for block in range(8192):
  f=(1,17,256,2048,4095)[(block//16)%5];q=(0,8191)[block%2];raw=[rng.randrange(-0x80000000,0x80000000) if block<256 else 0 for _ in range(32)]
  out,state=reference(raw,state,coeff(f,q));assert max(map(abs,out))<=LIMIT*16
 print('PASS modele entier :262144 samples bornes, modulation/resonance extremes puis silence ; pas de mesure CPU materielle',flush=True)
 print('PASS private shared-filter checks',flush=True)
if __name__=='__main__':main()
