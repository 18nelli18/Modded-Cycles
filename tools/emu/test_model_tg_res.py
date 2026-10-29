#!/usr/bin/env python3
"""Preuve du makeup de résonance entier de Model-TG (notes/85, tools/gen_model_tg.py RES_PATCHES) : le filtre en
échelle de Model-TG ne fait plus baisser le volume quand on monte la résonance, et son pic de résonance est arrondi
par un écrêtage doux (mc_sat) au lieu de taper dans une borne dure.

Le filtre tourne à deux endroits, retouchés de la même façon : ladder_run (le Sampler, 2x, x = s >> 13) et gflt_run
(Filtre / Résonance des machines d'origine, dans amp_hook, x = s >> 14). Le banc exécute leur code, celui du tweak
d'avant (--ref, par défaut 30-model-tg.json au commit 2594419) et celui d'après (--tweak) : leurs symboles sont aux
mêmes adresses (FLT_SYMBOLS du générateur).

Vérifications :
  1. machines d'origine, de bout en bout (boucle des voix, gflt_coef puis gflt_run), Filtre grand ouvert : niveau
     à Résonance 64 et 127 par rapport à Résonance 0, chaque machine : jamais plus de MAX_DROP_DB de baisse, et
     jamais moins qu'avant (les machines claires montent : le pic de résonance est vers 16 kHz) ;
  2. Résonance 0 : sortie identique, échantillon par échantillon, avant / après (grand ouvert = contourné, et
     Filtre 64 = boucle rapide), chaque machine ;
  3. les deux échelles appelées directement, Filtre grand ouvert, sinus 200 Hz à -6 dB : niveau à Résonance 64 et
     127 (avant / après) ;
  4. mc_sat seul, de -8x à +8x la pleine échelle : identité jusqu'à 3/4, puis la courbe quadratique, croissante,
     impaire, continue, bornée ; il garde d0 et la pile ;
  5. pic de résonance (Résonance 127, Filtre 32 .. 127, dent de scie 120 Hz à -1 dB et -12 dB) : jamais au-delà de
     la pleine échelle, sortie périodique comme l'entrée (aucun grondement : écart d'une période à l'autre < 1 %) ;
  6. coût : instructions de gflt_run par bloc, Résonance 0 (inchangé) et 127.

    python3 tools/emu/test_model_tg_res.py --cycles firmware/model-cycles_OS1.13.syx [--tweak ….json] [--ref ….json]
Environ 9 min.
"""
import argparse
import json
import pathlib
import struct
import subprocess
import sys

import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import mcengine as E                # noqa: E402
import test_model_tg as TG          # noqa: E402
import test_sdvintage as T          # noqa: E402

REPO = HERE.parent.parent
TWEAK = REPO / "tweaks" / "model-cycles_OS1.13" / "30-model-tg.json"
REF_COMMIT = "2594419"              # main avant notes/85 : le makeup à moitié, à l'entrée de l'échelle
MAX_DROP_DB = 1.0
RAIL = 131068                       # la borne de sortie des deux échelles (en unités de l'échelle)
FULL = 131072                       # pleine échelle, en unités de l'échelle
BUF = 0x40790000                    # tampons du banc (BSS libre de mcengine)
ZERO = 0x40791000                   # une « voix » sans nouvelle note (voice+56 = 0) pour gflt_run
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def db(a, b):
    return 20 * np.log10(a / b)


def rms(x):
    return float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))


class Rig:
    """Un Model-TG (tweak) dans le moteur de la boucle des voix, ses symboles de filtre."""

    def __init__(self, stock, tw, sym):
        p, _ = build.apply_writes(stock, [tw])
        pl, _ = build.build_payload([tw], stock, None)
        self.img = bytes(p) + pl
        self.sym = sym
        self.e = TG.engine(self.img)

    def u16(self, name, i):
        return struct.unpack(">H", bytes(self.e.uc.mem_read(self.sym[name] + 2 * i, 2)))[0]

    def coefs(self, dial, res, half):
        """f, fb, makeup comme sp_flt_go / gflt_coef : half = makeup de l'ancienne table filt_mkt."""
        r = res * 256
        fb = min((r >> 1) - (r >> 5), self.u16("filt_fbmax", dial))
        return self.u16("filt_coef", dial), fb, self.u16("filt_mkt", fb >> 7) if half else 4096

    def ladder(self, x, f, fb, mkup, track=0):
        """ladder_run (le Sampler) sur x (unités de l'échelle), par blocs de 32 paires."""
        uc = self.uc_reset(track, "filt_y1", 24, "filt_mk", mkup)
        out = []
        for b in range(0, len(x), 32):
            s = np.repeat(np.asarray(x[b:b + 32], dtype=np.int64) << 13, 2)
            uc.mem_write(BUF, s.astype(">i4").tobytes())
            sp = E.STACK - 0x200
            uc.mem_write(sp, struct.pack(">I", E.STOP))
            for reg, v in ((mk.UC_M68K_REG_D0, f), (mk.UC_M68K_REG_D1, fb), (mk.UC_M68K_REG_D4, track),
                           (mk.UC_M68K_REG_A1, BUF), (mk.UC_M68K_REG_A7, sp)):
                uc.reg_write(reg, v)
            uc.emu_start(self.sym["ladder_run"], E.STOP, count=200_000)
            y = np.frombuffer(bytes(uc.mem_read(BUF, 256)), dtype=">i4").astype(np.int64)
            assert np.array_equal(y[0::2], y[1::2])
            out.append(y[0::2] >> 13)
        return np.concatenate(out)

    def gflt(self, x, f, fb, mkup, track=0, count=False):
        """gflt_run (les machines d'origine) sur x (unités de l'échelle), par blocs de 32."""
        uc = self.uc_reset(track, "gflt_y1", 28, "gflt_mk", mkup)
        for name, v in (("gflt_f", f), ("gflt_q", fb), ("voice_ptr", ZERO)):
            uc.mem_write(self.sym[name] + 4 * track, struct.pack(">I", v))
        n = [0]
        h = uc.hook_add(UC_HOOK_CODE, lambda *a: n.__setitem__(0, n[0] + 1)) if count else None
        out = []
        for b in range(0, len(x), 32):
            uc.mem_write(BUF, (np.asarray(x[b:b + 32], dtype=np.int64) << 14).astype(">i4").tobytes())
            self.e.call(self.sym["gflt_run"], BUF, track)
            out.append(np.frombuffer(bytes(uc.mem_read(BUF, 128)), dtype=">i4").astype(np.int64) >> 14)
        if h is not None:
            uc.hook_del(h)
        return (np.concatenate(out), n[0] * 32 // len(x)) if count else np.concatenate(out)

    def sat(self, v):
        """mc_sat appelé directement : d6 en entrée et en sortie."""
        uc = self.e.uc
        sp = E.STACK - 0x200
        uc.mem_write(sp, struct.pack(">I", E.STOP))
        uc.reg_write(mk.UC_M68K_REG_D6, v & 0xffffffff)
        uc.reg_write(mk.UC_M68K_REG_D0, 0x12345678)
        uc.reg_write(mk.UC_M68K_REG_A7, sp)
        uc.emu_start(self.sym["mc_sat"], E.STOP, count=1000)
        assert uc.reg_read(mk.UC_M68K_REG_D0) == 0x12345678 and uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        return struct.unpack(">i", struct.pack(">I", uc.reg_read(mk.UC_M68K_REG_D6)))[0]

    def uc_reset(self, track, y1, stride, mkname, mkup):
        uc = self.e.uc
        for k in range(4):
            uc.mem_write(self.sym[y1] + stride * k + 4 * track, bytes(4))
        uc.mem_write(self.sym[mkname] + 4 * track, struct.pack(">I", mkup))
        uc.mem_write(ZERO, bytes(64))
        return uc

    def machine(self, t, dial, res, blocks=64):
        """La machine t sur la piste t, seule, Filtre dial et Résonance res : de bout en bout."""
        e = TG.engine(self.img)
        for k in range(6):
            e.set(k, machine=k, note=48, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0,
                  finetune=64, decay=120)
        e.uc.mem_write(E.PARAMS + 0xe + t * 0x42 + 48, struct.pack(">hh", min(dial * 256, 32512), res * 256))
        e.solo(t)
        return np.concatenate([e.block(1 << t if b == 1 else 0)[t] for b in range(blocks)]), e.unmapped


def ref_tweak(arg):
    if arg:
        return json.loads(pathlib.Path(arg).read_text(encoding="utf-8"))
    rel = TWEAK.relative_to(REPO).as_posix()
    return json.loads(subprocess.run(["git", "-C", str(REPO), "show", f"{REF_COMMIT}:{rel}"], check=True,
                                     capture_output=True, text=True).stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--tweak", default=str(TWEAK))
    ap.add_argument("--ref", help=f"le tweak d'avant (défaut : {TWEAK.name} au commit {REF_COMMIT})")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8"))
    sym = {k: int(v, 16) for k, v in tw["symbols"].items()}
    old, new = Rig(stock, ref_tweak(args.ref), sym), Rig(stock, tw, sym)

    print("1. machines d'origine, Filtre grand ouvert : niveau à Résonance 64 / 127 par rapport à 0 (dB)")
    print("   machine   avant 64  avant 127  après 64  après 127")
    ref0 = {}
    for t, name in enumerate(TG.NAMES):
        row = []
        for rig in (old, new):
            base, unm = rig.machine(t, 127, 0)
            ref0[(t, rig is new)] = base
            if unm:
                check(False, f"{name} : accès hors de la mémoire émulée {unm[:3]}")
            for res in (64, 127):
                y, _ = rig.machine(t, 127, res)
                row.append(db(rms(y[96:]), rms(base[96:])))
        print(f"   {name:6s} " + "".join(f"{v:10.2f}" for v in row))
        check(min(row[2], row[3]) > -MAX_DROP_DB and row[2] >= row[0] and row[3] >= row[1],
              f"{name} : Résonance 64 / 127 à {row[2]:+.2f} / {row[3]:+.2f} dB (avant {row[0]:+.2f} / {row[1]:+.2f}) : "
              f"aucune baisse de plus de {MAX_DROP_DB} dB")

    print("2. Résonance 0 : rien ne change (contourné grand ouvert, boucle rapide à Filtre 64)")
    for t, name in enumerate(TG.NAMES):
        a64, _ = old.machine(t, 64, 0, 48)
        b64, _ = new.machine(t, 64, 0, 48)
        check(np.array_equal(ref0[(t, False)], ref0[(t, True)]) and np.array_equal(a64, b64) and np.abs(a64).max() > 0,
              f"{name} : identique avant / après, grand ouvert et à Filtre 64")
    rng = np.random.default_rng(1)
    x = (rng.integers(-FULL // 2, FULL // 2, 3200)).astype(np.int64)
    for rig in (old, new):
        f, fb, _ = rig.coefs(64, 0, False)
        rig.r0 = (rig.ladder(x, f, fb, 4096), rig.gflt(x, f, fb, 4096))
    check(all(np.array_equal(a, b) for a, b in zip(old.r0, new.r0)),
          "ladder_run et gflt_run, Résonance 0 (boucles rapides) : identiques avant / après sur du bruit à -6 dB")

    print("3. les deux échelles, Filtre grand ouvert, sinus 200 Hz à -6 dB : niveau (dB) par rapport à l'entrée")
    n = 48000 // 4
    sine = np.round(FULL / 2 * np.sin(2 * np.pi * 200 * np.arange(n) / 48000)).astype(np.int64)
    for label, fn in (("ladder_run (Sampler)", "ladder"), ("gflt_run (machines)", "gflt")):
        vals = []
        for rig, half in ((old, True), (new, False)):
            for res in (0, 64, 127):
                f, fb, m = rig.coefs(127, res, half)
                vals.append(db(rms(getattr(rig, fn)(sine, f, fb, m)[n // 2:]), rms(sine[n // 2:])))
        print(f"   {label:22s} avant {vals[0]:+.2f} / {vals[1]:+.2f} / {vals[2]:+.2f}   "
              f"après {vals[3]:+.2f} / {vals[4]:+.2f} / {vals[5]:+.2f}   (Résonance 0 / 64 / 127)")
        check(max(abs(v) for v in vals[3:]) < MAX_DROP_DB and vals[2] < -5,
              f"{label} : à moins de {MAX_DROP_DB} dB de l'entrée à toute résonance (avant : {vals[2]:.1f} dB à 127)")

    print("4. l'écrêtage doux, mc_sat appelé directement, de -8x à +8x la pleine échelle")
    v = np.arange(0, 8 * FULL, 61, dtype=np.int64)
    v = np.concatenate([-v[:0:-1], v])
    y = np.array([new.sat(int(a)) for a in v])
    lin = np.abs(v) <= 98304
    knee = (np.abs(v) > 98304) & (np.abs(v) < 163840)
    model = np.sign(v) * np.minimum(np.abs(v) - (((np.abs(v) - 98304) >> 1) ** 2 >> 15), RAIL)
    check(np.array_equal(y[lin], v[lin]), "identité jusqu'à 3/4 de la pleine échelle (+-98304)")
    check(np.array_equal(y[knee], model[knee]) and np.all(np.diff(y) >= 0) and np.abs(y).max() == RAIL
          and np.array_equal(y, -y[::-1]),
          f"au-delà : v - (v - 98304)^2 / 131072, croissant, impair, borné à +-{RAIL} (atteint à +-163840)")
    check(np.abs(np.diff(y)).max() <= 61, "pente jamais au-dessus de 1 : aucun saut (continu, sans marche)")

    print("5. pic de résonance : Résonance 127, dent de scie 120 Hz, à -1 dB et à -12 dB")
    print("   échelle     niveau Filtre   crête avant/après   saturé* avant/après   écart périodique avant/après")
    P = 400
    for amp_db in (-1, -12):
        saw = np.round(10 ** (amp_db / 20) * FULL * (2 * (np.arange(P * 40) % P) / P - 1)).astype(np.int64)
        for label, fn in (("ladder_run", "ladder"), ("gflt_run", "gflt")):
            for dial in (32, 64, 96, 120, 127):
                m = []
                for rig, half in ((old, True), (new, False)):
                    f, fb, mkup = rig.coefs(dial, 127, half)
                    y = getattr(rig, fn)(saw, f, fb, mkup)[P * 20:]
                    per = rms(y[P:] - y[:-P]) / max(rms(y), 1)
                    m.append((int(np.abs(y).max()), float(np.mean(np.abs(y) > 98304)), per))
                (pa, ra, qa), (pb, rb, qb) = m
                print(f"   {label:11s} {amp_db:4d} dB {dial:5d}   {pa:7d} / {pb:7d}     {100 * ra:5.1f} % / {100 * rb:5.1f} %"
                      f"          {100 * qa:6.3f} % / {100 * qb:6.3f} %")
                check(pb <= RAIL and qb < 0.01,
                      f"{label}, {amp_db} dB, Filtre {dial} : crête {pb} <= {RAIL} (pas de débordement), sortie "
                      f"périodique comme l'entrée (écart {100 * qb:.3f} % < 1 % : pas de grondement)")
    print("   * saturé : échantillons au-delà de 3/4 de la pleine échelle, dans le coude de mc_sat (après) ;")
    print("     avant, le makeup à moitié laissait le pic plus bas, au prix de -5,5 dB dans la bande passante")

    print("6. coût de gflt_run par bloc de 32 (instructions)")
    for res in (0, 127):
        c = []
        for rig, half in ((old, True), (new, False)):
            f, fb, m = rig.coefs(64, res, half)
            c.append(rig.gflt(sine[:3200], f, fb, m, count=True)[1])
        print(f"   Résonance {res:3d} : avant {c[0]}, après {c[1]}")
        if res == 0:
            check(c[0] == c[1], f"Résonance 0 : même coût ({c[1]} instructions par bloc)")
        else:
            check(c[1] <= c[0] * 1.10, f"Résonance 127 : {c[1]} instructions par bloc (avant {c[0]}, "
                                       f"{100 * (c[1] - c[0]) / c[0]:+.1f} %)")

    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
