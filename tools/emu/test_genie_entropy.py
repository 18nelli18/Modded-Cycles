"""Note132 : vrai generateur, premiere graine variable, suites/contraintes conservees."""
import pathlib,sys,struct,random,argparse
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_midi_entry import boot_case
from test_seq_gen_menu import Rig
ROOT=HERE.parents[1]
def load(case):
 img,mem,ts=boot_case(case);sy={k:v for t in ts for k,v in t.get('symbols',{}).items()};r=Rig(img,{'writes':[]},{'writes':[],'symbols':sy})
 for at,size in ((0x43000000,0x800000),(0x46700000,0x500000),(0x80000000,0x200000),(0xfc070000,0x1000)):r.u.mem_map(at,size)
 for at,raw in mem:r.u.mem_write(at,raw)
 wrapper=0x93030000;r.u.mem_write(wrapper,bytes.fromhex('206f0004226f00084ef9')+struct.pack('>I',r.s['sg_generate']))
 return r,wrapper
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',default='usb');p.add_argument('--main',action='store_true');a=p.parse_args();base,be=load('build/genie-entropy/main198-'+a.profile);new,ne=load(('build/midi-machine/all/main-' if a.main else 'build/genie-entropy/')+a.profile)
 cfg,out=0x93010000,0x93020000;unique=set();rng=random.Random(132)
 for case in range(128):
  timer=rng.getrandbits(32);initial=0x6d2b79f5;seed=initial^timer or initial
  common=[64,80,48,84,0 if case<64 else case%5,0 if case<64 else case%12]
  for r,entry,value in ((base,be,seed),(new,ne,initial)):
   r.u.mem_write(cfg,struct.pack('>7I',*common,value));r.u.mem_write(out,b'\xa5'*80);r.w32(0xfc07000c,timer)
   if r is new:r.w32(r.s['ge_initialized'],0)
   result=r.call(entry,cfg,out)
   assert result<=64
  assert bytes(base.u.mem_read(out,80))==bytes(new.u.mem_read(out,80)),case
  assert base.r32(cfg+24)==new.r32(cfg+24)
  assert new.r32(new.s['ge_initialized'])==1
  if case<64:unique.add(bytes(new.u.mem_read(out,64)))
  # Changer le timer ensuite ne doit plus resemer la sequence.
  base.w32(0xfc07000c,1);new.w32(0xfc07000c,0xffffffff);base.call(be,cfg,out);new.call(ne,cfg,out)
  assert bytes(base.u.mem_read(out,80))==bytes(new.u.mem_read(out,80)) and base.r32(cfg+24)==new.r32(cfg+24)
 assert len(unique)>60
 # Premier appel invalide : aucune mutation, initialisation toujours en attente.
 new.w32(new.s['ge_initialized'],0);new.u.mem_write(cfg,struct.pack('>7I',0,50,48,72,0,0,initial));new.u.mem_write(out,b'\xa5'*80)
 assert new.call(ne,cfg,out)==0xffffffff and new.r32(cfg+24)==initial and new.r32(new.s['ge_initialized'])==0
 assert bytes(new.u.mem_read(out,80))==b'\xa5'*80
 print('PASS',a.profile,': 128 horaires initiaux, sortie/seed identiques au generateur avec graine attendue ; suite non resemee, configuration invalide intacte')
if __name__=='__main__':main()
