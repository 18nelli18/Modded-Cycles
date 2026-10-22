#!/usr/bin/env python3
"""Preuve du firmware de mesure (tools/gen_mesure.py, notes/75), sur le vrai code de l'OS de os.json (Unicorn) :

  1. octets : par rapport à l'OS de os.json, seuls changent les masques pris (et leurs constantes redirigées), les
     12 appels sondés, le vecteur de l'interruption audio, la boucle d'attente, et deux endroits du bloc de Model-TG ;
  2. son : 6 pistes (KICK, SDVtg, MACRO, ACID, MODAL, CHORD) jouées par le vrai séquenceur (seqrig) : la sortie des
     voix et l'état de chaque voix identiques, bloc par bloc, à l'OS sans les sondes ; les sondes notent leur retour
     et des durées emboîtées (minuteur qui avance à chaque lecture) ;
  3. la fin de bloc (m_block_end) et les écrans : 750 blocs de durées connues, puis l'écran AUDIO dessiné par la vraie
     page System de Model-TG (sys_render, écran 2) : les valeurs attendues ; ses écrans 0 et 1 toujours les siens ;
     le cran de DATA va jusqu'à l'écran 4 ;
  4. les essais d'étalonnage, minuteur à 2 instructions par tick (un cycle par instruction) : chaque essai s'exécute,
     la SRAM empruntée est rendue intacte, le code droit est bien généré, l'écran BENCH montre 270 MHz et 1,00
     instruction par cycle pour le calcul ; l'écran COLD alterne bloc normal et bloc froid ;
  5. m_isr (heure d'entrée, invalidation du cache d'instructions un bloc sur deux) et m_idle (temps libre).

    python3 tools/emu/test_mesure.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
"""
import argparse
import contextlib
import ctypes
import io
import pathlib
import struct
import sys
import tempfile

import numpy as np
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_UNMAPPED, UC_PROT_ALL
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_mesure as G              # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_acid_combos as tac      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402

BASE = G.BASE
DTIM0 = 0xfc07000c
STOP = 0x90000100
FAILS = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg)
    if not ok:
        FAILS.append(msg)


def stock_of(cycles):
    raw = pathlib.Path(cycles).read_bytes()
    stream, _ = build.unwrap(raw)
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


# --- 1. octets ------------------------------------------------------------------------------------------------------
def bytes_test(stock, os_tw, me_tw, syms, code):
    print("1. octets")
    a, _ = build.apply_writes(stock, os_tw)
    b, _ = build.apply_writes(stock, me_tw)
    mine = next(t for t in me_tw if t["id"] == "mesure")
    allowed = set()
    for w in mine["writes"]:
        allowed.update(range(w["off"], w["off"] + len(w["new"]) // 2))
    diff = [i for i in range(len(a)) if a[i] != b[i]]
    check(diff and all(i in allowed for i in diff),
          f"{len(diff)} octets changent, tous dans les écritures du firmware de mesure ({len(mine['writes'])}) : "
          f"{len(code)} masques et leurs constantes, {len(G.SITES)} appels, le vecteur, la boucle d'attente")
    ok = all(b[va - BASE:va - BASE + 6] == struct.pack(">HI", 0x4eb9, syms[f"m_w_{k}"])
             for k, (va, _, _) in enumerate(G.SITES))
    check(ok, "chaque appel sondé : jsr m_w_k")
    tg_a = next(t for t in os_tw if t["id"] == "model-tg-st")["append"]["parts"][0]
    tg_b = next(t for t in me_tw if t["id"] == "model-tg-st")["append"]["parts"][0]
    x, y, at = bytes.fromhex(tg_a["hex"]), bytes.fromhex(tg_b["hex"]), int(tg_a["dest"], 16)
    d = [at + i for i in range(len(x)) if x[i] != y[i]]
    spans = [(G.TG_DISPATCH[0], 10), (G.TG_PAGES[0], 6)]
    check(d and all(any(s <= v < s + n for s, n in spans) for v in d),
          f"bloc de Model-TG : {len(d)} octets changés, dans le choix de l'écran (sys_render) et le cran de DATA")


# --- 2. son ---------------------------------------------------------------------------------------------------------
TRACKS = ((0, "KICK"), (7, "SDVtg"), (12, "MACRO"), (13, "ACID"), (14, "MODAL"), (5, "CHORD"))


def play(fw, blocks, timer=False):
    e = fw.engine()
    S.ensure_map(e.uc, 0x46800000, 0x00100000)   # l'état des pistes MODAL (gen_modal.MODAL_RAM)
    rig = S.Rig(e, 120, keep=fw.keep)
    for t, (m, _) in enumerate(TRACKS):
        for k, v in dict(machine=m, pitch=64, color=70, shape=40, sweep=50, contour=60, decay=70).items():
            rig.param(t, E.SLOT[k], v * 256)
        for s in (0, 1, 2):
            rig.set_step(t, s, note=48 + t)
            rig.schedule_step(t, s, rig.now + 2 * rig.blk + s * S.STEP)
    n = [0]
    if timer:                                    # le minuteur avance de 1 à chaque lecture
        def rd(uc, access, addr, size, value, ud):
            n[0] += 1
            uc.mem_write(DTIM0, struct.pack(">I", n[0]))
        e.uc.hook_add(UC_HOOK_MEM_READ, rd, begin=DTIM0, end=DTIM0 + 3)
    outs, states = [], []
    for _ in range(blocks):
        info = rig.block()
        outs.append(info["out"])
        states.append(bytes(e.uc.mem_read(S.VOICE0, 6 * S.VSTRIDE)))
    return np.stack(outs), states, e


def sound_test(stock, os_tw, me_tw, ctx, syms, blocks):
    print("2. son")
    with contextlib.redirect_stdout(io.StringIO()):
        fa, fb = tac.Fw(stock, os_tw, ctx), tac.Fw(stock, me_tw, ctx)
    oa, sa, ea = play(fa, blocks)
    ob, sb, eb = play(fb, blocks)
    same = np.array_equal(oa, ob) and sa == sb
    names = ", ".join(n for _, n in TRACKS)
    check(same and np.abs(oa).max() > 1e6 and not ea.unmapped and not eb.unmapped,
          f"6 pistes ({names}), {blocks} blocs, séquenceur : sortie des voix et état des 6 voix identiques à l'OS "
          f"sans les sondes (crête {np.abs(oa).max() / 2 ** 31:.3f})")
    _, _, e = play(fb, 8, timer=True)
    site = syms["m_site"]
    rd = lambda o: struct.unpack(">12I", e.uc.mem_read(site + o, 48))
    ret, dur = rd(0), rd(96)
    inner = (2, 3, 4, 5, 6, 7, 8, 9, 10)
    ok_ret = all(ret[k] == G.SITES[k][0] + 6 for k in inner)
    ok_dur = all(dur[k] > 0 for k in inner)
    check(ok_ret and ok_dur, f"sondes de la fonction audio : retour noté (site + 6), durées notées {[dur[k] for k in inner]}")


# --- 3 à 5 : un émulateur du code de mesure -----------------------------------------------------------------------
class Emu:
    """L'image et la charge utile ; la SDRAM vue aussi sans cache (0x48000000.., la même mémoire) ; un compteur
    d'instructions ; le minuteur DMA 0 rend timer() à chaque lecture ; DRAW_TEXT noté."""

    def __init__(self, img, rt, dest):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        n = 0x08000000
        self.ram = ctypes.create_string_buffer(n)
        uc.mem_map_ptr(0x40000000, n, UC_PROT_ALL, self.ram)
        uc.mem_map_ptr(0x48000000, n, UC_PROT_ALL, self.ram)
        uc.mem_write(BASE, img)
        uc.mem_write(dest, rt)
        uc.mem_map(0x80000000, 0x20000)
        for lo, hi, d in gs.CY_SRAM_INIT:
            uc.mem_write(d, img[lo - BASE:hi - BASE])
        uc.mem_map(0x90000000, 0x100000)
        uc.mem_map(0xfc000000, 0x1000000)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        self.n, self.bad, self.texts, self.cacr = 0, [], [], 0
        self.timer = lambda: self.n // 2
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_CODE, self._count)
        uc.hook_add(UC_HOOK_MEM_READ, self._timer, begin=DTIM0, end=DTIM0 + 3)
        self.stubs = {0x40071a04: self._text, 0x40070dea: lambda a: 0}

    def _count(self, uc, addr, size, ud):
        self.n += 1
        if addr in self.stubs:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            r = self.stubs[addr](struct.unpack(">7I", uc.mem_read(sp + 4, 28)))
            uc.reg_write(mk.UC_M68K_REG_D0, (r or 0) & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        elif uc.mem_read(addr, 4) == b"\x4e\x7b\x00\x02":
            self.cacr += 1

    def _timer(self, uc, access, addr, size, value, ud):
        uc.mem_write(DTIM0, struct.pack(">I", self.timer() & 0xffffffff))

    def _text(self, a):
        s = bytes(self.uc.mem_read(a[6], 32)).split(b"\0")[0].decode("latin-1")
        y = a[3] - (1 << 32) if a[3] & 0x80000000 else a[3]
        self.texts.append((a[2], y, a[4], s))
        return 0

    def u32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def call(self, fn, *args, regs=None, until=STOP):
        sp = 0x9000f000
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        for r, v in (regs or {}).items():
            self.uc.reg_write(r, v)
        self.uc.emu_start(fn, until, count=50_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)


def screen(emu):
    """Les cases dessinées : {(colonne, rangée) : (étiquette, valeur)}."""
    out = {}
    for x, y, flags, s in emu.texts:
        row = (54 - y) // 10
        col = 1 if x >= 68 else 0
        cell = out.setdefault((col, row), ["", ""])
        cell[1 if flags == 0x14 else 0] = s
    return {k: tuple(v) for k, v in out.items()}


def emu_of(stock, me_tw, ctx):
    with contextlib.redirect_stdout(io.StringIO()):
        fw = tac.Fw(stock, me_tw, ctx)
    return Emu(fw.img, fw.runtime, fw.dest)


def window_test(stock, me_tw, ctx, syms):
    print("3. fin de bloc et écrans")
    emu = emu_of(stock, me_tw, ctx)
    s = syms
    site, per = s["m_site"], 90112
    dur = {0: 900, 1: 50000, 2: 1800, 3: 200, 4: 900, 5: 30000, 6: 400, 7: 100, 8: 3600, 9: 300, 10: 9000, 11: 1100}
    want_total = 66000
    emu.w32(s["m_idle_acc"], 0)
    t = 1_000_000
    for b in range(752):                         # 1er bloc : pas de période ; 750 pleins ; puis un de plus
        emu.w32(s["m_tisr"], t)
        emu.w32(site + 4 * (12 + 1), t + 5000)   # t0 de la fonction audio : en-tête de 5 000 ticks
        for k, v in dur.items():
            emu.w32(site + 4 * (24 + k), v)
        emu.timer = lambda t=t: t + want_total
        emu.w32(s["m_idle_acc"], emu.u32(s["m_idle_acc"]) + 9000)
        emu.call(s["m_block_end"])
        t += per
    c = per * 750 // 1000
    pct = lambda v: f"{v * 750 // c // 10}.{v * 750 // c % 10}%"
    want = {"SEQ": pct(5000 - dur[0]), "USB": pct(dur[0] + dur[11]), "SMOOTH": pct(dur[2]), "LFO": pct(dur[4]),
            "VOICES": pct(dur[5]), "POST": pct(dur[1] - dur[2] - dur[4] - dur[5] - dur[8] - dur[10]),
            "DIST": pct(dur[8]), "OUTPUT": pct(dur[10]), "TOTAL": pct(want_total),
            "PEAK": f"{want_total * 1000 // per // 10}.{want_total * 1000 // per % 10}%", "IDLE": pct(9000)}
    sys_render, sys_pg = 0x401b6f94, G.SYS_PG
    shots = {}
    for pg in range(5):
        emu.texts.clear()
        emu.w32(sys_pg, pg)
        emu.call(sys_render, regs={mk.UC_M68K_REG_D2: 0x90020000})
        shots[pg] = screen(emu)
    got = {lab: val for lab, val in shots[2].values()}
    bad = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
    check(not bad and not emu.bad, f"écran AUDIO (sys_render, écran 2) : {', '.join(f'{k} {v}' for k, v in got.items())} "
                                   f"{bad}")
    labels = lambda pg: {lab for lab, _ in shots[pg].values()}
    check({"CPU", "PEAK", "RAM", "FREE"} <= labels(0) and {"T1", "T6", "TRACKS", "TOTAL"} <= labels(1)
          and {"CPU", "I-MISS"} <= labels(3) and {"NORMAL", "COLD"} <= labels(4),
          "écrans 0 et 1 : ceux de Model-TG (CPU, PEAK, RAM, FREE ; T1..T6, TRACKS) ; 3 BENCH et 4 COLD : les nôtres")
    steps = {}
    for pg0, d0 in ((0, 1), (1, 1), (3, 1), (4, 1), (4, -1), (0, -1)):
        emu.w32(sys_pg, pg0)
        emu.call(0x401b1c9c, regs={mk.UC_M68K_REG_D0: d0 & 0xffffffff}, until=0x401b1cbc)
        steps[(pg0, d0)] = emu.u32(sys_pg)
    check(steps == {(0, 1): 1, (1, 1): 2, (3, 1): 4, (4, 1): 4, (4, -1): 3, (0, -1): 0},
          f"DATA (mm_e_sys) : un écran par cran, de 0 à 4 {steps}")


def bench_test(stock, me_tw, ctx, syms):
    print("4. essais d'étalonnage")
    emu = emu_of(stock, me_tw, ctx)
    s = syms
    sram0 = bytes(emu.uc.mem_read(0x80000000, 0x10000))
    emu.call(s["m_block_end"])                   # init (code droit, état)
    line = bytes(emu.uc.mem_read(0x4233b000, 2050))
    check(line == b"\x52\x80" * 1024 + b"\x4e\x75", "code droit : 128 lignes de addq.l #1,d0, puis rts")
    emu.call(s["m_render"], 0x90020000, 2)      # BENCH affiché
    emu.call(s["m_render"], 0x90020000, 3)      # COLD affiché
    t = [1_000_000]
    colds = []
    for b in range(760):
        emu.w32(s["m_tisr"], t[0])
        colds.append(emu.u32(s["m_cold"]))
        if b % 200 == 0:
            emu.call(s["m_render"], 0x90020000, 2)
            emu.call(s["m_render"], 0x90020000, 3)
        base = t[0]
        emu.timer = lambda: base + 60000 + emu.n // 2
        emu.call(s["m_block_end"])
        t[0] += 90112
    sram1 = bytes(emu.uc.mem_read(0x80000000, 0x10000))
    check(sram1 == sram0 and not emu.bad, "SRAM : rendue intacte après 760 blocs d'essais (zone de travail empruntée)")
    alt = all(colds[i] != colds[i + 1] for i in range(1, 700))
    check(alt and emu.cacr > 0, f"écran COLD affiché : un bloc sur deux froid (m_cold alterne), {emu.cacr} invalidations")
    emu.texts.clear()
    emu.call(s["m_render"], 0x90020000, 2)
    got = {lab: val for lab, val in screen(emu).values()}
    print("      BENCH :", got)
    ok = got.get("CPU") in ("269M", "270M", "271M") and got.get("ALU") == "1.00" and got.get("ALU SR") == "1.00" \
        and got.get("I-MISS") == "0.00" and got.get("D-MISS") == "0.00"
    check(ok, "écran BENCH, à un cycle par instruction et 2 instructions par tick : 270 MHz, ALU 1.00 dans le cache et "
              "en SRAM, aucune ligne manquée (l'émulation n'a pas de cache)")


def isr_idle_test(stock, me_tw, ctx, syms):
    print("5. entrée de l'interruption et temps libre")
    emu = emu_of(stock, me_tw, ctx)
    s = syms
    for cold in (0, 1):
        emu.w32(s["m_cold"], cold)
        emu.cacr = 0
        emu.timer = lambda: 0x12345678
        emu.uc.reg_write(mk.UC_M68K_REG_D0, 0xdeadbeef)
        sp = 0x9000e000
        emu.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        emu.uc.emu_start(s["m_isr"], G.TG["ISR_PROF"][0], count=100)
        ok = (emu.u32(s["m_tisr"]) == 0x12345678 and emu.uc.reg_read(mk.UC_M68K_REG_D0) == 0xdeadbeef
              and emu.uc.reg_read(mk.UC_M68K_REG_A7) == sp and emu.cacr == cold)
        check(ok, f"m_isr, bloc {'froid' if cold else 'normal'} : heure d'entrée notée, d0 et pile intacts, "
                  f"{emu.cacr} invalidation du cache d'instructions, puis isr_prof de Model-TG")
    seq = iter([100, 103, 108, 5000, 5004, 5010] + [5010] * 100)
    emu.timer = lambda: next(seq)
    emu.w32(s["m_idle_acc"], 0)
    emu.uc.reg_write(mk.UC_M68K_REG_A7, 0x9000e000)
    emu.uc.emu_start(s["m_idle"], 0, count=60)
    acc = emu.u32(s["m_idle_acc"])
    check(acc == 3 + 5 + 4 + 6, f"m_idle : écarts courts comptés (3 + 5 + 4 + 6), le long (interruption) non : {acc}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--blocks", type=int, default=420)
    args = ap.parse_args()
    stock = stock_of(args.cycles)
    with contextlib.redirect_stdout(io.StringIO()):
        me_tw, syms, code = G.build_tweaks(stock)
    os_tw = G.os_tweaks()
    st_img = syntakt.dsp_image(args.syntakt)
    ctx = dict(cycles=args.cycles, syntakt=args.syntakt, st_img=st_img, chord=tmx.chord_tables(stock))
    gs.set_base(gs.PAY_TG)
    bytes_test(stock, os_tw, me_tw, syms, code)
    sound_test(stock, os_tw, me_tw, ctx, syms, args.blocks)
    window_test(stock, me_tw, ctx, syms)
    bench_test(stock, me_tw, ctx, syms)
    isr_idle_test(stock, me_tw, ctx, syms)
    print("\nTOUT OK" if not FAILS else f"\n{len(FAILS)} ÉCHEC(S)")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
