from prof import *
img = load_stock()
e = E.Engine(img); e.machine_defaults(0, 0); e.solo(0)
p = Prof(e.uc, e.emac, record=False); p.on=False
e.block(1)
log=[]
def dbg(uc,a,s,u):
    if p.on: log.append((a, len(p.stack), p.stack[-1][0]))
e.uc.hook_add(UC_HOOK_CODE, dbg)
p.reset(); p.on=True
e.block(0)
prev=None
for a,n,f in log:
    if (n,f)!=prev: print(hex(a), n, hex(f)); prev=(n,f)
