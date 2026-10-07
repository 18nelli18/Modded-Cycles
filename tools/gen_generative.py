#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/49-generative.json : motifs génératifs dans le séquenceur d'origine (notes/50).

Par-dessus model-tg. SETTINGS + PATTERN tire de nouveaux rythmes, mélodies et accords pour les pistes non
verrouillées et les écrit dans le pattern en cours ; SETTINGS + TEMPO annule le dernier tirage (p-locks compris) ;
SETTINGS + PAGE ouvre la page GEN (rythmes euclidiens, plan de styles de batterie de FOUR à JUNGLE, notes et accords
dans une tonalité).

tools/machines/generative/ : core/ (le calcul, en C autonome, vérifié par les vecteurs dorés de vectors/) et tweak/
(hooks.S, tweak.c, page.c), liés par tweak/generative.ld juste après le bloc de Model-TG (0x401bf8c0), exécutés sur
place dans les blocs du cache du système de fichiers que Model-TG retire, plus un septième que ce tweak retire.

    python3 tools/gen_generative.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "generative"
TWEAKS = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = TWEAKS / "49-generative.json"
BASE = gx.BASE
AT = 0x401bf8c0          # fin du bloc ajouté de Model-TG v1.1.0
LIMIT = 0x401c7750       # fin du 7e bloc du cache retiré (Model-TG en retire 6)
CFLAGS = ["-mcpu=54418", "-Os", "-std=gnu99", "-ffreestanding", "-fno-builtin", "-nostdlib", "-fno-pic",
          "-fno-common", "-ffunction-sections", "-fdata-sections", "-fomit-frame-pointer",
          "-fno-tree-loop-distribute-patterns", "-Wall", "-Wextra", "-Werror"]
SOURCES = ["tweak/tweak.c", "tweak/page.c", "core/prng.c", "core/necklace.c", "core/nested.c", "core/layer1.c",
           "core/layer3.c", "core/generate.c"]
# Octets du bloc de Model-TG dont dépendent nos accroches (TG 70b39dd, 30-model-tg.json) : (VA, octets, rôle)
TG_BYTES = (
    (0x401bf3f8, "b1fc401ab7506606207c401bf8c0", "son effacement de la BSS épargne [0x401ab750, 0x401bf8c0)"),
    (0x401bf420, "41f9fc0440004ef94000053a", "la suite de son accroche de démarrage"),
    (0x401ae968, "206f00042028000c", "début de key_hook"),
    (0x401ae970, "4ab9401b6d8c", "rtg_on (page retrig ouverte)"),
    (0x401ae97a, "4ab9401bcaec", "sle_on (éditeur de tranches ouvert)"),
    (0x401ae9ce, "42b9401b2360", "mod_used"),
    (0x401ae9a6, "43fa39b4", "set_held (lea %pc@(0x401b235c),%a1)"),
    (0x401b3ffc, "4aba2d8e", "début de pad_hook (tstl %pc@(rtg_on))"),
    (0x401b401a, "43f9401001d0", "table pad -> piste de pad_hook"),
    (0x401b3f72, "4abae114", "mm_obj (rtg_open : tstl %pc@(0x401b2088))"),
    (0x401b1a52, "41fa06344290", "mm_dtor0 / mm_obj"),
)
# Nos écritures, sur l'image d'origine + model-tg : (VA, octets attendus, symbole ou nouveaux octets, rôle)
WRITES = (
    (0x40000532, "401bf3d8", "ours_boot", "démarrage : jsr boot_extra_hook de TG -> jsr ours_boot"),
    (0x4007240e, "401ae968", "ours_key_hook", "accesseur de touche : jmp key_hook de TG -> jmp ours_key_hook"),
    (0x4001d182, "401b3ffc", "ours_pad_hook", "méthode des pads : jmp pad_hook de TG -> jmp ours_pad_hook"),
    (0x40006a78, "40076ca2", "ours_led_frame", "trame des voyants : jsr 0x40076ca2 -> jsr ours_led_frame"),
    (0x400792f2, "401eb7c8", "401eb7dc", "cache du système de fichiers : un 7e bloc retiré (notes/50 §4.1)"),
    (0x400792bc, "401eb7ec", "401eb800", "idem, l'autre pointeur"),
)
SYMBOLS = ("ours_boot", "ours_key_hook", "ours_pad_hook", "ours_led_frame", "ours_res_end", "ours_end",
           "ours_controls", "ours_seed", "pg_obj", "pg_vt", "pg_sel", "pg_lock", "pg_owned", "pg_rhythm",
           "pg_last_idx")


def compile_code():
    """(octets de l'image, symboles) : core + tweak liés en 0x401bf8c0."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        objs = [d / "hooks.o"]
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(SRC / "tweak" / "hooks.S"), "-o", str(objs[0])])
        for c in SOURCES:
            o = d / (pathlib.Path(c).stem + ".o")
            gx.run([gx.CROSS + "gcc", *CFLAGS, "-c", str(SRC / c), "-o", str(o)])
            objs.append(o)
        elf, out = d / "generative.elf", d / "generative.bin"
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "tweak" / "generative.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                *map(str, objs)])
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".text", str(elf), str(out)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        return out.read_bytes(), syms


def build_tweak(stock):
    _, catalog = build.load_catalog()["model-cycles_OS1.13"]
    tg = catalog["model-tg"]
    blob = bytes.fromhex(tg["append"]["parts"][0]["hex"])
    a0 = int(tg["append"]["at"], 16)
    if a0 + len(blob) != AT:
        raise SystemExit(f"!! le bloc de model-tg ne finit plus en {AT:#x}")
    for va, want, role in TG_BYTES:
        if blob[va - a0:va - a0 + len(want) // 2].hex() != want:
            raise SystemExit(f"!! Model-TG a changé en {va:#x} ({role})")
    with_tg, _ = build.apply_writes(stock, [tg])
    code, syms = compile_code()
    if syms["ours_boot"] != AT or AT + len(code) != syms["ours_res_end"]:
        raise SystemExit(f"!! code mal placé : {len(code)} o, fin {syms['ours_res_end']:#x}")
    if syms["ours_end"] > LIMIT:
        raise SystemExit(f"!! le code et la .bss dépassent {LIMIT:#x} ({syms['ours_end']:#x})")
    writes = []
    for va, want, new, role in WRITES:
        old = with_tg[va - BASE:va - BASE + len(want) // 2].hex()
        if old != want:
            raise SystemExit(f"!! octets inattendus en {va:#x} sur l'OS d'origine + model-tg ({role})")
        writes.append({"off": va - BASE, "old": old, "new": f"{syms[new]:08x}" if new in syms else new})
    writes.sort(key=lambda w: w["off"])
    conflicts = sorted({"model-tg-st", "syntakt-tg-meter", "syntakt-tg-profile"}
                       | {t["id"] for t in catalog.values() if "model-tg-st" in t.get("requires", [])})
    return {
        "id": "generative",
        "order": 49,
        "name": "Motifs génératifs (page GEN)",
        "description": [
            "SETTINGS + PATTERN : nouveaux rythmes, mélodies et accords pour les pistes non verrouillées, écrits dans "
            "le pattern en cours. SETTINGS + TEMPO : annule le dernier tirage (trigs, notes, vélocités, longueurs, "
            "p-locks).",
            "SETTINGS + PAGE : page GEN. Rythmes euclidiens (cycle, densité, régularité, décalage), plan de styles de "
            "batterie de FOUR à JUNGLE (style, remplissage, chaos), mélodie sur Tone et accords diatoniques sur Chord "
            "(tonique, gamme).",
            "Les réglages GEN ne sont pas enregistrés ; les patterns écrits le sont. Les qualités d'accord sont des "
            "p-locks de SHAPE : piste 6 sur la machine Chord.",
            "Par-dessus model-tg : accroches de démarrage, de touches, de pads et des voyants ; un 7e bloc du cache du "
            "système de fichiers retiré (9 restent).",
            f"Code dans les blocs retirés, après Model-TG : {len(code)} o en {AT:#x}, .bss jusqu'à "
            f"{syms['ours_end']:#x}. Généré par tools/gen_generative.py, notes/50.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "requires": ["model-tg"],
        "conflicts": conflicts,
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
        "append": {"at": f"{AT:#x}", "dest": f"{AT:#x}", "size": len(code),
                   "parts": [{"dest": f"{AT:#x}", "hex": code.hex()}], "reloc": []},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((TWEAKS / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak = build_tweak(stock)
    _, catalog = build.load_catalog()["model-cycles_OS1.13"]
    build.apply_writes(stock, [catalog["model-tg"], tweak])    # les octets d'origine collent, par-dessus model-tg
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre compilateur ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écritures)")


if __name__ == "__main__":
    main()
