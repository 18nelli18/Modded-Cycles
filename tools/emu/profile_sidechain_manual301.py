"""Cout borne du correctif sidechain : instructions emulees, pas cycles CPU."""
from pathlib import Path
src=Path(__file__).with_name('test_sidechain_manual301.py').read_text().split('setup(4,5,True,16,0);live(4);process();assert')[0]
exec(compile(src,__file__,'exec'))
counts={}
for active in (False,True):
 cfg=[]
 for t in range(6):cfg.extend([63&~(1<<t) if active else 0,15,0,1,0])
 u.mem_write(sy['du_config'],bytes(cfg));u.mem_write(sy['du_fx'],bytes([3 if active else 0]*6));r.w32(sy['initialized'],0);r.call(sy['du_reset']);r.w32(0x800017ac,0);r.w32(0x800017b0,0)
 for t in range(6):note(t,1)
 fill();n=[0];hook=u.hook_add(UC_HOOK_CODE,lambda *args:n.__setitem__(0,n[0]+1));r.call(sy['du_process']);u.hook_del(hook);counts['active' if active else 'disabled']=n[0]
print('COST',fixed,counts,flush=True);a.output.write_text(json.dumps(dict(fixed=fixed,emulated_instructions=counts,not_hardware_cycles=True),indent=2)+'\n')
