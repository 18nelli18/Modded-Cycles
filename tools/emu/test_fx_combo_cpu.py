"""v74 : mixeur natif, Vinyl/chorus+reverb/crush+delay, sends/pans/stereo.
PCM exact face a v73 ; instructions du mixeur, pas CPU materiel.
"""
import sys,json,struct,random
from unicorn import UC_HOOK_CODE
from test_fx_menu_audio import fixture
from test_delay_crush_sends import setup,run
from test_fx_cpu import ROOT
import mcengine as E
OLD='validation/all-features-polivoks-cpu-trim-test-v73';NEW=sys.argv[1] if len(sys.argv)>1 else 'staging/all-features-polivoks-cpu-trim-test-v75'

def prep(f,rev,cr,amount,pan=64,side=False):
 e,m,sy,g=f;u=e.uc;setup(f,cr,[amount]*6,[amount]*6,pan=pan,tracks=tuple(range(6)));s=m['fx_menu']['symbols']
 for t in range(6):u.mem_write(E.PARAMS+56+66*t,struct.pack('>H',amount*256))
 for name,value in [('ch_mode',rev),('active',rev),('ready',1),('gain',256),('prior_gain',256),('fx_crackle',50),('fx_warble',50),('fx_wspeed',40)]:u.mem_write(s[name],struct.pack('>I',value))
 for name in ('fx_aux_ch','fx_aux_vi'):u.mem_write(s[name],struct.pack('>6I',*([amount]*6)))
 # Restaurer la vraie banque native du Delay, le vieux banc v53 utilisait a560.
 u.mem_write(0x8000b570,struct.pack('>I',0x8000b590))
 b=m['beat_repeat_symbols'];addr=0x40712000;flags=0x40713000
 u.mem_write(b['br_side'],struct.pack('>I',addr));u.mem_write(b['br_side_on'],struct.pack('>I',flags))
 u.mem_write(flags,struct.pack('>6I',*([1,0,1,0,0,0] if side else [0]*6)))
 u.mem_write(addr,struct.pack('>192i',*[int(90000000*((i%13)-6)/6) for i in range(192)]))
 return s

def main():
 rows=[];cases=[(rev,0,send,pan,st) for rev in (3,4,5,6) for send,pan,st in ((90,64,False),(127,21,True))]
 cases += [(0,cr,send,pan,st) for cr in (3,4) for send,pan,st in ((90,64,False),(127,21,True))]
 for n,(rev,cr,amount,pan,side) in enumerate(cases):
  fs=[fixture(stem,0) for stem in (OLD,NEW)];cost=[0,0];ss=[prep(f,rev,cr,amount,pan,side) for f in fs]
  for b in range(24):
   got=[]
   for j,f in enumerate(fs):
    e,m,sy,g=f
    if b==16:
     for t in range(6):
      e.uc.mem_write(E.PARAMS+54+66*t,bytes(2));e.uc.mem_write(E.PARAMS+56+66*t,bytes(2))
     for name in ('fx_aux_ch','fx_aux_vi'):e.uc.mem_write(ss[j][name],bytes(24))
     e.uc.mem_write(sy['cr_send'],bytes(24))
    counter=[0];h=e.uc.hook_add(UC_HOOK_CODE,lambda *a,counter=counter:counter.__setitem__(0,counter[0]+1))
    g=run(f,1);e.uc.hook_del(h);cost[j]+=counter[0]
    got.append((g['post'],g['wet'],g['rev_wet']))
   assert got[0]==got[1],('PCM',rev,cr,amount,pan,side,b,[k for k,(a,z) in enumerate(zip(*got)) if a!=z])
   for name,sz in [('gain_aux',48),('aux',256),('effect',256),('correction',256),('dust_seed',8),('dust_gain',8)]:
    # Buffers de travail hors branche active peuvent rester volontairement non ecrits.
    if name in ('effect','aux') and (amount==0 or b>=17):continue
    if name in ('aux','effect','correction') and rev not in (3,4,5,6):continue
    assert fs[0][0].uc.mem_read(ss[0][name],sz)==fs[1][0].uc.mem_read(ss[1][name],sz),('FX state',rev,cr,amount,pan,side,b,name)
  row=dict(reverb=rev,delay=cr,send=amount,pan=pan,stereo_source=side,instructions=cost,saving=1-cost[1]/cost[0],blocks=24);rows.append(row);print('PASS mixer exact',row,flush=True)
 (ROOT/('output/firmware/fx-combo-proof-'+NEW.rsplit('-',1)[-1]+'.json')).write_text(json.dumps(dict(candidate=NEW,sha256=fs[1][1]['sha256'],rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
