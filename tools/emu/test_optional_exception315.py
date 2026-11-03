"""Execute le predicat natif branche par Optional ; reproduit le PC fautif."""
from pathlib import Path
import argparse,json,struct,sys
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn import m68k_const as C
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
m=json.loads((a.build/'BUILD.json').read_text());s=m['optional_exception_fix']['symbols'];u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(C.UC_CPU_M68K_ANY)
for at,size in [(0x40000000,0x2400000),(0x46700000,0x300000),(0x90000000,0x20000)]:u.mem_map(at,size)
for name,at in [('native',0x40000400),('runtime',0x46700000)]:u.mem_write(at,(a.capture/(name+'.bin')).read_bytes())
entry=0x401bf4d0;original=bytes.fromhex('0c8000000005');hook=bytes(u.mem_read(entry,6));assert hook==bytes.fromhex('4ef9468d0982')
kit=0x90001000;stack=0x90010000;stop=0x90018000;rows=[]
def call(track,machine,enabled,null=False,baseline=False):
 u.mem_write(entry,original if baseline else hook);u.ctl_remove_cache(entry,entry+6)
 u.mem_write(0x40a78888,struct.pack('>I',0 if null else kit));u.mem_write(kit,bytes(600))
 if track<6:u.mem_write(kit+track*100+66,bytes([machine]))
 u.mem_write(0x468d0ff0,struct.pack('>I',0x7fffff if enabled else 0x7ffeff))
 u.reg_write(C.UC_M68K_REG_SR,0x2700);u.mem_write(stack,struct.pack('>I',stop));u.reg_write(C.UC_M68K_REG_A7,stack);u.reg_write(C.UC_M68K_REG_D0,track);u.reg_write(C.UC_M68K_REG_D1,0x12345678)
 try:u.emu_start(entry,stop,count=1000)
 except Exception:
  print('FAIL PC',hex(u.reg_read(C.UC_M68K_REG_PC)),'D0',hex(u.reg_read(C.UC_M68K_REG_D0)),'A0',hex(u.reg_read(C.UC_M68K_REG_A0)),'track',track,'baseline',baseline,flush=True);raise
 assert u.reg_read(C.UC_M68K_REG_PC)==stop
 assert u.reg_read(C.UC_M68K_REG_A7)==stack+4 and u.reg_read(C.UC_M68K_REG_D1)==0x12345678
 return u.reg_read(C.UC_M68K_REG_D0)
for track in [0,1,2,3,4,5,6,255,0xffffffff]:
 for machine in range(29):
  for null in [False,True]:
   stock=call(track,machine,True,null,True);fixed=call(track,machine,True,null);assert stock==fixed,(track,machine,null,stock,fixed)
   assert call(track,machine,False,null)==0
   rows.append([track,machine,null,fixed])
# Le meme point d'entree, avant correction, saute exactement vers le PC rapporte.
site=s['old_wave_predicate']+8;u.mem_write(site,struct.pack('>I',0x467a9a96));u.ctl_remove_cache(s['old_wave_predicate'],s['old_wave_predicate']+12)
seen=[]
def stop_bad(uc,pc,*unused):seen.append(pc);uc.emu_stop()
h=u.hook_add(UC_HOOK_CODE,stop_bad,begin=0x467a9a96,end=0x467a9a96)
try:call(0,0,True)
except AssertionError:pass
assert seen==[0x467a9a96];u.hook_del(h)
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(dict(cases=len(rows),enabled_matches_native=True,disabled_returns_false=True,ABI_preserved=True,old_reported_PC_reproduced=True,hardware_tested=False),indent=2)+'\n')
print('PASS',len(rows),'native Optional predicate cases; WAVE enabled/disabled, all machines, invalid tracks/null kit, ABI; old reported PC reproduced')
