"""145 : filtre MACRO parallele et HALL rapide, calculs identiques a144."""
import subprocess,struct,hashlib
from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
def apply(root,build,prefix,rt,tail,meta,patch):
 from gen_governor_recovery_test import BASE,RUNTIME,TAIL
 from hall_hot145 import prepare
 root=root.resolve();cross=str(root.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-')
 # Les deux noyaux partagent seulement un emplacement existant, sans nouvel etat.
 kernels=[]
 for name in ('halfband_fast.s','parallel145.S'):
  obj=build/(name+'.o');binary=obj.with_suffix('.bin');subprocess.run([cross+'as.exe','-mcpu=54418',str(root/'tools/machines/macro'/name),'-o',str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text',str(obj),str(binary)],check=True);kernels.append(binary.read_bytes())
 old,new=kernels;assert len(old)==len(new)==162
 table=meta['tiny_extra']['data'];render=int.from_bytes(tail[table+4*(24*2+12)-TAIL:table+4*(24*2+12)-TAIL+4],'big');at=render+0xea
 patch(at,old,new,rt)
 code,hall=prepare(root,build)
 assert meta['punch']['code']+meta['punch']['code_bytes']<=hall['code']
 assert hall['end']<0x468ae000 and not any(tail[hall['code']-TAIL:hall['end']-TAIL])
 patch(hall['code'],bytes(len(code)),code,tail)
 target=hall['old_entry'];before=bytes(tail[target-TAIL:target-TAIL+24]);cs=Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040);n=0
 for ins in cs.disasm(before,target):
  assert not ins.mnemonic.startswith(('b','j'));n+=ins.size
  if n>=6:break
 assert n>=6 and n%2==0
 patch(target,before[:n],b'\x4e\xf9'+struct.pack('>I',hall['entry'])+b'\x4e\x71'*((n-6)//2),tail)
 return dict(macro_filter=dict(at=at,size=162,old_sha256=hashlib.sha256(old).hexdigest(),sha256=hashlib.sha256(new).hexdigest(),parallel_loads=True),hall=hall,hall_code_bytes=len(code),hall_hook_size=n,quality_unchanged=True,hardware_tested=False,status='experimental')
