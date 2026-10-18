from unicorn import *
from unicorn.m68k_const import *
uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
uc.mem_map(0x1000, 0x1000); uc.mem_map(0x40000000, 0x10000)
code = bytes.fromhex("2010" "21400004" "22280008" "4e71")
uc.mem_write(0x1000, code)
uc.reg_write(UC_M68K_REG_A0, 0x40000100)
uc.emu_start(0x1000, 0x1000 + len(code))
ev = []
uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, lambda u, acc, a, s, v, d: ev.append((acc, hex(a), s)))
uc.emu_start(0x1000, 0x1000 + len(code))
print("sans vidage", ev)
ev.clear(); uc.ctl_flush_tb()
uc.emu_start(0x1000, 0x1000 + len(code))
print("après ctl_flush_tb", ev)
