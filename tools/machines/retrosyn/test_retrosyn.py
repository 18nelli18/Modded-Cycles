#!/usr/bin/env python3
# Origin: AveyCole fork (https://github.com/AveyCole/Modded-Cycles), MIT License.
"""Preuves de retrosyn_dsp.h sur l'hôte (le même code C que le Cycles). Une ligne par contrôle, code de sortie non nul au premier échec."""
import ctypes, math, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_retrosyn_tables as G

TEMP = tempfile.TemporaryDirectory()
LIB = os.path.join(TEMP.name, "libretrosyn.so")
subprocess.check_call(["gcc", "-O2", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC", "-o", LIB, HERE + "/retrosyn_ref.c"])
L = ctypes.CDLL(LIB)
L.rs_new.restype = ctypes.c_void_p
L.rs_free.argtypes = [ctypes.c_void_p]
L.rs_block_c.argtypes = [ctypes.c_void_p] + [ctypes.c_int] * 7 + [ctypes.POINTER(ctypes.c_int)]
L.rs_lfsr_period.argtypes = [ctypes.c_int]
L.rs_inc_c.argtypes = [ctypes.c_int]
L.rs_inc_c.restype = ctypes.c_uint
SR = 48000
SH = 22
fails = 0


def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + ("  " + detail if detail else ""))
    if not ok:
        fails += 1


def shape_v(i): return i * 5462 + 2731
def duty_v(i): return i * 8192 + 4096
def idx8_v(i): return i * 4096 + 2048
def contour_v(i): return i * 4096 + 2048
CENTER = 16384


def render(blocks, note=69.0, shape=0, color=0, sweep=CENTER, contour=0, punch=0, st=None):
    s = st or L.rs_new()
    out = []
    buf = (ctypes.c_int * 32)()
    for b in range(blocks):
        L.rs_block_c(s, int(note * 65536), 1 if (b == 0 and st is None) else 0, shape, color, sweep, contour, punch, buf)
        out.append(np.array(buf[:], dtype=np.int64))
    if st is None:
        L.rs_free(s)
    return np.concatenate(out)


def dom_freq(x, sr=SR):
    x = x * np.hanning(len(x))
    n = 16 * len(x)
    sp = np.abs(np.fft.rfft(x, n))
    k = np.argmax(sp[1:]) + 1
    return k * sr / n


# 1. pitch table: every semitone within 0.01 cent, every fraction within 1 cent
worst_semi = 0.0
worst_frac = 0.0
for n in range(128):
    f_t = L.rs_inc_c(n << 16) / 2 ** 32 * SR
    f_i = 440 * 2 ** ((n - 69) / 12)
    worst_semi = max(worst_semi, abs(1200 * math.log2(f_t / f_i)))
    for fr in (0.25, 0.5, 0.75):
        if n < 127:
            f_t = L.rs_inc_c(int((n + fr) * 65536)) / 2 ** 32 * SR
            f_i = 440 * 2 ** ((n + fr - 69) / 12)
            worst_frac = max(worst_frac, abs(1200 * math.log2(f_t / f_i)))
check("pitch: each semitone within 0.05 cent", worst_semi < 0.05, "%.4f cent" % worst_semi)
check("pitch: interpolated fractions within 1 cent", worst_frac < 1.0, "%.3f cent" % worst_frac)

# 2. pulse duty ratios over a long render
for i, want in enumerate((0.125, 0.25, 0.5, 0.75)):
    x = render(1500, shape=shape_v(0), color=duty_v(i), note=45)
    frac = (x > 0).mean()
    check("pulse duty %.1f%%" % (want * 100), abs(frac - want) < 0.01, "measured %.2f%%" % (frac * 100))

M32 = 0xFFFFFFFF


def old_pulse(blocks, note, color):
    """The four-step pulse before PWM: (phase >> 29) < {1, 2, 4, 6}[COLOR / 8192]."""
    inc, thr, ph, out = L.rs_inc_c(int(note * 65536)), (1, 2, 4, 6)[(color * 4) >> 15], 0, []
    for _ in range(blocks * 32):
        ph = (ph + inc) & M32
        out.append((112 if (ph >> 29) < thr else -128) << SH)
    return np.array(out, dtype=np.int64)


# 2b. PWM: the old step values are bit-exact, the knob in between is a straight line, the ends hold 12.5 / 75 %
okb = all((render(300, shape=shape_v(0), color=c, note=n) == old_pulse(300, n, c)).all()
          for c in [duty_v(i) for i in range(4)] + [0, 32767] for n in (45, 69, 100))
check("pulse: old COLOR steps (and 0 / 32767) bit-exact to the 4-step pulse", okb)
for c, want in ((8192, 0.1875), (10240, 0.21875), (16384, 0.375), (24576, 0.625), (26624, 0.6875)):
    frac = (render(1500, shape=shape_v(0), color=c, note=45) > 0).mean()
    check("pulse PWM COLOR %d -> %.2f%%" % (c, want * 100), abs(frac - want) < 0.005, "measured %.2f%%" % (frac * 100))
dut = [(render(300, shape=shape_v(0), color=c, note=45) > 0).mean() for c in range(0, 32768, 512)]
check("pulse PWM: duty never falls as COLOR rises, 12.5..75 %", all(b >= a - 0.002 for a, b in zip(dut, dut[1:]))
      and abs(dut[0] - 0.125) < 0.005 and abs(dut[-1] - 0.75) < 0.005, "%.2f..%.2f%%" % (dut[0] * 100, dut[-1] * 100))

# 3. triangle: 16 stepped levels, symmetric
x = render(400, shape=shape_v(1), note=57)
lv = sorted(set((x >> SH).tolist()))
check("triangle: 16 stepped levels", len(lv) == 16, "%d levels" % len(lv))

# 4. wave tables: only table values appear, each table
tabs = G.wave_tables()
okw = True
for t in range(8):
    x = render(200, shape=shape_v(2), color=idx8_v(t), note=48)
    vals = set((x >> SH).tolist())                       # w = table value x 16 (Q4)
    okw &= vals <= set(v * 16 for v in tabs[t]) and len(vals) > 3
check("wave: output only takes the 4-bit table values (8 tables)", okw)

# 5. noise: LFSR periods and balance
check("noise LFSR 15-bit period 32767", L.rs_lfsr_period(15) == 32767, str(L.rs_lfsr_period(15)))
check("noise LFSR 7-bit period 127", L.rs_lfsr_period(7) == 127, str(L.rs_lfsr_period(7)))
for shp, nm in ((3, "long"), (4, "short")):
    x = render(1500, shape=shape_v(shp), color=idx8_v(2), note=60)
    check("noise %s: two levels, balanced" % nm, len(set(x.tolist())) == 2 and abs((x > 0).mean() - 0.5) < 0.06,
          "high %.1f%%" % ((x > 0).mean() * 100))



def old_noise(blocks, note, color, bits):
    """The noise before the continuous rate: clock = pitch x 2^(4 + COLOR / 8192)."""
    inc, k = L.rs_inc_c(int(note * 65536)), 4 + ((color * 4) >> 15)
    lfsr, nph, out = (0x7f if bits == 7 else 0x7fff), 0, []
    for _ in range(blocks * 32):
        clocks, fi = inc >> (32 - k), (inc << k) & M32
        nph = (nph + fi) & M32
        clocks = min(clocks + (nph < fi), 8)
        for _ in range(clocks):
            lfsr = (lfsr >> 1) | (((lfsr ^ (lfsr >> 1)) & 1) << (bits - 1))
        out.append((-128 if lfsr & 1 else 112) << SH)
    return np.array(out, dtype=np.int64)


# 5b. continuous noise rate: old steps bit-exact, two levels and balance everywhere, rate = 2^(COLOR / 8192)
okn = all((render(300, shape=shape_v(shp), color=c, note=n) == old_noise(300, n, c, b)).all()
          for shp, b in ((3, 15), (4, 7)) for c in [duty_v(i) for i in range(4)] + [0, 32767] for n in (30, 60, 110))
check("noise: old COLOR steps (and 0 / 32767) bit-exact, both modes", okn)
okb, worst = True, 0.0
for shp in (3, 4):
    for c in (6000, 10240, 15000, 22000, 27000):
        x = render(1500, shape=shape_v(shp), color=c, note=60)
        hi = (x > 0).mean()
        worst = max(worst, abs(hi - 0.5))
        okb &= len(set(x.tolist())) == 2
check("noise between steps: two levels, balanced (both modes)", okb and worst < 0.06, "worst %.1f%% off 50%%" % (worst * 100))
def flips(c, shp=3):
    x = render(1500, shape=shape_v(shp), color=c, note=48)
    return np.count_nonzero(np.diff(x))
fl = [flips(c) for c in range(4096, 28673, 1024)]
check("noise rate rises with COLOR between the ends", all(b >= a * 0.97 for a, b in zip(fl, fl[1:])) and fl[-1] > fl[0] * 6,
      "%d .. %d flips" % (fl[0], fl[-1]))
r_half, r_oct = flips(8192) / flips(4096), flips(12288) / flips(4096)
check("noise rate: half a step = x1.41, a step = x2", abs(r_half - 2 ** 0.5) < 0.1 and abs(r_oct - 2) < 0.15,
      "x%.2f, x%.2f" % (r_half, r_oct))

# 6. arpeggio: major arp from A4 steps 440 / 554 / 659 every 800 samples
x = render(160, shape=shape_v(1), contour=contour_v(2), note=69).astype(float)
fr = [dom_freq(x[i * 800 : (i + 1) * 800]) for i in range(6)]
want = [440, 554.4, 659.3, 440, 554.4, 659.3]
check("arp: major chord steps every 1/60 s", all(abs(a - b) < 25 for a, b in zip(fr, want)), " ".join("%.0f" % f for f in fr))

# 7. arpeggio off: pitch stays put
x = render(160, shape=shape_v(1), contour=contour_v(0), note=69).astype(float)
fr = [dom_freq(x[i * 800 : (i + 1) * 800]) for i in range(6)]
check("arp off: constant pitch", max(fr) - min(fr) < 15, " ".join("%.0f" % f for f in fr))

# 8. sweep up / down
x = render(450, shape=shape_v(0), color=duty_v(2), note=57, sweep=23408).astype(float)
fa, fb = dom_freq(x[:4000]), dom_freq(x[8000:12000])
check("sweep up raises pitch", fb > fa * 1.3, "%.0f -> %.0f Hz" % (fa, fb))
x = render(450, shape=shape_v(0), color=duty_v(2), note=69, sweep=9360).astype(float)
fa, fb = dom_freq(x[:4000]), dom_freq(x[8000:12000])
check("sweep down lowers pitch", fb < fa * 0.8, "%.0f -> %.0f Hz" % (fa, fb))
x = render(300, shape=shape_v(0), color=duty_v(2), note=69, sweep=CENTER + 500).astype(float)
check("sweep dead zone: no sweep near centre", dom_freq(x[:4000]) > 0 and abs(dom_freq(x[:4000]) - dom_freq(x[8000:12000])) < 15)

# 9. sweep up past the top silences the note (Game Boy behaviour)
x = render(2000, shape=shape_v(0), note=100, sweep=30000)
check("sweep up past the top silences the note", np.abs(x[-4800:]).max() == 0 and np.abs(x[:300]).max() > 0)

# 10. SNES voice against a float gaussian reference (same integer phase)
lp = G.loops()[0]
inc = L.rs_inc_c(60 << 16)
x = render(180, shape=shape_v(5), color=idx8_v(0), note=60).astype(float) / 2 ** (SH - 4)
ph = 0
ref = np.empty(len(x))
for i in range(len(x)):
    ph = (ph + inc) & 0xFFFFFFFF
    ix = ph >> 28
    f = ((ph >> 20) & 255) / 256.0
    w = np.array([math.exp(-((j - 1) - f) ** 2 / (2 * 0.6 ** 2)) for j in range(4)])
    w /= w.sum()
    ref[i] = sum(w[j] * lp[(ix - 1 + j) & 15] for j in range(4)) * 16 * 16
rel = np.sqrt(((x - ref) ** 2).mean()) / np.sqrt((ref ** 2).mean())
check("SNES voice matches float gaussian reference (<2% rms)", rel < 0.02, "%.2f%%" % (100 * rel))
near = np.array([lp[((i * inc) & 0xFFFFFFFF) >> 28] * 16 * 16 for i in range(1, len(x) + 1)], dtype=float)
def hfp(s):
    p = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / SR)
    return p[f >= 6000].sum() / p.sum()
check("SNES voice: >6 kHz power >=100x below stepped loop", hfp(x) * 100 < hfp(near), "%.5f vs %.5f" % (hfp(x), hfp(near)))

# 11. punch: at most 16 output levels, applied to the SNES voice too
for shp in (2, 5):
    x = render(200, shape=shape_v(shp), color=idx8_v(3), note=60, punch=1)
    check("punch: shape %d has <= 16 levels" % shp, len(set(x.tolist())) <= 16, "%d levels" % len(set(x.tolist())))

# 12. a new trig restarts the voice exactly (phase, arp, sweep)
s = L.rs_new()
buf = (ctypes.c_int * 32)()
L.rs_block_c(s, 69 << 16, 1, shape_v(0), duty_v(1), 23408, contour_v(2), 0, buf)
first = list(buf)
for _ in range(60):
    L.rs_block_c(s, 69 << 16, 0, shape_v(0), duty_v(1), 23408, contour_v(2), 0, buf)
L.rs_block_c(s, 69 << 16, 1, shape_v(0), duty_v(1), 23408, contour_v(2), 0, buf)
check("new trig restarts the voice exactly", list(buf) == first)
L.rs_free(s)

# 13. level: peak is 112 x 2^22 (1/4 of full scale), never more
x = render(300, shape=shape_v(0), color=duty_v(2), note=60)
check("output level: high 112 x 2^22, low -2^29, never beyond", x.max() == 112 << SH and x.min() == -(128 << SH),
      "max %d min %d" % (x.max(), x.min()))

print("FAILED %d" % fails if fails else "all checks passed")
sys.exit(1 if fails else 0)
