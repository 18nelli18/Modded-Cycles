"""179 : vrai DUB148 stereo, PingPong/Delay146 exacts, controles et etats."""
from pathlib import Path
import sys,struct,json,math
from collections import deque
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_new_delays import native_rig,IN,OUT
rows=[]
def render(version,mode,feedback,source='center'):
 stem='staging/all-features-polivoks-cpu-trim-test-'+version;r,s,m,mac=native_rig(stem);u=r.u;param=IN+1024;u.mem_write(param,struct.pack('>2h',11000,feedback));r.w32(s['cr_mode'],mode)
 for name,value in [('nd_ready',1),('nd_active',mode),('nd_gain',256),('nd_prior',256)]:r.w32(s[name],value)
 ring=deque([bytes(256)]*8);work=r.r32(0x8000b570);output=[]
 for b in range(192):
  raw=ring.popleft();bank=raw+raw[-8:]*2;u.mem_write(work,bank+bank);signal=[]
  for i in range(32):
   x=int(.1*2147483647*math.sin(math.pi*(i+1)/33)) if b==64 else 0
   signal.extend([0 if source=='right' else x,0 if source=='left' else -x if source=='opposed' else x])
  u.mem_write(IN,struct.pack('>64i',*signal));r.call('fx_dfx',OUT,IN,param);ring.append(bytes(u.mem_read(work,256)));output.extend(struct.unpack('>64i',u.mem_read(OUT,256)))
 assert mac.macsr==0xa0 and all(mac.physical(i)==0 for i in range(4))
 y=np.array(output,dtype=np.int64).reshape(-1,2);energy=((y.astype(float)/2147483648)**2).sum(axis=0)
 return y,dict(version=version,mode=mode,feedback=feedback,source=source,energy=energy.tolist(),peaks=np.max(abs(y),axis=0).tolist())
for mode in [0,5,10]:
 for fb in [0,12000]:
  a,ra=render('v146',mode,fb);b,rb=render('v148',mode,fb);assert np.array_equal(a,b),(mode,fb);rows.append(rb);print('PASS native Delay/PingPong/Duck samples exact146',mode,fb,flush=True)
for fb in [0,12000]:
 y,row=render('v148',9,fb);assert row['energy'][0]>0
 # Le feedback natif Delay donne deja jusqu'a14LSB d'ecart L/R sur ce banc.
 # DUB mesure2LSB ; aucun changement de cette arithmetique native.
 row['max_channel_difference_q31']=int(np.max(np.abs(y[:,0]-y[:,1])))
 assert row['max_channel_difference_q31']<=(16 if fb else 0)
 assert abs(row['energy'][1]/row['energy'][0]-1)<1e-8
 rows.append(row);print('PASS DUB centered input L/R level balance from first echo',row,flush=True)
for source in ['left','right','opposed']:
 y,row=render('v148',9,12000,source)
 if source=='left':assert row['energy'][0]>0 and not np.any(y[:,1])
 elif source=='right':assert row['energy'][1]>0 and not np.any(y[:,0])
 else:assert min(row['energy'])>0,'stereo input phase cancellation'
 rows.append(row);print('PASS DUB stereo source preserved',row,flush=True)
old,row=render('v146',9,0);assert not np.any(old[:,0]) and np.any(old[:,1]);print('PASS old146 DUB right-only defect reproduced',flush=True)
(W/'private-v148').mkdir(exist_ok=True);(W/'private-v148/dub-stereo-proof.json').write_text(json.dumps(dict(rows=rows,hardware_tested=False,method='native DSP and feedback; DMA transport modeled at8blocks'),indent=2)+'\n')
print('PASS delivered DUB148 stereo fix with unchanged PingPong/native delay/duck',flush=True)
