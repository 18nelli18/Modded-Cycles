"""Le lissage des paramètres (0x40058474) atteint-il un point fixe exact ? (état 0x800011e8 inchangé d'un bloc à l'autre)"""
import sys, struct, random
import numpy as np
from prof import *
img = load_stock()
e = E.Engine(img)
e.emac.macsr = 0x20
TG = 0x800015a0
r = random.Random(3)
vals = [r.randint(-32768, 32767) for _ in range(238)]
vals[:20] = [0, 1, -1, 127 << 8, 64 << 8, 32767, -32768, 100, 255, 256, 12345, -12345, 40 << 8, 88 << 8, 3, 5, 7, 9, 11, 13]
e.uc.mem_write(TG, struct.pack(">238h", *vals))
prev = None
stat_at = None
for it in range(3000):
    e.call(0x40058474, TG)
    st = struct.unpack(">238i", bytes(e.uc.mem_read(0x800011e8, 952)))
    if prev == st and stat_at is None:
        stat_at = it
        break
    prev = st
out = struct.unpack(">238h", bytes(e.uc.mem_read(0x8000100c, 476)))
diff = [(v, o, s) for v, o, s in zip(vals, out, st) if v != o]
print("état stationnaire au bloc", stat_at, "; sorties différentes de la cible :", len(diff), diff[:8])
print("écarts état - cible<<16 :", sorted(set((s - (v << 16)) for v, s in zip(vals, st)))[:10])
