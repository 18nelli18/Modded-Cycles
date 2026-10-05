#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/43-boot-anim.json : animation de démarrage « modded-cycles » (notes/39).

Au démarrage, l'OS d'origine lance une petite tâche (0x400539fc, corps en 0x40053a6c) qui allume et éteint au
hasard 32 carreaux arrondis (80 images de 20 ms), pendant que la tâche principale charge le projet ; celle-ci
attend la fin de l'animation (0x40053a54) avant d'afficher l'écran normal.

Le tweak remplace le corps de cette tâche, à la même place, par l'animation du logo du site (quatre carrés arrondis en
2 x 2, celui en haut à droite en orange) : les carrés apparaissent un par un en rebondissant, celui d'accent se creuse
(un anneau et un cœur, puisque l'écran n'a pas de couleur), puis « modded-cycles » s'écrit lettre par lettre dessous.
Même cadence, mêmes tampons d'écran, même fin que l'original (10 ticks, signal, retrait du minuteur).

tools/machines/boot_anim/ : boot_anim.S, lié par boot_anim.ld en 0x40053a6c ; ce script écrit à côté anim.inc
(géométrie, horaire) et anim_data.inc (carrés, rebond, colonnes du texte). frames() est le modèle Python de la même
animation, image par image : tools/emu/test_boot_anim.py le compare à ce que le vrai code envoie à l'écran.

    python3 tools/gen_boot_anim.py --cycles model-cycles_OS1.13.syx [--check]
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
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "boot_anim"
OUT = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "43-boot-anim.json"
BASE = gx.BASE
W, H = 128, 64                     # écran, en pixels

# Tâche d'animation d'origine : son corps, remplacé, et la création de la tâche (inchangée), qui pointe dessus.
BODY, BODY_END = 0x40053a6c, 0x40053e74
TASK_PEA = (0x40053a2e, "487a003c")   # pea (0x40053a6c,pc) : seule référence vers le corps

# Horaire, en images de 20 ms (minuteur de 2 ticks de 10 ms, comme l'original)
NF = 80                            # images de l'animation, autant que l'original ; puis 10 ticks d'attente
SIDE = 16                          # côté d'un carré du logo
GROW = (2, 6, 10, 14, 18, 18)      # côtés pendant l'apparition, puis SIDE (rebond)
# carrés : (centre x, centre y, image de départ) ; haut gauche, bas gauche, bas droite, puis l'accent (haut droite)
GAP = 4
LX, LY = (W - 2 * SIDE - GAP) // 2, 5            # coin haut gauche du logo (36 x 36)
CX = (LX + SIDE // 2, LX + SIDE + GAP + SIDE // 2)
CY = (LY + SIDE // 2, LY + SIDE + GAP + SIDE // 2)
SQUARES = ((CX[0], CY[0], 4), (CX[0], CY[1], 10), (CX[1], CY[1], 16), (CX[1], CY[0], 24))
ACX, ACY = CX[1], CY[0]
PUNCH = 34                         # l'accent se creuse : anneau de 2 + 2d jusqu'à HOLE, puis cœur CORE
HOLE, CORE = 10, 6
TYPE = 40                          # une lettre toutes les 2 images à partir de là

# Police du texte : 14 lignes (3 de jambage haut, 8 de corps, 3 de jambage bas), traits de 2 pixels.
FONT = {
    "m": ["", "", "",
          "#########.",
          "##########",
          "##..##..##",
          "##..##..##",
          "##..##..##",
          "##..##..##",
          "##..##..##",
          "##..##..##"],
    "o": ["", "", "",
          ".#####.",
          "#######",
          "##...##",
          "##...##",
          "##...##",
          "##...##",
          "#######",
          ".#####."],
    "d": [".....##",
          ".....##",
          ".....##",
          ".######",
          "#######",
          "##...##",
          "##...##",
          "##...##",
          "##...##",
          "#######",
          ".######"],
    "e": ["", "", "",
          ".#####.",
          "#######",
          "##...##",
          "#######",
          "#######",
          "##.....",
          "#######",
          ".######"],
    "-": ["", "", "", "", "", "",
          "#####",
          "#####"],
    "c": ["", "", "",
          ".#####",
          "######",
          "##....",
          "##....",
          "##....",
          "##....",
          "######",
          ".#####"],
    "y": ["", "", "",
          "##...##",
          "##...##",
          "##...##",
          "##...##",
          "##...##",
          "##...##",
          "#######",
          ".######",
          ".....##",
          "#######",
          "######."],
    "l": ["##"] * 11,
    "s": ["", "", "",
          ".#####",
          "######",
          "##....",
          "#####.",
          ".#####",
          "....##",
          "######",
          "#####."],
}
TEXT = "modded-cycles"
TROWS = 14
SPACING = 1


def text_columns():
    """(colonnes 16 bits, bit TROWS-1 = la ligne du haut ; colonne de fin de chaque lettre)."""
    cols, ends = [], []
    for i, ch in enumerate(TEXT):
        g = FONT[ch]
        width = max(len(r) for r in g)
        for x in range(width):
            v = 0
            for y, row in enumerate(g):
                if x < len(row) and row[x] == "#":
                    v |= 1 << (TROWS - 1 - y)
            cols.append(v)
        ends.append(len(cols))
        if i < len(TEXT) - 1:
            cols.extend([0] * SPACING)
    return cols, ends


COLS, ENDS = text_columns()
TX0, TY0 = (W - len(COLS)) // 2, LY + 2 * SIDE + GAP + 5


# --- modèle Python, image par image (même calcul que boot_anim.S) -------------------------------------------------

def _square(img, cx, cy, s, on):
    if s <= 0:
        return
    x0, y0 = cx - s // 2, cy - s // 2
    for i in range(s):
        e = min(i, s - 1 - i)
        ins = max(0, 2 - e) if s >= 12 else (1 if s >= 5 and e == 0 else 0)
        for y in range(y0 + ins, y0 + s - ins):
            img[y][x0 + i] = on


def side(k, f):
    d = f - SQUARES[k][2]
    return 0 if d < 0 else (GROW[d] if d < len(GROW) else SIDE)


def frame(f):
    """Image f (0 <= f < NF) : liste de H lignes de W pixels (0 / 1)."""
    img = [[0] * W for _ in range(H)]
    for k, (cx, cy, _) in enumerate(SQUARES):
        _square(img, cx, cy, side(k, f), 1)
    d = f - PUNCH
    if d >= 0:
        _square(img, ACX, ACY, min(2 + 2 * d, HOLE), 0)
        if d >= 4:
            _square(img, ACX, ACY, CORE, 1)
    if f >= TYPE:
        n = min((f - TYPE) // 2 + 1, len(TEXT))
        for c in range(ENDS[n - 1]):
            for r in range(TROWS):
                if COLS[c] >> (TROWS - 1 - r) & 1:
                    img[TY0 + r][TX0 + c] = 1
    return img


def frames():
    return [frame(f) for f in range(NF)]


# --- assemblage ---------------------------------------------------------------------------------------------------

def includes():
    consts = dict(NF=NF, SIDE=SIDE, NGROW=len(GROW), PUNCH=PUNCH, HOLE=HOLE, CORE=CORE, ACX=ACX, ACY=ACY,
                  TYPE=TYPE, NLET=len(TEXT), TX0=TX0, TY0=TY0, TROWS=TROWS)
    inc = "/* Écrit par tools/gen_boot_anim.py */\n" + "".join(f"\t.equ\t{k}, {v}\n" for k, v in consts.items())
    data = ("/* Écrit par tools/gen_boot_anim.py */\n"
            "sq_tab:\t.byte\t" + ", ".join(str(v) for sq in SQUARES for v in sq) + "\n"
            "grow:\t.byte\t" + ", ".join(map(str, GROW)) + "\n"
            "txt_end:\t.byte\t" + ", ".join(map(str, ENDS)) + "\n"
            "\t.balign\t2\n"
            "txt_cols:\n" + "".join("\t.word\t" + ", ".join(f"0x{v:04x}" for v in COLS[i:i + 12]) + "\n"
                                    for i in range(0, len(COLS), 12)))
    return inc, data


def compile_anim():
    """(adresse, octets) de la section .anim, et les symboles."""
    inc, data = includes()
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "anim.inc").write_text(inc, encoding="utf-8")
        (d / "anim_data.inc").write_text(data, encoding="utf-8")
        obj, elf, out = d / "ba.o", d / "ba.elf", d / "anim.bin"
        gx.run([gx.CROSS + "as", "-mcpu=54418", "-I", str(d), str(SRC / "boot_anim.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "boot_anim.ld"), "--no-warn-rwx-segments", "-o", str(elf), str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".anim", str(elf), str(out)])
        addr = int(subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                                  check=True).stdout.split(".anim")[1].split()[1], 16)
        return addr, out.read_bytes(), syms


def build_tweak(stock):
    addr, code, syms = compile_anim()
    if addr != BODY or syms["ba_task"] != BODY or len(code) > BODY_END - BODY:
        raise SystemExit(f"!! {len(code)} o à {addr:#x}, place {BODY_END - BODY} o à {BODY:#x}")
    va, old = TASK_PEA
    if stock[va - BASE:va - BASE + 4] != bytes.fromhex(old) or va + 2 + struct.unpack(">h", bytes.fromhex(old)[2:])[0] != BODY:
        raise SystemExit(f"!! la création de la tâche ({va:#x}) ne pointe plus sur {BODY:#x}")
    if stock[BODY - BASE:BODY - BASE + 4] != bytes.fromhex("4fefff80"):     # lea -128(sp),sp
        raise SystemExit(f"!! octets d'origine inattendus en {BODY:#x}")
    old = stock[addr - BASE:addr - BASE + len(code)]
    return {
        "id": "boot-anim",
        "order": 43,
        "name": "Animation de démarrage modded-cycles",
        "description": [
            "Au démarrage, à la place des carreaux qui clignotent : les quatre carrés arrondis du logo "
            "apparaissent un par un, celui d'accent se creuse, puis « modded-cycles » s'écrit dessous.",
            f"{NF} images de 20 ms et la même fin que l'original (1,8 s en tout) : le démarrage ne dure pas plus "
            "longtemps.",
            f"Le corps de la tâche d'animation d'origine (0x40053a6c) est réécrit à sa place : {len(code)} o sur "
            f"{BODY_END - BODY}. Aucune place libre utilisée. Généré par tools/gen_boot_anim.py, notes/39.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "symbols": {"ba_task": f"{syms['ba_task']:#x}"},
        "writes": [{"off": addr - BASE, "old": old.hex(), "new": code.hex()}],
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
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} écriture)")


if __name__ == "__main__":
    main()
