"""Queue des machines d'origine (OS d'origine, piste seule) : dernier bloc où la sortie de render dépasse 2^13 après
un trig au bloc 1 (réglages par défaut, puis DECAY 20) ; et l'arrêt du prototype (64 blocs plus tard)."""
import sys
import numpy as np
from prof import *
img = load_stock()
NB = 3200
for m in range(6):
    for dec in (None, 20):
        e = E.Engine(img)
        e.machine_defaults(0, m)
        if dec is not None:
            e.set(0, decay=dec)
        e.solo(0)
        pk = []
        for b in range(NB):
            o = e.block(1 if b == 1 else 0)
            pk.append(int(np.abs(o[0]).max()))   # sortie divisée par 2
        pk = np.array(pk)
        loud = np.nonzero(pk >= 4096)[0]
        last = int(loud[-1]) if len(loud) else -1
        print(f"{list(E.MACH)[m]:5s} DECAY {e.trk[0]['decay']:3d} : dernier bloc au-dessus du seuil {last} "
              f"({last / 1500:.2f} s) ; crêtes aux blocs 100/500/1000/2000/3199 : "
              f"{pk[100]} {pk[500]} {pk[1000]} {pk[2000]} {pk[3199]}", flush=True)
