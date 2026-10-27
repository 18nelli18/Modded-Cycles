"""Fenêtre de valeur d'Attack, du Filtre et de la Résonance de Model-TG (notes/82) : écritures ajoutées à Model-TG.

Sous MACHINES + DECAY / SWEEP / CONTOUR, Model-TG montre Attack (0x0d), Filtre (0x0c) et Résonance (0x0b), des
identifiants « Error » de l'OS : pas de courbe, pas de grand nombre, un petit potard à la place. machines/popup_view
dessine leur fenêtre avec celle d'un vrai paramètre : Filtre et Résonance du Sampler (0x49, 0x4a), et pour Attack
celle d'Amp Decay (0x18) dont la courbe est retournée de gauche à droite. Le nom reste celui de Model-TG.

Entrée : wp_stock de wf_popup (Model-TG) saute à pv_popup au lieu de 0x4001d818 (MC_PATCHES de gen_model_tg.py,
même taille : aucun symbole de Model-TG ne bouge). Le code va dans le masque de sprite 48x22 libéré 0x401592bc
(tools/sprites.py), écrit avec Model-TG comme usb_steady et voice_loop.

Preuve : tools/emu/test_popup_view.py.
"""
import pathlib
import subprocess
import tempfile

import gen_sdvintage_exact as gx
import sprites

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "machines" / "popup_view"
BASE = 0x40000400
MASK = 0x401592bc                  # masque 48x22 libéré (192 o)
DECAY = 0x18                       # Amp Decay : sa fenêtre sert à Attack
X0, X1 = 7, 56                     # sa courbe : 50x22 centrée en (32, 19), x 7..56, y 8..29
NOTE = ("Fenêtre de valeur d'Attack, du Filtre et de la Résonance (tools/popup_view.py, notes/82) : grand nombre, "
        "points et courbe (Decay retourné pour Attack, ceux du Sampler pour Filtre et Résonance).")


def compile_view():
    """(octets à MASK, symboles)."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, out = d / "pv.o", d / "pv.elf", d / "cave.bin"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", f"-DPV_DECAY={DECAY}", f"-DPV_X0={X0}", f"-DPV_X1={X1}",
                "-c", str(SRC / "popup_view.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "popup_view.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".cave", str(elf), str(out)])
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout
        addr = int(heads.split(".cave ")[1].split()[1], 16)
        return addr, out.read_bytes(), syms


def writes(stock):
    """Le code dans le masque et la redirection de son sprite."""
    addr, code, syms = compile_view()
    room = sprites.zone(MASK)[1]
    if addr != MASK or syms.get("pv_popup") != MASK or len(code) > room:
        raise SystemExit(f"!! popup_view : {len(code)} o à {addr:#x}, place {room} o à {MASK:#x}")
    old = stock[addr - BASE:addr - BASE + len(code)]
    return [{"off": addr - BASE, "old": old.hex(), "new": code.hex()}, sprites.redirect_write(MASK)]
