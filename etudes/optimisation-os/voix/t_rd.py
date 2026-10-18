from unicorn import *
from unicorn.m68k_const import *
import unicorn
print(unicorn.__version__)
uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
uc.ctl_set_cpu_model(UC_CPU_M68K_CFV4E) if hasattr(uc, "ctl_set_cpu_model") else None
uc.mem_map(0x1000, 0x1000); uc.mem_map(0x40000000, 0x10000)
# move.l (a0),d0 ; move.l d0,4(a0) ; move.l 8(a0),d1 ; nop
code = bytes.fromhex("2010" "21400004" "22280008" "4e71")
uc.mem_write(0x1000, code)
uc.reg_write(UC_M68K_REG_A0, 0x40000100)
ev = []
uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, lambda u, acc, a, s, v, d: ev.append((acc, hex(a), s)))
uc.emu_start(0x1000, 0x1000 + len(code))
print(ev)
