"""v73 : veille pitch strictement vide, reveils/stale reset et pics face a v72."""
import sys,json,struct,random
from test_fx_cpu import rig,counted,IN,ROOT
OLD='validation/all-features-polivoks-cpu-trim-test-v72'
NEW=sys.argv[1] if len(sys.argv)>1 else 'validation/all-features-polivoks-cpu-trim-test-v74'
STATE={'nd_ring':65536,'nd_filter':48,'nd_aa':512,'nd_offset':8,'nd_phase':4,'nd_w':4,'nd_filled':4,'nd_aa_w':4,'nd_search_index':4,'nd_search_head':4,'nd_search_channel':4,'nd_search_ready':4,'nd_best_lag':4,'nd_best_error':4,'nd_ap':8192,'nd_ap_pos':16,'nd_ap_fill':16}

def main():
 report={};rng=random.Random(730)
 for mode in (6,7):
  fs=[rig(stem) for stem in (OLD,NEW)];costs={'busy':[[],[]],'idle':[[],[]]}
  for r,s,m in fs:r.w32(s['nd_active'],mode);r.call('fx_shift_reset')
  sleep_blocks=0
  for b in range(1500):
   if b==950:
    for r,s,m in fs:r.call('fx_shift_reset')
   excited=b<24 or 401<=b<425 or 820<=b<830 or 1250<=b<1280
   sig=[rng.randrange(-2147483648,2147483648) for _ in range(64)] if excited else [0]*64
   # Entrees sous le quantum positif : sortie identique au zero, jamais coupees au-dessus.
   if not excited and b%13==0:sig=[rng.randrange(2048) for _ in range(64)]
   idle=fs[1][0].r32(fs[1][1]['nd_zero_blocks'])>=258 and not excited
   sleep_blocks+=idle
   category='idle' if idle else 'busy';measured=b%32==0 or b in (176,177,178,304,305,306,400,401,402,448,449,450,816,820,949,950,1249,1250,1251)
   results=[]
   for i,(r,s,m) in enumerate(fs):
    r.u.mem_write(IN,struct.pack('>64i',*sig))
    if measured:costs[category][i].append(counted(r,'fx_delay_return',IN))
    else:r.call('fx_delay_return',IN)
    results.append(bytes(r.u.mem_read(IN,256))+bytes(r.u.mem_read(s['nd_pitch'],256))+bytes(r.u.mem_read(s['nd_clean'],256)))
   assert results[0]==results[1],('PCM',mode,b)
   for name,n in STATE.items():
    if n>32 and b%64 and b not in (400,401,402,819,820,949,950,1249,1250):continue
    assert bytes(fs[0][0].u.mem_read(fs[0][1][name],n))==bytes(fs[1][0].u.mem_read(fs[1][1][name],n)),('state',mode,b,name)
  assert sleep_blocks>100,sleep_blocks
  summary={key:{'old':v[0],'new':v[1],'reduction':1-sum(v[1])/sum(v[0]),'old_peak':max(v[0]),'new_peak':max(v[1])} for key,v in costs.items()}
  report[str(mode)]=dict(pcm_exact_blocks=1500,sleep_blocks=sleep_blocks,cost=summary)
  print('PASS Shimmer',mode-5,'1500 exact PCM/state blocks, silence/wake/stale reset;', {k:{a:b for a,b in v.items() if a not in ('old','new')} for k,v in summary.items()},flush=True)
 # Signal continuellement actif : isoler le cout de detection de la veille.
 for mode in (6,7):
  fs=[rig(stem) for stem in (OLD,NEW)];cost=[[],[]]
  for r,s,m in fs:r.w32(s['nd_active'],mode);r.call('fx_shift_reset')
  for b in range(512):
   signal=[rng.randrange(-2147483648,2147483648) for _ in range(64)];pcm=[]
   for i,(r,s,m) in enumerate(fs):
    r.u.mem_write(IN,struct.pack('>64i',*signal))
    if b%32==0 or b%64 in (48,49):cost[i].append(counted(r,'fx_delay_return',IN))
    else:r.call('fx_delay_return',IN)
    pcm.append(bytes(r.u.mem_read(IN,256))+bytes(r.u.mem_read(s['nd_pitch'],256)))
   assert pcm[0]==pcm[1],('active PCM',mode,b)
  saving=1-sum(cost[1])/sum(cost[0]);assert saving>.30 if mode==6 else saving>-.005
  report[str(mode)]['continuous_active']={'reduction':saving,'old':cost[0],'new':cost[1],'blocks':512}
  print('PASS continuously active Shimmer',mode-5,'exact PCM, instruction saving',round(saving*100,2),'percent',flush=True)
 # Le relais doit conserver les bits physiques memes si la lecture ACC native
 # aurait sature/arrondi ; modes F/I, SU, OMC et R sont tous couverts.
 from unicorn import m68k_const as C
 r,s,m=rig(NEW);r.w32(s['nd_active'],6)
 regs={getattr(C,'UC_M68K_REG_'+kind+str(i)):0x12340000+i for kind,ix in [('D',range(2,8)),('A',range(2,7))] for i in ix}
 for status in (0,0x20,0x30,0x40,0x60,0xa0,0xb0,0xe0):
  for case in range(8):
   r.mac.macsr=status;raw=[rng.getrandbits(48) for _ in range(4)]
   for k,x in enumerate(raw):r.mac.put_physical(k,x)
   for reg,val in regs.items():r.u.reg_write(reg,val)
   r.u.mem_write(IN,struct.pack('>64i',*[rng.randrange(-2147483648,2147483648) for _ in range(64)]));r.call('fx_shift',IN)
   assert r.mac.macsr==status and [r.mac.physical(k) for k in range(4)]==raw,(status,case)
   assert all(r.u.reg_read(reg)==val for reg,val in regs.items()),(status,case,'ABI')
 report['emac_contexts']=64
 print('PASS all48 physical ACC bits, MACSR and ABI preserved in64 EMAC contexts',flush=True)
 report.update(old=OLD,new=NEW,sha256=m['sha256'],hardware_tested=False,metric='executed instructions, not cycles')
 (ROOT/('output/firmware/fx-idle-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
