"""Repro : preferences synchronisees alors que DATA vient de bouger."""
from pathlib import Path
import sys,json,struct
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from test_fx_menu_control import fixture
from test_seq_gen_menu import EVENT
v=sys.argv[1] if len(sys.argv)>1 else 'v211';stem='staging/all-features-polivoks-cpu-trim-test-'+v;m=json.loads((R/'output/firmware'/(stem+'.json')).read_text());r,s,h,l,files,key,turn,data,bind=fixture(stem);fc=m['filter_modes']['symbols'];lp=m['lfo_polarity']['symbols'];u=r.u
def write(path):return path in files
r.call(0x468d0120,0,1);r.w32(lp['lp_dirty'],1);r.w32(0xfc07000c,1000000)
u.mem_write(EVENT,struct.pack('>6I',0x400fbebc,0,1,0,0,0));r.delta=1;r.call(0x400775f8,0,EVENT)
assert r.call(s['fx_input_quiet'])==0
r.call(fc['fc_frame']);r.call(lp['lp_frame']);print(v,'writes immediately after DATA',list(files),flush=True)
if m.get('ui_idle'):
 assert not write('/Filter.cfg') and not write('/LfoPol.cfg')
 for i in range(20):
  r.w32(0xfc07000c,1000000+i*13516800);r.call(0x400775f8,0,EVENT);r.call(fc['fc_frame']);r.call(lp['lp_frame']);assert not files
 r.w32(0xfc07000c,1000000+19*13516800+150000000);r.call(fc['fc_frame']);r.call(lp['lp_frame']);assert write('/Filter.cfg') and write('/LfoPol.cfg')
 print('PASS writes postponed during input; exact settings flush after idle',flush=True)
else:
 assert write('/Filter.cfg') and write('/LfoPol.cfg');print('PASS reproduced synchronous config writes during active encoder use',flush=True)
