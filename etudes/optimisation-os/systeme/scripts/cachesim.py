#!/usr/bin/env python3
"""Simulation des caches du MCF54415 sur la trace d'un bloc audio complet (trace.py) : 8 Ko d'instructions et 8 Ko
de données, 4 voies, lignes de 16 o, 128 ensembles, LRU (modèle des notes 27-28). Données cachées : 0x40000000..
0x47ffffff seulement (ACR0, copyback) ; SRAM (0x80000000) hors cache ; 0x48000000.. et périphériques : accès non
cachés précis. Coût : 1,54 cycle par instruction + 15 cycles par ligne lue (ou réécrite, copyback) en SDRAM,
166 667 cycles par bloc (même modèle que les notes, étalonné sur la machine).

Scénarios entre deux blocs (ce que fait l'interface pendant les ~23 % de temps libre) :
  chaud    : rien (borne basse : l'audio seul sur la machine) ;
  pollué K : K lignes étrangères (code ou données de l'interface) passent dans chaque cache ;
  vidé     : caches vidés (borne haute, notes/31 §7) ;
et, pour chacun, avec la moitié du cache d'instructions (ou de données) verrouillée (IHLCK / DHLCK) sur les lignes de
l'audio qui rapportent le plus (2 par ensemble).

    python3 cachesim.py trace_play.npz
"""
import random
import sys

import numpy as np

SETS, WAYS, LINE = 128, 4, 16
CPI, MISS, BLOCK = 1.54, 15, 166_667


class Cache:
    def __init__(self, locked=None):
        """locked : {set: [lignes]} gardées dans les voies 0..1 (jamais chassées) ; le reste partage 4 - len."""
        self.sets = [[] for _ in range(SETS)]       # LRU : fin = plus récent
        self.dirty = set()
        self.locked = locked or {}
        self.lockset = set(x for v in self.locked.values() for x in v)
        self.misses = 0
        self.wb = 0
        self.per_line = {}

    def access(self, line, write=False, count=True):
        if line in self.lockset:
            return
        s = line & (SETS - 1)
        lst = self.sets[s]
        if line in lst:
            lst.remove(line)
            lst.append(line)
        else:
            if count:
                self.misses += 1
                self.per_line[line] = self.per_line.get(line, 0) + 1
            cap = WAYS - len(self.locked.get(s, ()))
            if len(lst) >= cap:
                v = lst.pop(0)
                if v in self.dirty:
                    self.dirty.discard(v)
                    if count:
                        self.wb += 1
            lst.append(line)
        if write:
            self.dirty.add(line)

    def flush(self):
        self.sets = [[] for _ in range(SETS)]
        self.dirty = set()

    def pollute(self, k, rng, base):
        for _ in range(k):
            self.access(base + rng.randrange(1 << 16), write=False, count=False)


def blocks(npz):
    z = np.load(npz)
    code, daddr, dw, marks = z["code"], z["daddr"], z["dw"], z["marks"]
    out = []
    for i in range(len(marks) - 1):
        c = code[marks[i][0]:marks[i + 1][0]]
        da = daddr[marks[i][1]:marks[i + 1][1]]
        w = dw[marks[i][1]:marks[i + 1][1]]
        # lignes de code : une par changement de ligne (la lecture d'instructions suit le flot)
        cl = c >> 4
        keep = np.ones(len(cl), bool)
        keep[1:] = cl[1:] != cl[:-1]
        cl = cl[keep]
        cached = (da >= 0x40000000) & (da < 0x48000000)
        sram = (da >= 0x80000000) & (da < 0x80010000)
        unc = ~cached & ~sram & ~((da >= 0x90000000) & (da < 0x9f000000))   # pile du banc exclue
        out.append(dict(n=len(c), code=cl, dl=(da[cached] >> 4), dw=w[cached], unc=int(unc.sum()),
                        sram=int(sram.sum())))
    return out


def run(bl, mode, k=0, ilock=None, dlock=None, passes=3, seed=1):
    rng = random.Random(seed)
    ic, dc = Cache(ilock), Cache(dlock)
    res = None
    for p in range(passes):
        im = dm = wb = n = 0
        for b in bl:
            if mode == "vidé":
                ic.flush()
                dc.flush()
            elif mode == "pollué":
                ic.pollute(k, rng, 0x4000000 + 0x100000)     # code de l'interface (hors lignes audio, en gros)
                dc.pollute(k, rng, 0x4000000 + 0x300000)
            i0, d0, w0 = ic.misses, dc.misses, dc.wb
            for x in b["code"]:
                ic.access(int(x))
            for x, w in zip(b["dl"], b["dw"]):
                dc.access(int(x), bool(w))
            im += ic.misses - i0
            dm += dc.misses - d0
            wb += dc.wb - w0
            n += b["n"]
        nb = len(bl)
        res = dict(instr=n / nb, imiss=im / nb, dmiss=dm / nb, wb=wb / nb,
                   pct=100 * (n * CPI + MISS * (im + dm + wb)) / nb / BLOCK)
    return res, ic, dc


def best_lock(bl, which, mode="vidé", k=0):
    """2 lignes par ensemble : celles qui manquent le plus dans le scénario donné."""
    _, ic, dc = run(bl, mode, k)
    c = ic if which == "i" else dc
    by = {}
    for line, m in c.per_line.items():
        by.setdefault(line & (SETS - 1), []).append((m, line))
    return {s: [l for _, l in sorted(v, reverse=True)[:2]] for s, v in by.items()}


def main():
    bl = blocks(sys.argv[1])
    print(f"bloc moyen : {np.mean([b['n'] for b in bl]):.0f} instructions, "
          f"{np.mean([len(set(b['code'].tolist())) for b in bl]):.0f} lignes de code distinctes, "
          f"{np.mean([len(set(b['dl'].tolist())) for b in bl]):.0f} lignes de données cachées distinctes, "
          f"{np.mean([b['sram'] for b in bl]):.0f} accès SRAM, {np.mean([b['unc'] for b in bl]):.0f} accès non cachés")
    scen = [("chaud", 0), ("pollué", 128), ("pollué", 256), ("pollué", 512), ("pollué", 1024), ("vidé", 0)]
    il = best_lock(bl, "i", "pollué", 512)
    dl = best_lock(bl, "d", "pollué", 512)
    print(f"verrou I : {sum(len(v) for v in il.values())} lignes ; verrou D : {sum(len(v) for v in dl.values())} lignes")
    print(f"{'scénario':14s} {'instr':>7s} {'déf. I':>7s} {'déf. D':>7s} {'réécr.':>7s} {'% bloc':>7s} | "
          f"{'+verrou I':>10s} {'+verrou D':>10s} {'+I et D':>10s}")
    for mode, k in scen:
        r, _, _ = run(bl, mode, k)
        ri, _, _ = run(bl, mode, k, ilock=il)
        rd, _, _ = run(bl, mode, k, dlock=dl)
        rb, _, _ = run(bl, mode, k, ilock=il, dlock=dl)
        name = mode + (f" {k}" if k else "")
        print(f"{name:14s} {r['instr']:7.0f} {r['imiss']:7.0f} {r['dmiss']:7.0f} {r['wb']:7.0f} {r['pct']:7.2f} | "
              f"{ri['pct']:10.2f} {rd['pct']:10.2f} {rb['pct']:10.2f}   "
              f"(I verrou : déf. I {ri['imiss']:.0f} ; D verrou : déf. D {rd['dmiss']:.0f})")


if __name__ == "__main__":
    main()
