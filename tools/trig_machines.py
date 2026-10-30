"""Pas tenu + MACHINES : le navigateur des machines du pas s'ouvre au relâchement de MACHINES, et seulement si aucun
potard n'a tourné ni aucune autre touche n'a été pressée pendant (notes/86 §7) ; écritures ajoutées à Model-TG.

MACHINES tenue est le modificateur de Model-TG et du lo-fi de piste : pas tenu + MACHINES + potard pose un p-lock
d'Attack, Rate, Bits, Filtre ou Résonance, mais l'OS ouvrait le navigateur dès l'appui de MACHINES. Sans pas tenu, ou
avec FUNC, rien ne change. Code : tools/machines/trig_machines/trig_machines.S, dans les masques de sprite libérés
0x4018d918 (41x41) et 0x4016ea78 (52x22) (tools/sprites.py) ; quatre accroches sur l'OS (HOOKS), aucune sur Model-TG.
"""
import pathlib
import struct
import subprocess
import tempfile

import gen_sdvintage_exact as gx
import sprites

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "machines" / "trig_machines"
BASE = 0x40000400
CAVES = {".cave": 0x4018d918, ".cave2": 0x4016ea78}   # masques libérés : 41x41 (328 o), 52x22 (208 o)
# (adresse, octets d'origine, instruction, symbole, rôle)
HOOKS = (
    (0x4001c0d2, "4e56ffa848d73c7c", 0x4eb9, "mt_main",
     "MainScreenView::consumeKeyEvent : link.w fp,#-88 ; movem.l -> jsr mt_main ; nop"),
    (0x4001c27c, "4eb94006b736", 0x4eb9, "mt_trig", "son cas 5 (MACHINES) : jsr 0x4006b736 -> jsr mt_trig"),
    (0x4001f4f0, "4e56ffac48d73cfc", 0x4eb9, "mt_knob",
     "ParameterPageView::encoder : link.w fp,#-84 ; movem.l -> jsr mt_knob ; nop"),
    (0x4001f97e, "4e56ffd848d73c0c", 0x4eb9, "mt_key",
     "ParameterPageView::consumeKeyEvent : link.w fp,#-40 ; movem.l -> jsr mt_key ; nop"),
)
NOTE = ("Pas tenu + MACHINES (tools/trig_machines.py, notes/86 §7) : le navigateur des machines du pas s'ouvre au "
        "relâchement de MACHINES, et seulement si aucun potard ni aucune autre touche n'a servi pendant.")


def compile_mt():
    """{section: (adresse, octets)}, symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf = d / "mt.o", d / "mt.elf"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(SRC / "trig_machines.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "trig_machines.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout
        out = {}
        for line in heads.splitlines():
            p = line.split()
            if len(p) >= 4 and p[1] in CAVES:
                b = d / (p[1].strip(".") + ".bin")
                gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", p[1], str(elf), str(b)])
                out[p[1]] = (int(p[3], 16), b.read_bytes())
        return out, syms


SECS, SYMS = compile_mt()


def writes(stock):
    """Le code dans les masques, la redirection de leurs sprites et les quatre accroches."""
    out = []
    for name, mask in CAVES.items():
        addr, code = SECS[name]
        room = sprites.zone(mask)[1]
        if addr != mask or len(code) > room:
            raise SystemExit(f"!! trig_machines {name} : {len(code)} o à {addr:#x}, place {room} o à {mask:#x}")
        out += [{"off": addr - BASE, "old": stock[addr - BASE:addr - BASE + len(code)].hex(), "new": code.hex()},
                sprites.redirect_write(mask)]
    for va, old, op, sym, _ in HOOKS:
        if stock[va - BASE:va - BASE + len(old) // 2].hex() != old:
            raise SystemExit(f"!! trig_machines : octets d'origine inattendus en {va:#x}")
        new = struct.pack(">HI", op, SYMS[sym]) + (b"\x4e\x71" if len(old) == 16 else b"")
        out.append({"off": va - BASE, "old": old, "new": new.hex()})
    return out
