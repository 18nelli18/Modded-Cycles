#!/usr/bin/env python3
"""Proof of the RETROSYN machine in the Modded Cycles OS (notes/84, tools/gen_retrosyn.py):
31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-retrosyn.json on 30-model-tg-st.json, against the OS combination
without RETROSYN (31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid.json). The OS's own code, emulated (Unicorn).

  1. Boot: the bootstrap's decompressor reads the grown OS back; the boot hook rebuilds the payload (decompressed,
     instruction cache invalidated before the 2nd stage, CHORD's wavetables taken back), then resumes. Outside what
     counts the machines, the payload is the engines' alone; MACRO and ACID keep their place and bytes (those of the
     OS without RETROSYN); RETROSYN's code at gen_retrosyn.RS_AT, its variables at RS_BSS, above ACID's.
  2. Interface (test_model_tg_syntakt.interface): RETROSYN in MACHINES (machine 15, index 14), its name, its image,
     its 5 descriptors (COLOR, SHAPE 0..5, SWEEP, CONTOUR, DECAY) and their defaults, the knobs, the parameter rows
     (gs.ROWS8), the machine switch, the MACHINES screen with 15 marks on 2 rows of 8 at most. MACRO's lo-fi still
     under FUNC + PITCH.
  3. Sound, the voice loop alone (mcengine), DMA timer 0 one block further at each block:
     - before the amp chain, RETROSYN is exactly the same core compiled for the computer (retrosyn_ref.c): the 6
       waves, duty cycles, wavetables, SNES loops, PUNCH, SWEEP up and down, chords, knobs that move; a quiet voice is
       not computed; the amp chain reads in the voice exactly what it reads for TONE;
     - the 6 original machines, each engine, MACRO and ACID: identical to the OS without RETROSYN, and not one
       RETROSYN instruction without a RETROSYN track; RETROSYN mixed with them; 6 RETROSYN tracks;
     - machine locks RETROSYN -> ACID -> RETROSYN -> MACRO -> RETROSYN -> TONE -> RETROSYN -> KICK on one track: every
       entry into RETROSYN starts from a reset core (its mark at voice + 0x2c, erased by the other machines), and the
       whole track matches the reference core;
     - load governor: under overload it stops RETROSYN tracks too, never the Sampler; a held note it stopped, then a
       trig: RETROSYN restarts from the trig, exactly like the reference (why it needs no GOV_SKIP).
  4. Cost of a RETROSYN voice (informative), next to TONE and ACID.

    python3 tools/emu/test_retrosyn.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--quick]
"""
import argparse
import ctypes
import pathlib
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_acid as ga               # noqa: E402
import gen_acid_combos as gac       # noqa: E402
import gen_macro as gm              # noqa: E402
import gen_retrosyn as gr           # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import lofi_ui                      # noqa: E402
import mcengine as E                # noqa: E402
import syntakt                      # noqa: E402
import test_acid as ta              # noqa: E402
import test_acid_combos as tac      # noqa: E402
import test_macro as tm             # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_model_tg_syntakt as tms  # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402

check = t7.check
load = ta.load
SRC = HERE.parent / "machines" / "retrosyn"
tac.KINDS = ("macro", "acid", "retrosyn")

MARK = 0x52535931                   # 'RSY1', retrosyn.c
IDLE_LEVEL = 1 << 14
AMP = ((0x400a9252, 0x400a9302), (0x400a9430, 0x400a9498))     # AMP_ENV, VCA
TONE = ta.TONE
BLOCK, M32, GAINS, FULL = tmx.BLOCK, tac.M32, tmx.GAINS, tmx.FULL
BASE_KW = dict(note=60, pitch=64, color=0, shape=0, sweep=64, contour=0, punch=0, gate=0, finetune=64, decay=50)


# --- the reference core ------------------------------------------------------------------------------------------
class Ref:
    """retrosyn_dsp.h compiled for the computer (retrosyn_ref.c), called through ctypes."""

    def __init__(self, tmp):
        lib = tmp / "libretrosyn.so"
        subprocess.check_call(["gcc", "-O2", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", f"-I{SRC}",
                               "-o", str(lib), str(SRC / "retrosyn_ref.c")])
        self.c = ctypes.CDLL(str(lib))
        self.c.rs_new.restype = ctypes.c_void_p
        self.c.rs_free.argtypes = [ctypes.c_void_p]
        self.c.rs_block_c.argtypes = [ctypes.c_void_p] + [ctypes.c_int] * 7 + [ctypes.POINTER(ctypes.c_int)]

    def simulate(self, recs):
        """The blocks the OS rendered (recs from Probe): a new core at each init (mark not found)."""
        s, outs, buf = self.c.rs_new(), [], (ctypes.c_int * 32)()
        for r in recs:
            if r["init"]:
                self.c.rs_free(s)
                s = self.c.rs_new()
            if r["render"]:
                self.c.rs_block_c(s, r["note"], r["trig"], r["shape"], r["color"], r["sweep"], r["contour"],
                                  r["punch"], buf)
                outs.append(list(buf))
        self.c.rs_free(s)
        return np.array(outs, np.int64).reshape(-1, 32)


def knob(x):
    x = max(0, min(0x7f00, x))
    return x + (x >> 7)


class Probe:
    """On one track: what retrosyn_update reads (as retrosyn.c maps it), whether the render reached the amp chain, and
    the block before the amp chain."""

    def __init__(self, v, e, track=0, reads=False):
        self.recs, self.outs, self.block, self.out_at = [], [], 0, None
        self.reads = [] if reads else None
        self.vo = E.VOICE0 + track * E.VSTRIDE
        uc = e.uc
        arg = lambda k: struct.unpack(">I", uc.mem_read(uc.reg_read(mk.UC_M68K_REG_A7) + 4 * k, 4))[0]

        def upd(uc_, a, s, u):
            if arg(2) != self.vo:
                return
            pmod = struct.unpack(">i", struct.pack(">I", arg(1)))[0]
            pb, vb = bytes(uc.mem_read(arg(3), 0x40)), bytes(uc.mem_read(self.vo, E.VSTRIDE))
            p16 = lambda o: struct.unpack_from(">h", pb, o)[0]
            v32 = lambda o: struct.unpack_from(">I", vb, o)[0]
            n = p16(0x14) * 256 - (64 << 16) + pmod + (p16(0x22) - 0x4000) * 2
            self.recs.append(dict(
                block=self.block, note=max(0, min(127 << 16, n)), shape=max(0, min(5, p16(0x18) >> 8)) * 5462 + 2731,
                color=knob(p16(0x16)), sweep=16384 if p16(0x1a) == 0x4000 else knob(p16(0x1a)),
                contour=knob(p16(0x1c)), punch=int(p16(0x1e) != 0), trig=int(v32(0x38) != 0),
                init=int(v32(0x2c) != MARK), render=0))

        def rnd(uc_, a, s, u):
            if arg(2) == self.vo:
                self.out_at = arg(1)

        def amp(uc_, a, s, u):
            if v.pay <= arg(0) < v.code_end and arg(1) == self.vo:
                self.recs[-1]["render"] = 1
                self.outs.append(np.frombuffer(bytes(uc.mem_read(self.out_at, 128)), ">i4").astype(np.int64))

        uc.hook_add(UC_HOOK_CODE, upd, begin=v.upd, end=v.upd)
        uc.hook_add(UC_HOOK_CODE, rnd, begin=v.rnd, end=v.rnd)
        uc.hook_add(UC_HOOK_CODE, amp, begin=AMP[0][0], end=AMP[0][0])
        if reads:
            uc.hook_add(UC_HOOK_MEM_READ, self._read, begin=self.vo, end=self.vo + E.VSTRIDE - 1)

    def _read(self, uc, access, addr, size, value, ud):
        if any(lo <= uc.reg_read(mk.UC_M68K_REG_PC) < hi for lo, hi in AMP):
            self.reads.append((self.block, addr - self.vo, bytes(uc.mem_read(addr, size))))

    def got(self):
        return np.array(self.outs, np.int64).reshape(-1, 32)


def play(v, idx, kw, blocks, trigs=(1,), changes=None, track=0, reads=False):
    """One track on machine idx, the others off; with a Probe on RETROSYN."""
    e = v.engine(solo=track)
    e.set(track, machine=idx, **kw)
    pr = Probe(v, e, track, reads)
    out = []
    for b in range(blocks):
        for k, x in (changes or {}).get(b, {}).items():
            e.set(track, **{k: x})
        pr.block = b
        out.append(e.block(1 << track if b in trigs else 0)[track])
    return np.stack(out), pr, e.unmapped


# --- 1. boot -----------------------------------------------------------------------------------------------------
def boot(fw, ref_eng, ref_os, tgs):
    tac.boot(fw, ref_eng, tgs, ref_os)
    acid, a = fw.views["acid"], ref_os.views["acid"]
    same = (acid.pay == a.pay and fw.runtime[acid.pay - fw.dest:acid.code_end - fw.dest]
            == ref_os.runtime[a.pay - ref_os.dest:a.code_end - ref_os.dest])
    check(same, f"ACID at {acid.pay:#x}: its {acid.code_end - acid.pay} bytes, those of {ref_os.mine['id']}")
    rs, pay = fw.views["retrosyn"], fw.dest
    check(rs.pay == pay + gr.RS_AT and rs.code_end <= pay + gr.RS_BSS and acid.code_end <= pay + gac.ACID_BSS < rs.pay
          and rs.index == 14 and fw.nm == 15,
          f"RETROSYN machine 15 (index 14), code at {rs.pay:#x}..{rs.code_end:#x}, variables at "
          f"{pay + gr.RS_BSS:#x}, above ACID's ({pay + gac.ACID_BSS:#x})")


# --- 3. sound ----------------------------------------------------------------------------------------------------
def cases(quick):
    out = [("quiet voice", dict(BASE_KW, decay=0), (1,), None, 25)]
    out += [(f"SHAPE {sh}", dict(BASE_KW, shape=sh), (1,), None, 20) for sh in range(6)]
    out += [(f"pulse COLOR {c}", dict(BASE_KW, color=c, note=69), (1,), None, 16) for c in (0, 32, 64, 127)]
    out += [(f"wave COLOR {c}", dict(BASE_KW, shape=2, color=c, note=57), (1,), None, 16)
            for c in ((0, 48, 112) if quick else range(0, 128, 16))]
    out += [(f"SNES COLOR {c}", dict(BASE_KW, shape=5, color=c, note=64), (1,), None, 16) for c in (0, 40, 127)]
    out += [(f"noise COLOR {c}", dict(BASE_KW, shape=sh, color=c, note=n), (1,), None, 16)
            for sh, c, n in ((3, 0, 60), (3, 127, 100), (4, 64, 30), (4, 127, 0))]
    out += [("PUNCH SNES", dict(BASE_KW, shape=5, color=64, punch=1), (1,), None, 16),
            ("PUNCH wave", dict(BASE_KW, shape=2, color=100, punch=1), (1,), None, 16),
            ("SWEEP up to silence", dict(BASE_KW, sweep=127, note=96), (1,), None, 30),
            ("SWEEP down", dict(BASE_KW, sweep=0, note=84), (1,), None, 30),
            ("SWEEP 70, retrig", dict(BASE_KW, sweep=70, shape=1), (1, 15), None, 30),
            ("FINE and PITCH", dict(BASE_KW, finetune=100, pitch=40, shape=1), (1,), None, 16),
            ("lowest note", dict(BASE_KW, note=0, pitch=0, shape=5), (1,), None, 16),
            ("highest note", dict(BASE_KW, note=127, pitch=127, shape=2), (1,), None, 16)]
    out += [(f"CONTOUR {c}", dict(BASE_KW, contour=c, shape=sh), (1,), None, 30)
            for c, sh in ((16, 0), (40, 1), (64, 2), (90, 5), (127, 0))]
    if not quick:
        moves = {b: {"color": (7 * b) % 128, "contour": (5 * b) % 128, "sweep": (11 * b) % 128,
                     "shape": b % 6} for b in range(2, 40)}
        out.append(("knobs that move", dict(BASE_KW, decay=110), (1, 20), moves, 40))
    return out


def exact(v, ref, todo, label):
    """Before the amp chain: the reference core, sample for sample."""
    bad, quiet, peaks = [], 0, []
    for name, kw, trigs, changes, blocks in todo:
        out, pr, unm = play(v, v.index, kw, blocks, trigs, changes)
        want, got = ref.simulate(pr.recs), pr.got()
        idle = [r["block"] for r in pr.recs if not r["render"]]
        quiet += len(idle)
        peaks.append(int(np.abs(got).max()) if len(got) else 0)
        if not (len(got) and np.array_equal(want, got) and not unm and not out[idle].any()
                and sum(r["init"] for r in pr.recs) == 1):
            bad.append(name)
    check(not bad, f"{label}: before the amp chain, identical to the reference core ({len(todo)} cases, peaks "
                   f"{min(peaks):.2g} to {max(peaks):.2g}, {quiet} quiet blocks not computed and silent) {bad[:4]}")


def amp_like_tone(v, label):
    """The amp chain (AMP_ENV, VCA) reads in a RETROSYN voice exactly what it reads in a TONE voice."""
    res = []
    for kw in (dict(BASE_KW, decay=30), dict(BASE_KW, decay=90, gate=1)):
        _, pt, _ = play(v, TONE, kw, 60, reads=True)
        _, pr, unm = play(v, v.index, kw, 60, reads=True)
        stop = next((r["block"] for r in pr.recs if not r["render"]), 60)
        rm = [x for x in pr.reads if x[0] < stop]
        res.append(rm == [x for x in pt.reads if x[0] < stop] and len(rm) > 0 and not unm)
    check(all(res), f"{label}: the amp chain reads the voice as for TONE (DECAY 30, DECAY 90 with GATE)")


def mach_list(fw, ref):
    """Tracks: KICK, 1st engine, MACRO, Sampler, ACID, last engine."""
    return [0, gs.TG_FIRST, fw.views["macro"].index, 6, fw.views["acid"].index, gs.TG_FIRST + len(fw.codes) - 1]


def others_unchanged(fw, ref_os, label):
    """Without a RETROSYN track: identical to the OS without RETROSYN, not one RETROSYN instruction."""
    rs = fw.views["retrosyn"]
    mach = mach_list(fw, ref_os)
    setup = {t: dict(BASE_KW, machine=m, color=64, shape=64, sweep=64, contour=64, decay=60) for t, m in enumerate(mach)}
    setup[2].update(tm.BASE_KW, machine=mach[2], shape=0, decay=60)
    setup[4].update(ta.KW, machine=mach[4], decay=60)
    for t, c in ((1, fw.codes[0]), (5, fw.codes[-1])):
        k = gs.CATALOG[c]["knobs"]
        setup[t].update(color=k[0][2], shape=k[1][2], sweep=k[2][2], contour=k[3][2])
    trigs = {1: 0x3f, 150: 0x3f}
    r, unm_r = tmx.multi(ref_os, setup, 300, trigs)
    e = fw.engine()
    for t, kw in setup.items():
        e.set(t, **kw)
    ran = []
    e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=rs.pay, end=rs.code_end - 1)
    x = np.stack([e.block(trigs.get(b, 0)) for b in range(300)])
    peaks = [f"{np.abs(x[:, t]).max():.2g}" for t in range(6)]
    check(np.array_equal(r, x) and not ran and not (unm_r or e.unmapped) and all(np.abs(x[:, t]).max() > 0
                                                                                  for t in (0, 1, 2, 4, 5)),
          f"{label}: KICK, {gs.CATALOG[fw.codes[0]]['name']}, MACRO, Sampler, ACID, "
          f"{gs.CATALOG[fw.codes[-1]]['name']} identical to {ref_os.mine['id']}, no RETROSYN instruction "
          f"(peaks {peaks})")
    tmx.engines_like(fw, ref_os, fw.codes, gs.TG_FIRST, f"{label}, without RETROSYN")


def mixed(fw, ref_os, label):
    """RETROSYN on tracks 2 and 6 among KICK, MACRO, Sampler, ACID: the others identical to the OS without RETROSYN
    (their tracks there: KICK), each RETROSYN track identical to the same track played alone."""
    rs = fw.views["retrosyn"]
    mach = mach_list(fw, ref_os)
    mach[1] = mach[5] = rs.index
    setup = {t: dict(BASE_KW, machine=m, color=64, shape=64, decay=50) for t, m in enumerate(mach)}
    setup[2].update(tm.BASE_KW, machine=mach[2], shape=0, decay=50)
    setup[4].update(ta.KW, machine=mach[4], decay=50)
    ours = {1: dict(BASE_KW, shape=1, contour=64, decay=50), 5: dict(BASE_KW, shape=5, color=40, sweep=80, decay=50)}
    for t, k in ours.items():
        setup[t] = dict(k, machine=rs.index)
    trigs = {1: 0x3f, 150: 0x3f}
    x, unm = tmx.multi(fw, setup, 300, trigs)
    r, unm_r = tmx.multi(ref_os, {t: dict(k, machine=0) if t in ours else k for t, k in setup.items()}, 300, trigs)
    ok, cut = not unm and not unm_r, []
    for t in range(6):
        if t in ours:
            y, _, _ = play(rs, rs.index, ours[t], 300, (1, 150), track=t)
            good, f = tms.same_or_idle(y, x[:, t], 150)
            ok &= good and bool(x[:, t].any())
            cut.append(f)
        else:
            ok &= bool(np.array_equal(x[:, t], r[:, t]))
    check(ok, f"{label}: KICK, RETROSYN, MACRO, Sampler, ACID, RETROSYN together: the others identical to "
              f"{ref_os.mine['id']}, RETROSYN tracks identical to themselves alone (quiet voice stopped: {cut})")


def six_tracks(v, label):
    """6 RETROSYN tracks, the 6 waves: each identical to the same track alone, to the stop of a quiet voice."""
    e = v.engine()
    kws = [dict(BASE_KW, machine=v.index, shape=t, note=48 + 5 * t, contour=16 * t, decay=60) for t in range(6)]
    for t, kw in enumerate(kws):
        e.set(t, **kw)
    x = np.stack([e.block(0x3f if b in (1, 60) else 0) for b in range(120)])
    ok = not e.unmapped
    for t, kw in enumerate(kws):
        y, _, unm = play(v, v.index, {k: w for k, w in kw.items() if k != "machine"}, 120, (1, 60), track=t)
        good, _ = tms.same_or_idle(y, x[:, t], 60)
        ok &= good and not unm and bool(y.any())
    check(ok, f"{label}: 6 RETROSYN tracks together (SHAPE 0..5), each identical to the same track alone")


def locks(fw, ref, label):
    """Machine locks on one track: RETROSYN -> ACID -> RETROSYN -> MACRO -> RETROSYN -> TONE -> RETROSYN -> KICK.
    Each entry into RETROSYN finds no mark and resets the core; the RETROSYN blocks match the reference core with
    those resets; everything plays; RETROSYN's mark erased at the end."""
    rs, acid, macro = fw.views["retrosyn"], fw.views["acid"], fw.views["macro"]
    seq = [("RETROSYN (tri, chord, sweep)", dict(BASE_KW, machine=rs.index, shape=1, contour=64, sweep=90)),
           ("ACID", dict(ta.KW, machine=acid.index)),
           ("RETROSYN (pulse)", dict(BASE_KW, machine=rs.index, color=40, sweep=30)),
           ("MACRO", dict(tm.BASE_KW, machine=macro.index, shape=25)),
           ("RETROSYN (SNES)", dict(BASE_KW, machine=rs.index, shape=5, contour=100)),
           ("TONE", dict(ta.KW, machine=TONE)),
           ("RETROSYN (noise)", dict(BASE_KW, machine=rs.index, shape=3, color=90)),
           ("KICK", dict(ta.KW, machine=0))]
    e = fw.engine(solo=0)
    pr = Probe(rs, e, 0)
    out = []
    for b in range(40 * len(seq)):
        if b % 40 == 0:
            e.set(0, **dict(seq[b // 40][1], decay=60))
        pr.block = b
        out.append(e.block(1 if b % 40 == 1 else 0)[0])
    x = np.stack(out)
    parts = [int(np.abs(x[40 * k + 2:40 * k + 40]).max()) for k in range(len(seq))]
    inits = [r["block"] for r in pr.recs if r["init"]]
    mark = struct.unpack(">I", e.uc.mem_read(E.VOICE0 + 0x2c, 4))[0]
    want = ref.simulate(pr.recs)
    check(all(p > 1e6 for p in parts) and not e.unmapped and mark != MARK and inits == [0, 80, 160, 240]
          and np.array_equal(want, pr.got()),
          f"{label}: machine locks {' -> '.join(n for n, _ in seq)} on one track: all play (peaks "
          f"{[f'{p:.2g}' for p in parts]}), RETROSYN reset on each entry (blocks {inits}), identical to the reference "
          f"core with those resets ({len(want)} blocks), its mark erased at the end")


def governor(fw, tw, label):
    """Overload (as test_acid_combos.governor): 5 RETROSYN tracks and the Sampler on track 3. Fixed 97 % load: all
    RETROSYN tracks stopped, never the Sampler; 46 % + 7 % per computed voice: only some; the spared tracks
    identical to the reference, the stopped ones silent afterwards."""
    rs = fw.views["retrosyn"]
    sy = {k: int(v, 16) for k, v in tw["gov"].items()}
    setup = {t: dict(BASE_KW, machine=rs.index, shape=t % 6, note=40 + 6 * t, color=20 * t, gate=1, decay=100)
             for t in range(6)}
    setup[2] = dict(ta.KW, machine=6, decay=100)
    cost = 2 * 7 * BLOCK // 100

    def play_(load_):
        e = fw.engine()
        for t in range(6):
            for a in GAINS:
                e.uc.mem_write(a + 4 * t, struct.pack(">I", FULL))
        clock = {"t": 10_000_000, "fixed": None, "reads": 0}

        def read(uc, access, addr, size, value, ud):
            if clock["fixed"] is not None:
                v = clock["fixed"]
            else:
                clock["t"] += cost // 2
                clock["reads"] += 1
                v = clock["t"]
            uc.mem_write(tmx.TIMER, struct.pack(">I", v & M32))
        e.uc.hook_add(UC_HOOK_MEM_READ, read, begin=tmx.TIMER, end=tmx.TIMER + 3)
        for t, kw in setup.items():
            e.set(t, **kw)
        e.uc.mem_write(tms.gs_x(tw, "X_SLOW"), struct.pack(">I", 88 * 65536 // 100))
        out, stolen, now = [], set(), 10_000_000
        for b in range(300):
            clock["reads"], clock["t"] = 0, max(clock["t"], now)
            out.append(e.block(0x3f if b == 1 else 0))
            if load_ is not None:
                e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & M32))
                clock["fixed"] = now + load_(b, clock["reads"] // 2) * BLOCK // 100
                e.call(sy["audio_end"])
                clock["fixed"] = None
            now += BLOCK
            stolen |= {t for t, v in enumerate(bytes(e.uc.mem_read(sy["gov_stolen"], 6))) if v}
        return np.stack(out), stolen, e.unmapped
    ref, _, _ = play_(None)
    ours = set(range(6)) - {2}
    silent = lambda mod, ts: all(not np.abs(mod[-50:, t]).max() and np.abs(ref[-50:, t]).max() for t in ts)
    for name, load_, want in (("fixed 97 % load", lambda b, n: 97 if b < 200 else 50, lambda st: st == ours),
                              ("46 % + 7 % per computed voice", lambda b, n: 46 + 7 * n, lambda st: st and st < ours)):
        mod, stolen, unm = play_(load_)
        spared = set(range(6)) - stolen
        same = all(np.array_equal(ref[:, t], mod[:, t]) for t in spared)
        check(want(stolen) and same and silent(mod, stolen) and not unm,
              f"{label}: overload ({name}): RETROSYN tracks stopped {sorted(t + 1 for t in stolen)}, silent "
              f"afterwards, never the Sampler (track 3); the others {sorted(t + 1 for t in spared)} identical to the "
              "reference")


def skipped(fw, tw, ref, label):
    """A held RETROSYN note (GATE, chord and sweep running) that the governor stops under overload (blocks 20 to 49 at
    97 %), then a trig on another note (block 100): RETROSYN is not called while stopped, restarts from the trig, and
    every block it renders, before and after, is the reference core's, which never skipped a block."""
    rs = fw.views["retrosyn"]
    sy = {k: int(v, 16) for k, v in tw["gov"].items()}
    e = fw.engine(solo=0)
    e.set(0, machine=rs.index, **dict(BASE_KW, shape=1, contour=64, sweep=80, gate=1, decay=110))
    pr = Probe(rs, e, 0)
    cost = 2 * 7 * BLOCK // 100
    clock = {"t": 10_000_000, "fixed": None}

    def read(uc, access, addr, size, value, ud):
        if clock["fixed"] is not None:
            v = clock["fixed"]
        else:
            clock["t"] += cost // 2
            v = clock["t"]
        uc.mem_write(tmx.TIMER, struct.pack(">I", v & M32))
    e.uc.hook_add(UC_HOOK_MEM_READ, read, begin=tmx.TIMER, end=tmx.TIMER + 3)
    for a in GAINS:
        e.uc.mem_write(a, struct.pack(">I", FULL))
    e.uc.mem_write(tms.gs_x(tw, "X_SLOW"), struct.pack(">I", 88 * 65536 // 100))
    out, stolen, called, now = [], [], [], 10_000_000
    for b in range(160):
        pr.block = b
        clock["t"] = max(clock["t"], now)
        if b == 100:
            e.set(0, note=67)
        n0 = len(pr.recs)
        out.append(e.block(1 if b in (1, 100) else 0)[0])
        called.append(len(pr.recs) > n0)
        e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & M32))
        clock["fixed"] = now + (97 if 20 <= b < 50 else 40) * BLOCK // 100
        e.call(sy["audio_end"])
        clock["fixed"] = None
        if e.uc.mem_read(sy["gov_stolen"], 1)[0]:
            stolen.append(b)
        now += BLOCK
    x = np.stack(out)
    gap = [b for b in range(20, 100) if not called[b]]
    trigs = [r["block"] for r in pr.recs if r["trig"]]
    want = ref.simulate(pr.recs)
    ok = (stolen and len(gap) > 30 and not x[gap].any() and trigs[-1] in (100, 101) and np.abs(x[102:]).max() > 1e7
          and np.array_equal(want, pr.got()) and not e.unmapped)
    check(ok, f"{label}: held note stopped by the governor (from block {stolen[:1]}, not computed for {len(gap)} "
              f"blocks), the next trig (block {trigs[-1:]}) restarts it; every rendered block is the reference "
              f"core's ({len(want)} blocks): no GOV_SKIP needed")


def cost(v, acid, label):
    """Instructions per block of one voice (the whole voice loop, minus the same loop without a voice), informative."""
    def run(view, idx, kw, blocks=24):
        e = view.engine(solo=0)
        e.set(0, machine=idx, **kw)
        n = {"i": 0}

        def hk(uc, a, s, u):
            n["i"] += 1
        e.uc.hook_add(UC_HOOK_CODE, hk)
        per = []
        for b in range(blocks):
            i0 = n["i"]
            e.block(1 if b == 1 else 0)
            per.append(n["i"] - i0)
        return int(np.median(per[4:]))
    zero = run(v, tac.OFF, BASE_KW, 6)
    res = {"TONE": run(v, TONE, dict(ta.KW, decay=100)) - zero, "ACID": run(acid, acid.index, dict(ta.KW, decay=100)) - zero}
    for sh, name in enumerate(("pulse", "triangle", "wave", "noise 15", "noise 7", "SNES")):
        res[f"RETROSYN {name}"] = run(v, v.index, dict(BASE_KW, shape=sh, color=127, decay=100)) - zero
    res["RETROSYN SNES + chord + sweep + PUNCH"] = run(v, v.index, dict(BASE_KW, shape=5, contour=90, sweep=80, punch=1,
                                                                        decay=100)) - zero
    print(f"  [INFO] {label}: instructions per block and voice: " + ", ".join(f"{k} {n}" for k, n in res.items()))


# --- everything --------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--syntakt", required=True, help="official Syntakt_OS1.42.syx (or 1.41)")
    ap.add_argument("--eurorack", required=True, help="clone of pichenettes/eurorack (tools/gen_macro.py)")
    ap.add_argument("--quick", action="store_true", help="fewer exact cases")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    codes = list(gr.CODES)
    gs.CATALOG.setdefault("retrosyn", dict(gr.MACHINE, label="RETROSYN"))
    with tempfile.TemporaryDirectory() as d:
        repo = pathlib.Path(args.eurorack).resolve()
        gm.check_sources(repo)
        ctx = dict(cycles=args.cycles, syntakt=args.syntakt, st_img=syntakt.dsp_image(args.syntakt),
                   chord=tmx.chord_tables(stock))
        ref = Ref(pathlib.Path(d))
        tw = load(f"31-{gr.tweak_id()}.json")
        os_tw = load(f"31-{gac.tweak_id(gr.CODES, True, True)}.json")
        tg = load("30-model-tg-st.json")
        make = lambda *ts: tac.Fw(stock, [tg] + list(ts), ctx)
        fw, ref_os = make(tw), make(os_tw)
        ref_eng = make(load(f"31-{gs.tweak_id(codes, tg=True)}.json"))
        rs, label = fw.views["retrosyn"], f"RETROSYN in {tw['id']}"
        print(f"== {tw['id']}: Model-TG, {', '.join(gs.CATALOG[c]['name'] for c in codes)}, MACRO, ACID, RETROSYN "
              f"as machines 8..{fw.nm}")
        print("boot")
        t7.X.bootstrap_depack_ok(args.cycles, fw.tweaks, args.syntakt) or t7.FAIL.append("bootstrap " + tw["id"])
        tgs = {k: int(v, 16) for k, v in tg["symbols"].items()}
        tgs["knob_vec"] = tms.knob_vec_at(tw)
        boot(fw, ref_eng, ref_os, tgs)
        print("interface")
        tac.interface(stock, fw, tw, tgs, make())
        lofi_ui.check_lofi(ref_eng.img, fw.img, fw.payload, fw.views["macro"].index, f"MACRO in {tw['id']}", check,
                           end=fw.blob_end, base_end=ref_eng.blob_end, base_payload=ref_eng.payload,
                           base="the same mods without MACRO, ACID, RETROSYN", after=2)
        print("sound")
        gs.set_base(fw.dest)
        exact(rs, ref, cases(args.quick), label)
        amp_like_tone(rs, label)
        others_unchanged(fw, ref_os, label)
        mixed(fw, ref_os, label)
        six_tracks(rs, label)
        locks(fw, ref, label)
        print("load governor")
        governor(fw, tw, label)
        skipped(fw, tw, ref, label)
        print("cost")
        cost(rs, fw.views["acid"], label)
    fail = t7.FAIL + tms.FAIL
    print("\nALL OK" if not fail else f"\n{len(fail)} FAILURE(S)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
