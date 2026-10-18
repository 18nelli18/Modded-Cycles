from prof import *
img = load_stock()
def rv(e, t, o): return struct.unpack(">i", bytes(e.uc.mem_read(E.VOICE0 + t*E.VSTRIDE + o, 4)))[0]
for m in range(6):
    e = E.Engine(img); e.machine_defaults(0, m); e.solo(0)
    first0 = None; hist = []
    for b in range(6000):
        o = e.block(1 if b == 1 else 0)[0]
        pk = int(np.abs(o).max())
        st = (rv(e,0,0x230), rv(e,0,0x234), rv(e,0,0x23c), rv(e,0,0x2a8), rv(e,0,0x2ac), rv(e,0,0x2b0))
        if b in (0,1,2,3,4,10,100,1000) : print(m, b, pk, st)
        if b > 2 and st[0] == 0 and st[1] == 0 and first0 is None:
            first0 = b; print(m, "niveau à 0 au bloc", b, "crête", pk, st)
        if first0 is not None and b > first0 + 3 and (m != 1 or (st[3] == 0 and st[4] == 0)):
            print(m, "fin", b, pk, st); break
    else:
        print(m, "jamais à 0 en 6000 blocs", st, pk)
