#!/usr/bin/env python3
"""Preuve des trigless trigs atténués (notes/45, tweaks/model-cycles_OS1.13/47-trigless-dim.json).

Le vrai code de l'OS, sur le MAIN OS d'origine et sur le MAIN OS modifié :
  - une image de l'interface (30 Hz) : remise à zéro des 54 états de LED (0x4000602a), états posés comme le fait le
    mode grille (0x40005f86 : 2 = trig de note, 3 = trig avec p-locks, 4 ou 260 = trigless trig), fin de l'image
    (0x40006044 : les LED sans état passent à 1, relevé des LED dans l'état 260 par le mod, puis 0x4008e77e envoie
    les rangées qui ont changé) ;
  - le clignotement (0x40005efc, 2 Hz), qui arme les minuteurs de LED (0x4008e8c4) ;
  - le tick des LED (0x4008e7ca, 120 Hz) : minuteurs, puis envoi des rangées (0x4008e77e -> 0x4008e732 -> 0x40059fd2,
    qui écrit l'octet inversé dans la copie des verrous 0x40140aa8, lue par l'interruption du panneau).
  Intercepté : le verrou des LED (0x40001cc4, 0x40001df6). Une LED se lit dans 0x40140aa8 (bit de la table
  0x4010abf8) ; les touches de pas sont les LED logiques 1 à 16.

  1. Écritures : octets d'origine, masque libéré identique au masque gardé et désigné par la seule constante de son
     constructeur, aucune écriture différente d'un autre tweak sur les mêmes octets.
  2. Mode grille : un trigless trig prend l'état 260 (movea.w #260,a5 en 0x40021f52), et 260 n'est écrit que là.
  3. Clignotement : l'état 260 (modifié) donne les mêmes appels que 4 (origine) ; 3, 5 et 0x10004 inchangés.
  4. 50 ticks : trig de note et trig avec p-locks identiques à l'origine, tick par tick ; trigless trig allumé
     9 ticks sur 25 (allumé à fond à l'origine) ; toutes les autres LED identiques.
  5. 16 trigless trigs : les 16 touches suivent le même motif ; masque = leurs 16 bits de la table 0x4010abf8.
  6. Le clignotement d'origine d'un trigless trig (éteint 42 ticks toutes les 2 s) reste le même.
  7. Un tick au milieu d'une image (états remis à zéro, mode grille pas encore passé) : la touche reste atténuée
     (avec le .syx de djd_oz, elle se rallume à fond jusqu'à la fin de l'image).
  8. Pas encore d'objet des LED (pointeur nul, au démarrage) : comme l'origine. Registres d2-d7/a2-a6 et pile rendus par le tick et par la
     fin de l'image.
  9. Coût du tick et de la fin de l'image, en instructions.
  (--djd) Avec le .syx de djd_oz : mêmes LED, tick par tick, dans les cas 4 à 6.

    python3 tools/emu/test_trigless_dim.py --cycles model-cycles_OS1.13.syx \
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max,boot-anim \
         --syntakt Syntakt_OS1.42.syx] [--djd model-cycles_OS1.13_Trigless-Trigs-LED-36pct-v4-experimental.syx]
"""
import argparse
import json
import pathlib
import re
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import sprites                      # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "47-trigless-dim.json"
BASE = build.BASE
FAIL = []

STOP, STACK, OBJ = 0x9f000000, 0x9e000000, 0x93000000
MUTEX = (0x40001cc4, 0x40001df6)
LED_OBJ, LED_BIT, SHADOW = 0x40fe4200, 0x4010abf8, 0x40140aa8
SEND_FN, SEND_LATCH = 0x401492f8, 0x40059fd2           # pointeur posé au démarrage (0x4000556c)
CLEAR, SET_STATE, END_FRAME = 0x4000602a, 0x40005f86, 0x40006044
BLINK, BLINK_PHASE, TICK = 0x40005efc, 0x404a90f4, 0x4008e7ca
KEYS = list(range(1, 17))                              # LED logiques des 16 touches de pas
CALLEE = [mk.UC_M68K_REG_D2 + i for i in range(6)] + [mk.UC_M68K_REG_A2 + i for i in range(5)]


def check(ok, msg):
    print(f"  {'ok   ' if ok else 'ECHEC'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)


class Rig:
    """Le MAIN OS en mémoire, le crochet de démarrage exécuté (copie de .data en SRAM ; pour le .syx de djd_oz, la
    copie de son code en 0x42339000)."""

    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_map(0x80000000, 0x00020000)
        uc.mem_map(0x90000000, 0x10000000)
        uc.mem_write(BASE, img)
        self.icount, self.counting, self.bad = 0, False, []
        uc.hook_add(UC_HOOK_CODE, self._hook)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        self.call(0x4000045c)
        self.w32(SEND_FN, SEND_LATCH)
        self.w32(LED_OBJ, OBJ)
        uc.mem_write(SHADOW, b"\xff" * 8)
        self.table = struct.unpack(">54l", bytes(uc.mem_read(LED_BIT, 216)))

    def _hook(self, uc, addr, size, _):
        if self.counting:
            self.icount += 1
        if addr in MUTEX:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def call(self, fn, *args, regs=None):
        sp = STACK - 4 * (len(args) + 1)
        self.uc.mem_write(sp, struct.pack(">I", STOP) + b"".join(struct.pack(">I", a & 0xffffffff) for a in args))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        for r, v in (regs or {}).items():
            self.uc.reg_write(r, v)
        self.uc.emu_start(fn, STOP, count=50_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def frame(self, states):
        """Une image de l'interface : remise à zéro, états posés, fin de l'image."""
        self.call(CLEAR, OBJ)
        for idx, st in states.items():
            self.call(SET_STATE, OBJ, idx, st, 0x404a8cb8)
        self.call(END_FRAME, OBJ)

    def led(self, idx):
        b = self.table[idx]
        return (~self.uc.mem_read(SHADOW + (b >> 3), 1)[0] >> (b & 7)) & 1

    def leds(self):
        return "".join(str(self.led(i)) for i in range(1, 54))

    def ticks(self, n, watch):
        """n ticks des LED : pour chaque LED de watch, sa suite d'états ; et la suite de toutes les LED."""
        rows, alls = {i: "" for i in watch}, []
        for _ in range(n):
            self.call(TICK)
            for i in watch:
                rows[i] += str(self.led(i))
            alls.append(self.leds())
        return rows, alls


def expected_pattern(n, start=0):
    """Le motif du tweak : +9 modulo 25, allumé au passage de 25."""
    out, c = "", start
    for _ in range(n):
        c += 9
        out += "1" if c >= 25 else "0"
        c %= 25
    return out


def writes_ok(stock, img, tweak, others):
    for w in tweak["writes"]:
        o, old = w["off"], bytes.fromhex(w["old"])
        check(stock[o:o + len(old)] == old, f"octets d'origine en {o + BASE:#x} ({len(old)} o)")
    mask, (size, ref, _, shared) = 0x4018dba8, sprites.MASKS[0x4018dba8]
    check(stock[mask - BASE:mask - BASE + size] == stock[shared - BASE:shared - BASE + size],
          f"masque {mask:#x} identique au masque gardé {shared:#x}")
    refs = [m.start() + BASE for m in re.finditer(re.escape(struct.pack(">I", mask)), stock)]
    check(refs == [ref] and img[ref - BASE:ref - BASE + 4] == struct.pack(">I", shared),
          f"seule référence au masque : la constante de son constructeur ({ref:#x}), redirigée")
    clash = []
    for t in others:
        for v in t["writes"]:
            a, b = v["off"], v["off"] + len(v["old"]) // 2
            for w in tweak["writes"]:
                c, d = w["off"], w["off"] + len(w["old"]) // 2
                if a < d and c < b and (v["off"], v["new"]) != (w["off"], w["new"]):
                    clash.append(f"{t['id']}@{a + BASE:#x}")
    check(not clash, f"aucun autre tweak n'écrit autre chose sur ces octets ({len(others)} tweaks) {clash[:4]}")
    i = 0x40021f52 - BASE
    check(img[i:i + 4] == bytes.fromhex("3a7c0104"), "mode grille, trigless trig : movea.w #260,a5 en 0x40021f52")
    imm = [m.start() + BASE for m in re.finditer(re.escape(bytes.fromhex("0104")), img)
           if img[m.start() - 2:m.start()] in (b"\x3a\x7c", b"\x2a\x7c", b"\x7a\x00")]
    check(imm == [0x40021f54], f"l'état 260 n'est écrit qu'en 0x40021f52 (movea #260 : {[hex(a) for a in imm]})")


def blink(base, img):
    out = {}
    for name, im, lock in (("origine", base, 4), ("modifié", img, 260)):
        for phase in (0, 1):
            r = Rig(im)
            calls = []

            def h(uc, addr, size, _, calls=calls):
                sp = uc.reg_read(mk.UC_M68K_REG_A7)
                _, a1, a2 = struct.unpack(">III", uc.mem_read(sp, 12))
                calls.append((a1, a2))
            r.uc.hook_add(UC_HOOK_CODE, h, begin=0x4008e8c4, end=0x4008e8c4)
            for idx, st in {1: 2, 2: 3, 3: lock, 4: 1, 5: 5, 6: 0x10004}.items():
                r.w32(OBJ + 40 + 4 * idx, st)
            r.w32(BLINK_PHASE, phase)
            r.call(BLINK, OBJ)
            out[name, phase] = (calls, r.r32(BLINK_PHASE))
    for phase in (0, 1):
        check(out["origine", phase] == out["modifié", phase],
              f"clignotement, phase {phase} : mêmes appels de 0x4008e8c4 (état 4 / 260) {out['modifié', phase][0]}")


def dim(base, img, djd, cases):
    """Cas 4 et 5 : LED tick par tick."""
    watch = [1, 2, 3, 4, 5]
    states = {1: 2, 2: 3, 3: "L", 4: "L", 5: 2}
    res = {}
    for name, im, lock in [("origine", base, 4), ("modifié", img, 260)] + ([("djd_oz", djd, 260)] if djd else []):
        r = Rig(im)
        r.frame({i: (lock if s == "L" else s) for i, s in states.items()})
        res[name] = r.ticks(50, watch)
        print(f"     {name:8} trig de note {res[name][0][1]}  trig + p-lock {res[name][0][2]}  "
              f"trigless {res[name][0][3]}")
    o, m = res["origine"], res["modifié"]
    check(o[0][1] == m[0][1] and o[0][2] == m[0][2] and o[0][5] == m[0][5],
          "trig de note et trig avec p-locks : identiques à l'origine, tick par tick")
    check(o[0][3] == "1" * 50, "origine : trigless trig allumé à fond")
    want = expected_pattern(50)
    check(m[0][3] == want and m[0][4] == want and want.count("1") == 18,
          f"modifié : trigless trig allumé selon le motif 9/25 ({want.count('1')} ticks sur 50)")
    keep = [k for k in range(53) if k + 1 not in (3, 4)]
    check(all("".join(a[k] for k in keep) == "".join(b[k] for k in keep) for a, b in zip(o[1], m[1])),
          "toutes les autres LED identiques à l'origine, tick par tick")
    if "djd_oz" in res:
        check(res["djd_oz"][1] == m[1], "identique au .syx de djd_oz, toutes les LED, tick par tick")
    cases["dim"] = res

    res = {}
    for name, im, lock in [("origine", base, 4), ("modifié", img, 260)] + ([("djd_oz", djd, 260)] if djd else []):
        r = Rig(im)
        r.frame({i: lock for i in KEYS})
        rows, alls = r.ticks(50, KEYS)
        mask = bytes(r.uc.mem_read(int(json.loads(TWEAK.read_text())["symbols"]["td_mask"], 16), 8)) \
            if name == "modifié" else None
        res[name] = (rows, alls, mask, r)
    m = res["modifié"]
    check(all(m[0][k] == want for k in KEYS), "16 trigless trigs : les 16 touches suivent le même motif")
    # dernier tick : 50 = allumé ? le masque est celui du dernier tick éteint
    r = m[3]
    r.w32(int(json.loads(TWEAK.read_text())["symbols"]["td_cnt"], 16), 0)
    r.call(TICK)
    mask = bytes(r.uc.mem_read(int(json.loads(TWEAK.read_text())["symbols"]["td_mask"], 16), 8))
    bits = sorted(b for b in range(64) if mask[b >> 3] >> (b & 7) & 1)
    check(bits == sorted(r.table[i] for i in KEYS), f"masque d'un tick éteint = bits des 16 touches {bits}")
    if "djd_oz" in res:
        check(res["djd_oz"][1] == m[1], "16 trigless trigs : identique au .syx de djd_oz, tick par tick")


def blink_dim(base, img, djd):
    """Cas 6 : clignotement d'origine (phase 0 : 0x4008e8c4(LED, 42)) puis 60 ticks."""
    res = {}
    for name, im, lock in [("origine", base, 4), ("modifié", img, 260)] + ([("djd_oz", djd, 260)] if djd else []):
        r = Rig(im)
        r.frame({1: 2, 2: 3, 3: lock})
        r.w32(BLINK_PHASE, 0)
        r.call(BLINK, OBJ)
        res[name] = r.ticks(60, [1, 2, 3])
        print(f"     {name:8} trigless {res[name][0][3]}")
    o, m = res["origine"], res["modifié"]
    off_o = o[0][3].index("1")
    check(o[0][3][:off_o] == "0" * off_o and off_o in (41, 42), f"origine : trigless trig éteint {off_o} ticks")
    check(m[0][3][:off_o] == "0" * off_o and m[0][3][off_o:].count("1") > 0,
          "modifié : éteint pendant le même clignotement, puis atténué")
    check(o[0][1] == m[0][1] and o[0][2] == m[0][2], "trig de note et trig avec p-locks : identiques")
    if "djd_oz" in res:
        check(res["djd_oz"][1] == m[1], "clignotement : identique au .syx de djd_oz, tick par tick")


def midframe(base, img, djd):
    """Cas 7 : 10 ticks, puis le début d'une image (0x4000602a remet les états à zéro), puis 25 ticks avant la fin."""
    res = {}
    for name, im, lock in [("origine", base, 4), ("modifié", img, 260)] + ([("djd_oz", djd, 260)] if djd else []):
        r = Rig(im)
        r.frame({1: 2, 3: lock})
        a = r.ticks(10, [1, 3])[0]
        r.call(CLEAR, OBJ)
        b = r.ticks(25, [1, 3])[0]
        res[name] = (a[1] + b[1], a[3] + b[3])
        print(f"     {name:8} trigless {a[3]} | {b[3]}")
    want = expected_pattern(35)
    check(res["origine"][1] == "1" * 35 and res["origine"][0] == res["modifié"][0] == "1" * 35,
          "origine : trigless allumé à fond ; trig de note allumé, des deux côtés")
    check(res["modifié"][1] == want, "modifié : le trigless reste atténué selon le motif pendant l'image")
    if djd:
        check(res["djd_oz"][1] == want[:10] + "1" * 25,
              "avec le .syx de djd_oz, il se rallume à fond dès que les états sont remis à zéro (écart corrigé)")


def misc(base, img):
    for name, im in (("origine", base), ("modifié", img)):
        r = Rig(im)                                    # au démarrage : pas encore d'objet, aucun relevé
        r.frame({1: 2})
        r.w32(LED_OBJ, 0)
        before = r.leds()
        r.ticks(30, [])
        check(r.leds() == before and not r.bad, f"{name} : pointeur des LED nul, 30 ticks sans changement ni accès invalide")
    r = Rig(img)
    r.frame({i: 260 for i in KEYS})
    pre = {reg: 0x01010101 * (k + 1) for k, reg in enumerate(CALLEE)}
    sp0 = STACK - 4
    for _ in range(4):
        r.call(TICK, regs=pre)
        post = {reg: r.uc.reg_read(reg) for reg in CALLEE}
        if post != pre or r.uc.reg_read(mk.UC_M68K_REG_A7) != sp0 + 4:
            break
    check(post == pre and r.uc.reg_read(mk.UC_M68K_REG_A7) == sp0 + 4, "tick : d2-d7/a2-a6 et pile rendus")
    r.call(CLEAR, OBJ)
    for i in KEYS:
        r.call(SET_STATE, OBJ, i, 260, 0x404a8cb8)
    r.call(END_FRAME, OBJ, regs=pre)
    post = {reg: r.uc.reg_read(reg) for reg in CALLEE}
    check(post == pre and r.uc.reg_read(mk.UC_M68K_REG_A7) == STACK - 4, "fin de l'image : d2-d7/a2-a6 et pile rendus")
    cost = {}
    for name, im, lock in (("origine", base, 4), ("modifié", img, 260)):
        r = Rig(im)
        r.frame({i: lock for i in KEYS})
        n = []
        for _ in range(25):
            r.icount, r.counting = 0, True
            r.call(TICK)
            r.counting = False
            n.append(r.icount)
        cost[name] = (min(n), max(n), sum(n) / len(n))
    o, m = cost["origine"], cost["modifié"]
    print(f"     instructions par tick, 16 trigless trigs : origine {o[0]}..{o[1]}, modifié {m[0]}..{m[1]} "
          f"(moyenne +{m[2] - o[2]:.0f}, soit {(m[2] - o[2]) * 120 / 1e6:.3f} M instructions/s)")
    check(m[1] < 2000, "coût du tick borné (< 2 000 instructions, 120 fois par seconde)")
    frame = {}
    for name, im, lock in (("origine", base, 4), ("modifié", img, 260)):
        r = Rig(im)
        r.frame({i: lock for i in KEYS})
        r.icount, r.counting = 0, True
        r.call(END_FRAME, OBJ)
        r.counting = False
        frame[name] = r.icount
    print(f"     instructions par fin d'image : origine {frame['origine']}, modifié {frame['modifié']} "
          f"(+{frame['modifié'] - frame['origine']}, 30 fois par seconde)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="autres tweaks appliqués avant (ex. 6ch-usbup,model-tg)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    ap.add_argument("--djd", help="le .syx de djd_oz (Trigless-Trigs-LED-36pct-v4), pour comparer")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    files = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TWEAK.parent.glob("[0-9]*.json")}
    every = [json.loads(f.read_text(encoding="utf-8")) for i, f in files.items() if i != "trigless-dim"]
    tweaks = [json.loads(files[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)  # Model-TG : son code est ajouté après l'image
    base = build.apply_writes(stock, sorted(tweaks, key=lambda t: t["order"]))[0] + pl
    img = build.apply_writes(stock, sorted(tweaks + [tweak], key=lambda t: t["order"]))[0] + pl
    djd = T.main_os_from_syx(args.djd) if args.djd else None
    print(f"firmware : {', '.join(t['id'] for t in sorted(tweaks + [tweak], key=lambda t: t['order']))}")
    print("1-2. écritures")
    writes_ok(stock, img, tweak, every)
    print("3. clignotement (0x40005efc)")
    blink(base, img)
    print("4-5. tick des LED, 50 ticks")
    dim(base, img, djd, {})
    print("6. clignotement d'origine sur un trigless trig atténué")
    blink_dim(base, img, djd)
    print("7. tick au milieu d'une image")
    midframe(base, img, djd)
    print("8-9. pointeur nul, registres, coût")
    misc(base, img)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
