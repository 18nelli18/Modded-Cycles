#!/usr/bin/env python3
"""Preuve du tweak « plus de temps pour effacer un trig » (notes/33, tweaks/model-cycles_OS1.13/41-trig-hold.json).

La vraie chaîne de l'OS, exécutée sur le MAIN OS d'origine et sur le MAIN OS modifié, à la milliseconde :
  - l'interruption de lecture des touches (0x40059e64, 1 kHz, anti-rebond), qui appelle 0x4007fbde : événements
    d'appui et de relâchement, horodatés par le minuteur DMA 0 (0xfc07000c, 135,168 MHz) ;
  - l'horloge des touches (0x4007f914, 120 Hz) : événements de maintien (24 ticks, puis tous les 8 ticks) ;
  - chaque événement construit par le vrai constructeur de KeyEvent (0x4007238c) et passé au vrai
    PatternGridView::consumeKeyEvent (0x40022382), avec le vrai UIStates (ses méthodes, sur un objet en mémoire).
  Interceptés : la boîte aux lettres (0x40001fba, les événements sont rendus tout de suite), les trigs de la piste
  (0x40015c20 note ? 0x40015c7c lock ? 0x40017b48 / 0x40017bb0 / 0x40017c4e : poser, poser un lock, effacer),
  l'accès au projet et à la piste, le rafraîchissement de l'écran.
  Un tour de potard pendant l'appui est ce que fait l'OS en 0x4001e96a et 0x4001ea24 : UIStates::setHold(1)
  (0x4006b740).

  1. Accroches : octets d'origine dans l'OS d'origine ; th_press rend le bit FUNC comme 0x40072490.
  2. Trig existant, appuis de 100 ms à 1,5 s : effacé ou gardé, et instant où ses réglages s'affichent (maintien).
  3. Pas vide : le trig est posé et gardé, ses réglages s'affichent à 200 ms, comme à l'origine.
  4. Tour de potard pendant un appui court : le trig reste (comme à l'origine).
  5. Deux trigs tenus l'un après l'autre : le premier reste s'il a été tenu longtemps (plus de maintien reçu).
  6. FUNC + trig de note, et trig de lock : changés au relâchement d'un appui de 300 ms.
  7. Compteur du minuteur qui reboucle pendant l'appui.

    python3 tools/emu/test_trig_hold.py --cycles model-cycles_OS1.13.syx \
        [--with 6ch-usbup,model-tg-st,arp,syntakt-tg-sd-cp-toy-bits-swarm --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "41-trig-hold.json"
BASE = build.BASE
FAIL = []

DTIM_HZ = 135_168_000
ISR_KEYS = 0x40059e64             # interruption d'anti-rebond (1 kHz), se termine par rte (0x40059fd0)
SCAN = 0x4007fbde                 # (octet, nouvel état) : événements d'appui et de relâchement
TICK = 0x4007f914                 # horloge des touches, 120 Hz
RAW = 0x40a791cc                  # 4 octets lus sur le panneau
KEY_CB = 0x40a7925c               # pointeur de 0x4007fbde
SET_FUNC = 0x4007fadc             # (code) : touche FUNC (code 1)
POST = 0x40001fba                 # boîte aux lettres (boîte, entrée de 16 o : type, code, indicateurs, heure)
KEYEV_CTOR = 0x4007238c
GRID_KEY = 0x40022382             # PatternGridView::consumeKeyEvent
SET_HOLD = 0x4006b740             # UIStates::setHold(bool)
UIS_PTR = 0x40fe4218              # singleton UIStates
HOLD_KEY = 0x40148cd4             # touche dont l'horloge envoie les maintiens (-1 : aucune)
FUNC_IDX = 10                     # code 1 -> touche 10 (octet 1, bit 2)

STOP = 0x9f000000
STACK = 0x9e000000
UIS, VIEW, EVT, FAKE = 0x93000000, 0x93001000, 0x93002000, 0x93003000


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def key_bit(code, img):
    """(octet, masque) de la touche de ce code (table code -> touche 0x4010ae5c)."""
    idx = struct.unpack(">i", img[0x4010ae5c - BASE + 4 * code:][:4])[0]
    return idx >> 3, 1 << (idx & 7)


class Rig:
    """Un Model:Cycles réduit à son clavier et à son mode grille."""

    def __init__(self, img, t0=0):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)               # superviseur, avant de fixer la pile
        uc.mem_map(0x40000000, 0x02400000)                    # image + BSS
        uc.mem_write(BASE, img)
        uc.mem_map(0x90000000, 0x10000000)                    # pile, objets
        uc.mem_map(0xfc000000, 0x00100000)                    # registres : minuteur DMA 0, contrôleur d'interruptions
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        assert bytes(uc.mem_read(0x40059fd0, 2)) == b"\x4e\x73"
        uc.mem_write(0x40059fd0, b"\x4e\x75")                 # rte -> rts : appelée comme une fonction ici
        self.bad = []
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        self.img, self.t0, self.now, self.queue, self.log = img, t0, 0, [], []
        self.trigs = {}                                        # pas -> "note" | "lock"
        stubs = {
            POST: self._post,
            0x400cf866: lambda a: FAKE, 0x4000ee90: lambda a: FAKE, 0x400124b8: lambda a: 0,
            0x40012412: lambda a: 0, 0x4000f208: lambda a: FAKE, 0x4000cfcc: lambda a: FAKE + 0x100,
            0x40015c20: lambda a: int(self.trigs.get(a[1]) == "note"),
            0x40015c7c: lambda a: int(self.trigs.get(a[1]) == "lock"),
            0x40017b48: lambda a: self._set(a[1], "note"), 0x40017bb0: lambda a: self._set(a[1], "lock"),
            0x40017c4e: lambda a: self._set(a[1], None),
            0x400760ba: lambda a: 0, 0x40069b84: lambda a: 0, 0x40075f3c: lambda a: 0,
        }
        for addr, fn in stubs.items():
            uc.hook_add(UC_HOOK_CODE, self._stub(fn), begin=addr, end=addr)
        uc.mem_write(UIS, bytes(0x200))
        uc.mem_write(UIS + 357, b"\x01\x01")                  # mode grille, enregistrement (0x4006b978)
        uc.mem_write(VIEW, bytes(0x100))
        self.w32(UIS_PTR, UIS)
        self.w32(KEY_CB, SCAN)
        self.call(SET_FUNC, 1)
        self.raw = bytearray(4)
        self.next_tick = 0.0

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def _stub(self, fn):
        def hook(uc, addr, size, ud):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">4I", uc.mem_read(sp + 4, 16))
            uc.reg_write(mk.UC_M68K_REG_D0, fn(args) & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        return hook

    def _post(self, a):
        typ, code, flags, ts = struct.unpack(">B3xIII", self.uc.mem_read(a[1], 16))
        if typ == 0:
            self.queue.append((code, flags, ts))
        return 0

    def _set(self, step, kind):
        self.log.append((self.now, "trig", step, kind))
        if kind:
            self.trigs[step] = kind
        else:
            self.trigs.pop(step, None)
        return 0

    def call(self, fn, *args):
        sp = STACK - 0x100
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(fn, STOP, count=2_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def key(self, code, down):
        byte, bit = key_bit(code, self.img)
        self.raw[byte] = self.raw[byte] | bit if down else self.raw[byte] & ~bit

    def hold_mode(self):
        return self.uc.mem_read(UIS + 356, 1)[0]

    def step_ms(self):
        """Une milliseconde : interruption des touches, horloge à 120 Hz, puis les événements au mode grille."""
        self.w32(0xfc07000c, self.t0 + self.now * (DTIM_HZ // 1000))
        self.uc.mem_write(RAW, bytes(self.raw))
        self.call(ISR_KEYS)
        while self.next_tick <= self.now:
            self.call(TICK)
            self.next_tick += 1000 / 120
        while self.queue:
            code, flags, ts = self.queue.pop(0)
            self.call(KEYEV_CTOR, EVT, code, flags, ts, 0x7f)
            before = self.hold_mode()
            self.call(GRID_KEY, VIEW, EVT)
            kind = "maintien" if flags & 8 else "appui" if flags & 1 else "relâché"
            self.log.append((self.now, kind, code, flags))
            if not before and self.hold_mode():
                self.log.append((self.now, "affiché", code, flags))
        self.now += 1

    def run(self, events, until):
        """events : {ms: [(code, bas?) ou ("potard",)]} ; tourne jusqu'à until ms (touches relâchées avant)."""
        for _ in range(30):                                    # repos : l'anti-rebond se cale
            self.step_ms()
        self.log.clear()
        start = self.now
        for t in range(until):
            for ev in events.get(t, ()):
                if ev[0] == "potard":
                    self.call(SET_HOLD, UIS, 1)
                    self.log.append((self.now, "potard", 0, 0))
                else:
                    self.key(*ev)
            self.step_ms()
        if self.bad:
            check(False, f"accès hors mémoire : {[hex(a) for a in self.bad[:4]]}")
        return [(t - start, *rest) for t, *rest in self.log]


def shown_at(log):
    """Instant (ms depuis le début) où le maintien est marqué : les réglages du trig s'affichent."""
    return next((t for t, kind, *_ in log if kind == "affiché"), None)


def after(log):
    """Le même, compté depuis l'appui (à 10 ms), pour l'affichage."""
    s = shown_at(log)
    return f"{s - 10} ms" if s else "-"


def press(img, step_kind, dur, t0=0, extra=None, func=False):
    """Un appui de dur ms sur la touche du pas 0 (code 16), qui porte step_kind ; rend (trig final, journal)."""
    rig = Rig(img, t0)
    if step_kind:
        rig.trigs[0] = step_kind
    ev = {10: [(16, True)], 10 + dur: [(16, False)]}
    if func:
        ev = {0: [(1, True)], 10: [(16, True)], 10 + dur: [(16, False)], 20 + dur: [(1, False)]}
    for t, e in (extra or {}).items():
        ev.setdefault(t, []).extend(e)
    log = rig.run(ev, dur + 700)
    return rig.trigs.get(0), log


# --- 1. accroches -----------------------------------------------------------------------------------
def hook_tests(stock, img, tweak):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    sites = {0x4002249c: ("4eb940072490", "th_press"), 0x40022d44: ("4eb940072460", "th_hold"),
             0x40022da6: ("4eb94006b736", "th_release")}
    for va, (old, sym) in sites.items():
        ok = stock[va - BASE:va - BASE + 6].hex() == old and img[va - BASE:va - BASE + 6] == \
            struct.pack(">HI", 0x4eb9, syms[sym])
        check(ok, f"{va:#x} : {old} d'origine, jsr {sym} dans l'OS modifié")
    rig = Rig(img)
    same = True
    for flags in range(64):
        rig.uc.mem_write(EVT, bytes(24))
        rig.uc.mem_write(EVT + 12, struct.pack(">II", 16 + flags % 16, flags))
        same &= (rig.call(syms["th_press"], EVT) & 0xff) == (rig.call(0x40072490, EVT) & 0xff)
    check(same, "th_press rend le bit FUNC comme 0x40072490 (64 valeurs d'indicateurs)")


# --- 2 à 7 ------------------------------------------------------------------------------------------
def describe(final, start):
    return "gardé" if final == start else ("effacé" if final is None else f"changé en trig de {final}")


def existing(stock, img):
    rows = []
    for dur in (100, 150, 170, 190, 250, 350, 450, 470, 520, 600, 1000, 1500):
        a, la = press(stock, "note", dur)
        b, lb = press(img, "note", dur)
        rows.append((dur, a, shown_at(la), b, shown_at(lb)))
        print(f"    appui de {dur:4d} ms : origine {describe(a, 'note'):6s} (réglages affichés : {after(la):6s}) ; "
              f"modifié {describe(b, 'note'):6s} (affichés : {after(lb)})")
    by = {r[0]: r for r in rows}
    check(by[100][1] is None and by[150][1] is None and by[250][1] == "note",
          "origine : effacé à 100 et 150 ms, gardé à 250 ms (le défaut signalé)")
    check(all(by[d][3] is None for d in (100, 150, 170, 190, 250, 350, 450, 470)),
          "modifié : effacé pour tout appui jusqu'à 470 ms")
    check(all(by[d][3] == "note" for d in (520, 600, 1000, 1500)), "modifié : gardé à partir de 520 ms")
    sa = [by[d][2] for d in (250, 600, 1000)]
    sb = [by[d][4] for d in (600, 1000, 1500)]
    check(all(s is not None and 185 <= s - 10 <= 215 for s in sa),
          f"origine : les réglages s'affichent 200 ms après l'appui ({[s - 10 for s in sa]} ms)")
    check(all(s is not None and 515 <= s - 10 <= 545 for s in sb),
          f"modifié : les réglages s'affichent vers 533 ms ({[s - 10 for s in sb]} ms), plus de maintien avant")
    check(all(r[4] is None for r in rows if r[3] is None), "modifié : jamais affichés pour un trig effacé")


def empty(stock, img):
    for dur in (100, 300):
        a, la = press(stock, None, dur)
        b, lb = press(img, None, dur)
        check(a == b == "note" and shown_at(la) == shown_at(lb),
              f"pas vide, appui de {dur} ms : trig posé et gardé, réglages affichés : {after(lb)}, comme à l'origine")


def knob(stock, img):
    for dur in (120, 300):
        extra = {10 + dur // 2: [("potard",)]}
        a, _ = press(stock, "note", dur, extra=extra)
        b, _ = press(img, "note", dur, extra=extra)
        check(a == b == "note", f"tour de potard pendant un appui de {dur} ms : trig gardé (origine et modifié)")


def two_keys(stock, img):
    # pas 0 tenu, pas 4 appuyé à 300 ms : l'horloge envoie les maintiens au pas 4
    ev = {10: [(16, True)], 310: [(20, True)], 810: [(16, False)], 1110: [(20, False)]}
    for name, im in (("origine", stock), ("modifié", img)):
        rig = Rig(im)
        rig.trigs.update({0: "note", 4: "note"})
        rig.run(ev, 1600)
        check(rig.trigs == {0: "note", 4: "note"},
              f"{name} : pas 0 tenu 800 ms, pas 4 appuyé pendant : les deux trigs restent")
    # deux appuis courts qui se chevauchent : effacés tous les deux dans l'OS modifié
    ev = {10: [(16, True)], 110: [(20, True)], 310: [(16, False)], 360: [(20, False)]}
    rig = Rig(img)
    rig.trigs.update({0: "note", 4: "note"})
    rig.run(ev, 900)
    check(rig.trigs == {}, "modifié : deux appuis courts (300 et 250 ms) qui se chevauchent : les deux effacés")


def changes(stock, img):
    a, _ = press(stock, "note", 300, func=True)
    b, _ = press(img, "note", 300, func=True)
    check(a == "note" and b == "lock", f"FUNC + trig de note, 300 ms : origine {describe(a, 'note')}, "
                                       f"modifié {describe(b, 'note')}")
    a, _ = press(stock, "lock", 300)
    b, _ = press(img, "lock", 300)
    check(a == "lock" and b == "note", f"trig de lock, 300 ms : origine {describe(a, 'lock')}, "
                                       f"modifié {describe(b, 'lock')}")
    b, _ = press(img, "lock", 800)
    check(b == "lock", "trig de lock, 800 ms : gardé")


def wrap(img):
    for dur, want in ((300, None), (800, "note")):
        t0 = (1 << 32) - 150 * (DTIM_HZ // 1000)              # le compteur reboucle 150 ms après le début
        b, _ = press(img, "note", dur, t0=t0)
        check(b == want, f"compteur qui reboucle pendant un appui de {dur} ms : {describe(b, 'note')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="autres tweaks appliqués avant (ex. 6ch-usbup,model-tg)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TWEAK.parent.glob("*.json")
             if f.name != "device.json"}
    tweaks = [json.loads(by_id[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)  # Model-TG : son code est ajouté après l'image
    base = build.apply_writes(stock, tweaks)[0] + pl         # l'« origine » de la comparaison : les autres tweaks seuls
    img = build.apply_writes(stock, tweaks + [tweak])[0] + pl
    print(f"firmware : {', '.join(t['id'] for t in tweaks + [tweak])}")
    print("accroches")
    hook_tests(stock, img, tweak)
    print("trig existant, appui de durée croissante (mode grille, pas 0)")
    existing(base, img)
    print("pas vide")
    empty(base, img)
    print("tour de potard pendant l'appui")
    knob(base, img)
    print("deux trigs")
    two_keys(base, img)
    print("changements de trig au relâchement")
    changes(base, img)
    print("compteur du minuteur")
    wrap(img)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
