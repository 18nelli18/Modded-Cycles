#!/usr/bin/env python3
"""Banc du flux audio USB vers l'ordinateur (entrée USB de l'hôte, « IN »), notes/35.

Le vrai code du pilote de l'OS 1.13 (et des stubs du mod 6 canaux) tourne dans Unicorn ; le contrôleur USB, les
horloges et l'interruption audio sont modélisés en Python, à la micro-trame près :
  - l'horloge audio : un bloc de 32 trames toutes les 8 192 périodes du minuteur DMA 2 (0xfc07800c, 12,288 MHz =
    256 x 48 kHz : l'OS en tire les trames écoulées dans le bloc par (ticks + 128) >> 8). L'interruption DMA
    (0x400589c0) horodate le début du bloc (0x40a78e04) ; l'interruption de rendu (0x40058c5e) calcule le bloc
    (0x4005979e) puis l'envoie à l'USB : 0x40002912(0x40fe4b90, 32) en 0x40059392, donc à
    « début du bloc + temps de calcul » ;
  - l'hôte : une micro-trame toutes les 125 us de SON horloge (écart réglable avec l'horloge audio) ; à chacune,
    le contrôleur envoie le dTD en tête de file (les octets de la case à cet instant), ou rien si la file est vide ;
    l'interruption SOF de l'OS horodate la micro-trame (0x40004318 : 0x422ff024 + (FRINDEX & 31) x 8) ;
  - le démarrage du flux : 0x40002778 (vrai code) amorce 11 cases de silence (6 avec le mod 6 canaux), la 1re avec
    le rappel 0x4000264a (vrai code), appelé quand elle part, qui aligne le flux sur le bloc audio (trames à
    sauter, 0x404a0620, d'après l'horodatage de la micro-trame 0 de la trame USB où elle est partie) et lance
    l'envoi ; l'hôte commence ses transferts isochrones en début de trame (1 ms) ;
  - mise en file d'un dTD (0x40003f94) : interceptée (le dTD rejoint la file du modèle) ;
  - mesure du débit : la vraie routine de l'OS (0x4000238e), chaque milliseconde, sur les horodatages des micro-trames
    (0x422ff134, 0x422ff158), depuis la valeur de départ 6.0 ; l'écart d'horloge est réglable (-100 à +100 ppm).
Chaque trame porte un numéro (et sa piste) : côté hôte, une trame manquante, en double ou sautée est un défaut.

Temps de calcul par bloc (scénarios) :
  - « origine » : environ 77 % d'un bloc, presque constant (mesure sur la machine, notes/23) ;
  - « Model-TG » : des passages chargés (80 à 95 %) et creux (20 à 40 %, pistes mutées ou au repos, effets éteints),
    de 0,3 à 3 s chacun, comme quand on mute et démute des pistes ;
  - « pics » : 77 % avec un bloc à 99 % de temps en temps.

Parties :
  1. accroches : l'envoi suit bien le calcul dans l'OS d'origine ; octets d'origine aux endroits que le tweak change ;
  2. la copie des 6 pistes déroulée (machines/usb6/tracks6.S) contre le stub d'origine de ms-multi-output :
     mêmes octets écrits, mêmes registres et mêmes indicateurs, pour toutes les longueurs et positions de départ ;
  3. le flux, par scénario de charge, phase de démarrage et écart d'horloge, sur l'OS d'origine (stéréo),
     6ch-multiout (le ring et l'envoi du mod 6 canaux d'avant notes/35), 6ch-usbup, 6ch-usbup avec Model-TG et
     Model-TG seul (stéréo, ring d'origine) : les deux derniers portent le même envoi à heure fixe ;
  4. un long passage de 6ch-usbup (charge de Model-TG, vraie mesure du débit) : la file reste dans ses bornes.

    python3 tools/emu/test_usb_in.py --cycles model-cycles_OS1.13.syx [--seconds 2] [--long 60]
"""
import argparse
import json
import pathlib
import random
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import test_sdvintage as T          # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = build.BASE
FAIL = []

BLOCK = 8192                      # ticks du minuteur DMA 2 par bloc de 32 trames
UFRAME = 1536                     # ticks par micro-trame de 125 us (horloges égales)
FEED = 0x40002912                 # (source, trames) : envoi d'un bloc à l'USB
START = 0x40002778                # démarrage du flux (choix de l'interface audio par l'hôte)
PRIME = 0x40003f94                # (point d'accès, dTD) : mise en file
MIX = 0x40fe4b90                  # mix stéréo envoyé à l'USB (32 x {G, D})
TRACKS = 0x80001858               # 6 pistes x 32 trames (source du mod 6 canaux)
STAMP, BLKCNT = 0x40a78e04, 0x40a78e08
SOF_T, FRAME_NO, FRINDEX = 0x422ff024, 0x422ff124, 0x422ff134
RATE = 0x404a0654                 # 4 mesures du débit (trames par micro-trame, 16.16)
STOP = 0x9f000000
STACK = 0x9e000000


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Usb:
    """Le chemin USB IN de l'OS, avec un contrôleur et des horloges modélisés."""

    def __init__(self, img, channels, hooks=None):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x02400000)                    # image, BSS (dont 0x422ff024..)
        uc.mem_write(BASE, img)
        uc.mem_map(0x80000000, 0x00010000)                    # SRAM : ring, dTD, pistes
        uc.mem_map(0x90000000, 0x10000000)                    # pile
        uc.mem_map(0xfc000000, 0x00100000)                    # registres (lus, sans effet ici)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad = []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        self.queue = []                                         # dTD en file (adresses)
        uc.hook_add(UC_HOOK_CODE, self._prime, begin=PRIME, end=PRIME)
        uc.hook_add(UC_HOOK_CODE, self._ret0, begin=0x40004abe, end=0x40004abe)   # minuterie logicielle
        self.ch = channels
        self.hooks = hooks or {}

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def _ret(self, d0):
        uc = self.uc
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_D0, d0)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def _prime(self, uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        ep, dtd = struct.unpack(">II", uc.mem_read(sp + 4, 8))
        if ep == 7:                                             # point d'accès audio IN
            self.queue.append(dtd)
        self._ret(0)

    def _ret0(self, uc, addr, size, ud):
        self._ret(1)

    def call(self, fn, *args):
        sp = STACK - 0x200
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(fn, STOP, count=200_000)
        if self.uc.reg_read(mk.UC_M68K_REG_A7) != sp + 4:
            FAIL.append(f"pile déséquilibrée après 0x{fn:08x}")
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def fill(self, n):
        """Les sources du bloc n : chaque trame porte son numéro (et sa piste)."""
        f0 = n * 32
        self.uc.mem_write(MIX, b"".join(struct.pack(">II", (f0 + i) << 4 | 0, (f0 + i) << 4 | 1) for i in range(32)))
        self.uc.mem_write(TRACKS, b"".join(struct.pack(">I", (f0 + i) << 4 | 2 + t)
                                           for t in range(6) for i in range(32)))

    def run(self, seconds, load, *, ppm=0.0, start_ms=50.0, mode="stock", real_rate=True, trace=None):
        """mode : « stock » (envoi après le calcul, comme l'OS), « patched » (crochets du tweak : envoi au début du
        bloc suivant). real_rate : la vraie mesure du débit de l'OS (0x4000238e, chaque milliseconde, depuis la
        valeur de départ 6.0 de 0x40002d64), sinon la table reçoit le rapport exact. trace : liste qui reçoit
        (seconde, file min, file max) chaque seconde. Rend un dictionnaire de compteurs."""
        uf = UFRAME * (1 + ppm * 1e-6)                          # période d'une micro-trame en ticks audio
        rate = 0x60000 if real_rate else round(6 * 65536 * (1 + ppm * 1e-6))
        for i in range(4):
            self.w32(RATE + 4 * i, rate)
        if real_rate:
            self.uc.mem_write(0x404a0604, b"\x01")                # 1re mesure : remise à zéro (0x40002d92)
        sec_min, sec_max = 99, -1
        nblocks = int(seconds * 1500)
        k = 0                                                   # micro-trame
        t_start = start_ms * 12288
        armed = started = False
        stats = {"trous": 0, "sautées": 0, "doubles": 0, "trames": 0, "file_max": 0, "file_min": 99}
        expect = None
        events = []
        for n in range(nblocks):
            s = n * BLOCK
            c = load(n)
            events.append((s, 0, n, "stamp"))
            if mode == "stock":
                events.append((s + 40 + c, 1, n, "feed"))
            else:
                events.append((s + 40, 1, n, "isr"))            # début de l'interruption de rendu
                events.append((s + 40 + c, 2, n, "end"))        # fin du calcul : l'envoi est noté
        events.sort()
        ei = 0
        while ei < len(events):
            t_ev = events[ei][0]
            # micro-trames jusqu'à cet événement
            while k * uf <= t_ev:
                t = k * uf
                if not armed and t >= t_start:
                    self.call(START, 1)                         # l'hôte choisit l'interface audio
                    armed = True
                if armed and not started and k % 8 == 0:
                    started = True                              # ses transferts isochrones partent en début de trame
                fr = k & 0x3fff
                self.w32(FRINDEX, fr)
                self.w32(0x422ff158, int(t) & 0xffffffff)          # minuteur DMA 2 à la micro-trame (0x400043b2)
                self.w32(SOF_T + (fr & 31) * 8, int(t - self.r32(STAMP) + 0.5) & 0xffffffff)
                if real_rate and k % 8 == 0:
                    self.call(0x4000238e)                       # mesure du débit (rappel périodique de l'OS)
                if started:
                    if self.queue:
                        dtd = self.queue.pop(0)
                        tok, buf, cb = self.r32(dtd + 4), self.r32(dtd + 8), self.r32(dtd + 36)
                        self.w32(dtd + 4, tok & ~0x80)          # le contrôleur rend le dTD : bit Active effacé
                        data = bytes(self.uc.mem_read(buf, tok >> 16))
                        self.w32(FRAME_NO, (k >> 3) & 2047)
                        if cb:
                            self.call(cb)
                        expect = self._check(data, expect, stats)
                    elif self.r32(0x404a0644):
                        stats["trous"] += 1                     # rien à envoyer : l'hôte reçoit une micro-trame vide
                    if self.r32(0x404a0644):
                        stats["file_max"] = max(stats["file_max"], len(self.queue))
                        stats["file_min"] = min(stats["file_min"], len(self.queue))
                        sec_min, sec_max = min(sec_min, len(self.queue)), max(sec_max, len(self.queue))
                if trace is not None and k % 8000 == 7999:
                    trace.append((round(t / 12288000, 1), sec_min, sec_max, self.r32(0x4013e4e4)))
                    sec_min, sec_max = 99, -1
                k += 1
            _, _, n, what = events[ei]
            ei += 1
            if what == "stamp":
                self.w32(STAMP, n * BLOCK)
                self.w32(BLKCNT, n)
            elif what == "feed":
                self.fill(n)
                self.call(FEED, MIX, 32)
            elif what == "isr":
                self.call(self.hooks["isr"])                     # envoie le bloc noté au bloc précédent
            elif what == "end":
                self.fill(n)
                self.call(self.hooks["end"], MIX, 32)            # ce que fait 0x40059392 dans le tweak
        if self.bad:
            FAIL.append(f"accès hors mémoire : {[hex(a) for a in self.bad[:4]]}")
        return stats

    def _check(self, data, expect, stats):
        step = 4 * self.ch
        for i in range(0, len(data), step):
            v = [struct.unpack("<I", data[i + 4 * j:i + 4 * j + 4])[0] for j in range(self.ch)]   # little-endian USB
            if not any(v):
                continue                                        # silence d'amorçage
            f = v[0] >> 4
            tags = [x & 15 for x in v]
            want_tags = [0, 1] if self.ch == 2 else list(range(2, 8))
            if tags != want_tags or any(x >> 4 != f for x in v):
                stats["sautées"] += 1                           # trame mélangée (pistes de blocs différents)
            stats["trames"] += 1
            if expect is not None:
                if f == expect - 1 or f < expect - 1:
                    stats["doubles"] += 1
                elif f > expect:
                    stats["sautées"] += 1
            expect = f + 1
        return expect


def loads(seed):
    rnd = random.Random(seed)

    def stock(n):
        return int(BLOCK * rnd.uniform(0.74, 0.80))

    def spikes(n):
        return int(BLOCK * (0.99 if rnd.random() < 0.002 else rnd.uniform(0.74, 0.80)))

    state = {"until": 0, "lo": False}

    def model_tg(n):
        if n >= state["until"]:
            state["lo"] = not state["lo"]
            state["until"] = n + rnd.randint(450, 4500)          # 0,3 à 3 s
        return int(BLOCK * (rnd.uniform(0.20, 0.40) if state["lo"] else rnd.uniform(0.80, 0.95)))
    return {"origine (77 %)": stock, "pics à 99 %": spikes, "Model-TG (mutes)": model_tg}


def describe(st):
    return (f"{st['trames']} trames, {st['trous']} micro-trames vides, {st['sautées']} sautées/mélangées, "
            f"{st['doubles']} en double ; file de {st['file_min']} à {st['file_max']} cases")


def defects(st):
    return st["trous"] + st["sautées"] + st["doubles"]


def hook_tests(stock, after):
    p = lambda img, a, n: bytes(img[a - BASE:a - BASE + n])
    check(p(stock, 0x40059382, 6) == bytes.fromhex("4eb94005979e") and p(stock, 0x40059392, 6) == bytes.fromhex("4eb940002912"),
          "OS d'origine : 0x40059382 calcule le bloc (jsr 0x4005979e), puis 0x40059392 l'envoie à l'USB (jsr 0x40002912)")
    check(p(stock, 0x40058ca0, 6) == bytes.fromhex("a93c00000020"),
          "début de l'interruption de rendu : movel #32,%macsr en 0x40058ca0 (remplacé par l'appel de feed_isr)")
    tw = {w["off"] + BASE: w for w in after["writes"]}
    isr = int(tw[0x40058ca0]["new"][4:], 16)
    note = int(tw[0x40059392]["new"][4:], 16)
    check(tw[0x400593ce]["new"] == tw[0x40059392]["new"], "les deux envois de l'interruption (bloc calculé, silence) sont notés")
    return {"isr": isr, "end": note}


class Stub:
    """Un stub de copie (tracks6) exécuté seul : pistes au hasard, case du ring, registres au hasard."""

    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x00400000)
        uc.mem_write(BASE, img[:0x00400000 - 0x400])
        uc.mem_map(0x80000000, 0x00010000)
        uc.mem_map(0x90000000, 0x00100000)
        self.n = 0
        uc.hook_add(UC_HOOK_CODE, self._count)

    def _count(self, uc, addr, size, ud):
        self.n += 1

    def run(self, entry, d0, d3, regs, tracks):
        uc = self.uc
        uc.mem_write(TRACKS, tracks)
        uc.mem_write(0x80009800, b"\xee" * 0x700)
        names = [getattr(mk, f"UC_M68K_REG_D{i}") for i in range(8)] + [getattr(mk, f"UC_M68K_REG_A{i}") for i in range(7)]
        vals = dict(zip(names, regs))
        vals[mk.UC_M68K_REG_D0], vals[mk.UC_M68K_REG_D1], vals[mk.UC_M68K_REG_D3] = d0, 0x80009800 + 24, d3
        for r, v in vals.items():
            uc.reg_write(r, v)
        uc.reg_write(mk.UC_M68K_REG_A7, 0x90080000)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700 | (regs[0] & 0x1f))
        self.n = 0
        uc.emu_start(entry, 0x40002a26, count=20000)
        out = [uc.reg_read(r) for r in names + [mk.UC_M68K_REG_A7]] + [uc.reg_read(mk.UC_M68K_REG_SR) & 0xff]
        return bytes(uc.mem_read(0x80009800, 0x700)), out, self.n


def tracks_test(before, after, stub_va, new_va):
    rnd = random.Random(7)
    a, b = Stub(before), Stub(after)
    same, cases, ia, ib = True, 0, 0, 0
    for d0 in range(0, 17, 2):
        for d3 in list(range(0, 64)) + [0x7fffffe0, 0xffffffff]:
            regs = [rnd.getrandbits(32) for _ in range(15)]
            tracks = bytes(rnd.getrandbits(8) for _ in range(6 * 128))
            ra, rb = a.run(stub_va, d0, d3, regs, tracks), b.run(new_va, d0, d3, regs, tracks)
            same &= ra[0] == rb[0] and ra[1] == rb[1]
            cases += 1
            if d0 == 12:
                ia, ib = ia + ra[2], ib + rb[2]
    check(same, f"tracks6 déroulé : mêmes octets dans le ring, mêmes registres d0-d7/a0-a7 et mêmes indicateurs "
                f"que le stub d'origine ({cases} cas : 0 à 8 trames, départ 0 à 63 et au-delà)")
    n = 66
    check(ib < ia, f"6 trames (une case) : {ia / n:.0f} instructions avant, {ib / n:.0f} après "
                   f"(environ {(ia - ib) / n * 32 / 6:.0f} de moins par bloc de 32 trames)")


def scenario(img, ch, seconds, hooks=None, starts=(20.0, 20.33, 20.5), ppms=(30,), seed=1):
    res = {}
    for name, _ in loads(seed).items():
        for start in starts:
            for ppm in ppms:
                load = loads(seed)[name]
                st = Usb(img, ch, hooks).run(seconds, load, ppm=ppm, start_ms=start,
                                             mode="patched" if hooks else "stock")
                res[(name, start, ppm)] = st
    return res


def summary(res):
    by = {}
    for (name, _, _), st in res.items():
        by.setdefault(name, []).append(st)
    out = {}
    for name, sts in by.items():
        bad = sum(1 for st in sts if defects(st))
        out[name] = (bad, len(sts), sum(defects(st) for st in sts), min(st["file_min"] for st in sts),
                     max(st["file_max"] for st in sts))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--seconds", type=float, default=2, help="durée de chaque passage (secondes de flux)")
    ap.add_argument("--long", type=float, default=60, help="durée du long passage (0 : sauté)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in DEV.glob("*.json") if f.name != "device.json"}
    multi = json.loads(by_id["6ch-multiout"].read_text(encoding="utf-8"))
    usbup = json.loads(by_id["6ch-usbup"].read_text(encoding="utf-8"))
    tg = json.loads(by_id["model-tg"].read_text(encoding="utf-8"))
    before = build.apply_writes(stock, [multi])[0]
    after = build.apply_writes(stock, [usbup])[0]
    after_tg = build.apply_writes(stock, [tg])[0]
    after_tg6 = build.apply_writes(stock, [usbup, tg])[0]

    print("1. accroches")
    hooks = hook_tests(stock, usbup)
    check(hook_tests(stock, tg) == hooks, "Model-TG porte les mêmes crochets, vers le même code (tools/usb_steady.py)")

    print("2. copie des 6 pistes")
    import relocate_6ch as R
    old_va = next(va for name, va, *_ in R.STUBS if name == "tracks6")
    new_va = next(w["off"] + BASE for w in usbup["writes"] if w["old"].startswith("ffff") and
                  bytes.fromhex(w["new"])[-6:] == bytes.fromhex("4ef940002a26") and
                  bytes.fromhex(w["new"])[:4] == bytes.fromhex("4fefffe4"))
    tracks_test(before, after, old_va, new_va)

    print(f"3. le flux USB vers l'ordinateur ({args.seconds:g} s par passage, vraie mesure du débit)")
    ref = summary(scenario(stock, 2, args.seconds))
    for name in ("origine (77 %)", "pics à 99 %"):
        bad, n, d, lo, hi = ref[name]
        check(bad == 0, f"OS d'origine (stéréo, ring de 16), {name} : {n - bad}/{n} passages sans défaut, file {lo}..{hi}")
    bad, n, d, lo, hi = ref["Model-TG (mutes)"]
    print(f"  info  OS d'origine (stéréo) sous la charge de Model-TG : {bad}/{n} passages avec défauts ({d} trames "
          f"touchées), file {lo}..{hi} (rare en stéréo : il en faut souvent plus d'une seconde par passage)")
    old = summary(scenario(before, 6, args.seconds))
    for name, (bad, n, d, lo, hi) in old.items():
        print(f"  info  6ch-multiout (ring de 8, envoi après le calcul), {name} : {bad}/{n} passages avec défauts "
              f"({d} trames touchées), file {lo}..{hi}")
    check(old["Model-TG (mutes)"][0] == old["Model-TG (mutes)"][1], "6ch-multiout : la charge de Model-TG fait des "
                                                                    "défauts à chaque passage (le problème signalé)")
    starts, ppms = (20.0, 20.07, 20.2, 20.33, 20.5, 20.71, 21.0, 21.4), (-100, 30, 100)
    for label, img, ch, ring in (("6ch-usbup", after, 6, 9), ("6ch-usbup + Model-TG", after_tg6, 6, 9),
                                 ("Model-TG (stéréo)", after_tg, 2, 16)):
        new = summary(scenario(img, ch, args.seconds, hooks, starts=starts, ppms=ppms))
        for name, (bad, n, d, lo, hi) in new.items():
            check(bad == 0 and lo >= 1, f"{label} (ring de {ring}, envoi au début du bloc), {name} : {n - bad}/{n} "
                                        f"passages sans défaut, file {lo}..{hi} sur {ring}")

    if args.long:
        print(f"4. long passage de 6ch-usbup : {args.long:g} s, charge de Model-TG, +60 ppm")
        trace = []
        st = Usb(after, 6, hooks).run(args.long, loads(3)["Model-TG (mutes)"], ppm=60, start_ms=20.4,
                                      mode="patched", trace=trace)
        lo, hi = min(t[1] for t in trace[1:]), max(t[2] for t in trace[1:])
        rates = sorted({t[3] for t in trace[1:]})
        check(defects(st) == 0 and lo >= 1 and hi <= 8,
              f"{describe(st)} ; chaque seconde, file entre {lo} et {hi} ; débit mesuré "
              f"{rates[0] / 65536:.6f} à {rates[-1] / 65536:.6f} trames par micro-trame")
    print("ÉCHECS : " + "; ".join(FAIL) if FAIL else "tout est bon")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
