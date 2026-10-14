"""Rejouer la copie CHORD du vrai bootstrap MACRO avant les bancs DSP.

Les charges MACRO/ACID laissent ces tables nulles dans le flux compressé,
puis leur propre boot2 les copie depuis la SRAM initialisée par l'OS. Aucun
octet d'OS n'est conservé dans ce fichier ; on exécute le code propre du tweak.
"""
import struct
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN
from unicorn import m68k_const as m
import build

def boot_chord_waves(stock,destination,runtime):
 prefix=bytes.fromhex('41f980001c5c43f9')
 sites=[i for i in range(len(runtime)) if runtime.startswith(prefix,i)]
 if not sites:return runtime
 assert len(sites)==1,'copie CHORD ambiguë'
 at=sites[0];code=runtime[at:at+42];target=struct.unpack_from('>I',code,8)[0]
 assert code[12:24].hex()=='203c0000161622d8538066fa'
 assert code[24:42].hex()=='41f98000cac0203c0000080822d8538066fa'
 count=0x5858+0x2020;offset=target-destination
 assert 0<=offset<=len(runtime)-count and runtime[offset:offset+count]==bytes(count)
 u=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);u.ctl_set_cpu_model(m.UC_CPU_M68K_ANY);u.reg_write(m.UC_M68K_REG_SR,0x2000)
 u.mem_map(destination,(len(runtime)+0xfffff)&~0xfffff);u.mem_write(destination,runtime);u.mem_map(0x80000000,0x20000)
 for lo,hi,dst in ((0x4019b590,0x401a2a50,0x80000000),(0x401a2a50,0x401aa140,0x80008000)):
  u.mem_write(dst,stock[lo-build.BASE:hi-build.BASE])
 expected=bytes(u.mem_read(0x80001c5c,0x5858))+bytes(u.mem_read(0x8000cac0,0x2020))
 assert any(expected)
 u.emu_start(destination+at,destination+at+42,count=100000)
 assert u.reg_read(m.UC_M68K_REG_PC)==destination+at+42
 assert bytes(u.mem_read(target,count))==expected
 assert u.reg_read(m.UC_M68K_REG_A1)==target+count
 final=bytearray(runtime);final[offset:offset+count]=expected
 return bytes(final)
