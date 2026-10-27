"""Fenêtre de valeur d'Attack, du Filtre et de la Résonance de Model-TG (notes/82) : écritures ajoutées à Model-TG.

Sous MACHINES + DECAY / SWEEP / CONTOUR, Model-TG montre Attack (0x0d), Filtre (0x0c) et Résonance (0x0b), des
identifiants « Error » de l'OS : pas de courbe, pas de grand nombre, un petit potard à la place. machines/popup_view
dessine leur fenêtre avec celle d'un vrai paramètre : Filtre et Résonance du Sampler (0x49, 0x4a), et pour Attack
celle d'Amp Decay (0x18) dont la courbe est retournée de gauche à droite. Le nom reste celui de Model-TG. Le même
code rend entière la valeur enregistrée de ces trois identifiants (elle s'affichait « 83.00 »).

Entrée : wp_stock de wf_popup (Model-TG) saute à pv_popup au lieu de 0x4001d818 (MC_PATCHES de gen_model_tg.py,
même taille : aucun symbole de Model-TG ne bouge). Le code va dans deux masques de sprite 48x22 libérés
0x401592bc (fenêtre) et 0x40168a84 (texte de la valeur enregistrée), écrits avec Model-TG comme usb_steady et
voice_loop. Le second détourne le formateur décimal 0x4004a440 pour les seuls 0x0b/0x0c/0x0d vers le formateur
entier 0x400456c8 : aucun identifiant stocké ne change.

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
MASK = 0x401592bc                  # masque 48x22 libéré (192 o) : la fenêtre
MASK_TEXT = 0x40168a84             # second masque 48x22 libéré (192 o) : le texte de la valeur enregistrée
TEXT_PATCH = 0x4004a448            # formateur décimal 0x4004a440 : movel 24(%sp),%d2 ; movel 28(%sp),%d3
DECAY = 0x18                       # Amp Decay : sa fenêtre sert à Attack
X0, X1 = 7, 56                     # sa courbe : 50x22 centrée en (32, 19), x 7..56, y 8..29
NOTE = ("Fenêtre de valeur d'Attack, du Filtre et de la Résonance (tools/popup_view.py, notes/82) : grand nombre, "
        "points et courbe (Decay retourné pour Attack, ceux du Sampler pour Filtre et Résonance), et valeur "
        "enregistrée entière comme celle du Sampler.")


def compile_view():
    """(adresse et octets de la fenêtre à MASK, symboles, adresse et octets du texte à MASK_TEXT)."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf = d / "pv.o", d / "pv.elf"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", f"-DPV_DECAY={DECAY}", f"-DPV_X0={X0}", f"-DPV_X1={X1}",
                "-c", str(SRC / "popup_view.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "popup_view.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout

        def section(name):
            out = d / (name[1:] + ".bin")
            gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", name, str(elf), str(out)])
            addr = int(heads.split(name + " ")[1].split()[1], 16)
            return addr, out.read_bytes()
        addr, code = section(".cave")
        addr_text, code_text = section(".cave2")
        return addr, code, syms, addr_text, code_text


def writes(stock):
    """Le code dans les deux masques et la redirection de leurs sprites."""
    addr, code, syms, addr_text, code_text = compile_view()
    for a, c, sym, mask in ((addr, code, "pv_popup", MASK), (addr_text, code_text, "pv_text", MASK_TEXT)):
        room = sprites.zone(mask)[1]
        if a != mask or syms.get(sym) != mask or len(c) > room:
            raise SystemExit(f"!! popup_view : {sym} {len(c)} o à {a:#x}, place {room} o à {mask:#x}")
    out = []
    for a, c, mask in ((addr, code, MASK), (addr_text, code_text, MASK_TEXT)):
        old = stock[a - BASE:a - BASE + len(c)]
        out += [{"off": a - BASE, "old": old.hex(), "new": c.hex()}, sprites.redirect_write(mask)]
    old = stock[TEXT_PATCH - BASE:TEXT_PATCH - BASE + 6]
    out.append({"off": TEXT_PATCH - BASE, "old": old.hex(),
                "new": (b"\x4e\xf9" + MASK_TEXT.to_bytes(4, "big")).hex()})
    return out
