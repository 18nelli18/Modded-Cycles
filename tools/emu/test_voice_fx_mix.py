"""v74 : vrais sixmoteurs, lineup utilisateur et Syntakt, resonateur SRAM exact.
USB/FX/deadlines physiques ne sont pas simules par ce banc voix.
"""
import json,random,struct
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_wizard_playback import fixtures,ROOT
from profile_all_machines_cpu import DEFAULT
import mcengine as E
OLD='validation/all-features-polivoks-cpu-trim-test-v73';NEW='validation/all-features-polivoks-cpu-trim-test-v74'

def main():
 report=[]
 for machine in (7,8,9,10,11,-1):
  es=[fixtures(False,127,0,[stem],native_chordkeys=True)[0] for stem in (OLD,NEW)];rng=random.Random(741+machine);counts=[[],[]];calls=[0,0]
  for j,e in enumerate(es):
   for lane,m in enumerate((0,1,2,3,11,4)):
    e.set(lane,machine=m,**dict(zip(('color','shape','sweep','contour'),DEFAULT[m])))
   if machine>=0:e.set(5,machine=machine,**dict(zip(('color','shape','sweep','contour'),DEFAULT[machine])))
   def alias_check(u,pc,size,data,j=j):
    sp=u.reg_read(C.UC_M68K_REG_A7);out,n,state=struct.unpack('>III',u.mem_read(sp+4,12))
    if 0<n<10000:assert not (out<state+16 and out+4*n>state),('resonator alias',j,hex(out),n,hex(state))
    calls[j]+=1
   e.uc.hook_add(UC_HOOK_CODE,alias_check,begin=0x80003470,end=0x80003470)
  for b in range(32):
   change={}
   if b%4==0:
    for lane in range(6):
     vals=[rng.randrange(128) for _ in range(4)]
     if es[0].trk[lane]['machine']==10:vals[0]=rng.randrange(40,89)
     change[lane]=dict(zip(('color','shape','sweep','contour'),vals));change[lane].update(note=(24,60,96,127)[b//4%4],decay=(28,64,100,127)[b//4%4],punch=b//4%2,gate=b//8%2)
   out=[]
   for j,e in enumerate(es):
    for lane,kw in change.items():e.set(lane,**kw)
    e.count=0;out.append(e.block(63 if b%4==0 else 0,63 if b%12==10 else 0));counts[j].append(e.count)
   assert np.array_equal(*out),('PCM',machine,b)
   assert es[0].uc.mem_read(E.VOICE0,6*E.VSTRIDE)==es[1].uc.mem_read(E.VOICE0,6*E.VSTRIDE),('voices',machine,b)
   ram=[bytes(e.uc.mem_read(0x80000000,0x10000)) for e in es];off=0x3470
   assert ram[0][:off]+ram[0][off+62:]==ram[1][:off]+ram[1][off+62:],('SRAM',machine,b)
   assert es[0].uc.mem_read(0x46720000,0x11000)==es[1].uc.mem_read(0x46720000,0x11000),('Syntakt state/RNG',machine,b)
   assert es[0].emac.macsr==es[1].emac.macsr and [es[0].emac.physical(k) for k in range(4)]==[es[1].emac.physical(k) for k in range(4)],('EMAC',machine,b)
  assert calls[0]==calls[1] and not any(e.unmapped for e in es)
  row=dict(machine=machine,blocks=32,instructions=[sum(x) for x in counts],peak=[max(x) for x in counts],nonaliasing_resonator_calls=calls[0]);report.append(row)
  print('PASS six-voice PCM/state/EMAC exact, nonaliasing resonator buffers',row,flush=True)
 (ROOT/'output/firmware/voice-fx-mix-v74.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
