#!/usr/bin/env python3
"""Génère retrosyn_tables.h : les tables constantes de la machine RETROSYN (Game Boy / SNES).

Rien ici ne vient d'Elektron : ce sont des formes d'onde calculées (harmoniques), le noyau d'interpolation
gaussien, les incréments de phase par demi-ton et les pas de balayage. Le résultat est déterministe (math seulement).

    python3 gen_retrosyn_tables.py > retrosyn_tables.h
"""
import math

SR = 48000

# harmoniques 1..8 des 8 tables d'onde 32 pas (canal « wave » du Game Boy) : sinus, triangle, scie, carré doux,
# orgue, basse, formant, buzz
WAVE_H = [
    [1, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, -1 / 9, 0, 1 / 25, 0, -1 / 49, 0],
    [1, 1 / 2, 1 / 3, 1 / 4, 1 / 5, 1 / 6, 1 / 7, 1 / 8],
    [1, 0, 1 / 3, 0, 1 / 5, 0, 1 / 7, 0],
    [1, .8, .6, 0, 0, 0, 0, 0],
    [1, .9, .3, .1, 0, 0, 0, 0],
    [.3, .2, 1, .3, .9, .2, .1, 0],
    [1, 1 / 1.4, 1 / 1.7, 1 / 2, 1 / 2.2, 1 / 2.4, 1 / 2.6, 1 / 2.8],
]
# harmoniques 1..7 des 8 boucles de 16 échantillons (voix « SNES ») : cordes, cuivres, flûte, cloche, chœur, basse,
# nappe, buzz
LOOP_H = [
    [1, .5, .33, .25, .2, .16, .14],
    [.6, .8, 1, .9, .6, .3, .1],
    [1, .05, .25, 0, .05, 0, 0],
    [1, .1, .6, .1, .4, 0, .2],
    [1, .7, .2, .6, .1, .2, 0],
    [1, .9, .35, .1, 0, 0, 0],
    [1, .5, 0, .25, 0, 0, 0],
    [1, .7, .6, .5, .45, .4, .35],
]


def q4(x):
    v = math.floor(x * 7.5 + 0.5)
    return max(-8, min(7, v))


def wave_tables():
    out = []
    for w in range(8):
        x = [sum(WAVE_H[w][h] * math.sin(2 * math.pi * (h + 1) * k / 32) for h in range(8)) for k in range(32)]
        pk = max(abs(a) for a in x)
        out.append([q4(a / pk) for a in x])
    return out


def loops():
    out = []
    for w in range(8):
        x = [sum(LOOP_H[w][h] * math.sin(2 * math.pi * (h + 1) * k / 16 + 0.3 * h) for h in range(7)) for k in range(16)]
        pk = max(abs(a) for a in x)
        out.append([q4(a / pk) for a in x])
    return out


def gauss():
    out = []
    for f in range(256):
        fr = f / 256
        w = [math.exp(-((j - 1) - fr) ** 2 / (2 * 0.6 ** 2)) for j in range(4)]
        s = sum(w)
        k = [math.floor(a / s * 32768 + 0.5) for a in w]
        k[k.index(max(k))] += 32768 - sum(k)
        out.append(k)
    return out


def inc_table():
    # increment de phase 32 bits par échantillon pour les notes MIDI 0..127, + une 129e entrée pour interpoler
    t = []
    for n in range(129):
        f = 440 * 2 ** ((n - 69) / 12)
        t.append(min(0xFFFFFFFF, int(f / SR * 2 ** 32 + 0.5)))
    return t


def sweep_steps():
    # pas de hauteur d'un balayage Game Boy : f x (1 +- 2^-n) par tick, en demi-tons << 16, n = 0..7 (0 et 1 inutilisés)
    up = [round(12 * math.log2(1 + 2 ** -n) * 65536) if n >= 2 else 0 for n in range(8)]
    dn = [round(12 * math.log2(1 - 2 ** -n) * 65536) if n >= 2 else 0 for n in range(8)]
    return up, dn


def arr(name, ctype, rows, fmt="%d", per=16, nested=False):
    if nested:
        body = ",\n".join("\t{" + ", ".join(fmt % v for v in r) + "}" for r in rows)
        dims = "[%d][%d]" % (len(rows), len(rows[0]))
    else:
        lines = []
        for i in range(0, len(rows), per):
            lines.append("\t" + ", ".join(fmt % v for v in rows[i : i + per]))
        body = ",\n".join(lines)
        dims = "[%d]" % len(rows)
    return "static const %s %s%s = {\n%s\n};\n" % (ctype, name, dims, body)


def main():
    up, dn = sweep_steps()
    print("/* Généré par gen_retrosyn_tables.py : ne pas éditer. */")
    print("#ifndef RETROSYN_TABLES_H\n#define RETROSYN_TABLES_H\n")
    print(arr("RS_WT", "s8", wave_tables(), nested=True))
    print(arr("RS_LOOPS", "s8", loops(), nested=True))
    print(arr("RS_GAUSS", "s16", gauss(), nested=True))
    print(arr("RS_INC", "u32", inc_table(), fmt="0x%08xu", per=6))
    print(arr("RS_SWEEP_UP", "s32", up, per=8))
    print(arr("RS_SWEEP_DN", "s32", dn, per=8))
    print("#endif")


if __name__ == "__main__":
    main()
