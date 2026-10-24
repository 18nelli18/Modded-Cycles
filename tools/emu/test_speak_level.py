import sys,struct,json
import numpy as np
from test_fx_menu_audio import fixture
from test_delay_crush_sends import setup,run
from boot_candidate import ROOT
import mcengine as E
NEW=sys.argv[1];rows=[]
for stem,machine,shape in (('validation/all-features-polivoks-cpu-trim-test-v84',20,31),(NEW,20,31),(NEW,4,38)):
 f=fixture(stem,0);e,m,sy,g=f
 setup(f,0,[0]*6,[0]*6,tracks=(5,));e.set(5,machine=0);e.block(0);e.set(5,machine=machine,note=60,pitch=64,color=64 if machine==20 else 40,shape=shape,sweep=64 if machine==20 else 52,contour=80 if machine==20 else 42,punch=0,decay=127)
 vals=[];raw=[]
 for b in range(250):
  e.uc.mem_write(E.PARAMS+14+66*5+38,struct.pack('>H',60*256));x=e.block(32 if b==0 else 0);raw.extend(x[5])
  if b%25==24:
   z=run(f,1)
   if b>=74:vals.extend(struct.unpack('>64i',z['post']))
 a=np.array(vals)/2147483648;x=np.array(raw)/2147483648
 row=dict(candidate=stem,machine=machine,word=shape,volume=60,voice_peak=float(abs(x).max()),voice_rms=float(np.mean(x*x)**.5),mix_peak=float(abs(a).max()),mix_rms=float(np.mean(a*a)**.5));rows.append(row);print('MEASURE',row,flush=True)

assert rows[1]['mix_rms']>rows[0]['mix_rms']*20,rows
assert rows[1]['mix_rms']>rows[2]['mix_rms']*.25,rows
assert rows[1]['mix_peak']<.8,rows
(ROOT/'output/firmware'/('speak-level-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(dict(rows=rows,hardware_tested=False),indent=2)+'\n')
print('PASS native Vol+Dist60: speech level comparable to Tone in this fixture, large gain over84, no hard-clipped mix samples',flush=True)
