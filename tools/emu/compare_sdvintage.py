#!/usr/bin/env python3
"""Compare notre SD VINTAGE (Model:Cycles, tweak sdvintage-snare) au vrai SD VINTAGE du Syntakt (notes/16).

Les deux moteurs tournent en émulation, chacun dans SA vraie boucle des voix :
  - le Syntakt : programme du processeur audio (section 7 de TON Syntakt_OS1.41.syx), stengine.py ;
  - le Cycles  : TON model-cycles_OS1.13.syx patché par le tweak, mcengine.py.
Mêmes réglages des deux côtés (les potards du Cycles ont le sens de ceux du Syntakt), mêmes mesures
(hauteur et balayage du corps, durées, niveau et centre de l'amas aigu), et un WAV A/B par cas :
Syntakt, 0,3 s de silence, notre version (normalisation commune).

    pip install unicorn numpy        (+ objdump m68k : binutils-m68k-linux-gnu, ou binutils de Homebrew)
    python3 tools/emu/compare_sdvintage.py --cycles model-cycles_OS1.13.syx \\
        --syntakt Syntakt_OS1.41.syx [--wav dossier/] [--cases defaut,swep127,...]
"""
import argparse
import json
import pathlib
import sys
import wave

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import mcengine as E          # noqa: E402
import stengine as S          # noqa: E402
import syntakt                # noqa: E402
import test_sdvintage as T    # noqa: E402

SR = 48000
# Syntakt (valeurs d'interface) -> Cycles : TUNE=PITCH, INHM=COLOR, FCMP=SHAPE, SWEP=SWEEP, MENV=CONTOUR, DEC=DECAY
DEF = dict(tune=64, inhm=0, fcmp=110, swep=74, menv=80, dec=33, punch=0)
CASES = {
    "defaut": {}, "note48": {"note": 48}, "note72": {"note": 72},
    "swep0": {"swep": 0}, "swep30": {"swep": 30}, "swep127": {"swep": 127},
    "fcmp0": {"fcmp": 0}, "fcmp64": {"fcmp": 64}, "inhm127": {"inhm": 127}, "menv0": {"menv": 0}, "menv127": {"menv": 127},
    "dec10": {"dec": 10}, "dec60": {"dec": 60}, "dec90": {"dec": 90}, "punch": {"punch": 1},
}


def band(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f >= hi)] = 0
    return np.fft.irfft(X, len(x))


def env(x, w=96):
    return np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "same"))


def f0(seg, lo=60, hi=1500):
    seg = seg - seg.mean()
    X = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), 1 << 16))
    f = np.fft.rfftfreq(1 << 16, 1 / SR)
    m = (f > lo) & (f < hi)
    return float(f[m][np.argmax(X[m])])


def t_to(e, db):
    i0 = int(np.argmax(e))
    below = np.nonzero(e[i0:] < e.max() * 10 ** (db / 20))[0]
    return (i0 + below[0]) / 48 if len(below) else len(e) / 48


def metrics(x):
    ms = lambda t: int(t * 48)                                  # noqa: E731
    body, clus = band(x, 0, 900), band(x, 1500, 12000)
    X = np.abs(np.fft.rfft(clus[:ms(60)] * np.hanning(ms(60))))
    f = np.fft.rfftfreq(ms(60), 1 / SR)
    rms = lambda v: np.sqrt(np.mean(v ** 2)) + 1e-9              # noqa: E731
    return {
        "f0 0-8ms": f0(x[ms(0.5):ms(8)]), "f0 10-30ms": f0(x[ms(10):ms(30)]), "f0 40-120ms": f0(x[ms(40):ms(120)]),
        "corps -20dB": t_to(env(body), -20), "amas -20dB": t_to(env(clus), -20), "tout -40dB": t_to(env(x), -40),
        "amas/corps dB": 20 * np.log10(rms(clus[:ms(50)]) / rms(body[:ms(50)])),
        "centre amas Hz": float((f * X).sum() / X.sum()),
    }


def render_syntakt(img, blocks, note=60, **kw):
    e = S.Engine(img)
    e.solo(0)
    e.machine(0, "SD VINTAGE")
    e.note(0, note)
    p = dict(S.SDVN_DEFAULTS)
    p.update(tune=kw["tune"], p1=kw["inhm"], p2=kw["fcmp"], p3=kw["swep"], p4=kw["menv"], decay=kw["dec"], punch=kw["punch"])
    e.set(0, **p)
    x = e.render(blocks, trig_at=(1,))[64:].astype(float)
    assert not e.unmapped, e.unmapped[:3]
    return x


def render_cycles(os_img, extra, blocks, note=60, **kw):
    e = E.Engine(os_img, extra)
    e.solo(0)
    e.set(0, machine="SNARE", pitch=kw["tune"], note=note, color=kw["inhm"], shape=kw["fcmp"], sweep=kw["swep"],
          contour=kw["menv"], decay=kw["dec"], punch=kw["punch"], gate=0)
    x = e.render(blocks, trig_at=(1,))[64:].astype(float)
    assert not e.unmapped, e.unmapped[:3]
    return x


def write_ab(path, a, b):
    pk = max(np.abs(a).max(), np.abs(b).max()) or 1
    y = np.concatenate([a, np.zeros(int(0.3 * SR)), b]) / pk * 0.9 * 32767
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(y.astype("<i2").tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.41.syx officiel")
    ap.add_argument("--wav", help="dossier des WAV A/B (Syntakt puis Cycles)")
    ap.add_argument("--cases", default="defaut", help="cas, séparés par des virgules ('all' = tous) : " + ",".join(CASES))
    ap.add_argument("--ms", type=int, default=400, help="durée rendue par cas (ms)")
    args = ap.parse_args()
    names = list(CASES) if args.cases == "all" else args.cases.split(",")
    blocks = int(args.ms * SR / 1000 / 32) + 3
    img = syntakt.dsp_image(args.syntakt)
    stock = T.main_os_from_syx(args.cycles)
    patched, extra = T.apply(stock, json.loads(T.TWEAK.read_text(encoding="utf-8")))
    if args.wav:
        pathlib.Path(args.wav).mkdir(parents=True, exist_ok=True)
    for name in names:
        kw = dict(DEF)
        kw.update(CASES[name])
        note = kw.pop("note", 60)
        a = render_syntakt(img, blocks, note, **kw)
        b = render_cycles(patched, extra, blocks, note, **kw)
        ma, mb = metrics(a), metrics(b)
        print(f"== {name} {CASES[name] or ''}")
        for k in ma:
            print(f"   {k:15} Syntakt {ma[k]:8.1f}   Cycles {mb[k]:8.1f}")
        if args.wav:
            write_ab(pathlib.Path(args.wav) / f"sdvintage_{name}_syntakt-puis-cycles.wav", a, b)


if __name__ == "__main__":
    main()
