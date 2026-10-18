#!/usr/bin/env python3
"""Coût de l'envoi d'une image à l'écran (0x4008e622, OS 1.13 d'origine) : comparaison des deux tampons de 1 Ko
(0x401492f0 / 0x401492f4) par blocs de 8 x 8 pixels et envoi par DSPI1 des blocs changés (0x4008e580 :
position 3 trames + données 8 trames, par 0x40053e74 qui attend la fin de file, SR bit 28 EOQF).
Le DSPI est modélisé : EOQF toujours levé (attente nulle en émulation) ; le temps de ligne est calculé à part :
trames de 9 bits à 8,448 MHz (CTAR2 0x46000223, notes de ce dossier).

    python3 screencost.py sec3.bin
"""
import random
import sys

from unicorn import UC_HOOK_MEM_WRITE

import isrrig as R

CPU_HZ = (250e6, 270.336e6)


def main():
    img = open(sys.argv[1], "rb").read()
    r = R.Rig(img)
    a, b = 0x41f00000, 0x41f00400
    r.w32(0x401492f0, a)
    r.w32(0x401492f4, b)
    frames = [0]

    def hw(uc, acc, addr, s, v, u):
        if addr == 0xfc03c034:
            frames[0] += 1
        if addr == 0xfc03c02c:                       # l'OS écrit 1 pour effacer EOQF ; le modèle le relève aussitôt
            pass
    r.uc.hook_add(UC_HOOK_MEM_WRITE, hw)
    rng = random.Random(3)
    for label, nchg in (("rien de changé", 0), ("1 bloc", 1), ("16 blocs (une ligne de texte)", 16),
                        ("64 blocs (demi-écran)", 64), ("128 blocs (écran entier)", 128)):
        cur = bytes(rng.randrange(256) for _ in range(1024))
        r.uc.mem_write(a, cur)
        prev = bytearray(cur)
        blocks = rng.sample(range(128), nchg)
        for k in blocks:                             # bloc (d3, j) : octets d3 + 64 j + 8 i (0x4008e63c..)
            page, cb = divmod(k, 16)
            base = page + 64 * cb
            prev[base + 8 * rng.randrange(8)] ^= 0xff
        r.uc.mem_write(b, bytes(prev))
        r.w32(0x401492f0, a)
        r.w32(0x401492f4, b)
        r.uc.mem_write(0xfc03c02c, (1 << 28).to_bytes(4, "big"))
        frames[0] = 0
        # le bit EOQF reste à 1 en RAM : l'attente sort au premier test
        x = r.call(0x4008e622)
        spi_us = frames[0] * 9 / 8.448
        cyc = x["instr"] * 1.54
        print(f"{label:30s} {x['instr']:6d} instr, {frames[0]:5d} trames -> CPU {cyc / CPU_HZ[0] * 1e6:6.1f} µs "
              f"(250 MHz), SPI {spi_us:7.1f} µs d'attente active ; à 30 images/s : "
              f"{(cyc / CPU_HZ[0] + spi_us * 1e-6) * 30 * 100:4.2f} % du temps")
    print("hors mémoire :", r.unmapped[:3])


if __name__ == "__main__":
    main()
