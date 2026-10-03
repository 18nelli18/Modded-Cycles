#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/40-arp.json : l'arpégiateur à la place du retrig (notes/32).

tools/machines/arp/ : arp.c (l'arpège, côté audio, et les deux lignes du menu FUNC + RETRIG) et arp_hooks.S (les
accroches), liés par arp.ld dans quatre masques de sprites libérés (tools/sprites.py). Les accroches sur l'OS sont les
HOOKS ci-dessous ; chaque écriture porte ses octets d'origine, vérifiés sur le MAIN OS officiel.

    python3 tools/gen_arp.py --cycles model-cycles_OS1.13.syx [--check]
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

SRC = HERE / "machines" / "arp"
OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "40-arp.json"
BASE = gx.BASE
# sections de arp.ld : (masque libéré, début de la zone utilisée, taille disponible)
CAVES = {
    ".cave_audio": (0x4018a788, 0x4018a788, 1024),
    ".cave_menu": (0x4016cae8, 0x4016cba8, 832),       # le début garde le crochet des moteurs du Syntakt (188 o au plus)
    ".cave_rec1": (0x40189930, 0x40189930, 376),       # masques de deux sprites 47x47 : live rec (notes/32 §11)
    ".cave_rec2": (0x4018a220, 0x4018a220, 376),
}
# (adresse, octets d'origine, symbole, instruction, rôle)
HOOKS = (
    (0x40058e28, "72ff242a0008202a000c", "arp_filter_hook", 0x4eb9,
     "traitement des notes : moveq #-1,d1 ; move.l 8(a2),d2 ; move.l 12(a2),d0 -> jsr arp_filter_hook ; nop ; nop"),
    (0x400587f6, "4eb940091f20", "arp_copy", 0x4eb9,
     "répétition du retrig : jsr 0x40091f20 (copie de l'événement gardé) -> jsr arp_copy"),
    (0x4002d480, "4cef7c7c0018", "arp_menu_tail", 0x4ef9,
     "fin du constructeur du menu Retrig Setup : movem.l 24(sp),d2-d6/a2-a6 -> jmp arp_menu_tail"),
    (0x4001a1c4, "4eb940016086", "arp_rate_d3", 0x4eb9,
     "note jouée (touches, piste en d3) : jsr 0x40016086 (Rte de la piste) -> jsr arp_rate_d3"),
    (0x4001d25e, "4eb940016086", "arp_rate_d2", 0x4eb9,
     "note jouée (0x4001d1xx, piste en d2) : jsr 0x40016086 (Rte de la piste) -> jsr arp_rate_d2"),
    (0x40081908, "4ebaf2ec588f", "arp_post_on", 0x4eb9,
     "message d'une note jouée pour l'interface (0x4008171e) : jsr 0x40080bf6 ; addq.l #4,sp -> jsr arp_post_on"),
)
SYMBOLS = ("ui_cfg", "st", "ring")                     # pour tools/emu/test_arp.py
CONFLICTS = ["sdvintage-snare"]                        # il occupe les deux mêmes masques


def compile_arp():
    """Code lié (ELF) : {section: (adresse, octets)}, symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, hooks, elf = d / "arp.o", d / "hooks.o", d / "arp.elf"
        gx.run([gx.CROSS + "gcc", *gx.CFLAGS, "-c", str(SRC / "arp.c"), "-o", str(obj)])
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(SRC / "arp_hooks.S"), "-o", str(hooks)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "arp.ld"), "--no-warn-rwx-segments", "-o", str(elf), str(hooks),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        secs = {}
        for name in CAVES:
            out = d / (name.strip(".") + ".bin")
            gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", name, str(elf), str(out)])
            addr = int(subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                                      check=True).stdout.split(name)[1].split()[1], 16)
            secs[name] = (addr, out.read_bytes())
    return secs, syms


def build_tweak(stock):
    secs, syms = compile_arp()
    writes = []
    for name, (mask, lo, room) in CAVES.items():
        addr, code = secs[name]
        if addr != lo or len(code) > room:
            raise SystemExit(f"!! {name} : {len(code)} o à {addr:#x}, place {room} o à {lo:#x}")
        old = stock[addr - BASE:addr - BASE + len(code)]
        size, shared = sprites.MASKS[mask][0], (sprites.MASKS[mask][3:] or (None,))[0]
        if shared is None and old != b"\xff" * len(code):
            raise SystemExit(f"!! {name} : la zone {addr:#x} n'est pas libre dans l'OS d'origine")
        if shared is not None and stock[mask - BASE:mask - BASE + size] != stock[shared - BASE:shared - BASE + size]:
            raise SystemExit(f"!! {name} : le masque {mask:#x} n'est pas identique au masque gardé {shared:#x}")
        writes.append({"off": addr - BASE, "old": old.hex(), "new": code.hex()})
        writes.append(sprites.redirect_write(mask))
    for va, old_hex, sym, op, _ in HOOKS:
        old = bytes.fromhex(old_hex)
        if stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! octets d'origine inattendus en {va:#x}")
        new = struct.pack(">HI", op, syms[sym])
        new += b"\x4e\x71" * ((len(old) - len(new)) // 2)
        writes.append({"off": va - BASE, "old": old_hex, "new": new.hex()})
    writes.sort(key=lambda w: w["off"])
    used = {n: len(secs[n][1]) for n in CAVES}
    tweak = {
        "id": "arp",
        "order": 40,
        "name": "Arpégiateur à la place du retrig",
        "description": [
            "Avec RETRIG tenu (ou A.On), les notes tenues sur une piste sont jouées en arpège au rythme du retrig.",
            "Menu FUNC + RETRIG : deux lignes de plus, Arp (UP, DOWN, UPDN, RAND, PLAY, OFF) et Oct (1 à 4).",
            "Réglages enregistrés avec le pattern (octet +512 de la piste, inutilisé par l'OS), transmis au côté audio",
            "à chaque note jouée et à chaque changement dans le menu. Une note ajoutée entre dans l'arpège sans couper",
            "le rythme ; avec une seule note et 1 octave, c'est le retrig d'origine.",
            "En live rec, l'arpège enregistre les notes qu'il joue, une par une, avec leur durée (l'OS n'enregistrait",
            "qu'un pas avec retrig : une seule note répétée) ; une seule note tenue reste un pas avec retrig.",
            f"Code dans quatre masques de sprites libérés (tools/sprites.py) : {used['.cave_audio']} o en 0x4018a788,",
            f"{used['.cave_menu']} o en 0x4016cba8, {used['.cave_rec1']} o en 0x40189930, {used['.cave_rec2']} o",
            "en 0x4018a220. Généré par tools/gen_arp.py, notes/32.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": CONFLICTS,
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
    tweak, syms = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1) + "\n"
    for line in tweak["description"][-2:]:
        print("  " + line)
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre GCC ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures)")


if __name__ == "__main__":
    main()
