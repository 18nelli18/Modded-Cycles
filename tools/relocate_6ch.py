#!/usr/bin/env python3
"""Dérive la variante « 6ch-usbup » du patch 6 canaux, pour garder l'upgrade USB.

Le patch 6 canaux d'origine (ms-multi-output, tweak 6ch-multiout) loge ses 4 stubs dans
4 descripteurs USB : 2 configs CDC et 2 configs MIDI seule. Il redirige donc la table
des modes USB vers la config audio, et c'est ce qui casse CONFIG -> UPGRADE par USB.

Cette variante :
  - copie les 4 stubs, octet pour octet, dans une cave 0xFF du MAIN OS, avec un décalage
    constant multiple de 16 (même alignement, mêmes écarts entre stubs) ;
  - fait pointer les 4 crochets du pilote vers ces nouvelles adresses ;
  - laisse d'origine les 4 descripteurs et les 4 entrées de la table des modes USB ;
  - garde tout le reste à l'identique : pilote, ring, config audio passée en 6 canaux.

La cave est le masque 0xFF d'un sprite, libéré en faisant pointer ce sprite sur un
masque identique (tools/sprites.py, notes/14 §5) : la redirection est ajoutée au tweak.

Ce script lit tweaks/model-cycles_OS1.13/10-6ch-multiout.json et écrit 11-6ch-usbup.json.
Il n'a pas besoin de l'image firmware. build.py vérifie ensuite, sur TON image, que
les octets de la cave valent bien 0xFF et que rien d'autre ne pointe dedans.

    python3 tools/relocate_6ch.py                          # (ré)écrit 11-6ch-usbup.json
    python3 tools/relocate_6ch.py --check                  # vérifie que le fichier versionné est à jour
    python3 tools/relocate_6ch.py --cave 0x4015c044:720    # autre cave (VA:taille), stubs centrés
"""
import argparse
import json
import pathlib
import sys

import sprites

HERE = pathlib.Path(__file__).resolve().parent
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
SRC = DEV / "10-6ch-multiout.json"
DST = DEV / "11-6ch-usbup.json"
BASE = 0x40000400                       # VA = offset dans la section 3 + BASE

# Stubs de ms-multi-output relogés pour le Cycles : octets de notes/07 §1, recoupés ici
# avec les écritures de 10-6ch-multiout.json. (nom, VA d'origine, octets, crochet, reprise)
STUBS = [
    ("prime6", 0x4019b136,
     "4e71203c009000802540000424bcdead00017212e789254100204ef9400027fe", 0x400027e8, 0x400027fe),
    ("token6", 0x4019b182,
     "4e71204020042200e988e789d0812800484442444ef940002a4c", 0x40002a42, 0x40002a4c),
    ("tracks6", 0x4019b1e0,
     "4fefffd448d707ff2241781f2c03cc84e2886f000028247c8000185845f26c007e06241202c222c2"
     "45ea008053876600fff25286cc8453806e00ffdc4cd707ff4fef002c4ef940002a26", 0x40002a06, 0x40002a26),
    ("dstoff6", 0x4019b244,
     "2200e988e789d0812239404a05e8d2804ef9400029ee", 0x400029e4, 0x400029ee),
]
DESCRIPTORS = (0x4019b132, 0x4019b2b6)  # CDC x2, MIDI seule x2 (+ 2 descripteurs de périphérique)
MODE_TABLE = (0x4013e544, 0x4013e544 + 4 * 0x28)
# Masque 0xFF du sprite 64x90, libéré par sprites.redirect_write (notes/14 §5). L'ancienne
# cave 0x40154ae4 est le masque du sprite 32x260 : y écrire abîmait ce sprite, on la garde
# désormais intacte comme masque partagé.
CAVE = sprites.zone(0x4015c044)


def load_stubs(src):
    """Recoupe chaque octet de stub couvert par une écriture de 10-6ch-multiout.json."""
    written = {}
    for w in src["writes"]:
        for i, b in enumerate(bytes.fromhex(w["new"])):
            written[w["off"] + BASE + i] = b
    out = []
    for name, va, hexcode, hook, ret in STUBS:
        code = bytes.fromhex(hexcode)
        uncovered = []
        for i, b in enumerate(code):
            got = written.get(va + i)
            if got is None:
                uncovered.append(va + i)          # octet égal à celui du descripteur d'origine
            elif got != b:
                raise SystemExit(f"!! {name} : octet 0x{va + i:08x} = {got:02x} dans {SRC.name}, attendu {b:02x}")
        if len(uncovered) > 2:
            raise SystemExit(f"!! {name} : {len(uncovered)} octets non recoupés — table source inattendue")
        if code[-6:-4] != b"\x4e\xf9" or int.from_bytes(code[-4:], "big") != ret:
            raise SystemExit(f"!! {name} : le stub ne se termine pas par jmp 0x{ret:08x}")
        out.append((name, va, code, hook, uncovered))
    return out


def centered(stubs, cave):
    """Adresse du 1er stub qui centre le bloc dans la cave, au même alignement (mod 16) qu'avant."""
    lo, n = cave
    first = stubs[0][1]
    span = max(va + len(code) for _, va, code, _, _ in stubs) - first
    at = lo + (n - span) // 2
    return at - ((at - first) % 16)


def derive(src, cave, at=None):
    stubs = load_stubs(src)
    at = centered(stubs, cave) if at is None else at
    delta = at - stubs[0][1]
    if delta % 16:
        raise SystemExit(f"!! --at 0x{at:08x} : doit valoir 0x{stubs[0][1]:08x} modulo 16 (alignement du build testé)")
    lo, n = cave
    for name, va, code, _, _ in stubs:
        if not (lo <= va + delta and va + delta + len(code) <= lo + n):
            raise SystemExit(f"!! {name} tomberait hors de la cave 0x{lo:08x}..0x{lo + n - 1:08x}")
    targets = {va: va + delta for _, va, _, _, _ in stubs}

    writes, dropped, hooks = [], [], 0
    for w in src["writes"]:
        va = w["off"] + BASE
        if DESCRIPTORS[0] <= va < DESCRIPTORS[1] or MODE_TABLE[0] <= va < MODE_TABLE[1]:
            dropped.append(va)                    # descripteurs et table des modes : laissés d'origine
            continue
        new = bytes.fromhex(w["new"])
        if new[:2] == b"\x4e\xf9" and int.from_bytes(new[2:6], "big") in targets:
            new = new[:2] + targets[int.from_bytes(new[2:6], "big")].to_bytes(4, "big") + new[6:]
            hooks += 1
        writes.append({"off": w["off"], "old": w["old"], "new": new.hex()})
    if hooks != 4 or len(dropped) != 13:
        raise SystemExit(f"!! dérivation inattendue : {hooks} crochets, {len(dropped)} écritures retirées (attendu 4 et 13)")
    for name, va, code, _, _ in stubs:
        writes.append({"off": va + delta - BASE, "old": "ff" * len(code), "new": code.hex()})
    if lo in sprites.MASKS:
        writes.append(sprites.redirect_write(lo))   # libère le masque : le sprite lit le masque partagé
    writes.sort(key=lambda w: w["off"])

    tweak = {
        "id": "6ch-usbup",
        "order": 11,
        "name": "Sortie multipiste 6 canaux, upgrade USB conserve",
        "description": [                          # ASCII, comme 10-6ch-multiout.json
            "Meme sortie 6 canaux que 6ch-multiout : memes stubs, octet pour octet,",
            f"mais loges dans la cave 0x{lo:08x} au lieu des descripteurs USB CDC et MIDI seule.",
            "Cette cave est le masque 0xFF d'un sprite : le sprite est redirige vers un masque",
            "identique (meme rendu), voir tools/sprites.py et notes/14.",
            "Descripteurs et table des modes USB restent d'origine : CONFIG > UPGRADE par USB devrait refonctionner.",
            f"Genere par tools/relocate_6ch.py depuis 6ch-multiout (decalage des stubs : {delta:#x}).",
            "ATTENTION : jamais flashe. Variante experimentale, voir notes/13.",
        ],
        "device": src["device"],
        "os": src["os"],
        "section": src["section"],
        "conflicts": ["6ch-multiout"],
        "writes": writes,
    }
    return tweak, stubs, delta, dropped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cave", default=f"0x{CAVE[0]:08x}:{CAVE[1]}",
                    help="zone 0xFF à utiliser, VA:taille (défaut %(default)s, notes/09 §4bis)")
    ap.add_argument("--at", type=lambda s: int(s, 0),
                    help="VA du premier stub (défaut : bloc centré dans la cave)")
    ap.add_argument("--check", action="store_true", help="vérifie que 11-6ch-usbup.json est à jour")
    args = ap.parse_args()

    src = json.loads(SRC.read_text(encoding="utf-8"))
    va, size = args.cave.split(":")
    tweak, stubs, delta, dropped = derive(src, (int(va, 0), int(size, 0)), args.at)
    text = json.dumps(tweak, indent=1) + "\n"
    for name, va, code, hook, uncovered in stubs:
        note = f" (octets égaux au descripteur d'origine : {', '.join(f'0x{a:08x}' for a in uncovered)})" if uncovered else ""
        print(f"  {name:8s} 0x{va:08x} -> 0x{va + delta:08x}  {len(code):2d} o, crochet 0x{hook:08x}{note}")
    print(f"  {len(dropped)} écritures retirées (descripteurs USB + table des modes), {len(tweak['writes'])} écritures au total")
    if args.check:
        if DST.read_text(encoding="utf-8") != text:
            raise SystemExit(f"!! {DST.name} n'est pas à jour : relance tools/relocate_6ch.py")
        print(f"  {DST.name} est à jour")
        return
    DST.write_text(text, encoding="utf-8")
    print(f"  écrit : {DST.relative_to(HERE.parent)}")


if __name__ == "__main__":
    sys.exit(main())
