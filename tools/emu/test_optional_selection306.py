"""Optional3.06 : vrai detour encodeur natif, Stk/Sil et masques coherents."""
from pathlib import Path
import argparse,json,struct
from unicorn import UC_HOOK_CODE,m68k_const as C
from test_seq_gen_menu import Rig,STACK,STOP
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);p.add_argument('--cold-root',type=Path);a=p.parse_args();base=a.reference;out=a.generated;m=json.loads((base/'final/optional/full/BUILD.json').read_text());s=m['dummy300']['symbols'];rows=json.loads((out/'rows.json').read_text());order=list(range(17))+list(range(18,28))+[17]

def fixture(native,runtime):
 r=Rig(native,{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,0x300000);r.u.mem_write(0x46700000,runtime);r.u.mem_map(0xfc070000,0x1000)
 return r

def native_step(r,current,delta):
 r.w32(s['committing'],0);r.w32(s['rm_machine_valid'],0);r.w32(STACK,STOP)
 for reg,value in [(C.UC_M68K_REG_A7,STACK),(C.UC_M68K_REG_D0,current),(C.UC_M68K_REG_D5,delta&0xffffffff),(C.UC_M68K_REG_A0,0x93100000),(C.UC_M68K_REG_A1,0x93100010)]:r.u.reg_write(reg,value)
 r.u.emu_start(0x400148aa,0x400148bc,count=100000)
 assert r.u.reg_read(C.UC_M68K_REG_PC)==0x400148bc
 assert r.u.reg_read(C.UC_M68K_REG_A7)==STACK
 assert r.u.reg_read(C.UC_M68K_REG_A0)==0x93100000 and r.u.reg_read(C.UC_M68K_REG_A1)==0x93100010
 return r.u.reg_read(C.UC_M68K_REG_D0)

for row in rows:
 mask=row['mask']
 if not mask:continue
 cold=a.cold_root/str(mask)/'cold' if a.cold_root else None
 native=(cold/'native.bin').read_bytes() if cold and cold.exists() else (base/'cold/optional/full/native.bin').read_bytes()
 runtime=(cold/'runtime.bin').read_bytes() if cold and cold.exists() else (out/f'mask-{mask}.bin').read_bytes()
 r=fixture(native,runtime);want=[i for i in order if i<6 or mask&(1<<(i-6))];actual=[i for i in range(29) if r.call(s['dy_allowed'],i)];assert set(actual)==set(want),(mask,actual,want)
 assert r.r32(0x468d0ff0)==mask and r.r32(0x469c423c)==mask
 # Prouver l ancien echec en restaurant son seul masque MD divergent.
 if mask==1:
  old=fixture(native,runtime);old.w32(0x469c423c,0x3fffff);assert native_step(old,6,1)==7;assert native_step(r,6,1)==6
 selected=[0]
 def bind(at,fn):
  if at not in r.stubs:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
  r.stubs[at]=fn
 for at,fn in [(0x400cf866,lambda _:0x41400000),(0x40012412,lambda _:0),(0x4001e318,lambda _:selected[0]),(0x40076bee,lambda _:0)]:bind(at,fn)
 cases=0
 for current in want:
  for delta in (-1,1):
   expected=want[max(0,min(len(want)-1,want.index(current)+delta))]
   r.w32(s['mb_silent'],0);assert native_step(r,current,delta)==expected,('STK',mask,current,delta,expected)
   selected[0]=current;r.call(s['mb_cancel']);r.w32(s['mb_silent'],1);r.call(s['mb_rotate'],0x93110000,delta&0xffffffff,0,0)
   assert r.r32(s['mb_candidate'])==expected,('SIL',mask,current,delta,r.r32(s['mb_candidate']),expected)
   # Le commit doit reprendre le candidat, sans second pas ni masque divergent.
   r.w32(s['committing'],1);r.w32(STACK,STOP)
   r.u.reg_write(C.UC_M68K_REG_A7,STACK);r.u.reg_write(C.UC_M68K_REG_D0,current);r.u.reg_write(C.UC_M68K_REG_D5,1)
   r.u.emu_start(0x400148aa,0x400148bc,count=100000);assert r.u.reg_read(C.UC_M68K_REG_D0)==expected;r.w32(s['committing'],0);cases+=1
 row.update(native_roster_verified=True,physical_STK_encoder_verified=True,SIL_preview_commit_verified=True,selector_cases=cases,cold_booted=bool(cold and cold.exists()))
 print('PASS physical STK + SIL preview/commit',hex(mask),cases,'cases',flush=True)
(out/'proof.json').write_text(json.dumps(rows,indent=2)+'\n')
