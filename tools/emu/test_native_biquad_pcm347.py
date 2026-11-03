"""Biquad natif en registres : PCM, etat des voix et EMAC identiques sur24blocs."""
from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))
from native_biquad347 import apply
from gen_governor_recovery_test import read
import copy
native=bytearray(e.uc.mem_read(0x40000400,0x1ffc00));sram=bytearray(e.uc.mem_read(0x80000000,65536));rom=read(DEV/'firmware/model-cycles_OS1.13.syx')[2]
runtime=bytearray(e.uc.mem_read(0x46700000,0x300000))
d=apply(meta,native,runtime,rom,W/'module');at=d['code'];n=d['code_bytes'];e.uc.mem_write(at,bytes(runtime[at-0x46700000:at-0x46700000+n]));ops=emac.disasm(str(W/'module/native-biquad.bin'),at,at,at+n);e.emac.install(ops)
site=0x400a9cf6;old_fast={a:e.emac.fast[a] for a in e.emac.fast if site<=a<site+6};old_next={a:e.emac.next[a] for a in old_fast};prior_slow=e.emac._slow;optimized=False
def patched_guard(uc,address):
 if optimized and site<=address<site+6:return
 return prior_slow(uc,address)
e.emac._slow=patched_guard
from collections import Counter
hits=Counter()
def count_paths(uc,at,*unused):
 if optimized:hits[at]+=1

e.uc.hook_add(UC_HOOK_CODE,count_paths,begin=d['code'],end=d['code'])
regions=[(a,b-a+1) for a,b,permissions in e.uc.mem_regions() if a<0xfc000000];rows=[]
for label,machines in [('stock',[0,1,2,3,4,5]),('added',[7,8,9,10,11,0])]:
 hits.clear()
 for patch in d['patches']:e.uc.mem_write(patch['at'],bytes.fromhex(patch['old']));e.uc.ctl_remove_cache(patch['at'],patch['at']+len(bytes.fromhex(patch['old'])))
 for t,machine in enumerate(machines):
  e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=machine,note=48+3*t,color=64,shape=64,sweep=64,contour=64,decay=110,punch=1,gate=0)
 for t in range(6):e.uc.mem_write(E.VOICE0+t*E.VSTRIDE+56,struct.pack('>I',1))
 saved=[bytes(e.uc.mem_read(a,n)) for a,n in regions];context=e.uc.context_save();tracks=copy.deepcopy(e.trk);mode=e.emac.macsr;acc=[e.emac.physical(i) for i in range(4)];outputs=[]
 for optimized in (False,True):
  for (a,n),data in zip(regions,saved):e.uc.mem_write(a,data)
  e.uc.context_restore(context);e.trk=copy.deepcopy(tracks);e.emac.macsr=mode
  for i,value in enumerate(acc):e.emac.put_physical(i,value)
  for patch in d['patches']:e.uc.mem_write(patch['at'],bytes.fromhex(patch['new'] if optimized else patch['old']));e.uc.ctl_remove_cache(patch['at'],patch['at']+len(bytes.fromhex(patch['old'])))
  for a in old_fast:e.emac.fast.pop(a,None);e.emac.next.pop(a,None)
  if not optimized:e.emac.fast.update(old_fast);e.emac.next.update(old_next)
  blocks=[]
  for block in range(12):
   for t in range(6):e.set(t,color=[0,64,127][block//4],shape=[0,64,127][block//4])
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2700);pcm=e.block(63 if block in (0,4,8) else 0)
   actual=[int.from_bytes(e.uc.mem_read(E.VOICE0+t*E.VSTRIDE,4),'big') for t in range(6)]
   assert actual==machines,(label,block,optimized,actual,machines)
   blocks.append((pcm.copy(),bytes(e.uc.mem_read(E.VOICE0,6*E.VSTRIDE)),e.emac.macsr,[e.emac.physical(i) for i in range(4)]))
  outputs.append(blocks)
 for block,(x,y) in enumerate(zip(*outputs)):assert np.array_equal(x[0],y[0]) and x[1:]==y[1:],(label,block)
 if label=='stock':assert hits[d['code']]>0,(label,'biquad non execute')
 rows.append(dict(case=label,blocks=12,PCM_voice_state_EMAC_exact=True,biquad_calls=hits[d['code']]));print('PASS full native-biquad pipeline',label,flush=True)
args.output.write_text(json.dumps(dict(cases=rows,hardware_cycles=False),indent=2)+'\n')
