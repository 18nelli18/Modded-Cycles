#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/47-trigless-dim.json : les trigless trigs (lock trigs) atténués sur les touches de
pas (mod de djd_oz, notes/45).

En mode grille, l'OS allume une touche de pas qui porte un trigless trig (FUNC + touche de pas) comme un trig de note
(état de LED 4 : allumée, éteinte 0,35 s toutes les 2 s). Le mod donne à ces touches l'état 260, traité comme 4 par
l'OS, et les éteint en plus 16 ticks sur 25 de l'horloge des LED (120 Hz) : 36 % de lumière.

tools/machines/trigless_dim/ : trigless_dim.S (quatre accroches et l'état du motif), lié par trigless_dim.ld dans un
masque de sprite 47x47 libéré (tools/sprites.py). Les accroches sur l'OS sont les HOOKS et RAW ci-dessous ; chaque
écriture porte ses octets d'origine, vérifiés sur le MAIN OS officiel.

    python3 tools/gen_trigless_dim.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "trigless_dim"
OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "47-trigless-dim.json"
BASE = gx.BASE
MASK = 0x4018dba8                                      # masque 47x47 libéré (376 o)
# (adresse, octets d'origine, symbole, instruction, rôle)
HOOKS = (
    (0x40006086, "4ef94008e77e", "td_frame", 0x4ef9,
     "fin de l'image des LED (0x40006044, tâche de l'interface, 30 Hz) : jmp 0x4008e77e -> jmp td_frame (relevé des "
     "LED dans l'état 260, quand les états de l'image sont complets)"),
    (0x40005f36, "b2ac00286730", "td_blink", 0x4ef9,
     "clignotement des LED (0x40005efc, 2 Hz) : cmp.l 40(a4),d1 ; beq.s 0x40005f6c (état 4) -> jmp td_blink (4 ou 260)"),
    (0x4008e754, "b18371832f00", "td_send", 0x4ef9,
     "envoi d'une rangée de LED (0x4008e732) : eor.l d0,d3 ; mvz.b d3,d0 ; move.l d0,-(sp) -> jmp td_send (masque)"),
    (0x4008e7a8, "73b228007180", "td_cmp", 0x4ef9,
     "comparaison des 7 rangées (0x4008e77e) : mvz.b (a2,d2.l),d1 ; mvz.b d0,d0 -> jmp td_cmp (masque)"),
    (0x4008e7ca, "4feffff448d7040c", "td_tick", 0x4ef9,
     "début du tick des LED (120 Hz) : lea -12(sp),sp ; movem.l d2-d3/a2,(sp) -> jmp td_tick ; nop (motif ; masque = "
     "relevé ou rien)"),
)
# (adresse, octets d'origine, nouveaux octets, rôle)
RAW = (
    (0x40021f54, "0004", "0104",
     "mode grille (0x40021d22), pas qui porte un trigless trig : movea.w #4,a5 -> movea.w #260,a5 (état de sa LED)"),
    (0x4008e82e, "6704", "4e71",
     "tick des LED : beq.s 0x4008e834 (aucun minuteur expiré : pas d'envoi) -> nop, le masque change à chaque tick"),
)
SYMBOLS = ("td_cnt", "td_mask", "td_lock", "td_tick")            # pour tools/emu/test_trigless_dim.py


def compile_td():
    """(adresse, octets) de la section .cave, et les symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, out = d / "td.o", d / "td.elf", d / "cave.bin"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(SRC / "trigless_dim.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "trigless_dim.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".cave", str(elf), str(out)])
        addr = int(subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                                  check=True).stdout.split(".cave")[1].split()[1], 16)
        return addr, out.read_bytes(), syms


def build_tweak(stock):
    addr, code, syms = compile_td()
    size, shared = sprites.MASKS[MASK][0], sprites.MASKS[MASK][3]
    if addr != MASK or len(code) > size:
        raise SystemExit(f"!! {len(code)} o à {addr:#x}, place {size} o à {MASK:#x}")
    if stock[MASK - BASE:MASK - BASE + size] != stock[shared - BASE:shared - BASE + size]:
        raise SystemExit(f"!! le masque {MASK:#x} n'est pas identique au masque gardé {shared:#x}")
    writes = [{"off": addr - BASE, "old": stock[addr - BASE:addr - BASE + len(code)].hex(), "new": code.hex()},
              sprites.redirect_write(MASK)]
    for va, old_hex, sym, op, _ in HOOKS:
        old = bytes.fromhex(old_hex)
        if stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        new = struct.pack(">HI", op, syms[sym])
        new += b"\x4e\x71" * ((len(old) - len(new)) // 2)
        writes.append({"off": va - BASE, "old": old_hex, "new": new.hex()})
    for va, old_hex, new_hex, _ in RAW:
        if stock[va - BASE:va - BASE + len(old_hex) // 2].hex() != old_hex:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        writes.append({"off": va - BASE, "old": old_hex, "new": new_hex})
    writes.sort(key=lambda w: w["off"])
    tweak = {
        "id": "trigless-dim",
        "order": 47,
        "name": "Trigless trigs atténués sur les touches de pas",
        "description": [
            "Mode grille : une touche de pas qui porte un trigless trig (lock trig, FUNC + pas) s'allume à 36 % au "
            "lieu de pleine lumière ; elle garde le clignotement d'origine (éteinte 0,35 s toutes les 2 s).",
            "L'état de sa LED devient 260 au lieu de 4 (traité comme 4 par l'OS) ; elle est éteinte 16 ticks sur 25 "
            "de l'horloge des LED (120 Hz). Trigs de note, trigs avec p-locks, lumière de lecture, pads : inchangés.",
            "D'après le mod de djd_oz (envoyé à Maxime le 06/10/2026), réécrit pour s'exécuter en place : mêmes "
            "accroches, même motif. Les LED à atténuer sont relevées à la fin de chaque image de l'interface (accroche "
            "en plus en 0x40006086) : un tick tombé au milieu d'une image ne rallume plus les touches à fond.",
            f"Code et état dans le masque de sprite 47x47 libéré 0x4018dba8 (tools/sprites.py) : {len(code)} o. "
            "Généré par tools/gen_trigless_dim.py, notes/45.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }
    return tweak, syms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((OUT.parent / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak, _ = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures)")


if __name__ == "__main__":
    main()
