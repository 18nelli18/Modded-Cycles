"""145 : MACRO47modeles, modes FINE et melange HALL+Sidechain, PCM exact144."""
from pathlib import Path
import sys,json,struct
import numpy as np
R=Path(__file__).resolve().parents[2];W=R/'output/firmware';sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_wizard_playback import fixtures
from unicorn import m68k_const as C
import mcengine as E
v=sys.argv[1] if len(sys.argv)>1 else 'v149'
old='staging/all-features-polivoks-cpu-trim-test-v148';new='staging/all-features-polivoks-cpu-trim-test-'+v
if '--mixed-only' not in sys.argv:
 es=fixtures(False,127,0,[old],audit_count=False)+fixtures(False,127,0,[new],audit_count=False)
 for model in range(47):
  for e in es:
   e.uc.reg_write(C.UC_M68K_REG_SR,0x2700)
   for t in range(6):
    e.call(E.VOICE_RESET,E.VOICE0+t*E.VSTRIDE);e.set(t,machine=12 if t==0 else 17,note=48,pitch=64,finetune=64,shape=model,color=64,sweep=68,contour=40,decay=110,punch=1,gate=1)
  for b in range(8):
   outs=[]
   for e in es:
    if b==2:e.set(0,color=110,sweep=17,contour=80)
    if b==4:e.set(0,finetune=40)
    if b==6:e.set(0,finetune=90)
    outs.append(e.block(1 if b in (0,3,6) else 0,1 if b==5 else 0))
   assert np.array_equal(*outs),(model,b)
   assert es[0].emac.macsr==es[1].emac.macsr and es[0].emac.mask==es[1].emac.mask
  print('PASS delivered MACRO model',model,'PCM exact, FINE rate/bits, live controls, retrigger/release, MACSR/MASK',flush=True)
