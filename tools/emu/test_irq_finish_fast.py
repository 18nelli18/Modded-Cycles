"""Bilan IRQ avant/apres : compteurs exacts, bornes et wrap timer, ABI preservee."""
from pathlib import Path
src=Path(__file__).with_name('test_complete_irq_accounting.py').read_text().split('rows=[]')[0]
exec(compile(src,__file__,'exec'))
from unicorn import UC_HOOK_CODE
import random
fg=m['irq_finish_fast'];entry=fg['hook'];optimized=bytes(r.u.mem_read(entry,6));original=bytes.fromhex(fg['original_prefix']);rng=random.Random(293);rows=[]
irq=ps['gb_irq_active'];dx=ps['gb_enabled'];regions=[(irq-16,20),(dx-12,16),(ps['gb_blocks'],8)]
regs=[getattr(C,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(C,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
for case in range(384):
 elapsed=rng.choice([0,1,90111,90112,90113,901119,901120,901121,0xffffffff,rng.getrandbits(32)]);start=rng.getrandbits(32);now=(start+elapsed)&0xffffffff;budget=rng.choice([0,start,now,(now+100)&0xffffffff]);active=rng.choice([0,1,2]);enabled=rng.choice([0,1,2]);playing=rng.choice([0,1,2]);seed=[rng.getrandbits(32) for _ in regs]
 values={'gb_irq_active':active,'gb_irq_t0':start,'gb_budget_t0':budget,'gb_last_total':rng.getrandbits(32),'gb_last_tail':rng.getrandbits(32),'gb_enabled':enabled,'gb_peak':rng.choice([0,90112,0xffffffff,rng.getrandbits(32)]),'gb_over':rng.choice([0,9998,9999,0xffffffff]),'gb_sum':rng.getrandbits(32),'gb_blocks':rng.choice([0,999999,1000000,0xffffffff])};states=[];cost=[]
 for code in (original,optimized):
  r.u.mem_write(entry,code);r.u.ctl_remove_cache(entry,entry+64)
  for name,value in values.items():r.w32(ps[name],value)
  r.w32(0x40a7883c,playing)
  for reg,value in zip(regs,seed):r.u.reg_write(reg,value)
  n=[0];hook=r.u.hook_add(UC_HOOK_CODE,lambda *unused:n.__setitem__(0,n[0]+1));r.call(entry,now);r.u.hook_del(hook);cost.append(n[0]);assert [r.u.reg_read(reg) for reg in regs]==seed
  states.append([bytes(r.u.mem_read(at,length)) for at,length in regions])
 assert states[0]==states[1],(case,values,elapsed)
 assert cost[1]<=cost[0],(case,cost)
 rows.append(dict(active=active,stats=bool(enabled and playing==1),elapsed=elapsed,before=cost[0],after=cost[1]))
r.u.mem_write(entry,optimized);r.u.ctl_remove_cache(entry,entry+64)
print('PASS384 IRQ finish cases: exact counters, caps, unsigned wrap and ABI; never more executed instructions',flush=True)
print('INSTRUCTIONS',sum(x['before'] for x in rows)/len(rows),sum(x['after'] for x in rows)/len(rows),flush=True)
a.output.write_text(json.dumps(dict(cases=len(rows),rows=rows,hardware_cycles=False,hardware_tested=False),indent=2)+'\n')
