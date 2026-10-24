"""Preuves privees CPU/vols : vrais hooks v17/v18, timers simules, pas cycles.

Le scan et le chemin normal doivent etre exacts ; les seuls changements audio
acceptes sont les raccords d'un bloc apres annulation d'un fondu/vol.
"""
import argparse,json,pathlib,random,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as C
HERE=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE.parent)]
from boot_candidate import ROOT,boot
from test_seq_gen_menu import Rig,STACK,STOP
NOMINAL=90112;GB=0x46732000;GATE=0x8000e8a4;AFTER=0x8000730a;END=0x8000e6e0;BUF=0x93010000

def load(stem):
 image,mem=boot(ROOT/'output/firmware'/(stem+'.syx'));r=Rig(image,{'writes':[]},{'writes':[],'symbols':{}})
 for at,size in [(0x46700000,0x200000),(0x80000000,0x20000),(0xfc070000,0x1000)]:r.u.mem_map(at,size)
 r.u.mem_write(*mem[0]);blob=mem[0][1]
 for off,at,n in [(0,0x80001c5c,0x5858),(0x5858,0x8000cac0,0x2020)]:r.u.mem_write(at,blob[off:off+n])
 r.count=0
 def count(u,pc,size,data):r.count+=1
 r.u.hook_add(UC_HOOK_CODE,count)
 return r,json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())
def reset(r,m):
 r.u.mem_write(GB,bytes(0x1200))
 if 'recovery_symbols' in m:
  s=m['recovery_symbols'];r.u.mem_write(s['gr_last'],bytes(24));r.w32(s['gr_diag_sum'],0);r.w32(s['gr_diag_blocks'],0)
 r.w32(m['dx_symbols']['dx_enabled'],0);r.w32(0xfc07000c,1000)
def call(r,at,*args):
 saved={getattr(C,'UC_M68K_REG_'+x+str(i)):0x12340000+i for x,indices in [('D',range(2,8)),('A',range(2,7))] for i in indices}
 for reg,v in saved.items():r.u.reg_write(reg,v)
 r.call(at,*args)
 assert all(r.u.reg_read(reg)==v for reg,v in saved.items()),hex(at)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',choices=('all-features','no-filter'),default='all-features');p.add_argument('--polivoks',action='store_true');p.add_argument('--candidate');a=p.parse_args()
 rigs=[load(a.profile+'-macro-names-test-v17'),load(a.candidate or a.profile+('-polivoks-cpu-test-v20' if a.polivoks else '-cpu-recovery-test-v19'))];rng=random.Random(20261022)
 counts={'audible':[0,0],'quiet':[0,0]}
 for case in range(1024):
  pressure=case%2;threshold=1<<20 if pressure else 8192;lane=case%6
  values=[rng.randrange(-threshold,threshold) for _ in range(32)]
  audible=case%4!=0
  if audible:values[(case//4)%32]=rng.choice([-2147483648,2147483647,-threshold-1,threshold])
  outputs=[]
  for j,(r,m) in enumerate(rigs):
   reset(r,m);r.w32(GB+0x64,pressure);r.u.mem_write(GB+0x5e+lane,bytes([case%256]));r.u.mem_write(BUF,struct.pack('>32i',*values));r.count=0;call(r,AFTER,lane,BUF)
   counts['audible' if audible else 'quiet'][j]+=r.count;outputs.append((bytes(r.u.mem_read(BUF,128)),bytes(r.u.mem_read(GB,0x1200))))
  assert outputs[0]==outputs[1],('scan',case,pressure)
 print('PASS 1024 vrais voice_after : samples/etat exacts, six pistes, deux seuils, positions et extremes signes',flush=True)
 print('INSTRUCTIONS governor hook totals',counts,'includes candidate wrappers; not hardware cycles',flush=True)
 assert counts['audible'][1]<counts['audible'][0],counts
 # Periode nominale : decisions et tableaux natifs inchanges.
 traces=[]
 for r,m in rigs:
  reset(r,m);states=[];r.w32(GB+0xf00,1000000-NOMINAL)
  for t in range(6):r.u.mem_write(GB+0x3a+2*t,struct.pack('>H',80));r.w32(GB+0x0a+4*t,8000)
  for i,load_pct in enumerate([50]*8+[95]*12+[70]*40+[120]*8+[65]*12):
   start=1000000+i*NOMINAL;r.w32(GB+0x80,start);r.w32(0xfc07000c,start+load_pct*NOMINAL//100);call(r,END);states.append(bytes(r.u.mem_read(GB,0x1200)))
  traces.append(states)
 assert traces[0]==traces[1]
 print('PASS 80 blocs au rythme nominal : memes charges, seuils, moyennes et decisions CUT ; registres/pile preserves',flush=True)
 for duration_pct in (80,96,120,192):
  loads=[]
  for r,m in rigs:
   reset(r,m)
   for i in range(3):
    start=1000000+i*2*NOMINAL;r.w32(GB+0x80,start);r.w32(0xfc07000c,start+duration_pct*NOMINAL//100);call(r,END)
   loads.append(r.r32(GB+0x7c))
  assert loads==[duration_pct*NOMINAL//100*256//(2*NOMINAL),duration_pct*NOMINAL//100*256//NOMINAL],loads
  print('PASS late calls, render',duration_pct,'percent of deadline: old/new load units',loads,flush=True)
 # Le vrai chemin gate -> after annule le fondu au trig : verifier le raccord.
 old,new=rigs;rs=new[1]['recovery_symbols']['gr_last'];max_jump=[0,0]
 for lane in range(6):
  for flen,remaining in [(2,1),(2,2),(8,1),(8,2),(8,8)]:
   histories=[];oldlast=[]
   for r,m in rigs:
    reset(r,m);r.u.mem_write(GB+0x58+lane,bytes([remaining]));r.u.mem_write(GB+0x52+lane,bytes([flen]));r.u.mem_write(BUF,struct.pack('>32i',*([0x40000000]*32)));call(r,AFTER,lane,BUF)
    last=struct.unpack('>i',r.u.mem_read(BUF+124,4))[0];oldlast.append(last)
    call(r,GATE,lane,1,1);assert r.r32(GB)==1
    r.u.mem_write(BUF,struct.pack('>32i',*([-0x40000000]*32)));call(r,AFTER,lane,BUF);histories.append(struct.unpack('>32i',r.u.mem_read(BUF,128)))
    assert bytes(r.u.mem_read(GB+0x4c+lane,1))==b'\0'
   assert oldlast[0]==oldlast[1]
   expected=tuple((-0x40000000*(2114*i)+oldlast[1]*(65536-2114*i))//65536 for i in range(31))+(-0x40000000,)
   assert histories[1]==expected,(lane,flen,remaining,histories[1],expected)
   for j in range(2):max_jump[j]=max(max_jump[j],max(abs(x-y) for x,y in zip((oldlast[j],)+histories[j],histories[j])))
   assert histories[1][0]==oldlast[1] and histories[1][-1]==histories[0][-1]
   # Pas de changement aux autres pistes et aucun second raccord sans vol.
   assert new[0].u.mem_read(GB+0x46+lane,1)==bytes(1)
   fresh=struct.pack('>32i',*[rng.randrange(-2147483648,2147483648) for _ in range(32)]);new[0].u.mem_write(BUF,fresh);call(new[0],AFTER,lane,BUF);assert bytes(new[0].u.mem_read(BUF,128))==fresh
 print('PASS 30 reprises gate->after : premier/dernier samples exacts, un bloc, sorties bornees, aucune voix additionnelle ; maximum jumps',max_jump,flush=True)
 # Sampler protege : meme tableau et memes samples, meme apres un ancien vol.
 for r,m in rigs:
  reset(r,m);r.u.mem_write(GB+0x58,b'\1');r.u.mem_write(GB+0x52,b'\10');r.u.mem_write(BUF,struct.pack('>32i',*([123456789]*32)));call(r,AFTER,0,BUF);call(r,GATE,0,1,6)
  fresh=struct.pack('>32i',*([76543210]*32));r.u.mem_write(BUF,fresh);call(r,AFTER,0,BUF);assert bytes(r.u.mem_read(BUF,128))==fresh
 print('PASS Sample Wizard : chemin protege exact, aucun raccord impose',flush=True)
 # Moyenne du diagnostic et absence d'activite OFF.
 r,m=rigs[1];reset(r,m);s=m['recovery_symbols'];dx=m['dx_symbols'];r.w32(0x40a7883c,1)
 for active in (0,1):
  r.w32(dx['dx_enabled'],active);r.w32(s['gr_diag_sum'],0);r.w32(s['gr_diag_blocks'],0)
  for i,pct in enumerate((50,100,150)):
   start=1000000+i*NOMINAL;r.w32(GB+0x80,start);call(r,dx['dx_before'],start+pct*NOMINAL//100)
  assert r.r32(s['gr_diag_blocks'])==(3 if active else 0)
  assert r.r32(s['gr_diag_sum'])==(768 if active else 0)
 print('PASS DX : moyenne exacte 50/100/150%, counters OFF inactifs ; firmware test uniquement',flush=True)
 print('PASS',a.profile,'; peripheriques et timer simules, aucun resultat CPU/audio materiel revendique',flush=True)
if __name__=='__main__':main()
