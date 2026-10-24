"""Reproduire la reentree du singleton natif, sans singleton projet factice.

Le constructeur est intercepte uniquement pour simuler une frame/progression
pendant la construction. Le getter singleton et l appel FX sont reels.
"""
from pathlib import Path
import sys,json,struct,os
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'tools/emu')]
from boot_candidate import boot
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE,m68k_const as C
version=sys.argv[1] if len(sys.argv)>1 else 'v121';name='all-features-polivoks-cpu-trim-test-'+version
S=Path(os.environ.get('MC_TEST_STAGING_DIR',R/'output/firmware/staging'));m=json.loads((S/(name+'.json')).read_text());s=m['fx_project']['symbols'];im,mem=boot(S/(name+'.syx'))
def scenario(nested):
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(C.UC_CPU_M68K_ANY)
 u.mem_map(0x40000000,0x02400000);u.mem_write(0x40000400,im)
 for at,data in mem:u.mem_map(at,len(data));u.mem_write(at,data)
 u.mem_map(0x93000000,0x200000);u.reg_write(C.UC_M68K_REG_SR,0x2000)
 STOP=0x9300f000;STACK=0x93008000;SHIM=0x93010000
 u.mem_write(0x40fe4228,bytes(4));u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(C.UC_M68K_REG_A7,STACK)
 u.mem_write(SHIM,b'\x4e\xb9'+struct.pack('>I',s['fxp_sync'])+b'\x4e\xf9'+struct.pack('>I',STOP))
 hit=[];alloc=[]
 def malloc(u,at,size,data):
  sp=u.reg_read(C.UC_M68K_REG_A7);n=int.from_bytes(u.mem_read(sp+4,4),'big');alloc.append(n)
  u.reg_write(C.UC_M68K_REG_D0,0x93020000+len(alloc)*0x20000)
  u.reg_write(C.UC_M68K_REG_PC,int.from_bytes(u.mem_read(sp,4),'big'));u.reg_write(C.UC_M68K_REG_A7,sp+4)
 def ctor(u,at,size,data):
  hit.append(at)
  if nested and len(hit)==1:u.reg_write(C.UC_M68K_REG_PC,SHIM)
  else:u.emu_stop()
 u.hook_add(UC_HOOK_CODE,malloc,begin=0x400802e0,end=0x400802e0)
 u.hook_add(UC_HOOK_CODE,ctor,begin=0x4001134e,end=0x4001134e)
 u.emu_start(0x400cf866 if nested else s['fxp_sync'],STOP,count=100_000)
 return hit,alloc,u.reg_read(C.UC_M68K_REG_PC)
for nested in (False,True):
 hits,alloc,pc=scenario(nested)
 if version=='v119':
  assert len(hits)==(2 if nested else 1),(nested,hits,alloc,hex(pc))
  print('REPRODUCED v119: '+('project singleton recursively constructs a second project during a constructor callback' if nested else 'FX sync constructs the project before normal initialization'),flush=True)
 else:
  assert len(hits)==(1 if nested else 0) and pc==0x9300f000,(nested,hits,alloc,hex(pc))
  print('PASS startup '+('constructor callback does not reenter project initialization' if nested else 'FX sync leaves an uninitialized project singleton untouched'),flush=True)
