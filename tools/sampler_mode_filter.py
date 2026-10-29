"""Filtre et Résonance de piste pour le Sampler en modes Granular/Stretch/Pluck/Wave (notes/83) :
écritures ajoutées à Model-TG.

Sous MACHINES + SWEEP / CONTOUR sur une piste Sampler en mode Granular(3), Stretch(4), Pluck(5) ou
Wave(6), le réglage agit sur le filtre et la résonance de piste (identifiants 0x0c / 0x0b, trackData +48/+50,
gflt_coef / gflt_run), exactement comme sur toutes les autres machines.
En modes One shot(0), Loop(1), Slice(2), le Sampler conserve son propre filtre (0x49 / 0x4a) sans
double filtrage.

Entrées :
  - dh_atk / dbh_atk : jmp vers smf_descr au lieu de movel #sampler_descr_atk,%d0 ; rts ;
  - gflt_coef : jmp vers smf_gflt au lieu de cmpil #6,%d1 ; beqs gc_store.
Mêmes tailles (MC_PATCHES de gen_model_tg.py) : aucun symbole de Model-TG ne bouge. Le code va dans
le masque de sprite 48x22 libéré 0x4016bcd8 (tools/sprites.py), écrit avec Model-TG comme usb_steady,
voice_loop et popup_view.
"""
import pathlib
import subprocess
import tempfile

import gen_sdvintage_exact as gx
import sprites

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "machines" / "sampler_mode_filter"
BASE = 0x40000400
MASK = 0x4016bcd8                  # masque 48x22 libéré (192 o)

# Adresses fixes et symboles de Model-TG (invariants de taille)
CUR_PROJ = 0x400cf866
CUR_KIT = 0x4000eb90
SEL_TRACK = 0x40012412
LOOP_MODE = 0x401b2404
OTHER_DESCR = 0x401abf32
SAMPLER_DESCR_ATK = 0x401abee6
GC_CONT = 0x401bac2a                  # lo-fi de piste : ST_SPLIT_PATCHES de gen_model_tg.py (notes/86)
GC_STORE = 0x401bac98                 # ajoute 0x20 o avant gflt_coef (ailleurs : 0x401bac0a / 0x401bac78)

NOTE = ("Filtre et Résonance de piste pour le Sampler en modes Granular/Stretch/Pluck/Wave "
        "(tools/sampler_mode_filter.py, notes/83) : filtre de piste sous MACHINES+SWEEP/CONTOUR "
        "en modes >= 3, filtre propre intact en modes 0..2.")


def compile_filter():
    """(octets à MASK, symboles)."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, out = d / "smf.o", d / "smf.elf", d / "cave.bin"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418",
                f"-DCUR_PROJ={CUR_PROJ:#x}",
                f"-DCUR_KIT={CUR_KIT:#x}",
                f"-DSEL_TRACK={SEL_TRACK:#x}",
                f"-DLOOP_MODE={LOOP_MODE:#x}",
                f"-DOTHER_DESCR={OTHER_DESCR:#x}",
                f"-DSAMPLER_DESCR_ATK={SAMPLER_DESCR_ATK:#x}",
                f"-DGC_CONT={GC_CONT:#x}",
                f"-DGC_STORE={GC_STORE:#x}",
                "-c", str(SRC / "sampler_mode_filter.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "sampler_mode_filter.ld"), "--no-warn-rwx-segments", "-o", str(elf),
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


ADDR, CODE, SYMS = compile_filter()
DESCR = SYMS["smf_descr"]
GFLT = SYMS["smf_gflt"]


def writes(stock):
    """Le code dans le masque et la redirection de son sprite."""
    addr, code, syms = compile_filter()
    room = sprites.zone(MASK)[1]
    if addr != MASK or syms.get("smf_descr") != MASK or len(code) > room:
        raise SystemExit(f"!! sampler_mode_filter : {len(code)} o à {addr:#x}, place {room} o à {MASK:#x}")
    old = stock[addr - BASE:addr - BASE + len(code)]
    return [{"off": addr - BASE, "old": old.hex(), "new": code.hex()}, sprites.redirect_write(MASK)]


def check_syms(syms):
    """Les adresses de Model-TG écrites en dur ci-dessus, contre la table de symboles de sa construction (les deux
    variantes, model-tg et model-tg-st) : une retouche de Model-TG qui les déplacerait arrête la génération."""
    want = {"loop_mode": LOOP_MODE, "other_descr": OTHER_DESCR, "sampler_descr_atk": SAMPLER_DESCR_ATK,
            "gc_store": GC_STORE}
    bad = {n: (syms.get(n), v) for n, v in want.items() if syms.get(n) != v}
    if syms.get("gflt_coef", 0) + 18 != GC_CONT:             # après lea, moveml, moveq, puis les 8 o remplacés
        bad["gflt_coef+18"] = (syms.get("gflt_coef", 0) + 18, GC_CONT)
    if bad:
        raise SystemExit("!! sampler_mode_filter : adresses de Model-TG déplacées : "
                         + ", ".join(f"{n} {a if a is None else hex(a)} != {b:#x}" for n, (a, b) in bad.items()))
