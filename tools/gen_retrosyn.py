#!/usr/bin/env python3
"""Writes the tweak that adds the RETROSYN machine to the Modded Cycles OS (notes/84):
tweaks/model-cycles_OS1.13/31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn.json.

RETROSYN is a chiptune voice (Game Boy pulse and wave, NES triangle, two LFSR noises, a SNES loop with Gaussian
interpolation), with a pitch sweep, chord arpeggios and a 4-bit PUNCH. Its core comes from the AveyCole fork
(tools/machines/retrosyn/: retrosyn_dsp.h the core, retrosyn.c the bridge to the OS voice, retrosyn_tables.h written
by gen_retrosyn_tables.py).

It is the machine after ACID in the OS combination: Model-TG, the 5 Syntakt engines, MACRO, ACID, then RETROSYN,
machine 15 (index 14), the 8th added machine. Same mechanics as ACID in that combination (gen_acid_combos.py,
gen_macro_syntakt.py): the engines' bridge, MACRO and ACID keep their bytes and places; RETROSYN's code and tables
are linked at RS_AT, its variables at RS_BSS, above ACID's; the payload is stored compressed (aPLib). With 8 added
machines the parameter rows move to gs.ROWS8 and the MACHINES screen draws 8 marks per row (gs.marks_row).

RETROSYN is not compiled with GOV_SKIP (ACID's guard against a voice the engines' load governor stopped calling):
every trig resets RETROSYN's phase, sweep, arpeggio and silence flag (retrosyn_dsp.h), and it has no slide, so a
voice the governor skipped restarts from the trig like any other (proof: tools/emu/test_retrosyn.py).

    python3 tools/gen_retrosyn.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--check]

Without --cycles: retrosyn_tables.h only. Like 31-…-macro-acid.json, the file carries, from the OS, only the short
original bytes ("old") that check the official file; the descriptor table is copied at build time from YOUR file
(recipe "cycles") and the Syntakt code extracted from YOUR Syntakt_OS1.42.syx. RETROSYN, MACRO and ACID are compiled
by m68k-linux-gnu-gcc/g++ 13.3 (Ubuntu 24.04): another GCC gives other bytes, and --check says so.
"""
import argparse
import contextlib
import io
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))
sys.path.insert(0, str(HERE / "machines" / "retrosyn"))

import gen_acid as ga              # noqa: E402
import gen_acid_combos as gac      # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_retrosyn_tables as grt  # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import syntakt                     # noqa: E402

DEV = gs.DEV
SRC = HERE / "machines" / "retrosyn"
TABLES = SRC / "retrosyn_tables.h"
# Place in the payload (offsets from its start): above ACID's variables (gac.ACID_BSS + 6 x 124 o: up to 0x782e8),
# the code and tables (8 KB at most), then the variables of the 6 voices.
RS_AT = 0x79000
RS_BSS = 0x7b000
CODES = gac.FIVE                   # the OS combination: the 5 engines, MACRO, ACID
LINK = """SECTIONS
{{
  .text {code:#x} : {{ *(.text.retrosyn_update) *(.text.retrosyn_render) *(.text*) }}
  .rodata ALIGN(4) : {{ *(.rodata*) }}
  .data ALIGN(4) : {{ *(.data*) }}
  .bss {bss:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }}
  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
"""
# COLOR, SHAPE (6 waves: 0..5), SWEEP (centre 64: off), CONTOUR (8 chords); DECAY
MACHINE = dict(name="RETROSYN", image=4, decay=50,
               knobs=(("Color", "COLR", 0), ("Shape", "SHAP", 0, 0, 5), ("Sweep", "SWEP", 64), ("Contour", "CONT", 0)))
AVEYCOLE_REPO = "AveyCole/Modded-Cycles"


def tables_header():
    """retrosyn_tables.h as gen_retrosyn_tables.py prints it."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        grt.main()
    return buf.getvalue()


def compile_machine(tmp, at, bss_at):
    """RETROSYN's bridge and core linked at at (code, tables) and bss_at (variables); the code must end below bss_at.
    Returns (bytes, symbols, sections: dict name -> (address, size), end of the BSS)."""
    for f in ("retrosyn.c", "retrosyn_dsp.h", "retrosyn_tables.h"):
        (tmp / f).write_bytes((SRC / f).read_bytes())
    o = tmp / "retrosyn.o"
    gx.run([gx.CROSS + "gcc", *ga.CFLAGS, f"-I{tmp}", "-c", str(tmp / "retrosyn.c"), "-o", str(o)])
    ld, elf, out = tmp / "link.ld", tmp / "retrosyn.elf", tmp / "retrosyn.bin"
    ld.write_text(LINK.format(code=at, bss=bss_at))
    gx.run([gx.CROSS + "ld", "-T", str(ld), "--gc-sections", "--no-warn-rwx-segments", "-e", "retrosyn_update",
            "-u", "retrosyn_render", "-o", str(elf), str(o)])
    secs = {}
    for line in gx.run([gx.CROSS + "objdump", "-h", str(elf)]).splitlines():
        f = line.split()
        if len(f) > 4 and f[0].isdigit():
            secs[f[1]] = (int(f[3], 16), int(f[2], 16))
    if set(secs) - {".text", ".rodata", ".data", ".bss"}:
        raise SystemExit(f"!! unexpected sections: {sorted(secs)}")
    if secs.get(".data", (0, 0))[1]:
        raise SystemExit("!! initialised variables: the boot hook would not copy them")
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-R", ".bss", str(elf), str(out)])
    blob = out.read_bytes()
    syms = {p[2]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(elf)]).splitlines())
            if len(p) == 3}
    if at + len(blob) > bss_at:
        raise SystemExit(f"!! code too large: {len(blob)} bytes from {at:#x}, variables at {bss_at:#x}")
    bss = secs.get(".bss", (bss_at, 0))
    if bss[0] != bss_at:
        raise SystemExit("!! BSS")
    return blob, syms, secs, (bss[0] + bss[1] + 3) & ~3


_RS = {}


def retrosyn_part(pay):
    """RETROSYN linked at pay + RS_AT (variables at pay + RS_BSS): dict(machine, at, blob, end, syms, secs)."""
    if pay not in _RS:
        at, bss = pay + RS_AT, pay + RS_BSS
        with tempfile.TemporaryDirectory() as d:
            blob, syms, secs, end = compile_machine(pathlib.Path(d), at, bss)
        machine = dict(MACHINE, label="RETROSYN", update=syms["retrosyn_update"], render=syms["retrosyn_render"])
        _RS[pay] = dict(machine=machine, at=at, blob=blob, end=end, syms=syms, secs=secs)
    return _RS[pay]


def tweak_id():
    return gac.tweak_id(CODES, True, True) + "-retrosyn"


def build_tweak(img, st_img, repo, tg):
    """The OS combination (with Model-TG: tg, gs.tg_context) with RETROSYN after ACID."""
    gs.set_base(gs.PAY_TG)
    rs = retrosyn_part(gs.PAY_TG)
    out, info = gac.build_engines(img, st_img, repo, list(CODES), tg, True, more=[rs])
    base = gac.tweak_id(CODES, True, True)
    tid = tweak_id()
    index = gs.TG_FIRST + len(CODES) + 2
    desc = out["description"]
    k = next(i for i, d in enumerate(desc) if d.startswith("ensemble (notes/54 §11) : "))
    if not desc[k].endswith(f"ACID (machine {index}).") or not desc[k - 1].endswith(" et machine ACID (notes/54),"):
        raise SystemExit("!! description of the ACID combination changed: update gen_retrosyn.py")
    desc[k - 1] = desc[k - 1][:-len(" et machine ACID (notes/54),")] + ", machine ACID (notes/54)"
    desc[k] = ("et machine RETROSYN (notes/84), " + desc[k][:-1] + f", RETROSYN (machine {index + 1}).")
    k = next(i for i, d in enumerate(desc) if d.startswith("ACID d'après Open303"))
    desc.insert(k + 1, f"RETROSYN d'après le fork {AVEYCOLE_REPO} (cœur fourni par AveyCole, licence à confirmer, "
                       f"notes/84), lié à +{RS_AT:#x}, sans GOV_SKIP.")
    desc[:] = [d.replace("Le régulateur de charge des moteurs vaut aussi pour MACRO et ACID.",
                         "Le régulateur de charge des moteurs vaut aussi pour MACRO, ACID et RETROSYN.") for d in desc]
    desc.append("Généré par tools/gen_retrosyn.py, au-dessus de " + base + ".")
    ids = gac.all_ids(tg) | {base}
    out.update({
        "id": tid,
        "name": out["name"].replace(" et machine ACID (basse acide, d'après Open303, MIT)",
                                    ", machine ACID (basse acide, d'après Open303, MIT) et machine RETROSYN "
                                    "(chiptune, AveyCole)"),
        "conflicts": sorted(ids - {tid}),
    })
    out["symbols"].update({k: f"{rs['syms'][k]:#x}" for k in ("retrosyn_update", "retrosyn_render", "tracks")})
    secs = rs["secs"]
    info.update(text=secs[".text"][1], rodata=secs.get(".rodata", (0, 0))[1], bss=secs.get(".bss", (0, 0))[1],
                code=len(rs["blob"]), at=rs["at"], bss_at=rs["at"] - RS_AT + RS_BSS)
    return out, info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", help="official model-cycles_OS1.13.syx (without it: retrosyn_tables.h only)")
    ap.add_argument("--syntakt", help="official Syntakt_OS1.42.syx (or 1.41)")
    ap.add_argument("--eurorack", help=f"clone of {gm.EURORACK_REPO} at commit {gm.EURORACK_COMMIT[:7]}")
    ap.add_argument("--check", action="store_true", help="check that the committed files match")
    args = ap.parse_args()
    bad = gm.emit(TABLES, tables_header(), args.check)
    if args.cycles:
        if not (args.syntakt and args.eurorack):
            raise SystemExit("!! --cycles needs --syntakt and --eurorack")
        img = g7.cycles_main(args.cycles)
        if len(img) != gx.IMAGE_LEN:
            raise SystemExit("!! not the official MAIN OS 1.13")
        repo = pathlib.Path(args.eurorack).resolve()
        gm.check_sources(repo)
        st_img = syntakt.dsp_image(args.syntakt)
        tweak, info = build_tweak(img, st_img, repo, gs.tg_context(img))
        path = DEV / f"{tweak['order']}-{tweak['id']}.json"
        print(f"  {tweak['id']}: {len(tweak['writes'])} writes, {info['ndesc']} descriptors, payload {info['size']} "
              f"bytes, stored in {info['packed']} bytes, image up to {info['end']:#x} "
              f"({gs.END_LIMIT - info['end']} bytes left below {gs.END_LIMIT:#x})")
        print(f"  RETROSYN at {info['at']:#x}: text {info['text']} + rodata {info['rodata']} = {info['code']} bytes, "
              f"variables {info['bss']} bytes at {info['bss_at']:#x}")
        bad += gm.emit(path, json.dumps(tweak, indent=1) + "\n", args.check)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
