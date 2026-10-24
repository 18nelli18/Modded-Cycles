"""v76 : PS1 PCM/etats exacts, conflits quatre voies et mixeur six pistes.
Modele cache LRU idealise8Ko/16o, pas des cycles ni une preuve de gain materiel.
"""
import sys,json,struct,random,math
from collections import Counter
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from test_vinyl_dust import rig,IN,OUT
from test_fx_cpu import counted
from boot_candidate import ROOT
OLD='staging/all-features-polivoks-cpu-trim-test-v75'
NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v76'

class Cache:
 def __init__(self):self.sets=[[] for _ in range(128)];self.miss=self.dirty=self.access=0
 def touch(self,a,write):
  self.access+=1;line=a//16;at=self.sets[line%128];match=next((i for i,e in enumerate(at) if e[0]==line),None)
  if match is None:
   self.miss+=1
   if len(at)==4:self.dirty+=int(at.pop(0)[1])
   entry=[line,write]
  else:entry=at.pop(match);entry[1]|=write
  at.append(entry)

def state(r,s,stride):
 return b''.join(bytes(r.u.mem_read(s['ps_comb']+i*stride*2,4096)) for i in range(8))+b''.join(bytes(r.u.mem_read(s[n],size)) for n,size in [('ps_low',32),('ps_filter',32),('ps_previous',8),('ps_ap',4096),('ps_pos',16),('ps_fill',16),('ps_filled',4),('ps_w',4),('ps_decay',4),('ps_tone',4)])

def main():
 fs=[rig(stem) for stem in (OLD,NEW)];rng=random.Random(760);strides=[f[2]['fx_menu'].get('ps1_comb_stride',2048) for f in fs];assert strides==[2048,2056],strides
 cost=[0,0]
 for r,s,m in fs:r.call('fx_ps1_reset')
 for i in range(8):fs[1][0].u.mem_write(fs[1][1]['ps_comb']+i*4112+4096,b'\x5a'*16)
 for b in range(8192):
  if b in (1400,3600):
   for r,s,m in fs:r.call('fx_ps1_reset')
  sig=[rng.randrange(-2147483648,2147483648) for _ in range(64)] if b%700<64 else [0]*64
  if b%19<9:sig=[sig[i//2*2] for i in range(64)]
  if 1800<=b<2200:
   # Meme partie haute16bits, bas differents : partage entree valide.
   sig=[((rng.randrange(-32768,32768)<<16)|rng.randrange(65536)) for _ in range(32) for c in range(2)]
   for i in range(32):sig[2*i+1]=(sig[2*i]&-65536)|rng.randrange(65536)
  params=struct.pack('>hh',*(((-256,0,16384,32512,32767)[b//73%5]),((-256,0,16384,32512,32767)[b//47%5])))
  got=[]
  for j,(r,s,m) in enumerate(fs):
   r.u.mem_write(IN,struct.pack('>64i',*sig));r.u.mem_write(IN+1024,params)
   if b%256==0:cost[j]+=counted(r,'fx_ps1',OUT,IN,IN+1024)
   else:r.call('fx_ps1',OUT,IN,IN+1024)
   got.append(bytes(r.u.mem_read(OUT,256)))
  assert got[0]==got[1],('PCM',b)
  if b%31==0:assert state(fs[0][0],fs[0][1],strides[0])==state(fs[1][0],fs[1][1],strides[1]),('state',b)
 for i in range(8):assert bytes(fs[1][0].u.mem_read(fs[1][1]['ps_comb']+i*4112+4096,16))==b'\x5a'*16,('padding touched',i)
 assert cost[0]==cost[1],cost
 print('PASS8192 PS1 blocks exact : random/mono/stereo/reset/stale tails/controls, padding untouched, instructions identical',flush=True)
 report={'candidate':NEW,'sha256':fs[1][2]['sha256'],'pcm_exact_blocks':8192,'instructions':cost,'cache_model':'Idealized LRU,8KiB,4ways,16byte lines; PS1 state accesses only; no hardware cycle prediction','cache':[]}
 for r,s,m in fs:
  r.call('fx_ps1_reset');r.u.mem_write(IN+1024,struct.pack('>hh',25600,16384))
  for b in range(160):
   r.u.mem_write(IN,struct.pack('>64i',*[int(500000000*math.sin((32*b+i)*.03+c*.2)) for i in range(32) for c in range(2)]));r.call('fx_ps1',OUT,IN,IN+1024)
  cache=Cache();addresses={s[k] for k in ('ps_tone','ps_decay','ps_fill','ps_pos','ps_w','ps_filled','ps_previous','ps_filter','ps_low','ps_comb','ps_ap')};lo=min(addresses);hi=s['ps_comb']+m['fx_menu'].get('ps1_comb_stride',2048)*16
  def observe(u,access,a,size,value,data):
   for line in range(a//16,(a+size-1)//16+1):cache.touch(line*16,access==UC_MEM_WRITE)
  h=r.u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,observe,begin=lo,end=hi-1);rows=[]
  for b in range(16):
   before=(cache.access,cache.miss,cache.dirty);r.call('fx_ps1',OUT,IN,IN+1024);rows.append([v-z for v,z in zip((cache.access,cache.miss,cache.dirty),before)])
  r.u.hook_del(h);stride=m['fx_menu'].get('ps1_comb_stride',2048);sets=[((s['ps_comb']+2*stride*i)//16)%128 for i in range(8)];report['cache'].append({'stride':stride,'current_write_sets':sets,'rows_access_miss_dirty':rows});print('PASS layout',stride,'write sets',sets,'cache totals',[sum(x[i] for x in rows) for i in range(3)],flush=True)
 assert len(set(report['cache'][0]['current_write_sets']))==1
 assert len(set(report['cache'][1]['current_write_sets']))==8
 for metric in (1,2):assert sum(x[metric] for x in report['cache'][1]['rows_access_miss_dirty'])<sum(x[metric] for x in report['cache'][0]['rows_access_miss_dirty'])/2
 # Le code des autres effets, voix et raccourcis reste exactement celui de v75.
 for name in ('module.bin','chorus.bin','crush.bin','latch.bin','scramble_mask.bin','keep_params.bin','fx_dsp.c.o','fx_delays.c.o','fx_control.c.o','fx_popup.c.o','fx_keys.c.o','fx_hooks.S.o','fx_show.S.o'):
  assert (ROOT/'output/firmware/governor-recovery-v75'/name).read_bytes()==(ROOT/('output/firmware/governor-recovery-'+NEW.rsplit('-',1)[-1])/name).read_bytes(),name
 report['other_modules_exact']=True;report['hardware_tested']=False
 (ROOT/('output/firmware/ps1-cache-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS other DSP/voice/UI modules exact v75',flush=True)
if __name__=='__main__':main()
