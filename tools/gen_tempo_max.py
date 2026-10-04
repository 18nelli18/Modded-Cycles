#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/42-tempo-max.json : tempo jusqu'à 546 BPM au lieu de 300 (notes/38).

Le tempo de l'OS est en 1/120 de BPM (0x40149310 ; 120 BPM = 14 400). Le projet l'enregistre sur 16 bits
(champ +18, lu par mvz.w) : 65 535 / 120 = 546,1 BPM est le plafond sans changer le format des projets.
On prend 65 520 = 546,0 BPM, un pas exact de la molette (1 BPM = 120, 0,1 BPM = 12).

  - les six bornes à 36 000 (300 BPM) passent à 65 520 : moteur (0x40058b62, 0x40058bb4), horloge MIDI reçue
    (0x40080620), projet (0x4000c846), pattern (0x4001238e) et menu Tempo (0x4003d4b8) ;
  - les deux contrôles au chargement (tempo - 3 600 <= 32 400, sinon 120 BPM) suivent : 61 920 ;
  - le LFO synchronisé au tempo : son pas de phase (vitesse x tempo, décalé selon le multiplicateur) dépasse un
    cycle entier au-delà de 351,6 BPM avec la vitesse au maximum et le plus grand multiplicateur ; l'OS ne retire
    qu'un cycle, la phase sortait de sa plage. La remise dans le cycle devient une boucle, à la même place
    (16 octets au lieu de 18).

Le reste tient déjà : l'heure musicale est sur 32 bits (21,6 millions d'unités par noire, +240 x BPM par bloc de
0,67 ms, comparaisons signées), les durées de note (taux <= 25 451, produit < 2^31 jusqu'à 703 BPM), le temps de
delay et Model-TG divisent par le tempo, l'affichage a trois chiffres, l'horloge MIDI envoyée reste sous une
impulsion par bloc (jusqu'à 3 750 BPM). Aucune place libre n'est prise. Preuve : tools/emu/test_tempo_max.py.

    python3 tools/gen_tempo_max.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import test_sdvintage as T         # noqa: E402

OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "42-tempo-max.json"
BASE = build.BASE
STOCK_MAX = 36000                  # 300 BPM
MIN = 3600                         # 30 BPM, inchangé
MAX = 65520                        # 546,0 BPM : le champ du projet est sur 16 bits (65 535 = 546,1)
LFO_CYCLE = 1382400000             # un cycle de phase du LFO


def imm(op, v):
    """Instruction 6 octets « op #v » (op = 2 octets : cmpi.l / move.l #imm vers Dn)."""
    return bytes.fromhex(op) + struct.pack(">I", v)


# (adresse, octets d'origine, nouveaux octets, rôle)
CLAMPS = [
    (0x4000c86e, imm("223c", STOCK_MAX), imm("223c", MAX), "projet (0x4000c846), champ 16 bits +18 : move.l #max,d1"),
    (0x400123cc, imm("223c", STOCK_MAX), imm("223c", MAX), "pattern (0x4001238e), champ 32 bits : move.l #max,d1"),
    (0x4003d4bc, imm("243c", STOCK_MAX), imm("243c", MAX), "menu Tempo (0x4003d4b8), molette : move.l #max,d2"),
    (0x40058b94, imm("0c80", STOCK_MAX), imm("0c80", MAX), "moteur (0x40058b62) : cmpi.l #max,d0"),
    (0x40058b9c, imm("203c", STOCK_MAX), imm("203c", MAX), "moteur (0x40058b62) : move.l #max,d0"),
    (0x40058bc6, imm("0c80", STOCK_MAX), imm("0c80", MAX), "moteur (0x40058bb4) : cmpi.l #max,d0"),
    (0x40058bce, imm("203c", STOCK_MAX), imm("203c", MAX), "moteur (0x40058bb4) : move.l #max,d0"),
    (0x4008064c, imm("0c80", STOCK_MAX), imm("0c80", MAX), "horloge MIDI reçue (24 intervalles) : cmpi.l #max,d0"),
    (0x40080654, imm("203c", STOCK_MAX), imm("203c", MAX), "horloge MIDI reçue : move.l #max,d0"),
    (0x4005aac0, imm("0c81", STOCK_MAX - MIN), imm("0c81", MAX - MIN),
     "chargement (message du séquenceur) : tempo - 3600 <= max - 3600, sinon 120 BPM"),
    (0x4005b3f6, imm("0c81", STOCK_MAX - MIN), imm("0c81", MAX - MIN),
     "chargement du projet (copie du champ +18) : tempo - 3600 <= max - 3600, sinon 120 BPM"),
]
# 0x40091bd8 : après « phase >= un cycle », l'OS retire (ou ajoute, phase négative) UN cycle :
#   tst.l d7 ; blt.s +8 ; addi.l #-C,d2 ; bra.s +6 ; addi.l #C,d2
# devient une boucle qui revient au test (0x40091ba4) jusqu'à ce que la phase soit dans le cycle :
#   move.l #C,d1 ; tst.l d7 ; bge.s +2 ; neg.l d1 ; sub.l d1,d2 ; bra.s 0x40091ba4 ; nop
# (d1 est rechargé juste après, en 0x40091bea ; le repérage du demi-cycle, gardé par a3@, ne se refait pas)
LFO_AT = 0x40091bd8
LFO_OLD = bytes.fromhex("4a87" "6d08" "0682") + struct.pack(">i", -LFO_CYCLE) + bytes.fromhex("6006" "0682") \
    + struct.pack(">I", LFO_CYCLE)
LFO_NEW = bytes.fromhex("223c") + struct.pack(">I", LFO_CYCLE) + bytes.fromhex("4a87" "6c02" "4481" "9481") \
    + struct.pack(">Bb", 0x60, 0x40091ba4 - (LFO_AT + 16)) + bytes.fromhex("4e71")


def bpm(v):
    return f"{v // 120}.{(v % 120) // 12}"


def build_tweak(stock):
    writes = []
    for va, old, new, _ in CLAMPS + [(LFO_AT, LFO_OLD, LFO_NEW, "LFO")]:
        if stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        if len(new) != len(old):
            raise SystemExit(f"!! {va:#x} : {len(new)} octets au lieu de {len(old)}")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new.hex()})
    return {
        "id": "tempo-max",
        "order": 42,
        "name": f"Tempo jusqu'à {bpm(MAX)} BPM",
        "description": [
            f"Tempo de {bpm(MIN)} à {bpm(MAX)} BPM au lieu de {bpm(STOCK_MAX)} : molette du menu Tempo, tap tempo, "
            "horloge MIDI reçue, chargement d'un projet.",
            f"{bpm(MAX)} BPM est le plafond du format des projets (tempo en 1/120 de BPM sur 16 bits) ; un projet "
            "enregistré au-dessus de 300 BPM se rouvre à 120 BPM sur l'OS d'origine (son contrôle au chargement).",
            "Le LFO synchronisé au tempo reste juste au-delà de 351,6 BPM (sa phase est remise dans le cycle en "
            "boucle au lieu d'une seule fois).",
            "Aucune place libre utilisée : 11 constantes et 18 octets du LFO. Généré par tools/gen_tempo_max.py, "
            "notes/38.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "writes": writes,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((OUT.parent / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures, max {MAX} = {bpm(MAX)} BPM)")


if __name__ == "__main__":
    main()
