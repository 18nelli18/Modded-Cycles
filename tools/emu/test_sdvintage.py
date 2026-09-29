#!/usr/bin/env python3
"""Valide la machine SD VINTAGE dans le VRAI moteur du Model:Cycles, émulé (notes/14 §6).

Prend TON .syx officiel (aucune image n'est fournie), applique le tweak sdvintage-snare au
MAIN OS comme build.py, puis fait jouer la voix SNARE (= SD VINTAGE) dans la boucle des
6 voix de l'OS, bloc par bloc, et vérifie par des mesures objectives :
  - aucun accès mémoire hors zone, sortie finie ;
  - niveau comparable au SNARE d'origine ;
  - PITCH/note : 1 demi-ton par pas, corps à ~196 Hz par défaut ;
  - COLOR, SHAPE, SWEEP, CONTOUR, DECAY : chaque potard agit dans le bon sens ;
  - coût CPU inférieur au SNARE d'origine ;
  - stabilité sous modulation continue (façon LFO), retrigs et PUNCH.

    pip install unicorn numpy        (+ binutils-m68k-linux-gnu pour objdump)
    python3 tools/emu/test_sdvintage.py -i model-cycles_OS1.13.syx [--wav dossier/]
"""
import argparse
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
TOOLS = HERE.parent
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(HERE))

from mtlib import aplib, container   # noqa: E402
from mtlib.syx import unwrap          # noqa: E402
import mcengine as E                  # noqa: E402

TWEAK = TOOLS.parent / "tweaks" / "model-cycles_OS1.13" / "20-sdvintage-snare.json"
SR = 48000
DEF = dict(color=0, shape=110, sweep=74, contour=80, decay=33, punch=0)   # défauts SD VINTAGE v2 (= Syntakt)


def main_os_from_syx(path):
    stream, _ = unwrap(pathlib.Path(path).read_bytes())
    c = container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


def apply(main_os, tweak):
    img = bytearray(main_os)
    extra = []
    for w in tweak["writes"]:
        off, old, new = w["off"], bytes.fromhex(w["old"]), bytes.fromhex(w["new"])
        if img[off:off + len(old)] != old:
            raise SystemExit(f"!! octets 'old' inattendus @ 0x{off + E.BASE:08x} : pas l'OS 1.13 d'origine ?")
        img[off:off + len(new)] = new
        if old == b"\xff" * len(old):
            extra.append((off + E.BASE, len(new)))
    return bytes(img), extra


def f0(x, lo=60, hi=1500):
    x = x.astype(float) - np.mean(x)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), 1 << 16))
    fr = np.fft.rfftfreq(1 << 16, 1 / SR)
    band = (fr > lo) & (fr < hi)
    return float(fr[band][np.argmax(X[band])])


def centroid(x):
    x = x.astype(float) - np.mean(x)
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    return float(np.sum(fr * X) / (np.sum(X) + 1e-9))


def rms(x):
    return float(np.sqrt(np.mean(x.astype(float) ** 2)))


def lowpass(x, fc=500.0):
    a = np.exp(-2 * np.pi * fc / SR)
    y, s = np.zeros(len(x)), 0.0
    for i, v in enumerate(x.astype(float)):
        s = (1 - a) * v + a * s
        y[i] = s
    return y


def highpass(x, fc=1500.0):
    X = np.fft.rfft(np.asarray(x, float))
    X[np.fft.rfftfreq(len(x), 1 / SR) < fc] = 0
    return np.fft.irfft(X, len(x))


def mode2_ratio(x):
    """Rapport du 2e mode au fondamental (pics du spectre 1-25 ms, sous 1,5 kHz)."""
    seg = np.asarray(x[ms(1):ms(25)], float)
    X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 16))
    f = np.fft.rfftfreq(1 << 16, 1 / SR)
    m1 = (f > 150) & (f < 400)
    fund = f[m1][np.argmax(X[m1])]
    m2 = (f > 1.6 * fund) & (f < 3.2 * fund)
    return f[m2][np.argmax(X[m2])] / fund


def mode2_level(x):
    """Énergie autour du 2e mode (400-1100 Hz) sur 0-20 ms."""
    seg = np.asarray(x[:ms(20)], float)
    X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    return float(np.sqrt(X[(f > 400) & (f < 1100)].sum()))


def ms(t):
    return int(t * SR / 1000)


class Bench:
    def __init__(self, stock_os, patched_os, extra, wavdir=None):
        self.stock, self.patched, self.extra, self.wavdir = stock_os, patched_os, extra, wavdir
        self.fail = 0

    def run(self, stock=False, blocks=160, name=None, count=False, **kw):
        e = E.Engine(self.stock) if stock else E.Engine(self.patched, self.extra)
        e.solo(0)
        p = dict(color=0, shape=127, sweep=8, contour=0, decay=40, punch=0) if stock else dict(DEF)
        p.update(kw)
        e.set(0, machine="SNARE", **p)
        if count:
            e.count_instructions()
        x = e.render(blocks, trig_at=(1,))[32 * 2:]          # à partir du bloc déclenché
        if e.unmapped:
            self.check(False, f"accès hors zone : {[(hex(a), hex(b)) for a, b in e.unmapped[:3]]}")
        if self.wavdir and name:
            E.wav(str(pathlib.Path(self.wavdir) / f"{name}.wav"), x)
        return (x, e.instructions / blocks) if count else x

    def check(self, cond, msg):
        print(("  ok    " if cond else "  ECHEC ") + msg)
        if not cond:
            self.fail += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", required=True, help="ton .syx officiel (OS 1.13)")
    ap.add_argument("--wav", help="dossier où écrire les rendus WAV")
    args = ap.parse_args()
    if args.wav:
        pathlib.Path(args.wav).mkdir(parents=True, exist_ok=True)

    stock = main_os_from_syx(args.input)
    patched, extra = apply(stock, json.loads(TWEAK.read_text(encoding="utf-8")))
    b = Bench(stock, patched, extra, args.wav)
    print(f"tweak {TWEAK.name} appliqué, code ajouté : {', '.join(f'0x{va:08x} ({n} o)' for va, n in extra)}")

    print("[1] rendu, niveau, coût CPU")
    ref, c_ref = b.run(stock=True, blocks=40, count=True, name="snare_origine")
    x, c_sdv = b.run(blocks=40, count=True, name="sdvintage_defaut")
    b.check(np.all(np.isfinite(x)) and np.max(np.abs(x)) < 2 ** 31, "sortie finie et bornée")
    ratio = np.max(np.abs(x)) / np.max(np.abs(ref))
    b.check(0.3 < ratio < 3.0, f"crête SD VINTAGE / SNARE d'origine = {ratio:.2f}")
    b.check(c_sdv < c_ref, f"instructions par bloc (voix seule) : {c_sdv:.0f} contre {c_ref:.0f} pour SNARE")

    print("[2] PITCH et note du trig (sans balayage)")
    f_def = f0(b.run(sweep=0, name="pitch64")[ms(20):ms(90)])
    f_up = f0(b.run(sweep=0, pitch=76)[ms(20):ms(90)])
    f_note = f0(b.run(sweep=0, note=72)[ms(20):ms(90)])
    b.check(abs(f_def / 261.6 - 1) < 0.03, f"PITCH 64, note 60 : {f_def:.1f} Hz (attendu ~261,6, comme le Syntakt)")
    b.check(abs(f_up / f_def - 2) < 0.06, f"PITCH +12 : x{f_up / f_def:.3f} (attendu x2)")
    b.check(abs(f_note / f_def - 2) < 0.06, f"note +12 : x{f_note / f_def:.3f} (attendu x2)")

    print("[3] SWEEP = SWEP (balayage de la hauteur)")
    r = [f0(x[ms(0.5):ms(8)]) / f0(x[ms(60):ms(120)]) for x in (b.run(sweep=v, blocks=190) for v in (0, 74, 127))]
    b.check(r[0] < 1.05 and 1.3 < r[1] < 1.5 and 1.55 < r[2] < 1.8,
            f"f0 debut / fin, SWEEP 0/74/127 : x{r[0]:.2f} / x{r[1]:.2f} / x{r[2]:.2f} (Syntakt : x0,94 / x1,40 / x1,66)")

    print("[4] SHAPE = FCMP (amas aigu), COLOR = INHM et CONTOUR = MENV (2e mode)")
    lv = [rms(highpass(b.run(shape=v))[:ms(50)]) for v in (0, 64, 110)]
    b.check(lv[1] < lv[0] < lv[2], f"amas 0-50 ms, SHAPE 0/64/110 : {lv[0]:.3g} / {lv[1]:.3g} / {lv[2]:.3g} (non monotone, comme FCMP)")
    k = [mode2_ratio(b.run(color=v, contour=0, sweep=0)) for v in (0, 127)]
    b.check(abs(k[0] - 2.0) < 0.1 and abs(k[1] - 2.8) < 0.15, f"2e mode du corps, COLOR 0 -> 127 : x{k[0]:.2f} -> x{k[1]:.2f}")
    m = [mode2_level(b.run(contour=v, sweep=0)) for v in (0, 127)]
    b.check(1.5 < m[0] / m[1] < 3, f"2e mode 0-20 ms, CONTOUR 0 -> 127 : x{m[0] / m[1]:.2f} (Syntakt, MENV : x2,02)")

    print("[5] DECAY = DEC (enveloppe d'ampli d'origine, recalee sur le Syntakt)")
    t = [rms(b.run(decay=v, blocks=460)[ms(150):ms(300)]) for v in (10, 40, 90)]
    b.check(t[0] < t[1] < t[2], f"queue 150-300 ms, DECAY 10/40/90 : {t[0]:.3g} / {t[1]:.3g} / {t[2]:.3g}")

    print("[6] stabilité : modulation continue, retrigs, PUNCH")
    rng = np.random.default_rng(1)
    e = E.Engine(patched, extra)
    e.solo(0)
    e.set(0, machine="SNARE", **DEF)
    walk = {k: 64.0 for k in ("color", "shape", "sweep", "contour", "pitch")}

    def lfo(eng, blk):
        for k in walk:
            walk[k] = float(np.clip(walk[k] + rng.normal(0, 6), -20, 127.9))   # déborde exprès (<0, >0x7f00)
            eng.set(0, **{k: walk[k]})
        eng.set(0, punch=int(blk // 50) % 2, decay=int(rng.integers(0, 128)))
    y = e.render(500, trig_at=set(range(1, 500, 37)), on_block=lfo)
    b.check(not e.unmapped and np.all(np.isfinite(y)) and np.max(np.abs(y)) < 2 ** 31,
            f"500 blocs modulés, 14 retrigs : crête {np.max(np.abs(y)):.3g}, aucun accès hors zone")

    print("\nTOUT OK" if not b.fail else f"\n{b.fail} ECHEC(S)")
    return 1 if b.fail else 0


if __name__ == "__main__":
    sys.exit(main())
