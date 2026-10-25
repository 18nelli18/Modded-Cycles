"""Comparaison PCM native : Elder avant boost et Shadow x4 avant mixage."""
from pathlib import Path
import sys,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
v=sys.argv[1] if len(sys.argv)>1 else 'v124';stems=['staging/all-features-polivoks-cpu-trim-test-v122','staging/all-features-polivoks-cpu-trim-test-'+v]
m=json.loads((R/'output/firmware'/(stems[1]+'.json')).read_text());es=fixtures(False,127,0,stems,native_chordkeys=True,audit_count=False)
table=m['tiny_extra']['data'];count=m['tiny_extra']['machine_count'];es[0].uc.mem_write(table+4*(count*2+16),struct.pack('>I',m['fundamentals']['elder_render_original']))
peaks={}
for machine in [16,19]:
 audible=0;peak=0
 for note in [48,60,72]:
  for e in es:
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2000)
   for t in range(6):e.set(t,machine=machine if t==5 else 0,note=note,color=80,shape=100,sweep=80,contour=60,decay=127)
  for b in range(24):
   a,z=[e.block(63 if b in (0,16) else 0) for e in es]
   assert np.array_equal(a[:5],z[:5]),('other lane changed',machine,note,b)
   if machine==16:assert np.array_equal(a[5],z[5]),('Elder',note,b)
   # Le fondu natif de changement de machine contient encore la voix Elder
   # precedente : comparer le gain une fois cette transition terminee.
   elif b>=12:assert np.max(np.abs(z[5]-4*a[5]))<=3,('Shadow gain',note,b,int(np.max(np.abs(z[5]-4*a[5]))))
   peak=max(peak,int(np.max(np.abs(z[5]))));audible+=int(np.any(a[5]))
 assert audible>0,(machine,'silent fixture');peaks[machine]=peak
print('PASS144 native six-voice blocks: Elder exact original PCM, Shadow x4 within final divide rounding, other five lanes exact; peaks',peaks,flush=True)
