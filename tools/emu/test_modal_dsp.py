#!/usr/bin/env python3
"""Preuve du cœur de MODAL (tools/machines/modal/modal_dsp.h, notes/74) contre Rings en flottant.

La référence est la Part de Rings (pichenettes/eurorack, code MIT d'Émilie Gillet, au commit épinglé de MACRO),
compilée pour l'ordinateur (rings_ref.cc) depuis une copie de ses sources où ne changent que :
  - kMaxBlockSize : 32 (le bloc du Cycles) au lieu de 24 ;
  - les réglages « éco » choisis pour MODAL (notes/74 §3) : la moitié des modes du résonateur modal
    ((64 / polyphonie - 4) / 2) ; 4 cordes en tout au lieu de 8 (4, 2, 1 par voix selon la polyphonie), avec la
    table d'accords de Rings pour ce nombre de cordes.
Le cœur en virgule fixe est compilé pour l'ordinateur (modal_host.c) avec la même arithmétique que sur le Cycles
(EMAC simulée à l'octet près, modal_fix.h) ; tools/emu/test_modal.py prouve que le code du Cycles fait les mêmes
octets.

Pour chaque cas : 20 blocs de silence, puis des notes
(strum) ; la sortie de Rings (ODD - EVEN) comparée à celle du cœur : rapport signal / écart sur toute la durée,
au moins MIN_SNR dB.

    python3 tools/emu/test_modal_dsp.py --eurorack vendor/eurorack [--quick]
"""
import argparse
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import gen_macro as gm              # noqa: E402
import gen_modal as gmo             # noqa: E402

MIN_SNR = 35.0
PRE = 20                            # blocs de silence avant la 1re note
RINGS = ["rings/dsp/part.cc", "rings/dsp/resonator.cc", "rings/dsp/string.cc", "rings/dsp/fm_voice.cc",
         "rings/resources.cc", "stmlib/dsp/units.cc", "stmlib/utils/random.cc"]
ECO = (  # (fichier, avant, après) : les seules retouches de la copie de Rings
    ("rings/dsp/dsp.h", "const size_t kMaxBlockSize = 24;", "const size_t kMaxBlockSize = 32;"),
    ("rings/dsp/part.cc", "int32_t resolution = 64 / polyphony_ - 4;",
     "int32_t resolution = (64 / polyphony_ - 4) / 2;"),
    ("rings/dsp/part.cc", "num_strings = 2 * kMaxPolyphony / polyphony_;", "num_strings = kMaxPolyphony / polyphony_;"),
    ("rings/dsp/part.cc", "const float* chord = chords[polyphony_ - 1][chord_index];",
     "const float* chord = chords[std::min(2 * polyphony_, kMaxPolyphony) - 1][chord_index];"),
)
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg)
    if not ok:
        FAIL.append(msg)


def build(tmp, repo):
    src = tmp / "src"
    for d in ("rings/dsp", "stmlib/dsp", "stmlib/utils"):
        shutil.copytree(repo / d, src / d)
    for f in ("rings/resources.h", "rings/resources.cc", "stmlib/stmlib.h"):
        shutil.copy(repo / f, src / f)
    for f, a, b in ECO:
        p = src / f
        s = p.read_text(encoding="utf-8")
        if s.count(a) != 1:
            raise SystemExit(f"!! {f} : « {a} » introuvable")
        p.write_text(s.replace(a, b), encoding="utf-8")
    cxx = shutil.which("c++") or shutil.which("g++")
    cc = shutil.which("cc") or shutil.which("gcc")
    ref, fix = tmp / "rings_ref", tmp / "modal_host"
    subprocess.run([cxx, "-O2", "-DTEST", f"-I{src}", str(HERE / "rings_ref.cc"), *[str(src / f) for f in RINGS],
                    "-o", str(ref)], check=True, capture_output=True)
    subprocess.run([cc, "-O2", "-Wall", "-Wextra", "-Werror", f"-I{gmo.SRC}", str(HERE / "modal_host.c"), "-o",
                    str(fix)], check=True)
    return ref, fix


def rec(model=0, poly=1, strum=0, chord=0, note=0.0, tonic=48.0, st=0.28, br=0.5, da=0.5, po=0.31):
    """Un bloc (rings_ref.cc, modal_host.c) : excitateur interne, pas d'entrée."""
    q = lambda x: int(round(x * 65536))
    return struct.pack("<46i", model, poly, strum, 1, chord, q(note), q(tonic), 0, q(st), q(br), q(da), q(po),
                       *([0] * 32), 0, 0)


def run(exe, data):
    out = subprocess.run([str(exe)], input=data, capture_output=True, check=True).stdout
    a = np.frombuffer(out, "<f4").reshape(-1, 2, 32).astype(np.float64)
    return (a[:, 0, :] - a[:, 1, :]).ravel()


def snr(a, b):
    e = np.sqrt(np.mean((a - b) ** 2))
    return 999.0 if e == 0 else 20 * np.log10(np.sqrt(np.mean(a ** 2)) / e)


def scenario(model, poly, blocks=300, notes=((0, 0.0), (100, 3.0), (200, -5.0)), **kw):
    """notes : (bloc après le silence, note) ; kw : réglages, ou fonctions du bloc pour des potards qui bougent."""
    at = {PRE + b: n for b, n in notes}
    out, note = [], notes[0][1]
    for b in range(PRE + blocks):
        if b in at:
            note = at[b]
        k = {x: (v(b - PRE) if callable(v) else v) for x, v in kw.items()}
        out.append(rec(model=model, poly=poly, strum=int(b in at), note=note, **k))
    return out


def cases(quick):
    """Les 4 modèles de MODAL (SHAPE 0..3), sous leur numéro dans Rings (gmo.RINGS_MODEL : 0, 1, 2, 4)."""
    out = []
    shapes = list(enumerate(gmo.RINGS_MODEL))
    for shape, model in shapes:
        for poly in ((1, 2, 4) if not quick else (1, 4)):
            out.append((f"SHAPE {shape} ({gmo.MODELS[shape]}), {poly} voix", scenario(model, poly)))
    ramp = lambda lo, hi: (lambda b: lo + (hi - lo) * min(max(b, 0), 200) / 200)
    for shape, model in shapes:
        out.append((f"SHAPE {shape}, les 4 potards qui bougent", scenario(
            model, 1, st=ramp(0.1, 0.9), br=ramp(0.9, 0.1), da=ramp(0.3, 0.9), po=ramp(0.0, 1.0))))
    for chord in ((0, 3, 7, 10) if not quick else (5,)):
        for poly in (1, 2, 4):
            out.append((f"cordes en accord, accord {chord}, {poly} voix", scenario(4, poly, chord=chord)))
    for shape, model in shapes:
        for total in (0, 127):
            out.append((f"SHAPE {shape}, hauteur MIDI {total}", scenario(model, 1, notes=((0, total - 48.0),))))
    out += [
        ("SHAPE 1, DAMPING au maximum (résonance infinie)", scenario(1, 1, da=1.0)),
        ("SHAPE 2, DAMPING au maximum", scenario(2, 2, da=1.0)),
        ("SHAPE 2, BRIGHTNESS et POSITION aux bouts", scenario(2, 1, br=1.0, po=0.0)),
        ("SHAPE 0, STRUCTURE et BRIGHTNESS à 0", scenario(0, 1, st=0.0, br=0.0)),
        ("SHAPE 0, STRUCTURE et BRIGHTNESS au maximum", scenario(0, 4, st=1.0, br=1.0)),
    ]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eurorack", required=True, help="clone de pichenettes/eurorack au commit épinglé")
    ap.add_argument("--quick", action="store_true", help="moins de cas")
    args = ap.parse_args()
    repo = pathlib.Path(args.eurorack).resolve()
    gm.check_sources(repo)
    with tempfile.TemporaryDirectory() as d:
        ref, fix = build(pathlib.Path(d), repo)
        worst = []
        for name, recs in cases(args.quick):
            data = b"".join(recs)
            a, b = run(ref, data), run(fix, data)
            s = snr(a, b)
            worst.append((s, name))
            check(s >= MIN_SNR and np.abs(b).max() > 0,
                  f"{name} : {s:.1f} dB (crête {np.abs(a).max():.3f} pour Rings, {np.abs(b).max():.3f} pour MODAL)")
        worst.sort()
        print(f"\n  le plus faible : {worst[0][1]} ({worst[0][0]:.1f} dB) ; médiane {worst[len(worst) // 2][0]:.1f} dB")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
