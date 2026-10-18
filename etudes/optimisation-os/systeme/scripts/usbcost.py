#!/usr/bin/env python3
"""Coût fixe de l'USB par micro-trame (OS 1.13 d'origine), sans les rappels de données :
1. interruption USB 0x40004318 (vecteur 209, niveau 6) avec USBSTS = UI | SRI (fin de transfert + début de
   micro-trame), liste des rappels SOF = [0x4000238e] qui sort tôt (moins de 80 micro-trames depuis sa mesure) ;
2. interruption différée 0x40005078 (vecteur 134, niveau 4) forcée par la première, avec ENDPTCOMPLETE = 0 : le
   tour des 8 points d'accès sans rien à retirer (borne basse ; les rappels de données en plus).

    python3 usbcost.py sec3.bin
"""
import sys

import isrrig as R


def main():
    img = open(sys.argv[1], "rb").read()
    r = R.Rig(img)
    node = 0x41f10000
    r.w32(node, 0x4000238e)
    r.w32(node + 4, 0)
    r.w32(0x404a0a6c, node)
    r.w32(0xfc0b014c, 0x123 << 3)                  # FRINDEX
    r.w32(0x404a05dc, (0x123 << 3) - 10)           # dernière mesure il y a 10 micro-trames
    for k in range(3):
        r.w32(0xfc0b0144, 0x81)                    # USBSTS : SRI | UI
        r.w32(0xfc0b01a4, 0)                       # OTGSC : rien
        r.w32(0x404a09b4, 0)
        r.w32(0xfc04c014, 0)
        x = r.isr(0x40004318, 0x2000)
        forced = r.r32(0xfc04c014) & 0x40
        r.w32(0xfc0b01bc, 0)                       # ENDPTCOMPLETE vide
        r.w32(0xfc0b01ac, 0)                       # ENDPTSETUPSTAT vide
        y = r.isr(0x40005078, 0x2000)
    print("interruption USB (UI | SRI, rappel SOF qui sort tôt) :", R.fmt(x), "; différée forcée :", bool(forced))
    print("interruption différée, aucun point d'accès terminé       :", R.fmt(y))
    tot = x["instr"] + y["instr"]
    print(f"par micro-trame : {tot} instructions -> {tot * 1.54 * 8000 / 250e6 * 100:.2f} % du processeur à 250 MHz "
          f"(+ 2 entrées d'exception et les accès aux registres de l'USB, lents)")
    print("hors mémoire :", r.unmapped[:3])


if __name__ == "__main__":
    main()
