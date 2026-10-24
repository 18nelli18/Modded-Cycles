"""v71 : memes PCM/etats que v70, profil instructions par bloc et chemin natif."""
import sys,json,struct,random,math
from pathlib import Path
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_vinyl_dust import rig,IN,OUT
from test_new_delays import native_rig
from boot_candidate import ROOT
OLD='validation/all-features-polivoks-cpu-trim-test-v70'
NEW=sys.argv[1] if len(sys.argv)>1 else 'validation/all-features-polivoks-cpu-trim-test-v71'

def counted(r,fn,*args):
 n=[0];h=r.u.hook_add(UC_HOOK_CODE,lambda *a:n.__setitem__(0,n[0]+1));r.call(fn,*args);r.u.hook_del(h);return n[0]

def main():
 report={};rng=random.Random(710)
 for mode in (6,7):
  fs=[rig(stem) for stem in (OLD,NEW)];costs=[[],[]]
  for r,s,m in fs:r.w32(s['nd_active'],mode);r.call('fx_shift_reset')
  for b in range(600):
   sig=[rng.randrange(-1300000000,1300000001) if b%6 else 0 for _ in range(64)];results=[]
   for i,(r,s,m) in enumerate(fs):
    r.u.mem_write(IN,struct.pack('>64i',*sig))
    if b%16==0 or b in (143,175,191,239,255,303,319,367,383):costs[i].append(counted(r,'fx_delay_return',IN))
    else:r.call('fx_delay_return',IN)
    results.append(bytes(r.u.mem_read(IN,256))+bytes(r.u.mem_read(s['nd_pitch'],256))+bytes(r.u.mem_read(s['nd_clean'],256)))
   assert results[0]==results[1],('PCM',mode,b)
  for name,n in (('nd_ring',65536),('nd_filter',48),('nd_ap',8192),('nd_offset',8),('nd_phase',4),('nd_w',4)):
   assert bytes(fs[0][0].u.mem_read(fs[0][1][name],n))==bytes(fs[1][0].u.mem_read(fs[1][1][name],n)),('state',mode,name)
  for c in range(2):
   old_aa=bytes(fs[0][0].u.mem_read(fs[0][1]['nd_aa']+128*c,128))
   new_at=fs[1][1]['nd_aa']+256*c
   assert old_aa==bytes(fs[1][0].u.mem_read(new_at,128))==bytes(fs[1][0].u.mem_read(new_at+128,128)),('AA mirrored state',mode,c)
  assert sum(costs[1])<sum(costs[0]) and max(costs[1])<max(costs[0]),('instruction regression',mode,costs)
  report[str(mode)]={'baseline_instructions':costs[0],'candidate_instructions':costs[1],'sampled_reduction':1-sum(costs[1])/sum(costs[0]),'max_old':max(costs[0]),'max_new':max(costs[1]),'pcm_blocks_exact':600}
  print('PASS Shimmer',mode-5,'600 blocks PCM/state exact; instruction reduction',round(report[str(mode)]['sampled_reduction']*100,1),'percent; worst',max(costs[0]),'->',max(costs[1]),flush=True)
 # PS1 filtre/feedback et controle changeant : chaque bit reste identique.
 fs=[rig(stem) for stem in (OLD,NEW)];costs=[[],[]]
 for r,s,m in fs:r.call('fx_ps1_reset')
 for b in range(320):
  sig=[rng.randrange(-1800000000,1800000001) if b%3 else 0 for _ in range(64)];params=struct.pack('>hh',(b%128)*256,((b*31)%128)*256);got=[]
  for i,(r,s,m) in enumerate(fs):
   r.u.mem_write(IN,struct.pack('>64i',*sig));r.u.mem_write(IN+1024,params)
   if b%16==0:costs[i].append(counted(r,'fx_ps1',OUT,IN,IN+1024))
   else:r.call('fx_ps1',OUT,IN,IN+1024)
   got.append(bytes(r.u.mem_read(OUT,256)))
  assert got[0]==got[1],('PS1',b)
 report['ps1']={'baseline_instructions':costs[0],'candidate_instructions':costs[1],'sampled_reduction':1-sum(costs[1])/sum(costs[0]),'pcm_blocks_exact':320}
 print('PASS PS1 PCM exact; instruction reduction',round(report['ps1']['sampled_reduction']*100,1),'percent',flush=True)
 # Boucle native : EMAC/ABI et retour des vrais tampons SRAM, DLL seule simulee.
 from collections import deque
 for mode in (5,6,7):
  fs=[native_rig(stem) for stem in (OLD,NEW)];rings=[deque([bytes(256)]*64) for _ in fs]
  for r,s,m,mac in fs:
   for name,v in (('cr_mode',mode),('nd_active',mode),('nd_ready',1),('nd_gain',256),('nd_prior',256)):r.w32(s[name],v)
   r.u.mem_write(IN+1024,struct.pack('>hh',11000,12800))
  for b in range(320):
   sig=[int(200000000*math.sin((32*b+i)*.036)*math.exp(-b/40)) for i in range(32) for c in range(2)];outs=[]
   for i,(r,s,m,mac) in enumerate(fs):
    work=r.r32(0x8000b570);raw=rings[i].popleft();bank=raw+raw[-8:]*2;r.u.mem_write(work,bank+bank);r.u.mem_write(IN,struct.pack('>64i',*sig));r.call('fx_dfx',OUT,IN,IN+1024);rings[i].append(bytes(r.u.mem_read(work,256)));outs.append(bytes(r.u.mem_read(OUT,256))+rings[i][-1]);assert mac.macsr==0xa0 and all(mac.physical(k)==0 for k in range(4))
   assert outs[0]==outs[1],('native',mode,b)
  report[str(mode)+'_native']=True;print('PASS native mode',mode,'320blocks feedback/wet exact, EMAC restored',flush=True)
 report.update(hardware_tested=False,old=OLD,new=NEW,baseline_sha256=fs[0][2]['sha256'],candidate_sha256=fs[1][2]['sha256'],metric='Unicorn executed instruction counts; not hardware cycle timing')
 (ROOT/('output/firmware/fx-cpu-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
