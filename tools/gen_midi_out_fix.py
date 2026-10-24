#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/52-midi-out-fix.json : la sortie MIDI ne fige plus le Model:Cycles (notes/79).

Un gel de l'OS 1.13 d'Elektron (relevé par l'étude de l'OS optimisé, notes/70 §5, « D2 ») : 0x40001232 range un octet
pour la sortie MIDI ; quand son anneau de 1 Kio est plein, il attend qu'une interruption de niveau 4 le vide. Appelé
à un niveau de 4 ou plus (le top d'horloge MIDI, après une longue surcharge : 1 024 tops sans service, 21 s à 120 BPM),
il attend pour toujours : tout se fige, son compris. Ici l'attente reste celle de l'OS quand elle peut finir, et
l'octet est jeté quand elle ne le peut pas (tools/machines/midi_out_fix/ring_wait.S, détour 0x4000123a).

Le correctif de l'OS optimisé (bgt.s vers la sortie en 0x40001246) jetait l'octet dans tous les cas, même quand
l'attente aurait fini (envoi depuis l'interface) : pas repris. L'autre gel de notes/70 (D1, MACHINES sur une machine
inconnue) est déjà corrigé dans le Modded Cycles OS par les détours des enregistrements (notes/20 §5) : la preuve le
vérifie.

Code dans un masque de sprite libéré (tools/sprites.py). Preuve : tools/emu/test_midi_out_fix.py.

    python3 tools/gen_midi_out_fix.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build                     # noqa: E402
import sprites                   # noqa: E402

SRC = HERE / "machines" / "midi_out_fix"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "52-midi-out-fix.json"
BASE = build.BASE
CROSS = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if shutil.which(c + "as")), "m68k-linux-gnu-")
MASK = 0x4014a890                # 27x27, libre (REGISTRY.md §1)
HOOK = (0x4000123a, "20394049dccc")          # move.l 0x4049dccc,%d0 : le début de l'attente
CONTEXT = ((0x40001240, "0c80000003ff6ef240c2"),     # cmpi.l #1023,%d0 ; bgt.s 0x4000123a ; move.w %sr,%d2
           (0x400012c4, "46c2241f261f4e75"),         # move.w %d2,%sr ; move.l (sp)+,d2 ; move.l (sp)+,d3 ; rts
           (0x40001522, "13c1fc04c075"))             # move.b %d1,0xfc04c075 : niveau 4 de la source 53
SYMBOLS = ("ring_wait", "ring_drop")


def assemble(src, at):
    """Assemble src à l'adresse at : (octets de .text, {symbole : adresse})."""
    with tempfile.TemporaryDirectory() as d:
        o, elf, b = (pathlib.Path(d) / n for n in ("a.o", "a.elf", "a.bin"))
        subprocess.run([CROSS + "as", "-mcpu=54418", "-o", str(o), str(SRC / src)], check=True)
        subprocess.run([CROSS + "ld", "-e", "0", f"-Ttext={at:#x}", "-o", str(elf), str(o)], check=True)
        subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", ".text", str(elf), str(b)], check=True)
        nm = subprocess.run([CROSS + "nm", str(elf)], check=True, capture_output=True, text=True).stdout
        code = b.read_bytes()
    return code, {p[2]: int(p[0], 16) for p in (l.split() for l in nm.splitlines()) if len(p) == 3}


def build_tweak(stock):
    for va, ex in CONTEXT:
        if stock[va - BASE:va - BASE + len(ex) // 2].hex() != ex:
            raise SystemExit(f"!! {va:#x} : {ex} attendu dans l'OS d'origine")
    code, syms = assemble("ring_wait.S", MASK)
    size = sprites.MASKS[MASK][0]
    if len(code) > size:
        raise SystemExit(f"!! {len(code)} o, le masque {MASK:#x} n'en a que {size}")
    writes = []

    def put(va, new, old=None):
        cur = stock[va - BASE:va - BASE + len(new)]
        if old is not None and cur != bytes.fromhex(old):
            raise SystemExit(f"!! {va:#x} : {old} attendu dans l'OS d'origine, {cur.hex()} trouvé")
        writes.append({"off": va - BASE, "old": cur.hex(), "new": new.hex()})

    put(MASK, code)
    writes.append(sprites.redirect_write(MASK))
    put(HOOK[0], bytes.fromhex("4ef9") + syms["ring_wait"].to_bytes(4, "big"), HOOK[1])
    writes.sort(key=lambda x: x["off"])
    tweak = {
        "id": "midi-out-fix",
        "order": 52,
        "name": "Sortie MIDI sans gel : l'horloge MIDI ne fige plus le Model:Cycles après une longue surcharge",
        "description": [
            "Un gel de l'OS 1.13 d'origine : quand la sortie MIDI est engorgée, l'OS attend qu'une place se libère, "
            "même là où rien ne peut la libérer (le top d'horloge MIDI, à un niveau d'interruption de 4 ou plus) : "
            "après une longue surcharge, tout se fige, son compris (notes/79).",
            "Ici l'attente reste celle de l'OS quand elle peut finir ; quand elle ne le peut pas, l'octet est jeté. "
            "Identique à l'OS d'origine dans tous les cas où celui-ci revient.",
            f"Code dans un masque de sprite libéré (tools/sprites.py) : {len(code)} o. "
            "Généré par tools/gen_midi_out_fix.py, notes/79.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": ["os-optimise"],
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }
    return tweak, len(code), size


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stream, _ = build.unwrap(pathlib.Path(args.cycles).read_bytes())
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    stock = build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]
    if build.sha(stock) != json.loads((DEV / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak, n, size = build_tweak(stock)
    build.apply_writes(stock, [tweak])                # les octets d'origine collent
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    print(f"  masque {MASK:#x} : {n}/{size} o ; détour {HOOK[0]:#x}")
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autres binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures)")


if __name__ == "__main__":
    main()
