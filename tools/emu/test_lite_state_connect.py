"""Reproduire l'ABI incorrecte206 via le vrai connecteur natif, puis207."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
for version in (204,206,207):
 stem=f'staging/all-features-polivoks-cpu-trim-test-v{version}';m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,l,f,k,t,data,bind=fixture(stem)
 connect=m['tiny_extra']['symbols']['state_connect'];seen=[]
 outer,inner=0x931a0000,0x931a0010
 bind(outer,lambda a:seen.append(('OUTER',*a[:3])) or 11)
 bind(inner,lambda a:seen.append(('INNER',*a[:3])) or 22)
 for slot in range(76):
  at=0x40a71754+100*slot;r.u.mem_write(at,bytes(100))
  # Le sous-objet connect est a+20, comme dans les detours approuves Full.
  r.w32(at+8,1);r.w32(at+12,outer);r.w32(at+28,1);r.w32(at+32,inner)
 for slot in range(76):
  seen.clear();owner=0x931b0000+slot*4;assert r.call(connect,slot,owner)==0x40a71500
  expected='OUTER' if version==206 else 'INNER';assert seen==[(expected,0x40a71754+100*slot+(0 if version==206 else 20),owner,0x40a71500)],(version,slot,seen)
 print('PASS',version,'actual native400ddf60 dispatches',expected,'for all76 stock descriptors; correct owner/result and callback arguments',flush=True)
print('PASS206 reproduces wrong callback selection;207 matches verified Full204 native connection ABI',flush=True)
