#!/usr/bin/env python3
"""Machine MODAL : un résonateur d'après Rings d'Émilie Gillet (Mutable Instruments, code MIT), en machine ajoutée
du Model:Cycles (notes/74).

Le son est notre code (tools/machines/modal/ : modal_dsp.h, le cœur, réécrit en virgule fixe d'après rings/dsp et
stmlib de pichenettes/eurorack ; modal_fix.h, son arithmétique ; modal.c, la passerelle). Ses tables
(modal_tables.h) sont calculées ici avec les formules de rings/resources/lookup_tables.py et de stmlib/dsp/units.cc,
arrondies en float32 comme le fait le module, puis converties en entiers. Licence : LICENSE-Rings (MIT).

MODAL vient après ACID, 15e machine du Modded Cycles OS : le tweak de l'OS,
31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json, est celui des 5 moteurs du Syntakt, de MACRO et d'ACID
(gen_acid_combos.py), avec MODAL en plus (gen_macro_syntakt.build_tweak, « more »). Huit machines ajoutées : rangées
et enregistrements de gs.ROWS8, deux lignes de 8 repères sur l'écran MACHINES.

    python3 tools/gen_modal.py --tables [--check]
    python3 tools/gen_modal.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--check]

Le JSON versionné est compilé par m68k-linux-gnu-gcc 13.3 (Ubuntu 24.04), comme les autres machines ajoutées : un
autre GCC donne d'autres octets, et --check le dit (modal_tables.h et LICENSE-Rings, eux, ne dépendent pas du
compilateur).
"""
import argparse
import json
import math
import pathlib
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

SRC = HERE / "machines" / "modal"
TABLES = SRC / "modal_tables.h"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
LICENSE_OUT = DEV / "LICENSE-Rings"
TWEAK_ID = "syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal"
FIVE = ("sd", "cp", "toy", "bits", "swarm")

FS = 48000.0
BLOCK = 32                      # le bloc du Cycles (Rings : 24)

# Place de MODAL dans la charge utile (décalages depuis son début) : après ACID et ses variables (gen_acid_combos :
# ACID_AT 0x76000, ACID_BSS 0x78000, jusqu'à 0x78300), le code et les tables (40 Ko au plus), puis ses variables.
# L'état de ses 6 pistes (160 Ko chacune : la Part de Rings, puis la réverbe) est au-dessus de la charge utile, à
# MODAL_RAM (modal.c) : 0x46800000..0x468f0000, juste au-dessus de la zone d'échantillons de Model-TG et de la
# charge utile (notes/74 §5).
MODAL_AT = 0x79000
MODAL_BSS = 0x83000
MODAL_RAM = 0x46800000
TRACK_SIZE = 0x28000

# --- la machine (comme gm.MACHINE) : COLOR, SHAPE, SWEEP, CONTOUR = (nom long, nom court, défaut[, min, max]) ;
# decay : DECAY (DAMPING de Rings). SHAPE choisit le modèle (0..5) ; FUNC + SHAPE la polyphonie (FINE, modal.c).
MODELS = ("MODAL", "SYMPATHETIC STRING", "STRING", "FM VOICE", "SYMPATHETIC STRING QUANTIZED", "STRING AND REVERB")
MACHINE = dict(name="MODAL", image=2, decay=64,
               knobs=(("Brightness", "BRIG", 64), ("Model", "MODL", 0, 0, len(MODELS) - 1),
                      ("Position", "POS", 40), ("Structure", "STRC", 36)))
SHAPE_KNOB = 5                  # numéro de potard de SHAPE pour l'OS (PITCH = 2 : l'entrée potard - 2 de l'enregistrement)

CFLAGS = ["-mcpu=54418", "-O2", "-malign-int", "-U_FORTIFY_SOURCE", "-ffreestanding", "-fno-builtin",
          "-fno-tree-loop-distribute-patterns", "-nostdlib", "-fno-pic", "-fno-common", "-ffunction-sections",
          "-fdata-sections", "-fomit-frame-pointer", "-Wall", "-Wextra", "-Werror"]
LINK = """SECTIONS
{{
  .text {code:#x} : {{ *(.text.modal_update) *(.text.modal_render) *(.text*) }}
  .rodata ALIGN(4) : {{ *(.rodata*) }}
  .data ALIGN(4) : {{ *(.data*) }}
  .bss {bss:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }}
  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
"""
ENTRIES = ("modal_update", "modal_render", "modal_poly_step", "modal_poly_fmt", "modal_poly_draw")

LICENSE = """Machine MODAL of Modded-Cycles: fixed-point code written after Rings by Emilie Gillet (the Part of
rings/dsp and what it uses of stmlib: modal resonator, strings, sympathetic strings and chords, FM voice,
internal exciters, reverb, note filter, limiter; https://github.com/pichenettes/eurorack, commit 08460a6),
under the MIT license:

Copyright 2015 Emilie Gillet.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


def f32(x):
    """x arrondi en float32, comme une constante ou une table de Rings."""
    return struct.unpack("<f", struct.pack("<f", x))[0]


def q(x, bits):
    v = int(round(x * (1 << bits)))
    return max(-0x80000000, min(0x7fffffff, v))


def lut_stiffness():
    out = []
    for i in range(257):
        g = i / 256.0
        if g < 0.25:
            v = -(0.25 - g) * 0.25
        elif g < 0.3:
            v = 0.0
        elif g < 0.9:
            v = 0.01 * 10 ** ((g - 0.3) / 0.6 * 2.005) - 0.01
        else:
            h = ((g - 0.9) / 0.1) ** 2
            v = 1.5 - math.cos(h * math.pi) / 2.0
        out.append(v)
    out[-1] = out[-2] = 2.0
    return out


def lut_fm_frequency_quantizer():
    ratios = [0.5, 0.5 * 2 ** (16 / 1200.0), math.sqrt(2) / 2, math.pi / 4, 1.0, 1.0 * 2 ** (16 / 1200.0),
              math.sqrt(2), math.pi / 2, 7.0 / 4, 2, 2 * 2 ** (16 / 1200.0), 9.0 / 4, 11.0 / 4, 2 * math.sqrt(2), 3,
              math.pi, math.sqrt(3) * 2, 4, math.sqrt(2) * 3, math.pi * 3 / 2, 5, math.sqrt(2) * 4, 8]
    scale = []
    for r in ratios:
        r = 12 * math.log2(r)
        scale.extend([r, r, r])
    size = 2 ** math.ceil(math.log2(len(scale)))
    while len(scale) < size:
        diffs = [scale[i + 1] - scale[i] for i in range(len(scale) - 1)]
        gap = diffs.index(max(diffs))                    # le premier écart maximal, comme numpy.argmax
        scale = scale[:gap + 1] + [(scale[gap] + scale[gap + 1]) / 2] + scale[gap + 1:]
    scale.append(scale[-1])
    return scale


# Accords des cordes sympathiques quantifiées (part.cc, BRYAN_CHORDS, défini dans rings/dsp/dsp.h) : polyphonie 1
# (8 cordes), 2 (4 cordes), 3 et 4 (2 cordes, la même table)
CHORDS = [
    [[-12, -0.01, 0, 0.01, 0.02, 11.98, 11.99, 12], [-12, -5, 0, 6.99, 7, 11.99, 12, 19],
     [-12, -5, 0, 5, 7, 11.99, 12, 17], [-12, -5, 0, 3, 7, 3.01, 12, 19], [-12, -5, 0, 3, 7, 3.01, 10, 19],
     [-12, -5, 0, 3, 14, 3.01, 10, 19], [-12, -5, 0, 3, 7, 3.01, 10, 17], [-12, -5, 0, 2, 7, 9, 16, 19],
     [-12, -5, 0, 4, 7, 11, 14, 19], [-12, -5, 0, 4, 7, 11, 10.99, 19], [-12, -5, 0, 4, 7, 11.99, 12, 19]],
    [[-12, 0, 0.01, 12], [-12, 6.99, 7, 12], [-12, 5, 7, 12], [-12, 3, 11.99, 12], [-12, 3, 10, 12],
     [-12, 3, 10, 14], [-12, 3, 10, 17], [-12, 2, 9, 16], [-12, 4, 11, 14], [-12, 4, 7, 11], [-12, 4, 7, 12]],
    [[0, -12], [0, 2], [0, 3], [0, 4], [0, 5], [0, 7], [0, 9], [0, 10], [0, 11], [0, 12], [-12, 12]],
]


def xf(x):
    """(m, e) du flottant maison de modal_fix.h : x = m 2^(e - 30), |m| dans [2^30, 2^31)."""
    if x == 0:
        return 0, -100000
    e = math.floor(math.log2(abs(x)))
    m = int(round(x / 2.0 ** e * 2 ** 30))
    if abs(m) >= 2 ** 31:
        m //= 2
        e += 1
    return m, e


def lfo_inc(f):
    """Incrément de phase (2^32 = un tour) du CosineOscillator<APPROXIMATE>(f) de stmlib, par sa constante c
    calculée en float32 : 0,5 + 0,5 cos(n theta), cos(theta) = c / 2."""
    f = f32(f32(f) - 0.25)
    sign = 16.0
    if f < 0:
        f = -f
    elif f > 0.5:
        f = f32(f - 0.5)
    else:
        sign = -16.0
    c = f32(f32(sign * f) * f32(1.0 - f32(2.0 * f)))
    return int(round(math.acos(max(-1.0, min(1.0, c / 2))) / (2 * math.pi) * 2 ** 32)) & 0xffffffff


def constants():
    """Constantes de modal_tables.h, d'après les valeurs float32 de Rings et de stmlib."""
    pi = math.pi
    pif = f32(pi)
    a3 = f32(440.0 / FS)
    lm, mh, lo = f32(160.0 / FS), f32(1600.0 / FS), f32(8.0 / FS)
    srb = f32(FS / BLOCK)                                 # cadence des blocs (note_filter)
    xfs = {                                               # flottants maison
        "M_0001": 0.001, "M_02": 0.2, "M_04": 0.4, "M_049": f32(0.49), "M_0499": f32(0.499), "M_08": 0.8,
        "M_015": 0.15, "M_255": 255.0, "M_27": 27.0, "M_9": 9.0, "M_500": 500.0, "M_A3": a3,
        "M_F220": f32(220.0 / FS), "M_FCIDLE": f32(10.0 / FS), "M_LN1000": -math.log(f32(0.001)),
        "M_M0618": -0.618, "M_M120": -120.0, "M_R080": f32(1.0 / f32(0.8)), "M_R100": f32(1.0 / 100.0),
        "M_R150": f32(1.0 / 1.5), "M_RT60FM": f32(0.1 * FS), "M_RT60S": f32(f32(0.07) * FS),
    }
    k = {}
    for name, v in xfs.items():
        k[name + "_M"], k[name + "_E"] = xf(v)
    q31 = lambda x: q(x, 31)
    k.update({
        "M_001": q31(f32(0.01)), "M_049Q": q31(f32(0.49)), "M_04999": q31(f32(0.4999)), "M_09": q31(f32(0.9)),
        "M_095": q31(f32(0.95)), "M_0999": q31(f32(0.999)), "M_F220Q": q31(f32(220.0 / FS)),
        "M_FOL_LM": q31(f32(2 * pif * lm)), "M_FOL_MH": q31(f32(2 * pif * mh)), "M_LIM_DEC": q31(f32(0.00002)),
        "M_NF_FAST": q31(f32(1.0 / f32(f32(0.001) * srb))), "M_NF_SLOW": q31(f32(1.0 / f32(f32(0.010) * srb))),
        "M_NF_LAG": q31(f32(1.0 / f32(f32(0.050) * srb))), "M_NF_DELAY": min(15, int(f32(f32(0.004) * srb))),
        "M_NF_JUMP": 26214, "M_POLE10": q31(f32(1.0 - 10.0 / FS)), "M_POLE20": q31(f32(1.0 - 20.0 / FS)),
        "M_0025U": q(0.025, 24), "M_005": q(0.05, 16), "M_09999Q30": q(f32(0.9999), 30),
        "M_D220": q(1.0 / f32(220.0 / FS), 20), "M_FIFTH": q(7.01955, 16),
        "M_INC220": int(2 ** 32 * f32(220.0 / FS)),
        "M_PI27": q(pif, 27), "M_TD_A27": q(f32(f32(0.3736) * pi ** 3), 27),
        "M_TF_A26": q(f32(f32(0.326) * pi ** 3), 26), "M_TF_B25": q(f32(f32(0.1823) * pi ** 5), 25),
        "M_TA_A21": q(f32(f32(3.333314036e-01) * pi ** 3), 21), "M_TA_B21": q(f32(f32(1.333923995e-01) * pi ** 5), 21),
        "M_TA_C21": q(f32(f32(5.33740603e-02) * pi ** 7), 21), "M_TA_D21": q(f32(f32(2.900525e-03) * pi ** 9), 21),
        "M_TA_E19": q(f32(f32(9.5168091e-03) * pi ** 11), 19),
        "M_RV_LFO1": lfo_inc(f32(f32(0.5 / FS) * 32)), "M_RV_LFO2": lfo_inc(f32(f32(0.3 / FS) * 32)),
    })
    arrays = {
        "M_DETUNE": ("s32", [q(f32(x), 16) for x in (0.013, 0.011, 0.007, 0.017)]),
        "M_FOL_ATT": ("s32", [q31(lm), q31(f32(math.sqrt(lm * mh))), q31(f32(math.sqrt(mh * 0.5)))]),
        "M_FOL_DEC": ("s32", [q31(f32(math.sqrt(lm * lo))), q31(lm), q31(f32(math.sqrt(mh * lm)))]),
        "M_GAINS": ("s32", [q31(f32(g) / 2) for g in (1.4, 1.0, 1.4, 0.7, 1.0, 1.4)]),
        "M_SLFO": ("u32", [lfo_inc(f32(f32(BLOCK / FS) * f32(f))) for f in (0.5, 0.4, 0.35, 0.23, 0.211, 0.2,
                                                                         0.171, 0.0)]),
        "M_SQRTG": ("s32", [0] + [q31(f32(1.0 / math.sqrt(n * 2.0))) for n in range(1, 9)]),
        "M_SYMG": ("s32", [0] + [q31(f32(0.2 / n)) for n in range(1, 9)]),
    }
    return k, arrays


def tables():
    """(tableaux {nom: (type, valeurs)}, constantes {nom: valeur}) de modal_tables.h."""
    t = {
        # Interpolate(lut, x, 256) : x en Q31, index = x >> 23
        "M_STIFF": ("s32", [q(f32(v), 29) for v in lut_stiffness()]),                       # Q29
        "M_DEC4": ("s32", [q(f32(10 ** (4 * i / 256.0)), 17) for i in range(257)]),        # Q17 (1..10 000)
        "M_SVFSHIFT": ("s32", [q(f32(2.0 * math.atan(1.0 / 2.0 ** (i / 12.0)) / (2.0 * math.pi)), 31)
                              for i in range(257)]),                                       # Q31
        "M_FMQ": ("s32", [q(f32(v), 16) for v in lut_fm_frequency_quantizer()]),           # demi-tons, Q16
        # SemitonesToRatio : 2^((i - 128) / 12) x 2^(j / 3072), mantisses Q30
        "M_P12": ("s32", [q(2 ** (n / 12.0), 30) for n in range(12)]),
        "M_P256": ("s32", [q(2 ** (j / 3072.0), 30) for j in range(256)]),
        # accords, demi-tons Q16 : 11 x 4 (polyphonie 1, en eco), puis 11 x 2 (2 et 4)
        "M_CHORDS": ("s32", [q(f32(v), 16) for rows in CHORDS[1:] for row in rows for v in row]),
    }
    k, arrays = constants()
    t.update(arrays)
    return t, k


def tables_header():
    t, k = tables()
    out = ["/* Tables de MODAL, calculees par tools/gen_modal.py (formules de Rings et de stmlib, MIT) : ne pas",
           " * modifier a la main. */",
           "#ifndef MODAL_TABLES_H", "#define MODAL_TABLES_H", ""]
    for name, v in k.items():
        out.append(f"#define {name} {v:#x}u" if name in ("M_INC220", "M_RV_LFO1", "M_RV_LFO2") else
                   f"#define {name} ({v})")
    if k:
        out.append("")
    for name, (typ, v) in t.items():
        out.append(f"static const {typ} {name}[{len(v)}] = {{")
        for i in range(0, len(v), 6):
            out.append("\t" + ", ".join(f"{x:#010x}u" if typ == "u32" else str(x) for x in v[i:i + 6]) + ",")
        out.append("};")
    return "\n".join(out + ["", "#endif", ""])


def emit(path, text, check):
    if check:
        ok = path.exists() and path.read_text(encoding="utf-8") == text
        print(f"    {path.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre GCC ?)'}")
        return not ok
    path.write_text(text, encoding="utf-8")
    print(f"    écrit : {path}")
    return 0


def compile_machine(tmp, pay, tables_h):
    """Le cœur et la passerelle de MODAL liés à pay + MODAL_AT (code, tables) et pay + MODAL_BSS (variables).
    Renvoie (octets, symboles, fin du BSS)."""
    import gen_sdvintage_exact as gx                       # noqa: E402
    at, bss_at = pay + MODAL_AT, pay + MODAL_BSS
    (tmp / "modal_tables.h").write_text(tables_h)          # les tables de ce générateur, pas celles du dépôt
    for f in ("modal.c", "modal_dsp.h", "modal_fix.h"):
        (tmp / f).write_bytes((SRC / f).read_bytes())
    o = tmp / "modal.o"
    gx.run([gx.CROSS + "gcc", *CFLAGS, f"-DMODAL_RAM={MODAL_RAM:#x}", f"-I{tmp}", "-c", str(tmp / "modal.c"), "-o",
            str(o)])
    ld, elf, out = tmp / "link.ld", tmp / "modal.elf", tmp / "modal.bin"
    ld.write_text(LINK.format(code=at, bss=bss_at))
    gx.run([gx.CROSS + "ld", "-T", str(ld), "--gc-sections", "--no-warn-rwx-segments", "-e", ENTRIES[0],
            *[a for e in ENTRIES[1:] for a in ("-u", e)], "-o", str(elf), str(o)])
    secs = {}
    for line in gx.run([gx.CROSS + "objdump", "-h", str(elf)]).splitlines():
        f = line.split()
        if len(f) > 4 and f[0].isdigit():
            secs[f[1]] = (int(f[3], 16), int(f[2], 16))
    if set(secs) - {".text", ".rodata", ".data", ".bss"}:
        raise SystemExit(f"!! sections inattendues : {sorted(secs)}")
    if secs.get(".data", (0, 0))[1]:
        raise SystemExit("!! variables initialisées : le crochet de démarrage ne les recopierait pas à part")
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-R", ".bss", str(elf), str(out)])
    blob = out.read_bytes()
    syms = {p_[2]: int(p_[0], 16) for p_ in (l.split() for l in gx.run([gx.CROSS + "nm", str(elf)]).splitlines())
            if len(p_) == 3}
    if at + len(blob) > bss_at:
        raise SystemExit(f"!! code et tables de MODAL : {len(blob)} o, au-delà de {bss_at:#x}")
    bss = secs.get(".bss", (bss_at, 0))
    if bss[0] != bss_at:
        raise SystemExit("!! BSS")
    return blob, syms, (bss[0] + bss[1] + 3) & ~3


def modal_part(pay):
    """MODAL lié à sa place : dict(machine, at, blob, end, syms), pour gen_macro_syntakt.build_tweak (more)."""
    with tempfile.TemporaryDirectory() as d:
        blob, syms, end = compile_machine(pathlib.Path(d), pay, tables_header())
    machine = dict(MACHINE, label="MODAL", update=syms["modal_update"], render=syms["modal_render"],
                   fine=dict(knob=SHAPE_KNOB, step=syms["modal_poly_step"], fmt=syms["modal_poly_fmt"],
                             draw=syms["modal_poly_draw"]))
    return dict(machine=machine, at=pay + MODAL_AT, blob=blob, end=end, syms=syms)


def build_tweak(img, st_img, repo):
    """Le tweak de l'OS : Model-TG, les 5 moteurs du Syntakt, MACRO, ACID et MODAL."""
    import gen_acid_combos as gac                          # noqa: E402
    import gen_macro as gm                                 # noqa: E402
    import gen_macro_syntakt as gms                        # noqa: E402
    import gen_syntakt_engines as gs                       # noqa: E402
    import gov_asm                                         # noqa: E402
    tg = gs.tg_context(img)
    pay = gs.PAY_TG
    acid = gac.acid_part(pay)
    modal = modal_part(pay)
    if modal["end"] > pay + gms.TG_ROOM:
        raise SystemExit(f"!! charge utile jusqu'à {modal['end']:#x} : au-delà de la place laissée par Model-TG")
    out, info = gms.build_tweak(img, st_img, repo, list(FIVE), tg, macro=True, acid=acid, more=[modal])
    macro_syms = gms.compile_macro(repo, pay)[1]
    first = gs.TG_FIRST
    which = ", ".join(f"{gs.CATALOG[c]['name']} = {gs.CATALOG[c]['label']} (machine {first + i + 1})"
                      for i, c in enumerate(FIVE))
    k = first + len(FIVE)
    which += f", MACRO (machine {k + 1}), ACID (machine {k + 2}), MODAL (machine {k + 3})"
    gov = [gov_asm.NOTE] if gov_asm.NOTE in out["description"] else []
    out.update({
        "id": TWEAK_ID,
        "name": "Model-TG + vrais moteurs du Syntakt (" + ", ".join(gs.CATALOG[c]["name"] for c in FIVE)
                + "), machines MACRO (Braids), ACID (d'après Open303) et MODAL (d'après Rings, Émilie Gillet, MIT)",
        "description": [
            "Version combinée avec Model-TG (notes/31) : s'ajoute après model-tg-st, le Sampler reste la 7e machine.",
            "Moteurs du Syntakt (OS 1.42 ou 1.41, extraits AU BUILD de TON Syntakt_OS1.42.syx), machine MACRO (notes/43),",
            "machine ACID (notes/54) et machine MODAL (notes/74), ensemble : " + which + ".",
            "Passerelle des moteurs reprise telle quelle de " + gs.tweak_id(list(FIVE), tg=True)
            + f" ; MACRO compilé comme 25-macro.json ({gm.EURORACK_REPO} {gm.EURORACK_COMMIT[:7]}, licence MIT : "
            "LICENSE-Braids), à la place des tweaks -macro.",
            gac.acid_line(),
            f"MODAL d'après Rings (Émilie Gillet, licence MIT : LICENSE-Rings), réécrit en virgule fixe, lié à "
            f"+{MODAL_AT:#x} ; l'état de ses pistes à {MODAL_RAM:#x}.",
            "Charge utile rangée compressée (aPLib), décompressée au démarrage ; tables d'ondes de CHORD reprises en",
            "SRAM. Le régulateur de charge des moteurs vaut aussi pour MACRO, ACID et MODAL.",
            "Généré par tools/gen_modal.py. De l'OS, seuls les octets d'origine (old) qui vérifient le fichier",
            "officiel ; la table des descripteurs est recopiée au build (recette cycles).",
        ] + gov,
        "conflicts": sorted((gac.all_ids(tg) | {"syntakt-tg-meter", "syntakt-tg-profile"}) - {TWEAK_ID}),
    })
    gac.symbols(out, macro_syms, acid)
    out["symbols"].update({k_: f"{modal['syms'][k_]:#x}" for k_ in ENTRIES + ("ctl",)})
    return out, dict(info, code=len(modal["blob"]), bss=modal["end"] - pay - MODAL_BSS)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tables", action="store_true", help="modal_tables.h et LICENSE-Rings seulement")
    ap.add_argument("--cycles", help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--eurorack", help="clone de pichenettes/eurorack au commit épinglé (Braids, pour MACRO)")
    ap.add_argument("--check", action="store_true", help="vérifier sans écrire")
    args = ap.parse_args()
    bad = emit(TABLES, tables_header(), args.check)
    bad += emit(LICENSE_OUT, LICENSE, args.check)
    if not args.tables:
        if not (args.cycles and args.syntakt and args.eurorack):
            raise SystemExit("!! --cycles, --syntakt et --eurorack (ou --tables)")
        import gen_macro as gm                             # noqa: E402
        import gen_sdvintage_7th as g7                     # noqa: E402
        import gen_sdvintage_exact as gx                   # noqa: E402
        import syntakt                                     # noqa: E402
        img = g7.cycles_main(args.cycles)
        if len(img) != gx.IMAGE_LEN:
            raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
        repo = pathlib.Path(args.eurorack).resolve()
        gm.check_sources(repo)
        st_img = syntakt.dsp_image(args.syntakt)
        tweak, info = build_tweak(img, st_img, repo)
        print(f"  {tweak['id']} : {len(tweak['writes'])} écritures, {info['ndesc']} descripteurs, charge utile "
              f"{info['size']} o, rangée en {info['packed']} o, image jusqu'à {info['end']:#x} ; MODAL : code et "
              f"tables {info['code']} o, variables {info['bss']} o")
        bad += emit(DEV / f"{tweak['order']}-{tweak['id']}.json", json.dumps(tweak, indent=1) + "\n", args.check)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
