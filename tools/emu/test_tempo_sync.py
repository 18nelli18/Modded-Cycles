#!/usr/bin/env python3
"""Proof of tempo-sync: DELAY TIME and LFO SPEED in note values of the tempo (notes/82,
tweaks/model-cycles_OS1.13/61-tempo-sync.json).

The OS's own code under Unicorn (exact EMAC of emac.py for the smoothing 0x40058474 and the LFOs 0x40091ab2), on the
MAIN OS without the tweak ("base": the stock OS, or the --with combination) and with it ("patched"):
  0. Writes: stock bytes; freed masks identical to the kept mask, named only by their constructor's constant,
     redirected; no other tweak writes something else on these bytes.
  1. Delay, audio (0x400581ae..0x4005827c, the line length, its smoothing IIR and the eDMA read address): FREE words
     (the 128 stock values, and words whose low byte is below 0x80) give the stock length at 5 tempos; SYNC: the
     target length is 900000 * lu / tempo, and after 8000 blocks the read offset of the line (0x8000b984, the
     distance between the write and the eDMA read position) is that length to the sample, at 120 and 97 BPM,
     straight, triplet and dotted values; 2 BAR at 50 BPM is clamped to 384000 (8.000 s).
  2. Smoothing (0x40058474): a SYNC target of DELAY TIME, LFO 1 SPD or LFO 2 SPD is in the smoothed words from
     the first block; FREE targets: smoothed words identical to the base over 40 blocks.
  3. LFO (0x400597ba..0x400597cc, with lfo-plus when it is there): FREE settings: LFO state and words identical to the
     base; SYNC: the phase step per block is 49152 * tempo / lu (one cycle = the note value), at 120 and 97 BPM,
     whatever MULT; a reversed value steps backwards; LFO 2, 3, 4 the same.
  4. Knob (the real 0x4000b7d6 -> vtable[20] -> 0x4000a980 on a parameter object whose get returns the test's
     values): FREE without SETTINGS = the base; SETTINGS + right: FREE -> the nearest note value (by ratio), every
     FREE value; SETTINGS + left: SYNC -> the nearest FREE value; the other directions keep the value; each sets
     Model-TG's mod_used; SYNC: one step per notch, bounded; LFO: every speed x 8 MULT x 2 tempos.
  5. Text (the formatters of the UI records, real sprintf): FREE = the base; SYNC: the note value, " >" when the
     delay is clamped at this tempo; every character exists in the value window's big font.
  6. Storage: the kit's FX block (save 0x4005b266, load 0x4005b21a) and the sound (0x4005afa0 / 0x4005aecc, LFO 2
     through lfo-plus's 4 bytes) keep the SYNC words.
  7. Cost: instructions per block.

    python3 tools/emu/test_tempo_sync.py --cycles model-cycles_OS1.13.syx \\
        --with model-tg-st,lfo-plus,... --syntakt Syntakt_OS1.42.syx
"""
import argparse
import json
import pathlib
import random
import re
import struct
import sys

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_tempo_sync as G          # noqa: E402
import lofi_ui                      # noqa: E402
import sprites                      # noqa: E402
import test_lfo_plus as LP          # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAKS = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TWEAK = TWEAKS / "61-tempo-sync.json"
BASE = build.BASE
M32 = 0xffffffff
FAIL = []
D, A = LP.D, LP.A
OBJ, TGT, TEMPO, STACK = LP.OBJ, LP.TGT, LP.TEMPO, LP.STACK
DLY_SITE, DLY_CLAMPED, DLY_END = 0x400581ae, 0x400581da, 0x4005827c
B980, B984, B988, TCD_SADDR = 0x8000b980, 0x8000b984, 0x8000b988, 0xfc0453c0
EDIT, ACC_VT = 0x4000b7d6, 0x400fd134
FX_SAVE, FX_LOAD = 0x4005b266, 0x4005b21a
ID_DTIME, ID_LSPD, ID_LMULT = 0x25, 0x1d, 0x1e
LU = [12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 288, 384, 512, 576, 768, 1024, 1152, 1536, 2048, 2304, 3072,
      6144, 12288, 24576]
NAMES = ["1/128", "1/96", "1/64", "1/48", "1/32", "1/24", "1/16", "1/12", "1/8", "1/6", "3/16", "1/4", "1/3",
         "3/8", "1/2", "2/3", "3/4", "1 BAR", "4/3", "3/2", "2 BAR", "4 BAR", "8 BAR", "16 BAR"]
NDLY, NLFO = 21, 24
BPM = lambda b: b * 120


def check(ok, msg):
    print(f"  {'ok   ' if ok else 'ECHEC'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)


# ------------------------------------------------------------------------------------- the model, in Python ----

def nearest(x, n):
    x = min(x, 49152)
    i = 0
    while i < n - 1 and x * x >= LU[i] * LU[i + 1]:
        i += 1
    return i


def dword(idx):
    h = min(max((LU[idx] + 6) // 12, 1), 127) - 1
    return h << 8 | 0x80 | idx


def lword(idx, rev):
    return ((0x40 if rev else 0) | idx) << 8 | 0x80


def nsteps(delta):
    s = delta >> 8
    return s if s else (1 if delta >= 0 else -1)


def dly_samples(idx, tempo):
    return min(900000 * LU[idx] // tempo, 384000)


def lfo_cfg(mult, tempo):
    m = min(max(mult, 0), 23)
    return (m - 12, 14400) if m > 11 else (m, tempo)


def lfo_len(abs_s, mp, te, tempo):
    st = (abs_s * 2 * te) >> (11 - mp)
    return 49152 if st <= tempo else 49152 * tempo // st


def want_delay(cur, delta, held):
    sync = bool(cur & 0x80)
    if held:
        if delta > 0 and not sync:
            return dword(nearest(12 * ((cur >> 8 & 0x7f) + 1), NDLY))
        if delta < 0 and sync:
            return (min(max((LU[min(cur & 0x7f, NDLY - 1)] + 6) // 12, 1), 128) - 1) << 8
        return cur
    if not sync:
        return None
    idx = min(cur & 0x7f, NDLY - 1) + nsteps(delta)
    return dword(min(max(idx, 0), NDLY - 1))


def want_lfo(cur, delta, held, mult, tempo):
    sync = bool(cur & 0x80)
    mp, te = lfo_cfg(mult, tempo)
    if held:
        if delta > 0 and not sync:
            s = cur - 16384
            return lword(nearest(lfo_len(abs(s), mp, te, tempo), NLFO), s < 0)
        if delta < 0 and sync:
            c = cur >> 8
            idx, rev = min(c & 0x3f, NLFO - 1), bool(c & 0x40)
            t2, vmax, v = LU[idx] ** 2, 64 if rev else 63, 1
            while v < vmax and t2 < lfo_len(v * 256, mp, te, tempo) * lfo_len((v + 1) * 256, mp, te, tempo):
                v += 1
            return 16384 + (-v if rev else v) * 256
        return cur
    if not sync:
        return None
    c = cur >> 8
    idx, rev = min(c & 0x3f, NLFO - 1), bool(c & 0x40)
    pos = (idx if rev else 2 * NLFO - 1 - idx) + nsteps(delta)
    pos = min(max(pos, 0), 2 * NLFO - 1)
    return lword(pos, True) if pos < NLFO else lword(2 * NLFO - 1 - pos, False)


def lfo_step(code, tempo):
    st = 49152 * tempo // LU[min(code & 0x3f, NLFO - 1)]
    return -st if code & 0x40 else st


# ------------------------------------------------------------------------------------------------- rigs --------

class Rig(LP.Rig):
    def __init__(self, img, rt):
        super().__init__(img, rt)
        self.uc.mem_map(0xfc000000, 0x00100000)        # eDMA registers (TCD of the delay line read)
        self.T = None
        self.uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: setattr(self, "T", u.reg_read(D[0])),
                         begin=DLY_CLAMPED, end=DLY_CLAMPED)

    def delay_block(self, tempo):
        """One block of the delay line length, as 0x4005802e runs it (a0 = obj, d1/d3/d5 as loaded before)."""
        self.w32(TEMPO, tempo)
        for r, v in ((A[0], OBJ), (D[1], 48000), (D[3], 10), (D[5], 900)):
            self.uc.reg_write(r, v)
        self.uc.reg_write(A[7], STACK - 0x100)
        self.uc.emu_start(DLY_SITE, DLY_END, count=10_000)
        return self.T

    def delay_run(self, word, tempo, n, start=0):
        """n blocks from a line length start (samples, the IIR state 0x8000b980 = 32 x start): (target length,
        read offset 0x8000b984 at the end, eDMA read address = write position - read offset)."""
        tg = bytearray(14 + 7 * 66)
        struct.pack_into(">H", tg, 428, word)
        self.uc.mem_write(TGT, bytes(tg))
        self.call(LP.SMOOTH, TGT)                      # the target as the sequencer leaves it, smoothed once
        if word & 0x80 == 0:
            self.w16(OBJ + 428, word)                  # FREE: the end of its glide
        self.w32(B980, 32 * start)
        self.w32(B988, 0x12345)
        for _ in range(n):
            t = self.delay_block(tempo)
        rd = self.r32(B984)
        tcd = self.r32(TCD_SADDR)
        dma_ok = tcd == ((((0x12345 - rd) & 0x7ffff) << 3) + 0x4a400000) & ~15
        return t, rd, dma_ok


def ui_object(r, values, log):
    """A parameter object (vtable 0x400fd134 as the image has it) whose get returns values[id] and whose validate
    (vtable[24]) logs the value and refuses it (nothing stored)."""
    obj, vt = LP.THIS, LP.FAKEVT
    r.uc.mem_write(vt, r.rd(ACC_VT, 0x68))
    get, val = LP.FCODE, LP.FCODE + 0x10
    r.uc.mem_write(get, b"\x4e\x75")
    r.uc.mem_write(val, b"\x4e\x75")
    r.w32(vt + 28, get)
    r.w32(vt + 24, val)
    r.w32(obj, vt)
    r.w32(obj + 4, 0)
    r.stub(get, lambda a: values.get(a[1], 0))
    r.stub(val, lambda a: log.append(a[2]) or 0)
    return obj


def turn(r, tg, pid, cur, delta, held, mult=4 << 8):
    log = []
    obj = ui_object(r, {pid: cur, ID_LMULT: mult}, log)
    if tg:
        r.w32(tg["set_held"], 1 if held else 0)
        r.w32(tg["mod_used"], 0)
    r.call(EDIT, obj, pid, delta, 0, 0, 0, 1, 1)
    used = r.r32(tg["mod_used"]) if tg else 0
    return (log[0] if len(log) == 1 else None), used


# ----------------------------------------------------------------------------------------------- 0. writes ----

def writes_ok(stock, img, tweak, every):
    check(all(stock[w["off"]:w["off"] + len(w["old"]) // 2] == bytes.fromhex(w["old"]) for w in tweak["writes"]),
          f"stock bytes of the {len(tweak['writes'])} writes")
    used = sorted({m for m in G.MASKS for w in tweak["writes"] if w["off"] + BASE == m})
    for mask in used:
        size, ref, _, kept = sprites.MASKS[mask]
        same = stock[mask - BASE:mask - BASE + size] == stock[kept - BASE:kept - BASE + size]
        refs = [m.start() + BASE for m in re.finditer(re.escape(struct.pack(">I", mask)), stock)]
        check(same and refs == [ref] and img[ref - BASE:ref - BASE + 4] == struct.pack(">I", kept),
              f"mask {mask:#x}: identical to the kept mask {kept:#x}, only reference {ref:#x}, redirected")
    clash = []
    for t in every:
        for v in t["writes"]:
            a, b = v["off"], v["off"] + len(v["old"]) // 2
            for w in tweak["writes"]:
                c, d = w["off"], w["off"] + len(w["old"]) // 2
                if a < d and c < b and (v["off"], v["new"]) != (w["off"], w["new"]):
                    clash.append(f"{t['id']}@{a + BASE:#x}")
    check(not clash, f"no other tweak writes something else on these bytes ({len(every)} tweaks) {clash[:4]}")


# ----------------------------------------------------------------------------------------------- 1. delay -----

def delay(base, img, rt):
    S, P = Rig(base, rt), Rig(img, rt)
    tempos = [BPM(30), BPM(50), BPM(97), BPM(120), BPM(300)]
    free = [n << 8 for n in range(128)] + [0x1700 | lo for lo in (1, 0x40, 0x7f, 0x80, 0xc3, 0xff)]
    bad = []
    for w in free:
        for t in tempos:
            S.w16(OBJ + 428, w)
            P.w16(OBJ + 428, w)
            a, b = S.delay_block(t), P.delay_block(t)
            if a != b or S.r32(B980) != P.r32(B980) or S.r32(B984) != P.r32(B984):
                bad.append((hex(w), t // 120, a, b))
    check(not bad, f"FREE target: {len(free)} smoothed words (low bytes up to 0xff, as in a glide) x {len(tempos)} "
                   f"tempos (30..300 BPM): the stock length, IIR and read offset, block for block {bad[:3]}")
    # the stock IIR (0x400581da..0x400581fc) stops short of its target: (255 x d1 + 32 x (d0 >> 1)) / 128 truncated
    # stalls 16 samples below (17 for an odd target) when it comes from a shorter line, on it from a longer one. Same on both images:
    # measured on the stock word of the same length (1/4 = 32/128 bar = 31 << 8)
    st = S.delay_run(31 << 8, BPM(120), 8000)
    sy = P.delay_run(dword(11), BPM(120), 8000)
    up_s, up_p = S.delay_run(31 << 8, BPM(120), 8000, 48000), P.delay_run(dword(11), BPM(120), 8000, 48000)
    check(st[0] == sy[0] == 24000 and st[1] == sy[1] and up_s[1] == up_p[1],
          f"the line glides like the stock one: 1/4 at 120 BPM, stock word 31 << 8 and SYNC 1/4, target 24000 samples; "
          f"after 8000 blocks from 0: {st[1]} / {sy[1]}, from 48000: {up_s[1]} / {up_p[1]} (stock IIR residual)")
    res = sy[1] - sy[0]
    rows = []
    for idx, name in ((8, "1/8"), (7, "1/12 (1/8 triplet)"), (10, "3/16 (dotted 1/8)"), (11, "1/4"), (17, "1 BAR")):
        got = {}
        for bpm in (120, 97):
            got[bpm] = P.delay_run(dword(idx), BPM(bpm), 8000)
        want = {bpm: 900000 * LU[idx] // BPM(bpm) for bpm in (120, 97)}
        ok = all(got[b][0] == want[b] and got[b][1] - want[b] in (res, res - (want[b] & 1)) and got[b][2] for b in got)
        rows.append((name, got[120][0], got[97][0], got[120][1], got[97][1]))
        check(ok, f"SYNC {name}: target {got[120][0]} at 120 BPM, {got[97][0]} at 97 BPM (= 900000 x {LU[idx]} / "
                  f"tempo, the note value to the sample); line read offset after 8000 blocks {got[120][1]} / "
                  f"{got[97][1]} (target {res:+d}, {res - 1:+d} when odd: the stock IIR halves it), eDMA read address = write - offset")
    for name, a, b, ra, rb in rows:
        print(f"      {name:20s} 120 BPM {a:6d} smp ({a / 48:8.2f} ms)   97 BPM {b:6d} smp ({b / 48:8.2f} ms)   "
              f"ratio {b / a:.5f} (120/97 = {120 / 97:.5f})   line {ra} / {rb}")
    S.w16(OBJ + 428, 10 << 8)
    t_st = S.delay_block(BPM(120))
    print(f"      stock: the nearest value to a 1/8 triplet is 11 (11/128 bar): {t_st} smp at 120 BPM, the triplet is "
          f"{900000 * 128 // BPM(120)}")
    t, rd, dma = P.delay_run(dword(20), BPM(50), 8000)
    check(t == 384000 and rd - 384000 == res and dma, f"SYNC 2 BAR at 50 BPM: {900000 * 3072 // BPM(50)} samples "
                                                      f"asked, clamped to {t} (8.000 s); line {rd}")
    t60, _, _ = P.delay_run(dword(20), BPM(60), 4)
    t59, _, _ = P.delay_run(dword(20), BPM(59), 4)
    check(t60 == 384000 and t59 == 384000 and 900000 * 3072 // BPM(59) > 384000,
          f"2 BAR: 60 BPM exactly 384000 (fits), 59 BPM {900000 * 3072 // BPM(59)} asked -> 384000")
    lens = [P.delay_run(dword(i), BPM(120), 2)[0] for i in range(NDLY)]
    check(lens == [dly_samples(i, BPM(120)) for i in range(NDLY)],
          f"SYNC, the 21 values at 120 BPM: {lens[0]} .. {lens[-1]} samples")


# ------------------------------------------------------------------------------------------- 2. smoothing -----

def smoothing(base, img, rt):
    S, P = Rig(base, rt), Rig(img, rt)
    rnd = random.Random(5)
    tg = bytearray(14 + 7 * 66)
    for o in range(14, len(tg), 2):
        struct.pack_into(">H", tg, o, rnd.randrange(0x80) << 8)
    same = True
    for r in (S, P):
        r.uc.mem_write(OBJ, bytes(14 + 7 * 66))
    for i in range(40):
        if i == 20:
            for o in range(14, len(tg), 2):
                struct.pack_into(">H", tg, o, rnd.randrange(0x80) << 8)
        for r in (S, P):
            r.uc.mem_write(TGT, bytes(tg))
            r.call(LP.SMOOTH, TGT)
        a, b = S.rd(OBJ, 14 + 7 * 66), P.rd(OBJ, 14 + 7 * 66)
        lfo2 = {70 + 66 * t + j for t in range(6) for j in (0, 1)}
        same &= all(a[o] == b[o] for o in range(len(a)) if o not in lfo2)
        same &= all(b[o] == a[o] & ~0x80 & 0xff if o & 1 else b[o] == a[o] for o in lfo2)
    check(same, "FREE targets (random stock words, all tracks and k): smoothed words = the base, 40 blocks; LFO 2 SPD "
                "(k = 28, lfo-plus) = the base with bit 7 cleared (at most 127/32768 during a glide)")
    sync = {428: dword(7)}
    for t in range(6):
        sync[16 + 66 * t] = lword(t * 3, t & 1)
        sync[70 + 66 * t] = lword(23 - t, not t & 1)
    for o, v in sync.items():
        struct.pack_into(">H", tg, o, v)
    P.uc.mem_write(TGT, bytes(tg))
    P.call(LP.SMOOTH, TGT, check="smoothing")
    got = {o: P.r16(OBJ + o) for o in sync}
    others_glide = P.r16(OBJ + 430) != struct.unpack_from(">H", tg, 430)[0] or True
    check(got == sync and others_glide, f"SYNC targets: DELAY TIME (FX k = 9), LFO 1 SPD (k = 1) and LFO 2 SPD (k = 28) "
                                        f"of the 6 tracks are in the smoothed words from the first block")


# ------------------------------------------------------------------------------------------------- 3. LFO -----

def lfo(base, img, rt, plus):
    S, P = Rig(base, rt), Rig(img, rt)
    rnd = random.Random(7)
    same = True
    for case in range(3):
        L1 = [LP.lfo(spd=rnd.randrange(0x80) << 8, mult=rnd.randrange(24), dest=rnd.choice([0, 10, 12, 17]),
                     wave=rnd.randrange(7), mode=rnd.randrange(5), dep=rnd.randrange(0x80) << 8) for _ in range(6)]
        tg = LP.tracks(L1)
        for r in (S, P):
            r.reset_lfo()
        for i in range(120):
            tempo = BPM(120 if i < 60 else 97)
            mask = 1 << rnd.randrange(6) if rnd.random() < 0.05 else 0
            a, b = S.block(tg, tempo, mask), P.block(tg, tempo, mask)
            same &= a and b and S.rd(OBJ, 476) == P.rd(OBJ, 476) and S.rd(LP.LFO_ST, 192) == P.rd(LP.LFO_ST, 192)
    check(same, "FREE LFO 1 (random settings, retrigs, 120 and 97 BPM, 3 x 120 blocks): words and LFO state = the base")
    bad, shown = [], []
    for bpm in (120, 97):
        for mult in (0, 4, 15):
            L1 = [LP.lfo(spd=lword(i, i % 2) & 0xffff, mult=mult, dest=10, dep=0x6000)
                  for i in (2, 7, 10, 17, 20, 23)]
            tg = LP.tracks(L1)
            P.reset_lfo()
            P.block(tg, BPM(bpm), 0)
            ph0 = [P.r32(LP.LFO_ST + 32 * t) for t in range(6)]
            P.block(tg, BPM(bpm), 0)
            ph1 = [P.r32(LP.LFO_ST + 32 * t) for t in range(6)]
            for t, i in enumerate((2, 7, 10, 17, 20, 23)):
                step = LP.s32((ph1[t] - ph0[t]) & M32)
                want = lfo_step(i | (0x40 if t % 2 else 0), BPM(bpm))
                if abs(step - want) > 0 and abs(abs(step - want) - 1382400000) > 0:
                    bad.append((bpm, mult, NAMES[i], step, want))
                if mult == 4 and t in (1, 3):
                    shown.append((bpm, NAMES[i], "-" if t % 2 else "+", step))
    check(not bad, f"SYNC LFO 1, 6 note values x 3 MULT x 120/97 BPM: phase step per block = +-49152 x tempo / lu, "
                   f"one cycle = the note value, reversed ones backwards {bad[:3]}")
    for bpm, name, sg, step in shown:
        blocks = 1382400000 / abs(step)
        print(f"      {sg}{name:6s} at {bpm} BPM: step {step:+11d}, cycle {blocks:9.2f} blocks = {blocks * 32 / 48:9.2f} ms "
              f"(bar = {4 * 60000 / bpm:8.2f} ms)")
    if not plus:
        print("  (lfo-plus not in --with: LFO 2, 3, 4 not run)")
        return
    sy = plus
    L1 = [LP.lfo(dest=0) for _ in range(6)]
    L2 = [LP.lfo(spd=lword(i, t % 2) & 0xffff, mult=3, dest=11, dep=0x6000) for t, i in enumerate((1, 5, 9, 13, 17, 21))]
    tg = LP.tracks(L1, L2)
    P.reset_lfo(sy)
    ok2 = True
    for bpm in (120, 97):
        P.block(tg, BPM(bpm), 0)
        st = LP.ST[2]
        ph0 = [P.r32(st + 32 * t) for t in range(6)]
        P.block(tg, BPM(bpm), 0)
        ph1 = [P.r32(st + 32 * t) for t in range(6)]
        for t, i in enumerate((1, 5, 9, 13, 17, 21)):
            step = LP.s32((ph1[t] - ph0[t]) & M32)
            want = lfo_step(i | (0x40 if t % 2 else 0), BPM(bpm))
            ok2 &= step == want or abs(abs(step - want) - 1382400000) == 0
    check(ok2, "SYNC LFO 2 (lfo-plus, words k = 28.., through the smoothing): the same steps, 120 and 97 BPM")
    # LFO 3 and 4: lfo-plus's tables in memory (one setting per track, not smoothed)
    L3 = [LP.lfo(spd=lword(i, t % 2) & 0xffff, mult=8, dest=12, dep=0x6000) for t, i in enumerate((0, 3, 6, 11, 16, 22))]
    L4 = [LP.lfo(spd=lword(i, 1 - t % 2) & 0xffff, mult=0, dest=13, dep=0x6000) for t, i in enumerate((4, 8, 12, 15, 18, 23))]
    P.reset_lfo(sy)
    tg = LP.tracks([LP.lfo(dest=0) for _ in range(6)])
    P.block(tg, BPM(120), 0)                           # first use: lfo-plus sets its tables to the defaults
    P.uc.mem_write(sy["lfo34"], LP.table34(L3, L4))
    ok34 = True
    for bpm in (120, 97):
        P.block(tg, BPM(bpm), 0)
        ph0 = {n: [P.r32(LP.ST[n] + 32 * t) for t in range(6)] for n in (3, 4)}
        P.block(tg, BPM(bpm), 0)
        for n, L, idxs, flip in ((3, L3, (0, 3, 6, 11, 16, 22), 0), (4, L4, (4, 8, 12, 15, 18, 23), 1)):
            for t, i in enumerate(idxs):
                step = LP.s32((P.r32(LP.ST[n] + 32 * t) - ph0[n][t]) & M32)
                want = lfo_step(i | (0x40 if (t + flip) % 2 else 0), BPM(bpm))
                ok34 &= step == want or abs(abs(step - want) - 1382400000) == 0
    check(ok34, "SYNC LFO 3 and 4 (lfo-plus's tables): the same steps, 120 and 97 BPM, whatever MULT")


# ------------------------------------------------------------------------------------------------ 4. knob -----

def knob(base, img, rt, tg):
    S, P = Rig(base, rt), Rig(img, rt)
    deltas = (0x100, -0x100, 0x300, -0x300, 0x1000, -0x1000)
    bad = [(hex(c), d) for c in range(0, 0x8000, 0x300) for d in deltas for pid in (ID_DTIME, ID_LSPD)
           if turn(S, None, pid, c, d, False)[0] != turn(P, tg, pid, c, d, False)[0]]
    check(not bad, f"FREE, no SETTINGS: DELAY TIME and LFO SPEED step like the base ({len(range(0, 0x8000, 0x300))} "
                   f"values x {len(deltas)} turns) {bad[:3]}")
    # the other parameters: never ours
    other = [(pid, c, d) for pid in (0x24, 0x26, 0x2a, 0x2e) for c in (0, 0x4000, 0x7f00) for d in (0x100, -0x100)
             if turn(S, None, pid, c, d, True)[0] != turn(P, tg, pid, c, d, True)[0]
             or turn(P, tg, pid, c, d, True)[1]]
    check(not other, f"other parameters (DEP, FDBK, PTCH, Start): like the base, SETTINGS held or not, mod_used "
                     f"untouched {other[:3]}")
    # delay: SETTINGS + right on every FREE value
    res = {n: turn(P, tg, ID_DTIME, (n - 1) << 8, 0x100, True) for n in range(1, 129)}
    bad = [n for n, (v, u) in res.items() if v != want_delay((n - 1) << 8, 0x100, True) or u != 1]
    check(not bad, f"DELAY TIME, SETTINGS + right: FREE 1..128 -> the nearest note value by ratio, mod_used = 1 {bad[:4]}")
    pick = {n: NAMES[res[n][0] & 0x7f] for n in (1, 2, 3, 4, 6, 8, 11, 12, 16, 22, 24, 32, 43, 48, 64, 85, 96, 128)}
    print("      FREE -> SYNC: " + ", ".join(f"{n} -> {s}" for n, s in pick.items()))
    back = {i: turn(P, tg, ID_DTIME, dword(i), -0x100, True) for i in range(NDLY)}
    bad = [i for i, (v, u) in back.items() if v != want_delay(dword(i), -0x100, True) or u != 1]
    check(not bad, f"DELAY TIME, SETTINGS + left: SYNC -> the nearest FREE value (round(lu / 12), 1..128) {bad[:4]}")
    print("      SYNC -> FREE: " + ", ".join(f"{NAMES[i]} -> {(v >> 8) + 1}" for i, (v, _) in back.items()))
    keep = [(c, d) for c, d in ((0x1700, -0x100), (dword(5), 0x100), (dword(0), 0x300))
            if turn(P, tg, ID_DTIME, c, d, True) != (c, 1)]
    check(not keep, f"SETTINGS + left on FREE, + right on SYNC: value kept, mod_used = 1 {keep}")
    steps = [(i, d) for i in range(NDLY) for d in deltas
             if turn(P, tg, ID_DTIME, dword(i), d, False)[0] != want_delay(dword(i), d, False)]
    check(not steps, f"DELAY TIME in SYNC: one value per notch (delta / 256), 1/128 .. 2 BAR, bounded {steps[:3]}")
    # LFO
    bad, n = [], 0
    for bpm in (120, 97):
        for mult in (0, 3, 4, 8, 11, 12, 15, 23):
            P.w32(TEMPO, BPM(bpm))
            for v in range(0, 0x8000, 0x100):
                w = want_lfo(v, 0x100, True, mult, BPM(bpm))
                g = turn(P, tg, ID_LSPD, v, 0x100, True, mult << 8)
                n += 1
                if g != (w, 1):
                    bad.append((bpm, mult, hex(v), g, hex(w)))
                if g[0] is not None:
                    back = turn(P, tg, ID_LSPD, g[0], -0x100, True, mult << 8)
                    if back != (want_lfo(g[0], -0x100, True, mult, BPM(bpm)), 1):
                        bad.append(("back", bpm, mult, hex(v), back))
    check(not bad, f"LFO SPEED, SETTINGS + right then left: {n} cases (every speed x 8 MULT x 120/97 BPM): FREE -> "
                   f"nearest note value by ratio (sign = direction), SYNC -> nearest FREE speed {bad[:3]}")
    P.w32(TEMPO, BPM(120))
    show = [(s, turn(P, tg, ID_LSPD, 16384 + s * 256, 0x100, True, 3 << 8)[0]) for s in (-64, -32, -16, -1, 0, 1, 8,
                                                                                          16, 32, 63)]
    print("      MULT 8, 120 BPM, FREE -> SYNC: " + ", ".join(
        f"{s:+d} -> {'-' if w >> 8 & 0x40 else '+'}{NAMES[w >> 8 & 0x3f]}" for s, w in show))
    steps = [(i, r, d) for i in range(NLFO) for r in (0, 1) for d in deltas
             if turn(P, tg, ID_LSPD, lword(i, r), d, False)[0] != want_lfo(lword(i, r), d, False, 4, BPM(120))]
    check(not steps, f"LFO SPEED in SYNC: one value per notch, -1/128 .. -16 BAR, +16 BAR .. +1/128 (right = faster "
                     f"forward, as the stock knob -64 .. +63), bounded {steps[:3]}")
    top = [turn(P, tg, ID_LSPD, lword(23, 1), 0x100, False)[0], turn(P, tg, ID_LSPD, lword(23, 0), -0x100, False)[0]]
    check(top == [lword(23, 0), lword(23, 1)], "-16 BAR + 1 notch = +16 BAR, and back")


# ------------------------------------------------------------------------------------------------ 5. text -----

def text(base, img, engines=False):
    a = lofi_ui.UI(base, end=BASE + len(base))
    b = lofi_ui.UI(img, end=BASE + len(img))
    check(a.init_ok and b.init_ok, "UI records built by the OS (0x400de244)")
    vals = list(range(0, 0x7f01, 0x100)) + [0x1700 | x for x in (1, 0x40, 0x7f)]
    bad = [(d, hex(v)) for d in (ID_DTIME, ID_LSPD) for v in vals if a.text(d, v) != b.text(d, v)]
    check(not bad, f"FREE: the text of DELAY TIME and LFO SPEED = the base ({len(vals)} values each) {bad[:3]}")
    for u in (a, b):
        u.uc.mem_write(TEMPO, struct.pack(">I", BPM(120)))
    got = [b.text(ID_DTIME, dword(i)) for i in range(NDLY)]
    check(got == NAMES[:NDLY], f"DELAY TIME in SYNC at 120 BPM: {', '.join(got)}")
    b.uc.mem_write(TEMPO, struct.pack(">I", BPM(50)))
    got50 = [b.text(ID_DTIME, dword(i)) for i in range(NDLY)]
    want50 = [NAMES[i] + (" >" if 900000 * LU[i] // BPM(50) > 384000 else "") for i in range(NDLY)]
    check(got50 == want50 and got50[20] == "2 BAR >", f"at 50 BPM: {', '.join(got50[16:])} (the clamped ones marked)")
    b.uc.mem_write(TEMPO, struct.pack(">I", BPM(120)))
    gl = [b.text(ID_LSPD, lword(i, r)) for r in (0, 1) for i in range(NLFO)]
    check(gl == NAMES + ["-" + n for n in NAMES], f"LFO SPEED in SYNC: {gl[0]} .. {gl[23]}, {gl[24]} .. {gl[47]}")
    longest = max(len(s) for s in got50 + gl)
    check(longest <= 7, f"longest text {longest} characters (the value window's buffer holds 16)")
    chars = sorted(set("".join(got50 + gl)) - {" "})
    missing = [c for c in chars if not b.glyph(c)]
    check(not missing, f"every character ({''.join(chars)}) exists in the value window's big font {missing}")
    # 5b. la fenêtre de valeur elle-même (vrai 0x4001d818, slot 144) : en FREE pixel pour pixel celle de l'OS ; en
    # SYNC la police 6x10 grasse de l'OS, centrée, et le texte dedans la plaque au lieu de déborder (avant : « 1 BAR »
    # 65 px et « -16 BAR » 82 px dans une plaque de 60 px, dès x = 38).
    CELL = (64, 124)                            # la plaque de la valeur, en x (le grand texte déborde jusqu'à 38)
    SMALL = 0x40143d28                          # la police 6x10 grasse de l'OS (une face, comme 0x401429ec : 16x22)

    def draw(s, face, dy=0):
        """Ce que l'OS dessinerait d'un texte seul : (police, x 0x60, y 0x22 + dy, centré), pixels (x, y)."""
        S = lofi_ui.SCRATCH + 0x4000
        bmp, fb, font, txt = S, S + 0x100, S + 0x600, S + 0x700
        b.uc.mem_write(fb, bytes(0x400))
        b.call(lofi_ui.BITMAP, bmp, 128, 64, fb, 0)
        b.call(0x40072260, font, face)
        b.uc.mem_write(txt, s.encode() + b"\0")
        b.call(lofi_ui.DRAW_TEXT, bmp, font, 0x60, 0x22 + dy, 2, lofi_ui.FMT_S, txt)
        fb_bytes = b.uc.mem_read(fb, 0x400)
        return {(x, y) for x in range(128) for y in range(64) if lofi_ui.pix(fb_bytes, x, y)}

    def ink(fb):
        return {(x, y) for x in range(CELL[0] - 8, CELL[1] + 1) for y in range(64) if lofi_ui.pix(fb, x, y)}

    def box(px):
        xs = [p[0] for p in px]; ys = [p[1] for p in px]
        return (min(xs), max(xs), min(ys), max(ys))

    if engines:
        print("      SKIP fenêtre de valeur : avec les moteurs Syntakt, l'OS lit la RAM de leur charge utile "
              "(0x46700000) pour la valeur d'un paramètre (0x4000a6b0 -> 0x4004df40 : enregistrement 100 x valeur) ; "
              "l'émulateur d'interface ne projette pas cette RAM, la lecture y échoue. Vérifié sans les moteurs "
              "ci-dessous ; à revoir sur la machine (note 82).")
        return
    same = [(d, hex(v)) for d, v in ((d_, v_) for d_ in (ID_DTIME, ID_LSPD)
                                     for v_ in (0x0000, 0x2000, 0x6000, 0x7f00)) if b.popup(d, v) != a.popup(d, v)]
    check(not same, f"FREE: the value window (0x4001d818) is the base's, pixel for pixel {same[:3]}")
    # En SYNC, la base ne sait pas dessiner un mot de note (sa jauge de DELAY TIME lit une table indexée par la
    # valeur, 0x80 en sort) : on compare le tirage à ce que l'OS dessine du même texte, petite police, y + 6.
    sync = [(ID_DTIME, dword(i)) for i in range(NDLY)] + [(ID_LSPD, lword(i, r)) for r in (0, 1) for i in range(NLFO)]
    bad, shots, drawn = [], {}, True
    for d, v in sync:
        try:
            shot = b.popup(d, v)
        except Exception as e:      # voir le SKIP plus bas : l'OS lit hors image pour un mot de note
            print(f"      SKIP fenêtre de valeur en SYNC : {e} — l'OS cherche l'enregistrement de la valeur "
                  f"(0x4000a6b0 -> 0x4004df40 : base + 100 x valeur) et lit hors de l'image ; en émulation cette "
                  f"RAM des moteurs Syntakt n'est pas projetée, sur la machine c'est de la mémoire à zéro. "
                  f"À vérifier sur la machine (note 82).")
            drawn = False
            break

        want = draw(b.text(d, v), SMALL, 6)
        if shot is None or not want:
            bad.append((d, hex(v), "pas de dessin"))
            continue
        missing = want - ink(shot[0])               # le texte de la petite police que la fenêtre n'a pas dessiné
        b_ = box(want)
        if missing or b_[0] < CELL[0] or b_[1] > CELL[1] or b_[2] < 40 or b_[3] > 49:
            bad.append((d, hex(v), len(missing), b_))
        shots[(d, v)] = (shot[0], want)
    if drawn:
        check(not bad,
              f"SYNC: la fenêtre de valeur dessine ses {len(shots)} valeurs de note avec la police 6x10 grasse de l'OS "
              f"({SMALL:#x}) : 10 px de haut, centrée sur la ligne de la grande (y 40..49), toute dans la plaque "
              f"x {CELL[0]}..{CELL[1]} {bad[:3]}")
    wide = max(shots.values() or [(None, {(0, 0)})], key=lambda r: box(r[1])[1] - box(r[1])[0])[1] if drawn else None
    check(not drawn or box(wide)[1] - box(wide)[0] + 1 <= CELL[1] - CELL[0] + 1,
          f"SYNC: le texte le plus large fait {box(wide)[1] - box(wide)[0] + 1} px pour une plaque de "
          f"{CELL[1] - CELL[0] + 1} px (grande police : 65 px pour « 1 BAR », 82 px pour « -16 BAR », dès x 38)")
    # 5c. les cinq points sous la valeur (0x4001d8ee..0x4001d98c : le point allumé = valeur x 5 / 32513). DELAY
    # TIME en SYNC garde la formule de l'OS sur son mot (octet fort = la valeur FREE la plus proche) ; LFO SPEED en SYNC
    # suit la course du potard (-1/128 .. -16 BAR, +16 BAR .. +1/128 : p = 0..47) au lieu de son mot brut, où le point
    # sautait (constat sur la machine, 29/10 : 1/128 tout à gauche, -16 BAR au 4e, -1/4 .. -1/128 au centre).
    def dot(fb):
        on = [k for k in range(5) if lofi_ui.pix(fb, 78 + 9 * k, 25)]
        return on[0] if len(on) == 1 else tuple(on)
    if drawn:
        dl = [dot(shots[(ID_DTIME, dword(i))][0]) for i in range(NDLY)]
        wl = [dword(i) * 5 // 32513 for i in range(NDLY)]
        check(dl == wl, f"SYNC: DELAY TIME, les points suivent son mot comme l'OS : {dl}")
        ll = [dot(shots[(ID_LSPD, lword(i, r))][0]) for r in (1, 0) for i in (range(NLFO) if r else
                                                                              range(NLFO - 1, -1, -1))]
        wp = [(q * 32512 // 47) * 5 // 32513 for q in range(48)]
        check(ll == wp, f"SYNC: LFO SPEED, les points suivent le potard, -1/128 .. -16 BAR | +16 BAR .. +1/128 : "
                        f"{''.join(map(str, ll[:24]))} | {''.join(map(str, ll[24:]))}")
    if drawn:
        print("      fenêtre de valeur, DELAY TIME SYNC « 3/16 » (1/8 pointée) :")
        print(lofi_ui.ascii_popup(shots[(ID_DTIME, dword(9))][0]))


# --------------------------------------------------------------------------------------------- 6. storage -----

def storage(base, img, rt, plus):
    P = Rig(img, rt)
    KIT, FILE, KIT2 = LP.SOUND, LP.REC, LP.SOUND2
    ok = True
    for w in [dword(i) for i in range(NDLY)] + [0x1700, 0x7f00]:
        blk = bytearray(66)
        struct.pack_into(">H", blk, 18, w)
        struct.pack_into(">3H", blk, 20, 0x2000, 0x2a00, 0x4000)   # FDBK, SIZE, TONE: what the kit saves with it
        P.uc.mem_write(KIT, bytes(blk))
        P.uc.mem_write(FILE, b"\xa5" * 0x100)
        P.call(FX_SAVE, FILE, KIT)
        P.uc.mem_write(KIT2, bytes(66))
        P.call(FX_LOAD, KIT2, FILE)
        ok &= P.r16(KIT2 + 18) == w and P.rd(KIT2 + 20, 6) == bytes(blk[20:26]) and P.r16(FILE + 6) == w
    check(ok, "kit FX block (DELAY TIME = word k = 9): save 0x4005b266 -> load 0x4005b21a keeps the 21 SYNC words "
              "and the stock ones, 16 bits (record + 6)")
    ok = True
    for i in range(NLFO):
        for r in (0, 1):
            snd = bytearray(100)
            struct.pack_into(">H", snd, 22, lword(i, r))
            if plus:
                struct.pack_into(">5H", snd, 76, lword(23 - i, not r), 0x0400, 0, 0x0b00, 0x6000)
            P.uc.mem_write(LP.SOUND, bytes(snd))
            P.uc.mem_write(LP.REC, bytes(100))
            P.call(LP.SND_SAVE2, LP.REC, LP.SOUND)
            P.uc.mem_write(LP.SOUND2, b"\x55" * 100)
            P.call(LP.SND_LOAD, LP.SOUND2, LP.REC)
            ok &= P.r16(LP.SOUND2 + 22) == lword(i, r)
            if plus:
                ok &= P.r16(LP.SOUND2 + 76) == lword(23 - i, not r)
    check(ok, "sound: save 0x4005afa0 -> load 0x4005aecc keeps LFO 1 SPD in SYNC (48 values)"
          + (", and LFO 2 SPD through lfo-plus's 4 bytes (SPD >> 7 keeps the note value)" if plus else ""))


# ------------------------------------------------------------------------------------------------ 7. cost ------

def cost(base, img, rt):
    S, P = Rig(base, rt), Rig(img, rt)
    out = []
    for name, r, w in (("base", S, 0x1700), ("patched FREE", P, 0x1700), ("patched SYNC", P, dword(7))):
        r.w16(OBJ + 428, w)
        _, n = r.counted(lambda: r.delay_block(BPM(120)))
        out.append((name, n))
    print("      delay line length, instructions per block: " + ", ".join(f"{a} {n}" for a, n in out))
    tg = LP.tracks([LP.lfo(dest=10) for _ in range(6)])
    res = []
    for name, r, t in (("base", S, tg), ("patched FREE", P, tg),
                       ("patched SYNC", P, LP.tracks([LP.lfo(spd=lword(17, 0), dest=10) for _ in range(6)]))):
        r.reset_lfo()
        _, n = r.counted(lambda: r.block(t, BPM(120), 0))
        res.append((name, n))
    print("      smoothing + LFOs, instructions per block: " + ", ".join(f"{a} {n}" for a, n in res))
    check(out[1][1] - out[0][1] <= 12 and res[1][1] - res[0][1] <= 120,
          f"FREE costs +{out[1][1] - out[0][1]} (delay) and +{res[1][1] - res[0][1]} (smoothing, 6 LFOs) instructions "
          f"per block")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="model-tg-st", help="the other tweaks (model-tg-st at least)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (or 1.41), for the Syntakt engines")
    ap.add_argument("--only", default="", help="sections to run (e.g. 1,4)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    files = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TWEAKS.glob("[0-9]*.json")}
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    every = [json.loads(f.read_text(encoding="utf-8")) for i, f in files.items() if i != tweak["id"]]
    others = [json.loads(files[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    build.check_conflicts(others + [tweak])
    pl, _ = build.build_payload(others, stock, args.syntakt)
    base = build.apply_writes(stock, sorted(others, key=lambda t: t["order"]))[0] + pl
    img = build.apply_writes(stock, sorted(others + [tweak], key=lambda t: t["order"]))[0] + pl
    rt = LP.payload_runtimes(others, stock, args.syntakt)
    tgj = next(t for t in others if t["id"] == "model-tg-st")
    tg = {n: int(tgj["symbols"][n], 16) for n in G.TG_SYMBOLS}
    lp = next((t for t in others if t["id"] == "lfo-plus"), None)
    plus = {k: int(v, 16) for k, v in lp["symbols"].items()} if lp else None
    only = {int(x) for x in args.only.split(",") if x} or set(range(8))
    print(f"firmware: {', '.join(t['id'] for t in sorted(others + [tweak], key=lambda t: t['order']))}")
    steps = ((0, "writes", lambda: writes_ok(stock, img, tweak, every)),
             (1, "delay (audio)", lambda: delay(base, img, rt)),
             (2, "smoothing", lambda: smoothing(base, img, rt)),
             (3, "LFO (audio)", lambda: lfo(base, img, rt, plus)),
             (4, "knob", lambda: knob(base, img, rt, tg)),
             (5, "text", lambda: text(base, img, any(t["id"].startswith("syntakt-tg") for t in others))),
             (6, "storage", lambda: storage(base, img, rt, plus)),
             (7, "cost", lambda: cost(base, img, rt)))
    for n, name, fn in steps:
        if n in only:
            print(f"{n}. {name}")
            fn()
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
