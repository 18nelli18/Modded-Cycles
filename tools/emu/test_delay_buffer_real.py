"""Regression v60 : ne pas forcer un faux pointeur DMA dans le banc natif."""
import sys,struct,json
from pathlib import Path
from test_new_delays import native_rig,IN,OUT
from boot_candidate import ROOT
for version in ('v60','v61'):
 stem='validation/all-features-polivoks-cpu-trim-test-'+version;r,s,m,mac=native_rig(stem);u=r.u;work=r.r32(0x8000b570);assert work==0x8000b590
 for name,val in [('cr_mode',5),('nd_ready',1),('nd_active',5),('nd_gain',256),('nd_prior',256)]:r.w32(s[name],val)
 u.mem_write(IN,struct.pack('>64i',*([100000000,100000000]*32)));u.mem_write(IN+1024,struct.pack('>2h',11000,12000));r.call('fx_dfx',OUT,IN,IN+1024)
 feed=struct.unpack('>64i',u.mem_read(s['nd_feed'],256));expect=not any(feed) if version=='v60' else feed==tuple([100000000,0]*32)
 assert expect,(version,feed[:8]);assert any(u.mem_read(work,256))==(version=='v61')
 print('PASS',version,'native initialized pointer',hex(work),'silent bug reproduced' if version=='v60' else 'source and feedback nonzero, no forced pointer',flush=True)
