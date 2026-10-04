#!/usr/bin/env python3
"""Preuve du tweak « tempo jusqu'à 546 BPM » (notes/38, tweaks/model-cycles_OS1.13/42-tempo-max.json).

Le vrai code de l'OS, sur le MAIN OS d'origine et sur le MAIN OS modifié (tempo en 1/120 de BPM) :
  1. Écritures : octets d'origine, aucune place libre, et application avec les autres mods (6ch-usbup, Model-TG,
     arpégiateur, effacement des trigs, moteurs du Syntakt) sans chevauchement.
  2. Le moteur : 0x40058bb4 (tempo en attente) et 0x40058b62 (tempo appliqué), de 10 à 833 BPM demandés.
  3. Le projet (champ 16 bits +18, 0x4000c846), le pattern (0x4001238e) et la molette du menu Tempo (0x4003d4b8).
  4. L'horloge MIDI reçue : le calcul du tempo sur 24 intervalles (0x40080618), de 120 à 700 BPM.
  5. Le chargement : les deux contrôles (0x4005aab2, 0x4005b3e8) qui remettent 120 BPM hors de la plage.
  6. L'affichage : 0x4009602e (1/120 de BPM -> BPM et dixième), comme le menu Tempo et le tap tempo.
  7. Le LFO synchronisé au tempo : la vraie mise à jour des 6 LFO (0x40091ab2, EMAC exacte de emac.py), vitesse
     au maximum (et au minimum), multiplicateurs 9 à 11, 300 mises à jour par tempo : la phase reste dans son cycle
     et vaut exactement (ancienne + pas) modulo le cycle ; d'origine, elle en sort au-delà de 351,6 BPM.

    python3 tools/emu/test_tempo_max.py --cycles model-cycles_OS1.13.syx [--syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import struct
import sys
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import emac                         # noqa: E402
import gen_tempo_max as G           # noqa: E402
import test_sdvintage as T          # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TWEAK = DEV / "42-tempo-max.json"
BASE = build.BASE
FAIL = []
STOP = 0x9f000000
STACK = 0x9e000000
OBJ = 0x93000000
TEMPO = 0x40149310
PENDING = 0x40140a84               # tempo en attente (0x40058bb4)
APPLY = 0x40140a88                 # appliquer tout de suite ?
SET_TEMPO = 0x40091780             # (mode, tempo, notifier) : appliqué par 0x40058b62
LFO = 0x40091ab2                   # (paramètres des pistes, tempo, masque des retrigs) : les 6 LFO
LFO_PHASE = 0x40fde838             # 6 x 32 o : phase +0, valeur +4, ... ; indicateurs +28
C = G.LFO_CYCLE


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def s32(v):
    v &= 0xffffffff
    return v - (1 << 32) if v & 0x80000000 else v


class Rig:
    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x01000000)
        uc.mem_write(BASE, img)
        uc.mem_map(0x90000000, 0x10000000)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad = []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        self.set_calls = []
        uc.hook_add(UC_HOOK_CODE, self._set_tempo, begin=SET_TEMPO, end=SET_TEMPO)
        uc.hook_add(UC_HOOK_CODE, self._ret0, begin=0x40001fba, end=0x40001fba)     # boîte aux lettres
        with tempfile.NamedTemporaryFile(suffix=".bin") as f:
            f.write(img)
            f.flush()
            instrs = {}
            for lo, hi in ((0x4008f100, 0x40091d50),):
                instrs.update(emac.disasm(f.name, BASE, lo, hi))
        self.emac = emac.EMAC(uc)
        self.emac.install(instrs)

    def _ret(self, d0):
        sp = self.uc.reg_read(mk.UC_M68K_REG_A7)
        self.uc.reg_write(mk.UC_M68K_REG_D0, d0 & 0xffffffff)
        self.uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", self.uc.mem_read(sp, 4))[0])
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def _set_tempo(self, uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        self.set_calls.append(struct.unpack(">3i", uc.mem_read(sp + 4, 12)))
        self._ret(0)

    def _ret0(self, uc, addr, size, ud):
        self._ret(0)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def r16(self, a):
        return struct.unpack(">H", self.uc.mem_read(a, 2))[0]

    def call(self, fn, *args):
        sp = STACK - 0x200
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(fn, STOP, count=5_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0), self.uc.reg_read(mk.UC_M68K_REG_D1)

    def snippet(self, start, until, regs, stack=()):
        """Exécute [start, until) avec ces registres (et ces mots en haut de pile) ; rend les registres de données."""
        self.uc.reg_write(mk.UC_M68K_REG_A7, STACK - 0x400)
        self.uc.mem_write(STACK - 0x400, struct.pack(f">{len(stack)}I", *[x & 0xffffffff for x in stack]))
        for name, v in regs.items():
            self.uc.reg_write(getattr(mk, "UC_M68K_REG_" + name.upper()), v & 0xffffffff)
        self.uc.emu_start(start, until, count=100_000)
        return {f"d{i}": self.uc.reg_read(getattr(mk, f"UC_M68K_REG_D{i}")) for i in range(8)}


def clamp(t, hi):
    return max(G.MIN, min(hi, t))


def test_engine(rigs):
    asked = [1200, 3599, 3600, 14400, 36000, 36001, 42188, 48000, 60000, 65520, 65521, 65535, 100000]
    for name, rig, hi in rigs:
        got = []
        for t in asked:
            rig.w32(APPLY, 0)
            rig.call(0x40058bb4, t)
            got.append(rig.r32(PENDING))
        check(got == [clamp(t, hi) for t in asked],
              f"{name} : 0x40058bb4 garde {', '.join(G.bpm(g) for g in got[3:10])} BPM (demandés 120 à 546,0)")
        rig.set_calls.clear()
        for t in asked:
            rig.call(0x40058b62, t)
        check([c[1] for c in rig.set_calls] == [clamp(t, hi) for t in asked],
              f"{name} : 0x40058b62 applique jusqu'à {G.bpm(max(c[1] for c in rig.set_calls))} BPM")


def test_setters(rigs):
    asked = [3000, 3600, 14400, 36000, 40000, 65520, 65535, 70000]
    for name, rig, hi in rigs:
        proj, pat, menu = [], [], []
        for t in asked:
            rig.uc.mem_write(OBJ, bytes(64))
            rig.snippet(0x4000c86e, 0x4000c88c, {"d2": t, "d0": OBJ})
            proj.append(rig.r16(OBJ + 18))
            rig.snippet(0x400123cc, 0x400123e8, {"d2": t, "d0": OBJ + 32})
            pat.append(rig.r32(OBJ + 32))
            # 0x4003d4b8 a empilé d2 et d3 : la vue à sp@(12), le tempo demandé à sp@(16)
            menu.append(rig.snippet(0x4003d4bc, 0x4003d4dc, {}, stack=(0, 0, 0, 0, t))["d2"])
        want = [clamp(t, hi) for t in asked]
        check(proj == want, f"{name} : projet (16 bits) {[G.bpm(x) for x in proj]}")
        check(pat == want, f"{name} : pattern (32 bits) {[G.bpm(x) for x in pat]}")
        check(menu == want, f"{name} : molette du menu Tempo {[G.bpm(x) for x in menu]}")


def test_midi_clock(rigs):
    for name, rig, hi in rigs:
        got = []
        for b in (120, 300, 400, 546, 700):
            sum24 = round(1900800000 * 512 / (120 * b))          # 24 intervalles, minuteur DMA (135,168 MHz)
            rig.w32(0x40fb57d4, sum24)
            got.append(rig.snippet(0x40080618, 0x4008065a, {})["d0"])
        want = [clamp(round(120 * b), hi) for b in (120, 300, 400, 546, 700)]
        check(all(abs(g - w) <= 2 for g, w in zip(got, want)),
              f"{name} : horloge MIDI reçue à 120/300/400/546/700 BPM -> {[G.bpm(g) for g in got]}")


def test_load(rigs):
    asked = [0, 3599, 3600, 14400, 36000, 36001, 48000, 65520, 65521, 65535]
    for name, rig, hi in rigs:
        a, b = [], []
        for t in asked:
            rig.uc.mem_write(OBJ, bytes(64))
            rig.uc.mem_write(OBJ + 18, struct.pack(">H", t))
            rig.snippet(0x4005b3e8, 0x4005b406, {"a3": OBJ, "a2": OBJ + 32})
            a.append(rig.r16(OBJ + 32 + 18))
            rig.uc.mem_write(OBJ + 4, struct.pack(">H", t))
            rig.snippet(0x4005aab2, 0x4005aad0, {"a1": OBJ, "a0": OBJ + 48, "d1": 0xdead0000})
            b.append(rig.r32(OBJ + 48))
        want = [t if G.MIN <= t <= hi else 14400 for t in asked]
        check(a == want and b == want,
              f"{name} : chargement, {G.bpm(48000)} BPM {'gardé' if a[6] == 48000 else 'remis à 120'}, "
              f"{G.bpm(65520)} {'gardé' if a[7] == 65520 else 'remis à 120'}, hors plage remis à 120")


def test_display(rig):
    out = [rig.call(0x4009602e, t, 120, 1, 1) for t in (3600, 14400, 36000, 48012, 65520)]
    check(out == [(30, 0), (120, 0), (300, 0), (400, 1), (546, 0)],
          "affichage : " + ", ".join(f"{a}.{b}" for a, b in out) + " BPM (trois chiffres, comme 300.0)")


def lfo_params(speeds, mults):
    """Paramètres des 6 pistes (66 o chacune, la fonction lit à partir de +22) : vitesse, multiplicateur, fondu
    nul, destination hors tableau (pas d'écriture), forme 0, mode libre, profondeur."""
    blob = bytearray(66 * 6 + 64)
    for k, (sp, mu) in enumerate(zip(speeds, mults)):
        p = 22 + 66 * k
        struct.pack_into(">h", blob, p - 6, sp)
        struct.pack_into(">b", blob, p - 4, mu)
        struct.pack_into(">h", blob, p - 2, 16384)
        struct.pack_into(">b", blob, p, 127)
        struct.pack_into(">h", blob, p + 6, 0)
        struct.pack_into(">h", blob, p + 8, 16384)
    return bytes(blob)


def test_lfo(rigs):
    speeds = [32767, 0, 32767, 32767, 24000, 0]              # SPD +63,99, -64, ..., en 1/512
    mults = [11, 11, 10, 9, 11, 10]
    for tempo in (14400, 36000, 42187, 48000, 65520):
        res = {}
        for name, rig, _ in rigs:
            rig.uc.mem_write(LFO_PHASE, bytes(32 * 6))
            rig.uc.mem_write(OBJ, lfo_params(speeds, mults))
            rig.emac.macsr = 0x20
            model = [0] * 6
            out = worst = 0
            exact = True
            for _ in range(300):
                rig.call(LFO, OBJ, tempo, 0)
                for k in range(6):
                    inc = ((speeds[k] - 16384) * 2 * tempo) >> (11 - mults[k])
                    model[k] = (model[k] + inc) % C
                    ph = rig.r32(LFO_PHASE + 32 * k)
                    if ph >= C:
                        out += 1
                        worst = max(worst, ph)
                    exact &= ph == model[k]
            res[name] = (out, exact, rig.bad[:])
        (o0, e0, b0), (o1, e1, b1) = res["d'origine"], res["modifié"]
        check(o1 == 0 and e1 and not b1,
              f"LFO à {G.bpm(tempo)} BPM, modifié : phase toujours dans le cycle, = (ancienne + pas) mod cycle")
        if tempo <= 42187:
            check(o0 == 0 and e0, f"LFO à {G.bpm(tempo)} BPM, d'origine : identique (déjà juste)")
        else:
            check(o0 > 0, f"LFO à {G.bpm(tempo)} BPM, d'origine : phase hors du cycle {o0} fois sur 1800 "
                          "(le défaut corrigé)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx : vérifie aussi l'application avec les moteurs")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    check(tweak == G.build_tweak(stock), "42-tempo-max.json = tools/gen_tempo_max.py sur l'OS officiel")
    check(all(set(bytes.fromhex(w["old"])) != {0xff} for w in tweak["writes"]), "aucune place libre utilisée")
    patched, _ = build.apply_writes(stock, [tweak])
    patched = bytes(patched)

    # 1. avec les autres mods
    others = [json.loads((DEV / f).read_text(encoding="utf-8")) for f in
              ("11-6ch-usbup.json", "30-model-tg-st.json", "40-arp.json", "41-trig-hold.json",
               "31-syntakt-tg-sd-cp-toy-bits-swarm.json")]
    try:
        build.apply_writes(stock, others + [tweak])
        mine = {(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]}
        clash = [o["id"] for o in others for w in o["writes"]
                 if any(w["off"] < b and a < w["off"] + len(w["new"]) // 2 for a, b in mine)]
        check(not clash, "avec 6ch-usbup, Model-TG (version combinée), arpégiateur, effacement des trigs et les 5 "
                         "moteurs du Syntakt : aucune écriture en commun")
    except SystemExit as e:
        check(False, f"application avec les autres mods : {e}")

    rigs = [("d'origine", Rig(stock), G.STOCK_MAX), ("modifié", Rig(patched), G.MAX)]
    test_engine(rigs)
    test_setters(rigs)
    test_midi_clock(rigs)
    test_load(rigs)
    test_display(rigs[1][1])
    test_lfo(rigs)
    for name, rig, _ in rigs:
        check(not rig.bad, f"{name} : aucun accès hors mémoire")
    print("\nTOUT EST BON" if not FAIL else f"\n{len(FAIL)} ECHEC(S)")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
