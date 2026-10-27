#!/usr/bin/env python3
"""Preuve du cœur de MODAL (tools/machines/modal/modal_dsp.h, notes/74) contre Rings en flottant.

La référence est la Part de Rings (pichenettes/eurorack, code MIT d'Émilie Gillet, au commit épinglé de MACRO),
compilée pour l'ordinateur (rings_ref.cc) depuis une copie de ses sources où ne changent que :
  - les réglages « éco » choisis pour MODAL (notes/74 §3) : la moitié des modes du résonateur modal
    ((64 / polyphonie - 4) / 2) ; 4 cordes en tout au lieu de 8 (4, 2, 1 par voix selon la polyphonie), avec la
    table d'accords de Rings pour ce nombre de cordes (ECO) ;
  - Rings calculé à 24 kHz, par blocs de 16 (la moitié du bloc du Cycles), puis remonté à 48 kHz par la passerelle
    (notes/81) : ce qui compte en échantillons est recalé pour garder ses durées et ses fréquences en secondes et en
    hertz (SR24). C'est la définition du son de MODAL ; tools/emu/modal_ecoute.py en fait des paires à écouter.
Le cœur en virgule fixe est compilé pour l'ordinateur (modal_host.c) avec la même arithmétique que sur le Cycles
(EMAC simulée à l'octet près, modal_fix.h) ; tools/emu/test_modal.py prouve que le code du Cycles fait les mêmes
octets.

Pour chaque cas : 20 blocs de silence, puis des notes
(strum), avec l'excitateur interne ou un sample en entrée (internal_exciter = 0, rejoué depuis le début à chaque
note : le sample excitateur de MODAL, notes/80) ; la sortie de Rings (ODD - EVEN) comparée à celle du cœur : rapport
signal / écart sur toute la durée, au moins MIN_SNR dB.

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
# POSITION qui balaie tout en 200 blocs (0,13 s) pendant que le sample excite encore les modes : l'écart connu des
# amplitudes interpolées linéairement sur le bloc quand la position bouge (notes/74 §5.1), plus visible avec une
# entrée qui dure qu'avec une frappe (POSITION seule : 37 dB avec le sample, 55 dB avec l'excitateur interne)
MIN_SNR_SWEEP_IN = 30.0
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
SR24 = (  # Rings à 24 kHz (notes/81) : après ECO
    ("rings/dsp/dsp.h", "static const float kSampleRate = 48000.0f;", "static const float kSampleRate = 24000.0f;"),
    ("rings/dsp/dsp.h", "const size_t kMaxBlockSize = 32;", "const size_t kMaxBlockSize = 16;"),
    # les lignes des cordes : la même note la plus grave en hertz (23,4 Hz), deux fois moins de mémoire
    ("rings/dsp/string.h", "const size_t kDelayLineSize = 2048;", "const size_t kDelayLineSize = 1024;"),
    # l'entrée externe (le sample excitateur) : la même coupure en hertz
    ("rings/dsp/part.cc", ": 0.4f * SemitonesToRatio((cutoff - 1.0f) * 108.0f);",
     ": 0.8f * SemitonesToRatio((cutoff - 1.0f) * 108.0f);"),
    # le filtre d'excitation : la borne de 48 kHz (0,499 x 48 kHz), sa tangente exacte (celle de Rings, « dirty »,
    # n'est juste que sous 8 kHz à 48 kHz) ; sa bosse de résonance (Q 1,5 ou 0,8), dans la dernière octave à 48 kHz,
    # s'efface au-dessus de 7,2 kHz (Q vers 0,707)
    ("rings/dsp/part.cc", "      : (10.0f / kSampleRate), 0.499f);", "      : (10.0f / kSampleRate), 0.998f);"),
    ("rings/dsp/part.cc", "    float filter_q = performance_state.internal_exciter ? 1.5f : 0.8f;",
     "    float filter_q = performance_state.internal_exciter ? 1.5f : 0.8f;\n"
     "    filter_q += (0.7071f - filter_q) * min(max((filter_cutoff - 0.6f) / 0.398f, 0.0f), 1.0f);"),
    ("rings/dsp/part.cc", "excitation_filter_[voice].set_f_q<FREQUENCY_DIRTY>(filter_cutoff, filter_q);",
     "excitation_filter_[voice].set_f_q<FREQUENCY_EXACT>(filter_cutoff, filter_q);"),
    # le résonateur modal : facteur de qualité en hertz (q x 1/2), tangente exacte, et les modes près de la moitié
    # de la fréquence d'échantillonnage gardent leur durée en secondes (Q x cos(pi f) : le filtre d'état numérique
    # les fait durer 1 / cos(pi f) fois plus longtemps que voulu)
    ("rings/dsp/resonator.cc", "float q = 500.0f * Interpolate(", "float q = 250.0f * Interpolate("),
    ("rings/dsp/resonator.cc", "    f_[i].set_f_q<FREQUENCY_FAST>(\n        partial_frequency,\n"
     "        1.0f + partial_frequency * q);",
     "    f_[i].set_f_q<FREQUENCY_EXACT>(\n        partial_frequency,\n"
     "        (1.0f + partial_frequency * q) * cosf(3.14159265f * partial_frequency));"),
    # le pincement : son peigne et sa bouffée de bruit en secondes, le bruit à la même densité par hertz, son filtre
    # comme celui de l'excitation
    ("rings/dsp/plucker.h", "while (comb_period >= 255.0f) {", "while (comb_period >= 127.5f) {"),
    ("rings/dsp/plucker.h", "in = 2.0f * Random::GetFloat() - 1.0f;",
     "in = (2.0f * Random::GetFloat() - 1.0f) * 0.70710678f;"),
    ("rings/dsp/plucker.h", "svf_.set_f_q<FREQUENCY_DIRTY>(std::min(cutoff, 0.499f), 1.0f);",
     "svf_.set_f_q<FREQUENCY_EXACT>(std::min(cutoff, 0.998f), "
     "1.0f + (0.7071f - 1.0f) * std::min(std::max((cutoff - 0.6f) / 0.398f, 0.0f), 1.0f));"),
    # la corde : le FIR d'amortissement garde sa courbe aux basses fréquences (b' = (3 + b) / 4), le bruit de
    # dispersion sa coupure (deux pas de 48 kHz par pas de 24 kHz), le passe-bas de la boucle son prototype de
    # 48 kHz (g = 2 tan(pi f48), f48 la coupure de 48 kHz, bornée à 0,499 comme dans Rings)
    ("rings/dsp/string.cc", "fir_damping_filter_.Configure(damping_coefficient, brightness, size);",
     "fir_damping_filter_.Configure(damping_coefficient, 0.75f + 0.25f * brightness, size);"),
    ("rings/dsp/string.cc", "float noise_filter = SemitonesToRatio((brightness_ - 1.0f) * 48.0f);",
     "float noise_filter = SemitonesToRatio((brightness_ - 1.0f) * 48.0f);\n  noise_filter *= 2.0f - noise_filter;"),
    ("rings/dsp/string.cc",
     "  float damping_f = min(frequency_ * SemitonesToRatio(damping_cutoff), 0.499f);",
     "  float damping_f = min(0.5f * frequency_ * SemitonesToRatio(damping_cutoff), 0.499f);"),
    ("rings/dsp/string.cc",
     "  iir_damping_filter_.set_f_q<FREQUENCY_ACCURATE>(damping_f, 0.5f);",
     "  iir_damping_filter_.set_g_q(2.0f * OnePole::tan<FREQUENCY_ACCURATE>(damping_f), 0.5f);"),
    # le limiteur : ses temps en secondes (1 - (1 - a)^2 par échantillon)
    ("rings/dsp/limiter.h", "SLOPE(peak_, peak, 0.05f, 0.00002f);", "SLOPE(peak_, peak, 0.0975f, 0.00004f);"),
)
MB = gmo.BLOCK                      # trames par bloc du cœur : 16 (24 kHz)
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
    for f, a, b in ECO + SR24:
        p = src / f
        s = p.read_text(encoding="utf-8")
        if s.count(a) != 1:
            raise SystemExit(f"!! {f} : « {a} » introuvable")
        p.write_text(s.replace(a, b), encoding="utf-8")
    cxx = shutil.which("c++") or shutil.which("g++")
    cc = shutil.which("cc") or shutil.which("gcc")
    ref, fix = tmp / "rings_ref", tmp / "modal_host"
    subprocess.run([cxx, "-O2", "-DTEST", f"-DBLK={MB}", f"-I{src}", str(HERE / "rings_ref.cc"),
                    *[str(src / f) for f in RINGS], "-o", str(ref)], check=True, capture_output=True)
    subprocess.run([cc, "-O2", "-Wall", "-Wextra", "-Werror", f"-I{gmo.SRC}", str(HERE / "modal_host.c"), "-o",
                    str(fix)], check=True)
    return ref, fix


def rec(model=0, poly=1, strum=0, chord=0, note=0.0, tonic=48.0, st=0.28, br=0.5, da=0.5, po=0.31, x=None):
    """Un bloc (rings_ref.cc, modal_host.c) : excitateur interne, pas d'entrée ; x : MB échantillons d'entrée (UNIT,
    1,0 = 2^24), l'excitateur interne coupé (le sample excitateur de MODAL, notes/80)."""
    q = lambda v: int(round(v * 65536))
    return struct.pack(f"<{14 + MB}i", model, poly, strum, 0 if x is not None else 1, chord, q(note), q(tonic), 0,
                       q(st), q(br), q(da), q(po), *(list(x) if x is not None else [0] * MB), 0, 0)


def run(exe, data):
    out = subprocess.run([str(exe)], input=data, capture_output=True, check=True).stdout
    a = np.frombuffer(out, "<f4").reshape(-1, 2, MB).astype(np.float64)
    return (a[:, 0, :] - a[:, 1, :]).ravel()


def snr(a, b):
    e = np.sqrt(np.mean((a - b) ** 2))
    return 999.0 if e == 0 else 20 * np.log10(np.sqrt(np.mean(a ** 2)) / e)


def scenario(model, poly, blocks=300, notes=((0, 0.0), (100, 3.0), (200, -5.0)), sample=None, **kw):
    """notes : (bloc après le silence, note) ; kw : réglages, ou fonctions du bloc pour des potards qui bougent ;
    sample : l'entrée (UNIT), rejouée depuis le début à chaque note, comme le fait la machine MODAL."""
    at = {PRE + b: n for b, n in notes}
    out, note, pos = [], notes[0][1], None
    for b in range(PRE + blocks):
        if b in at:
            note = at[b]
            pos = 0 if sample is not None else None
        k = {x: (v(b - PRE) if callable(v) else v) for x, v in kw.items()}
        x = None
        if sample is not None:
            x = [0] * MB
            if pos is not None:
                x = [sample[pos + i] if pos + i < len(sample) else 0 for i in range(MB)]
                pos = pos + MB if pos + MB < len(sample) else None
        out.append(rec(model=model, poly=poly, strum=int(b in at), note=note, x=x, **k))
    return out


def unit_sample(kind, n, seed=1):
    """Des samples de synthèse en UNIT, comme la machine les lit (int16 << 9), à 24 kHz (après la décimation de la
    passerelle) : frappe (bruit qui s'éteint), sinus (440 Hz qui s'éteint)."""
    k = np.arange(n)
    if kind == "frappe":
        v = np.random.RandomState(seed).uniform(-1, 1, n) * np.exp(-k / 200.0) * 20000
    else:
        v = np.sin(2 * np.pi * 440 * k / 24000) * np.exp(-k / 3000.0) * 24000
    return [int(x) << 9 for x in np.clip(np.round(v), -32768, 32767).astype(np.int64)]


def cases(quick):
    """Les 4 modèles de MODAL (SHAPE 0..3), sous leur numéro dans Rings (gmo.RINGS_MODEL : 0, 1, 2, 4)."""
    out = []
    shapes = list(enumerate(gmo.RINGS_MODEL))
    for shape, model in shapes:
        for poly in ((1, 2, 3, 4) if not quick else (1, 3)):        # 3 au plus dans MODAL (notes/81) ; 4 : Rings
            out.append((f"SHAPE {shape} ({gmo.MODELS[shape]}), {poly} voix", scenario(model, poly)))
    ramp = lambda lo, hi: (lambda b: lo + (hi - lo) * min(max(b, 0), 200) / 200)
    for shape, model in shapes:
        out.append((f"SHAPE {shape}, les 4 potards qui bougent", scenario(
            model, 1, st=ramp(0.1, 0.9), br=ramp(0.9, 0.1), da=ramp(0.3, 0.9), po=ramp(0.0, 1.0))))
    for chord in ((0, 3, 7, 10) if not quick else (5,)):
        for poly in (1, 2, 3):
            out.append((f"cordes en accord, accord {chord}, {poly} voix", scenario(4, poly, chord=chord)))
    for shape, model in shapes:                      # à 24 kHz : le résonateur sonne jusqu'à la note 126 (11,8 kHz),
        for total in (0, 120 if shape == 0 else 108):  # les cordes montent jusqu'à 6 kHz (retard de 4 échantillons)
            out.append((f"SHAPE {shape}, hauteur MIDI {total}", scenario(model, 1, notes=((0, total - 48.0),))))
    fr, si = unit_sample("frappe", 1200), unit_sample("sinus", 4500)
    for shape, model in shapes:                      # le sample excitateur (notes/80) : l'entrée de Rings
        for poly in ((1, 3) if not quick else (1,)):
            out.append((f"SHAPE {shape}, sample « frappe » en entrée, {poly} voix", scenario(model, poly, sample=fr)))
        out.append((f"SHAPE {shape}, sample « sinus » en entrée, relancé avant sa fin",
                    scenario(model, 2, sample=si, notes=((0, 0.0), (60, 7.0), (120, -2.0)))))
    for shape, model in shapes if not quick else shapes[:1]:
        out.append((f"SHAPE {shape}, sample en entrée, les 4 potards qui bougent", scenario(
            model, 1, sample=fr, st=ramp(0.1, 0.9), br=ramp(0.9, 0.1), da=ramp(0.3, 0.9), po=ramp(0.0, 1.0)),
            MIN_SNR_SWEEP_IN))
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
        for name, recs, *lim in cases(args.quick):
            data = b"".join(recs)
            a, b = run(ref, data), run(fix, data)
            s = snr(a, b)
            floor = lim[0] if lim else MIN_SNR
            worst.append((s, name))
            check(s >= floor and np.abs(b).max() > 0,
                  f"{name} : {s:.1f} dB (crête {np.abs(a).max():.3f} pour Rings, {np.abs(b).max():.3f} pour MODAL)"
                  + (f" ; seuil {floor:.0f} dB" if lim else ""))
        worst.sort()
        print(f"\n  le plus faible : {worst[0][1]} ({worst[0][0]:.1f} dB) ; médiane {worst[len(worst) // 2][0]:.1f} dB")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
