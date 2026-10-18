#!/usr/bin/env python3
"""Plan « SRAM réorganisée » sur la trace d'un bloc (trace.py), modèle de cachesim.py :
  - les 30 tables d'ondes de CHORD quittent la SRAM (0x80001c5c..0x800074b4, 0x8000cac0..0x8000eae0) : leurs lectures
    deviennent des lectures en SDRAM cachée (comme dans les firmwares des moteurs du Syntakt, notes/28) ;
  - le code chaud passe dans la place libérée : voix 0x400a7d10..0x400ab7c0 (15,0 Ko), LFO 0x400918b0..0x40091d90
    (1,2 Ko), lissage + interruption de rendu 0x40058470..0x400597f0 (4,9 Ko) -> zone de 22,6 Ko ; étage de sortie
    0x40056520..0x400582d0 (7,4 Ko) -> zone de 8,2 Ko. Ses lignes ne passent plus par le cache d'instructions (cas
    « SRAM hors cache ») ou y passent avec un remplissage à P cycles au lieu de 15 (cas « SRAM cachée »).
  - option --etats : les états des 6 voix (0x42308828, 6 x 0x31c) en SRAM (il faudrait 4,8 Ko de plus : pas de place
    dans ce plan, chiffre donné pour comparaison).

    python3 cachesim_sram.py trace_play.npz
"""
import sys

import numpy as np

import cachesim as C

HOT = ((0x400a7d10, 0x400ab7c0), (0x400918b0, 0x40091d90), (0x40058470, 0x400597f0), (0x40056520, 0x400582d0))
CHORD = ((0x80001c5c, 0x800074b4), (0x8000cac0, 0x8000eae0))
STATES = (0x42308828, 0x42308828 + 6 * 0x31c)


def transform(bl, states=False):
    out = []
    for b in bl:
        code = b["code"]
        hot = np.zeros(len(code), bool)
        for lo, hi in HOT:
            hot |= (code >= lo >> 4) & (code < hi >> 4)
        nb = dict(b)
        nb["code"] = code[~hot]
        nb["sram_code"] = code[hot]
        out.append(nb)
    return out


def blocks_full(npz, states=False):
    z = np.load(npz)
    code, daddr, dw, marks = z["code"], z["daddr"], z["dw"], z["marks"]
    out = []
    for i in range(len(marks) - 1):
        c = code[marks[i][0]:marks[i + 1][0]]
        da = daddr[marks[i][1]:marks[i + 1][1]].astype(np.int64)
        w = dw[marks[i][1]:marks[i + 1][1]]
        ch = np.zeros(len(da), bool)
        for lo, hi in CHORD:
            ch |= (da >= lo) & (da < hi)
        da2 = da.copy()
        da2[ch] = da[ch] - 0x80000000 + 0x46000000          # tables recopiées en SDRAM cachée (adresse fictive)
        if states:
            st = (da >= STATES[0]) & (da < STATES[1])
            da2[st] = 0x8000f800                              # en SRAM : hors cache
        cl = c >> 4
        keep = np.ones(len(cl), bool)
        keep[1:] = cl[1:] != cl[:-1]
        cl = cl[keep]
        cached = (da2 >= 0x40000000) & (da2 < 0x48000000)
        out.append(dict(n=len(c), code=cl, dl=(da2[cached] >> 4), dw=w[cached], chord=int(ch.sum())))
    return out


def run(bl, mode, k, penalty):
    r, ic, dc = C.run(bl, mode, k)
    extra = 0
    if penalty is not None:                                   # SRAM cachée : ses lignes passent par le cache I
        bl2 = [dict(b, code=np.concatenate([b["code"], b["sram_code"]])) for b in bl]
        r2, ic2, _ = C.run(bl2, mode, k)
        # défauts supplémentaires dus au code en SRAM, comptés à P cycles au lieu de 15
        sram_lines = r2["imiss"] - r["imiss"]
        r = dict(r2)
        r["pct"] = r2["pct"] - sram_lines * (C.MISS - penalty) * 100 / C.BLOCK
    return r


def main():
    npz = sys.argv[1]
    base = C.blocks(npz)
    print(f"{'scénario':12s} | {'origine':>8s} | {'SRAM hors cache':>16s} | {'SRAM cachée P=4':>16s} | "
          f"{'+ états en SRAM':>16s}")
    for states in (False,):
        bl = transform(blocks_full(npz))
        bls = transform(blocks_full(npz, states=True))
        for mode, k in (("chaud", 0), ("pollué", 256), ("pollué", 512), ("vidé", 0)):
            r0, _, _ = C.run(base, mode, k)
            r1 = run(bl, mode, k, None)
            r2 = run(bl, mode, k, 4)
            r3 = run(bls, mode, k, None)
            name = mode + (f" {k}" if k else "")
            print(f"{name:12s} | {r0['pct']:7.2f}% | {r1['pct']:6.2f}% ({r1['pct'] - r0['pct']:+5.2f}) | "
                  f"{r2['pct']:6.2f}% ({r2['pct'] - r0['pct']:+5.2f}) | {r3['pct']:6.2f}% ({r3['pct'] - r0['pct']:+5.2f})"
                  f"   déf. I {r0['imiss']:.0f} -> {r1['imiss']:.0f}, déf. D {r0['dmiss']:.0f} -> {r1['dmiss']:.0f}")
        print("accès aux tables de CHORD par bloc (passés en SDRAM) :", np.mean([b["chord"] for b in bl]))


if __name__ == "__main__":
    main()
