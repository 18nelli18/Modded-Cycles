#!/usr/bin/env python3
"""Quels périphériques du MCF5441x le firmware utilise-t-il ? (notes/21 §10)

Compte, dans chaque section de l'OS officiel, les constantes 32 bits qui tombent dans
le bloc de registres (16 Ko) d'un périphérique du MCF5441x. Sert à recouper les puces
vues sur le PCB avec ce que le code adresse : init DDR2, flash SPI, eMMC, MIDI, USB...

Adresses de base : MCF5441x Reference Manual (MCF54418RM), tables 1-3 et 1-4.

Limite : un compte faible dans le MAIN OS (1,7 Mo, beaucoup de tables) peut être du
bruit. Les lignes "bruit" donnent le compte médian, le 99e centile et le maximum des
blocs 0xFCxx_xxxx / 0xECxx_xxxx situés hors de la plage des périphériques (aucun
registre n'y existe). Au-dessus du maximum : sûr. Entre le 99e centile et le maximum :
un indice seulement.

    python3 tools/hw_periph_refs.py -i model-cycles_OS1.13.syx
"""
import argparse
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mtlib import aplib, container  # noqa: E402
from mtlib.syx import unwrap  # noqa: E402

SLOT = 0x4000
# (base, nom) : tous les blocs des tables 1-3 et 1-4, sauf le crossbar (0xFC00_4000)
PERIPH = [
    (0xFC008000, "FlexBus (chip selects)"), (0xFC020000, "FlexCAN 0"),
    (0xFC024000, "FlexCAN 1"), (0xFC038000, "I2C1"), (0xFC03C000, "DSPI1"),
    (0xFC040000, "SCM"), (0xFC044000, "eDMA"), (0xFC048000, "INTC0"),
    (0xFC04C000, "INTC1"), (0xFC050000, "INTC2"), (0xFC054000, "INTC IACK"),
    (0xFC058000, "I2C0"), (0xFC05C000, "DSPI0 (broches du boot série)"),
    (0xFC060000, "UART0"), (0xFC064000, "UART1"), (0xFC068000, "UART2"),
    (0xFC06C000, "UART3"), (0xFC070000, "timer DMA 0"), (0xFC074000, "timer DMA 1"),
    (0xFC078000, "timer DMA 2"), (0xFC07C000, "timer DMA 3"), (0xFC080000, "PIT0"),
    (0xFC084000, "PIT1"), (0xFC088000, "PIT2"), (0xFC08C000, "PIT3"),
    (0xFC090000, "Edge port"), (0xFC094000, "ADC"), (0xFC098000, "DAC0"),
    (0xFC09C000, "DAC1"), (0xFC0A8000, "RTC"), (0xFC0AC000, "SIM (carte à puce)"),
    (0xFC0B0000, "USB On-the-Go"), (0xFC0B4000, "USB hôte"),
    (0xFC0B8000, "contrôleur DDR"), (0xFC0BC000, "SSI0"), (0xFC0C0000, "PLL"),
    (0xFC0C4000, "RNG"), (0xFC0C8000, "SSI1"), (0xFC0CC000, "eSDHC"),
    (0xFC0D4000, "Ethernet 0"), (0xFC0D8000, "Ethernet 1"),
    (0xFC0DC000, "switch Ethernet 0"), (0xFC0E0000, "switch Ethernet 1"),
    (0xFC0FC000, "contrôleur NAND"), (0xEC008000, "1-Wire"), (0xEC010000, "I2C2"),
    (0xEC014000, "I2C3"), (0xEC018000, "I2C4"), (0xEC01C000, "I2C5"),
    (0xEC038000, "DSPI2"), (0xEC03C000, "DSPI3"), (0xEC060000, "UART4"),
    (0xEC064000, "UART5"), (0xEC068000, "UART6"), (0xEC06C000, "UART7"),
    (0xEC070000, "UART8"), (0xEC074000, "UART9"), (0xEC088000, "mcPWM"),
    (0xEC090000, "CCM, reset, alimentation"), (0xEC094000, "GPIO / multiplexage des broches"),
]
NAMES = {5: "meta", 2: "bootstrap", 3: "MAIN OS", 4: "updater"}
COMPRESSED = (2, 3)


def sections(path):
    stream, _ = unwrap(Path(path).read_bytes())
    c = container.parse(stream)
    for s in c["sections"]:
        raw = c["blob"][s["off"]:s["off"] + s["size"]]
        data = aplib.depack(raw)[0] if s["id"] in COMPRESSED else raw
        yield s["id"], bytes(data)


def count(data):
    """{base du bloc: nombre de constantes 32 bits alignées sur 2 octets}"""
    hits = {}
    for o in range(0, len(data) - 3, 2):
        if data[o] in (0xFC, 0xEC):
            base = int.from_bytes(data[o:o + 4], "big") & ~(SLOT - 1)
            hits[base] = hits.get(base, 0) + 1
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-i", "--input", required=True, help="OS officiel (.syx)")
    ap.add_argument("--all", action="store_true", help="montrer aussi les blocs jamais adressés")
    a = ap.parse_args()

    cols = [(i, d, count(d)) for i, d in sections(a.input) if i != 5]
    print("%-12s %-46s" % ("base", "périphérique")
          + "".join("%12s" % NAMES.get(i, i) for i, _, _ in cols))
    for base, name in PERIPH:
        if a.all or any(h.get(base, 0) for _, _, h in cols):
            print("0x%08X   %-46s" % (base, name)
                  + "".join("%12d" % h.get(base, 0) for _, _, h in cols))
    # bruit : blocs 0xFCxx_xxxx / 0xECxx_xxxx hors de la plage des périphériques
    slots = 2 * 15 * (0x100000 // SLOT)
    noise = []
    for _, _, h in cols:
        other = sorted(n for b, n in h.items() if b & 0x00F00000)
        noise.append([0] * (slots - len(other)) + other)
    for label, pick in (("médiane", lambda v: statistics.median(v)),
                        ("99e centile", lambda v: v[len(v) * 99 // 100]),
                        ("maximum", lambda v: v[-1])):
        print("%-12s %-46s" % ("", "bruit hors périphériques : " + label)
              + "".join("%12g" % pick(v) for v in noise))
    print("%-12s %-46s" % ("", "taille (octets)")
          + "".join("%12d" % len(d) for _, d, _ in cols))


if __name__ == "__main__":
    main()
