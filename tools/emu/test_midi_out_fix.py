#!/usr/bin/env python3
"""Preuve de la sortie MIDI sans gel (notes/79, tweaks/model-cycles_OS1.13/52-midi-out-fix.json) dans le Modded Cycles
OS : « base » = l'OS de os.json sans midi-out-fix, « corrigé » = avec. Le vrai code de l'OS (Unicorn) :

  1. écritures : les octets changés dans l'image sont ceux du tweak ;
  2. 0x40001232 (ranger un octet pour la sortie MIDI) appelé directement, à chaque niveau d'interruption (0 à 7),
     l'anneau vide, à moitié plein, plein à une place près et plein (1 024, 1 500) : partout où la base revient, le
     corrigé rend exactement le même état (anneau, index, compte, liaison série, contrôleurs, d2/d3, SR, pile) ; là
     où la base ne revient pas (anneau plein à un niveau de 4 ou plus), le corrigé revient sans rien ranger ; anneau
     plein à un niveau de 0 à 3 : les deux attendent, puis, l'anneau vidé par l'interruption de niveau 4 (simulée
     après 50 tours), rangent l'octet de la même façon ;
  3. le top d'horloge MIDI (0x4005420c, son corps à IPL 7) sous une surcharge où le niveau 4 n'est jamais servi : la
     base range 1 024 tops puis se fige au 1 025e ; le corrigé revient à tous, les 1 024 premiers identiques, les
     suivants jettent leur octet ; liaison série libre : 0xF8 envoyé tout de suite, identique ;
  4. l'autre gel de notes/70 (D1, MACHINES sur une machine inconnue), déjà corrigé dans cet OS par les détours des
     enregistrements (notes/20 §5) : machines 15, 16, 100, 255 et -1 -> l'enregistrement de KICK, potards de KICK,
     aucun accès avant le tableau.

    python3 tools/emu/test_midi_out_fix.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
"""
import argparse
import contextlib
import io
import json
import pathlib
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UcError
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_mesure as G              # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402
import test_model_tg_syntakt as tms  # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as tsy  # noqa: E402

TID = "midi-out-fix"
BASE = 0x40000400
PUT, RET = 0x40001232, 0x40007000        # ranger un octet ; une adresse de retour factice (nop, nop)
TICK, TICK_RTE = 0x4005420c, 0x40054288  # top d'horloge MIDI : entrée, rte
SPIN = (0x4000123a, 0x40001248)          # l'attente d'origine
RING = 0x4a3e0000                         # l'anneau (comme l'OS : 0x400013e8)
COUNT, WIDX, BUSY = 0x4049dccc, 0x4049dcc8, 0x4049dca0
FAILS = []


def check(ok, msg):
    print(("  ok    " if ok else "  ÉCHEC ") + msg, flush=True)
    if not ok:
        FAILS.append(msg)


def firmwares(cycles, syntakt_path):
    stock = T.stock_of(cycles)
    ctx = dict(syntakt=syntakt_path, st_img=syntakt.dsp_image(syntakt_path), chord=tmx.chord_tables(stock))
    tw = G.os_tweaks()
    if TID not in {t["id"] for t in tw}:          # pas encore dans os.json : ajouté pour « corrigé »
        tw = sorted(tw + [json.loads((G.DEV / "52-midi-out-fix.json").read_text(encoding="utf-8"))],
                    key=lambda t: t["order"])
    base = [t for t in tw if t["id"] != TID]
    with contextlib.redirect_stdout(io.StringIO()):
        return tmo.Fw(stock, base, ctx), tmo.Fw(stock, tw, ctx), next(t for t in tw if t["id"] == TID)


class Rig:
    """L'image de l'OS, la liaison série et les contrôleurs en mémoire simple (ce que lit et écrit 0x40001232)."""

    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x01000000)
        uc.mem_map(0x4a000000, 0x00400000)
        uc.mem_map(0xfc000000, 0x00100000)
        uc.mem_map(0xec000000, 0x00100000)
        uc.mem_map(0x90000000, 0x00010000)
        uc.mem_write(BASE, bytes(img))
        uc.mem_write(RET, b"\x4e\x71\x4e\x71")
        self.w32(0x4049dcac, RING)
        for a in (BUSY, 0x4049dcc4, WIDX, COUNT):
            self.w32(a, 0)
        self.drain = None                         # (adresse de la boucle, tours, nouveau compte)
        self.turns = 0
        uc.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, uc, addr, size, ud):
        if self.drain and addr == self.drain[0]:
            self.turns += 1
            if self.turns == self.drain[1]:       # l'interruption de niveau 4 a vidé une partie de l'anneau
                self.w32(COUNT, self.drain[2])

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def state(self):
        u = self.uc
        regs = [u.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in ("D1", "D2", "D3", "A7")]
        regs.append(u.reg_read(mk.UC_M68K_REG_SR) & 0xff00)       # le masque d'interruption (pas les drapeaux)
        return (bytes(u.mem_read(RING, 1024)), self.r32(WIDX), self.r32(COUNT), self.r32(BUSY),
                self.r32(0x4049dca4), bytes(u.mem_read(0xec07400c, 1)), bytes(u.mem_read(0xfc044019, 1)),
                bytes(u.mem_read(0xfc04c01d, 1)), tuple(regs))

    def put(self, byte, ipl, count, busy, uart_free=False, limit=200_000):
        """0x40001232(byte) à ce niveau : (revenu ?, état). L'anneau tient déjà count octets."""
        u = self.uc
        self.w32(COUNT, count)
        self.w32(WIDX, count & 1023)
        self.w32(BUSY, busy)
        u.mem_write(0xec074004, b"\x04" if uart_free else b"\x00")
        sp = 0x9000f000
        u.mem_write(sp, struct.pack(">II", RET, byte))
        u.reg_write(mk.UC_M68K_REG_SR, 0x2000 | ipl << 8)    # avant la pile (SR choisit la pile du superviseur)
        u.reg_write(mk.UC_M68K_REG_A7, sp)
        u.reg_write(mk.UC_M68K_REG_D2, 0x22222222)
        u.reg_write(mk.UC_M68K_REG_D3, 0x33333333)
        self.setup = self.state()
        try:
            u.emu_start(PUT, RET, count=limit)
        except UcError as e:
            return f"erreur {e}", self.state()
        return u.reg_read(mk.UC_M68K_REG_PC) == RET, self.state()


# --- 2. 0x40001232 à chaque niveau ---------------------------------------------------------------------------------
def put_tests(fa, fb, sym):
    print("2. ranger un octet, à chaque niveau d'interruption")
    same, drop, spin, bad = 0, 0, 0, []
    for ipl in range(8):
        for count in (0, 512, 1023, 1024, 1500):
            for busy in (0, 2):
                for uart_free in (False, True):
                    ra, rb = Rig(fa.img), Rig(fb.img)
                    a, sa = ra.put(0x90, ipl, count, busy, uart_free)
                    b, sb = rb.put(0x90, ipl, count, busy, uart_free)
                    case = (ipl, count, busy, uart_free)
                    if a is True:
                        same += b is True and sa == sb
                        if not (b is True and sa == sb):
                            bad.append(("différent", case))
                    elif a is False:                      # la base ne revient pas : elle tourne dans l'attente
                        pc = ra.uc.reg_read(mk.UC_M68K_REG_PC)
                        full = count > 1023
                        if not (SPIN[0] <= pc < SPIN[1] and full):
                            bad.append(("base bloquée ailleurs", case, hex(pc)))
                        elif ipl >= 4:
                            ok = b is True and sb[:8] == rb.setup[:8] and sb[8][1:] == (0x22222222, 0x33333333,
                                                                                        0x9000f004, 0x2000 | ipl << 8)
                            drop += ok
                            if not ok:
                                bad.append(("corrigé : octet pas jeté proprement", case))
                        else:
                            pcb = rb.uc.reg_read(mk.UC_M68K_REG_PC)
                            ok = b is False and sym["ring_wait"] <= pcb < sym["ring_drop"]
                            spin += ok
                            if not ok:
                                bad.append(("corrigé : n'attend pas au niveau < 4", case))
                    else:
                        bad.append(("base", case, a))
    check(not bad, f"partout où la base revient, le corrigé rend le même état ({same} cas) ; anneau plein à un niveau "
          f">= 4 : la base reste dans l'attente, le corrigé revient sans rien ranger, SR et pile intacts ({drop} cas) ; "
          f"plein à un niveau < 4 : les deux attendent ({spin} cas)" + (f" {bad[:4]}" if bad else ""))
    ok, n = True, 0
    for ipl in range(4):                              # l'anneau vidé pendant l'attente : la suite est la même
        res = []
        for fw, loop in ((fa, SPIN[0]), (fb, sym["ring_wait"])):
            r = Rig(fw.img)
            r.drain = (loop, 50, 1000)
            res.append(r.put(0x5a, ipl, 1024, 2))
        (a, sa), (b, sb) = res
        ok &= a is True and b is True and sa == sb and sa[2] == 1001 and sa[0][1024 & 1023] == 0x5a
        n += 1
    check(ok, f"anneau plein à un niveau de 0 à 3, vidé après 50 tours d'attente : l'octet rangé, état identique à la "
          f"base ({n} niveaux)")


# --- 3. le top d'horloge MIDI --------------------------------------------------------------------------------------
class ClockRig(Rig):
    def __init__(self, img):
        super().__init__(img)
        self.w32(0x40fe4228, 1)                       # sortie MIDI prête
        self.uc.mem_write(0x404e9b50, b"\x00\x00\x01")    # OUT (pas THR), 0x404e9b52 : ports = DIN
        self.w32(0x40a70148, 1)                       # envoi d'horloge activé
        self.w32(0x40a78630, 0)
        self.uc.mem_write(0x40a788e6, b"\x00")

    def tick(self, limit=200_000):
        u = self.uc
        u.reg_write(mk.UC_M68K_REG_SR, 0x2500)        # entrée d'interruption de niveau 5
        u.reg_write(mk.UC_M68K_REG_A7, 0x9000f000)
        try:
            u.emu_start(TICK, TICK_RTE, count=limit)
        except UcError as e:
            return f"erreur {e}"
        return u.reg_read(mk.UC_M68K_REG_PC) == TICK_RTE

    def short(self):
        return self.state()[:8]


def clock_tests(fa, fb):
    print("3. le top d'horloge MIDI")
    sent = []
    for img in (fa.img, fb.img):
        r = ClockRig(img)
        r.uc.mem_write(0xec074004, b"\x04")           # liaison série libre : envoyé tout de suite
        sent.append((r.tick(), r.short()))
    check(sent[0] == sent[1] and sent[0][0] is True and sent[0][1][5] == b"\xf8" and sent[0][1][2] == 0,
          "liaison série libre : 0xF8 envoyé tout de suite, anneau vide, identique à la base")
    res = {}
    for name, img in (("base", fa.img), ("corrigé", fb.img)):     # surcharge : le niveau 4 n'est jamais servi
        r = ClockRig(img)
        r.w32(BUSY, 2)
        r.uc.mem_write(0xec074004, b"\x00")
        states = []
        for k in range(1, 1031):
            ok = r.tick()
            if ok is not True:
                res[name] = (k, r.uc.reg_read(mk.UC_M68K_REG_PC), r.uc.reg_read(mk.UC_M68K_REG_SR), states)
                break
            states.append(r.short())
        else:
            res[name] = (None, None, None, states)
    k, pc, sr, st = res["base"]
    check(k == 1025 and pc is not None and SPIN[0] <= pc < SPIN[1] and (sr >> 8) & 7 == 7,
          f"base : 1 024 tops rangés, le 1 025e ne revient pas (dans l'attente 0x4000123a..46, IPL 7) : top {k}"
          + (f", PC {pc:#x}, SR {sr:#06x}" if pc is not None else ""))
    k2, _, _, st2 = res["corrigé"]
    check(k2 is None and len(st2) == 1030, f"corrigé : les 1 030 tops reviennent ({len(st2)})")
    check(st2[:1024] == st[:1024], "corrigé : les 1 024 premiers tops identiques à la base, top après top (anneau, "
          "index, compte, liaison série, contrôleurs)")
    check(all(s == st2[1023] for s in st2[1024:]), "corrigé : au-delà, chaque top jette son octet (rien ne bouge)")


# --- 4. MACHINES sur une machine inconnue (déjà corrigé) ----------------------------------------------------------
def machines_tests(fb):
    print("4. MACHINES sur une machine inconnue (notes/70 D1 ; corrigé dans cet OS depuis notes/20 §5)")
    u = tms.UI(fb)
    t7.fill_records(u)
    tsy.poison(u)
    u.bad.clear()
    kick_of, kick_at = u.call(0x4004df76, 0), u.call(0x4004df5c, 1)
    of = {m: u.call(0x4004df76, m) for m in (15, 16, 100, 255, -1)}
    at = {i: u.call(0x4004df5c, i) for i in (16, 17, 100, 255, -1)}
    check(all(v == kick_of for v in of.values()) and all(v == kick_at for v in at.values()) and not u.bad
          and kick_of != tsy.REC_BASE - tsy.REC_LEN,
          f"accesseurs 0x4004df76 (machines {list(of)}) et 0x4004df5c (index {list(at)}) : l'enregistrement de KICK "
          f"({kick_of:#x}), jamais 76 o avant le tableau, aucun accès hors mémoire")
    this, vec = 0x93900000, 0x93910000
    u.uc.mem_write(vec, struct.pack(">8i", 1, 2, 3, 4, 5, 6, 0, 0))
    u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 24, vec + 24))
    knobs, bad = {}, False
    for m in (0, 15, 16, 100):
        u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
        u.bad.clear()
        knobs[m] = [u.call(0x4001e814, this, k, 0, 0) for k in range(2, 8)]
        bad |= bool(u.bad)
    check(not bad and all(knobs[m] == knobs[0] for m in knobs),
          f"potards de l'écran principal (0x4001e814), machines 15, 16, 100 : ceux de KICK {knobs[0]}, aucun accès "
          "hors mémoire")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    args = ap.parse_args()
    fa, fb, tweak = firmwares(args.cycles, args.syntakt)
    sym = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    print("1. écritures")
    d = [i for i in range(min(len(fa.img), len(fb.img))) if fa.img[i] != fb.img[i]]
    spans = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]]
    check(len(fa.img) == len(fb.img) and d and all(any(lo <= i < hi for lo, hi in spans) for i in d),
          f"{len(d)} octets changés dans l'image, tous dans les {len(tweak['writes'])} écritures du tweak")
    put_tests(fa, fb, sym)
    clock_tests(fa, fb)
    machines_tests(fb)
    print("\nTOUT OK" if not FAILS else f"\n{len(FAILS)} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
