import sys, struct
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu"); sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import mcengine as E
from unicorn import UC_HOOK_CODE
img = open("/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin","rb").read()
e = E.Engine(img)
cnt = {}
def hk(uc, a, s, u):
    cnt[a] = cnt.get(a, 0) + 1
e.uc.hook_add(UC_HOOK_CODE, hk)
for t in range(6): e.machine_defaults(t, t)
e.block(0x3f)
cnt.clear()
e.emac.count = 0
e.block(0)
emac_addrs = set(e.emac.ops)
print("total", sum(cnt.values()), "emac seen by global hook", sum(v for a, v in cnt.items() if a in emac_addrs), "emac slow count", e.emac.count)
