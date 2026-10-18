import collections
from prof import *
from unicorn import UC_HOOK_MEM_READ
img = load_stock()
e = E.Engine(img)
e.set(0, machine=0)
e.block(1)
c = collections.Counter()
h = e.uc.hook_add(UC_HOOK_MEM_READ | 2048, lambda uc, acc, a, s, v, d: c.__setitem__((acc, region(a)), c[(acc, region(a))] + 1))
e.block(0)
print("lecture seule", dict(c))
e.uc.ctl_flush_tb(); c.clear()
e.block(0)
print("après vidage des TB", dict(c))
