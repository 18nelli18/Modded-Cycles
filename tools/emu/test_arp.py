#!/usr/bin/env python3
"""Preuve de l'arpégiateur (notes/32, tweaks/model-cycles_OS1.13/40-arp.json) : le code du tweak et celui de l'OS,
exécutés fonction par fonction sur le MAIN OS modifié.

  0. Accroches des notes jouées (0x4001a1c4, piste en d3 ; 0x4001d25e, piste en d2), à la place de la lecture de Rte :
     rendent Rte comme 0x40016086 et transmettent le réglage de l'arpège de la piste (son objet, octet +512).
  1. Filtre du jeu en direct (accroche 0x40058e28) : instructions rejouées (d0, d1, d2), première note (le retrig
     d'origine démarre), notes ajoutées (ignorées par l'OS, entrées dans l'arpège), fins de note (ignorées tant qu'il
     reste des notes, la dernière devient la fin de la note en cours), sens OFF (retrig d'origine), liste remise à zéro
     quand le retrig s'est arrêté, autres événements intacts.
  2. Répétitions (accroche 0x400587f6, vraie copie 0x40091f20) : la suite de notes de chaque sens, avec 1 et 2 octaves,
     le reste de l'événement copié tel quel ; sens OFF : la note gardée.
  3. Menu FUNC + RETRIG (vrai constructeur 0x4002d138) : cinq lignes, les deux dernières avec nos fonctions ; libellés
     « Arp » et « Oct » (vraie std::string) ; affichage (UP… et 1 à 4) ; changements bornés de l'octet +512, signalés
     comme ceux de Len, et transmis tout de suite pour la piste sélectionnée.
  Le réglage arrive au côté audio par les accroches de 0 (l'objet de la piste, comme pour Rte), dans tous les tests.
  4. Sans le tweak, le menu garde ses trois lignes et les accroches leurs octets d'origine.
  5. De bout en bout, par la vraie boucle d'événements de l'interruption audio.
  6. Live rec (notes/32 §11) : l'arpège envoie à l'interface, comme des touches, les notes qu'il joue (note puis fin de
     note avec sa durée) ; une seule note sur 1 octave : un seul message, avec la vitesse du retrig (un pas avec retrig,
     comme d'origine) ; rien hors du live rec. Par les vraies fonctions de l'OS (0x4008171e, 0x4008145e) : ses messages
     de touche avec retrig ne partent plus (sauf pas tenus, sens OFF, sans retrig) et ceux de l'arpège leur sont
     identiques octet pour octet.

    python3 tools/emu/test_arp.py --cycles model-cycles_OS1.13.syx \\
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_model_tg as TM          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "40-arp.json"
FAIL = []
EV, EV2 = 0x93100000, 0x93100100                  # événements de test
UI_CFG = 0                                         # adresse de ui_cfg (symbols du tweak)
RING = 0                                           # adresse de ring (tampons des messages du live rec)
RTG = 0x40a78d58
CUR = 0x40fe4cb4
MODES = ["UP", "DOWN", "UPDN", "RAND", "PLAY", "OFF"]


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Emu(t7.UI):
    def __init__(self, img):
        super().__init__(img)
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        self.uc.mem_map(0x80000000, 0x20000)      # SRAM interne : l'heure audio (0x8000184c), lue par le live rec
        self.heap = 0x92000000
        self.uc.hook_add(UC_HOOK_CODE, self._new, begin=0x400802e0, end=0x400802e0)
        self.uc.hook_add(UC_HOOK_CODE, self._ret, begin=0x400802ec, end=0x400802ec)
        self.img_ = img
        self.fn = self.call
        self.track = Track(self, 0x93400000)

    def _pop(self, uc, d0=None):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        if d0 is not None:
            uc.reg_write(mk.UC_M68K_REG_D0, d0)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def _new(self, uc, addr, size, ud):            # operator new : un tas factice
        n = struct.unpack(">I", uc.mem_read(uc.reg_read(mk.UC_M68K_REG_A7) + 4, 4))[0]
        a, self.heap = self.heap, (self.heap + n + 15) & ~15
        uc.mem_write(a, b"\xa5" * n)
        self._pop(uc, a)

    def _ret(self, uc, addr, size, ud):            # operator delete
        self._pop(uc)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a, signed=False):
        return struct.unpack(">i" if signed else ">I", self.uc.mem_read(a, 4))[0]

    def cfg(self, t, byte):
        return play_cfg(self, t, byte)

    def retrig(self, t, running):
        self.w32(RTG + 28 * t + 4, 0xffffffff if running else 0)
        self.w32(RTG + 28 * t + 20, 0x93300000 if running else 0)

    def event(self, a, onoff, t, note, src=2, flags=0x38001 | 0x8000):
        self.uc.mem_write(a, bytes(80))
        for off, v in ((4, onoff), (8, t), (12, src), (22, 100 << 8), (28, note), (40, flags)):
            if off == 22:
                self.uc.mem_write(a + off, struct.pack(">H", v))
            else:
                self.w32(a + off, v)

    def filt(self, hook):
        """jsr de l'accroche 0x40058e28, a2 = l'événement ; renvoie (d0, d1, d2) et l'événement."""
        self.uc.reg_write(mk.UC_M68K_REG_A2, EV)
        for r in (mk.UC_M68K_REG_D3, mk.UC_M68K_REG_D4, mk.UC_M68K_REG_D5, mk.UC_M68K_REG_A3):
            self.uc.reg_write(r, 0x5a5a5a5a)
        self.call(hook)
        keep = all(self.uc.reg_read(r) == 0x5a5a5a5a for r in
                   (mk.UC_M68K_REG_D3, mk.UC_M68K_REG_D4, mk.UC_M68K_REG_D5, mk.UC_M68K_REG_A3)) \
            and self.uc.reg_read(mk.UC_M68K_REG_A2) == EV
        regs = tuple(self.uc.reg_read(r) for r in (mk.UC_M68K_REG_D0, mk.UC_M68K_REG_D1, mk.UC_M68K_REG_D2))
        return regs, keep, self.r32(EV + 12, True), self.r32(EV + 28, True)


def target(img, va):
    """Cible du jsr/jmp abs.l écrit en va."""
    return struct.unpack(">I", img[va - build.BASE + 2:va - build.BASE + 6])[0]


class Track:
    """Objet « piste du pattern » factice, comme ceux de 0x4000cfcc : vtable[10] rend ses données (+512 : arpège,
    +514 : Rte), vtable[4] est le signal de modification."""

    def __init__(self, emu, base, data=True):
        self.obj, self.vt, self.f10, self.f4, self.data = base, base + 0x100, base + 0x200, base + 0x210, base + 0x1000
        emu.w32(self.obj, self.vt)
        emu.w32(self.vt + 40, self.f10)
        emu.w32(self.vt + 16, self.f4)
        emu.uc.mem_write(self.f10, b"\x20\x3c" + struct.pack(">I", self.data if data else 0) + b"\x4e\x75")
        emu.uc.mem_write(self.f4, b"\x4e\x75")
        emu.uc.mem_write(self.data, bytes(722))


def play_cfg(emu, t, byte, rate=9):
    """Le réglage de la piste t, tel qu'une note jouée le lit : par l'accroche de 0x4001a1c4 (piste en d3) ou de
    0x4001d25e (piste en d2), selon t ; renvoie ce qu'elle rend (Rte)."""
    tr = emu.track
    emu.uc.mem_write(tr.data + 512, bytes([byte]))
    emu.uc.mem_write(tr.data + 514, bytes([rate]))
    site, reg = (0x4001a1c4, mk.UC_M68K_REG_D3) if t % 2 else (0x4001d25e, mk.UC_M68K_REG_D2)
    emu.uc.reg_write(reg, t)
    return emu.fn(target(emu.img_, site), tr.obj) & 0xff


# --- 0. accroches des notes jouées --------------------------------------------------------------------------------
def rate_tests(img):
    e = Emu(img)
    keep = (mk.UC_M68K_REG_D4, mk.UC_M68K_REG_D5, mk.UC_M68K_REG_D6, mk.UC_M68K_REG_A2, mk.UC_M68K_REG_A3)
    for site, reg, t, name in ((0x4001a1c4, mk.UC_M68K_REG_D3, 3, "d3"), (0x4001d25e, mk.UC_M68K_REG_D2, 4, "d2")):
        e.uc.mem_write(e.track.data + 512, bytes([0x1a]))
        e.uc.mem_write(e.track.data + 514, bytes([7]))
        e.uc.reg_write(reg, t)
        for r in keep:
            e.uc.reg_write(r, 0x5a5a5a5a)
        r = e.call(target(img, site), e.track.obj)
        got = e.uc.mem_read(UI_CFG, 6)[t]
        kept = all(e.uc.reg_read(r_) == 0x5a5a5a5a for r_ in keep) and e.uc.reg_read(reg) == t
        check(r & 0xff == 7 and got == 0x1a and kept,
              f"note jouée, accroche de {site:#x} (piste en {name}) : rend Rte (7) comme 0x40016086, transmet le "
              f"réglage de la piste {t} (0x1a), registres gardés")
    empty = Track(e, 0x93480000, data=False)
    before = bytes(e.uc.mem_read(UI_CFG, 6))
    e.uc.reg_write(mk.UC_M68K_REG_D3, 1)
    r = e.call(target(img, 0x4001a1c4), empty.obj)
    check(r & 0xff == 0 and bytes(e.uc.mem_read(UI_CFG, 6)) == before,
          "objet sans données : rend 0 comme 0x40016086, rien de transmis")
    e.uc.reg_write(mk.UC_M68K_REG_D3, 6)
    e.call(target(img, 0x4001a1c4), e.track.obj)
    check(bytes(e.uc.mem_read(UI_CFG, 6)) == before, "piste hors 0..5 : rien de transmis")


# --- 1. filtre ----------------------------------------------------------------------------------------------------
def filter_tests(img):
    e = Emu(img)
    hook = target(img, 0x40058e28)
    t = 2
    e.cfg(t, 0)                                   # UP, 1 octave
    e.retrig(t, False)
    e.event(EV, 1, t, 60)
    regs, keep, src, note = e.filt(hook)
    check(regs == (2, 0xffffffff, t) and keep and src == 2,
          "1re note avec retrig : laissée à l'OS (le retrig d'origine démarre) ; d0/d1/d2 rejoués, registres gardés")
    e.retrig(t, True)                             # l'OS a démarré le retrig
    for n in (67, 64):
        e.event(EV, 1, t, n)
        regs, keep, src, note = e.filt(hook)
        check(src == -1 and regs[0] == 0xffffffff and keep,
              f"note {n} ajoutée pendant l'arpège : ignorée par l'OS (+12 = -1, d0 = -1 : le traitement saute)")
    e.event(EV, 1, t, 64)
    _, _, src, _ = e.filt(hook)
    check(src == -1, "note déjà tenue rejouée : ignorée, pas de doublon")
    e.event(EV, 1, t, 72, flags=0x30001)          # sans retrig
    _, _, src, _ = e.filt(hook)
    check(src == 2, "note sans retrig sur la piste : laissée à l'OS (il arrête le retrig)")
    e.event(EV, 1, t, 72, flags=0x38001 | 0x8000 | 0x40000)
    _, _, src, _ = e.filt(hook)
    check(src == 2, "répétition (0x40000) : laissée à l'OS")
    e.event(EV, 1, t, 72, src=1)
    _, _, src, _ = e.filt(hook)
    check(src == 1, "note du séquenceur (+12 = 1) : intacte")
    e.event(EV, 2, t, 67)
    _, _, src, note = e.filt(hook)
    check(src == -1 and note == 67, "fin de la note 67, deux autres tenues : ignorée, l'arpège continue")
    e.event(EV, 2, t, 61)
    _, _, src, note = e.filt(hook)
    check(src == 2 and note == 61, "fin d'une note jamais tenue : laissée à l'OS")
    e.event(EV, 2, t, 60)
    _, _, src, note = e.filt(hook)
    check(src == -1, "fin de la note 60, une reste tenue : ignorée")
    e.w32(CUR + 4 * t, 76)                        # la note en cours : la dernière jouée par l'arpège
    e.event(EV, 2, t, 64)
    _, _, src, note = e.filt(hook)
    check(src == 2 and note == 76,
          "fin de la dernière note tenue : devient la fin de la note en cours (76), l'OS arrête le retrig")
    # sens OFF : retrig d'origine
    e.cfg(t, 5)
    e.retrig(t, False)
    e.event(EV, 1, t, 60)
    e.filt(hook)
    e.retrig(t, True)
    e.event(EV, 1, t, 62)
    _, _, src, _ = e.filt(hook)
    check(src == 2, "sens OFF : une 2e note passe à l'OS (elle remplace la 1re, comme d'origine)")
    e.event(EV, 2, t, 60)
    _, _, src, note = e.filt(hook)
    check(src == 2 and note == 60, "sens OFF : les fins de note passent à l'OS telles quelles")
    # liste périmée : retrig arrêté par l'OS entre-temps
    e.cfg(t, 0)
    e.retrig(t, False)
    e.event(EV, 1, t, 50)
    e.filt(hook)
    e.retrig(t, True)
    e.event(EV, 1, t, 55)
    e.filt(hook)
    e.retrig(t, False)                            # le séquenceur a arrêté le retrig
    e.event(EV, 2, t, 50)
    _, _, src, note = e.filt(hook)
    check(src == 2 and note == 50, "retrig arrêté par l'OS : liste oubliée, la fin de note passe à l'OS")
    for ty, desc in ((6, "répétition programmée (type 6)"), (3, "autre type")):
        e.event(EV, 1, t, 60)
        e.w32(EV, ty)
        regs, _, src, _ = e.filt(hook)
        check(src == 2 and regs == (2, 0xffffffff, t), f"{desc} : intact, instructions rejouées")
    e.event(EV, 1, 6, 60)
    regs, _, src, _ = e.filt(hook)
    check(src == 2 and regs[2] == 6, "piste hors 0..5 : intact")


# --- 2. répétitions -----------------------------------------------------------------------------------------------
def held(e, t, notes, cfg):
    """Notes tenues dans cet ordre (filtre), retrig en marche ; renvoie l'accroche de la répétition."""
    hook = target(e.img_, 0x40058e28)
    e.cfg(t, cfg)
    e.retrig(t, False)
    for k, n in enumerate(notes):
        e.event(EV, 1, t, n)
        e.filt(hook)
        e.retrig(t, True)


def repeats(e, t, n):
    copy = target(e.img_, 0x400587f6)
    out = []
    e.event(EV2, 1, t, 60, flags=0x38001 | 0x8000)       # l'événement gardé (la 1re note)
    e.w32(EV2 + 56, 9)
    for _ in range(n):
        e.uc.mem_write(EV, b"\xee" * 80)
        e.call(copy, EV, EV2)
        out.append(e.r32(EV + 28, True))
    same = bytes(e.uc.mem_read(EV, 28)) == bytes(e.uc.mem_read(EV2, 28)) and \
        bytes(e.uc.mem_read(EV + 32, 48)) == bytes(e.uc.mem_read(EV2 + 32, 48))
    return out, same


def repeat_tests(img):
    t = 4
    want = {
        (0, (60, 67, 64)): [64, 67, 60, 64, 67, 60],                  # UP
        (1, (60, 67, 64)): [67, 64, 60, 67, 64, 60],                  # DOWN : sous 60 rien, on repart d'en haut
        (2, (60, 67, 64)): [64, 67, 64, 60, 64, 67, 64, 60],          # UPDN, sans rejouer les bouts
        (4, (60, 67, 64)): [67, 64, 60, 67, 64, 60],                  # PLAY : ordre de jeu
        (0 | 1 << 3, (60, 67, 64)): [64, 67, 72, 76, 79, 60, 64],     # UP, 2 octaves
        (4 | 1 << 3, (60, 67, 64)): [67, 64, 72, 79, 76, 60, 67],     # PLAY, 2 octaves
        (2, (60,)): [60, 60, 60],                                     # une seule note : le retrig d'origine
        (0 | 3 << 3, (60,)): [72, 84, 96, 60, 72],                    # une note, 4 octaves
        (0 | 3 << 3, (100,)): [112, 124, 100, 112],                   # 4 octaves bornées à 127
    }
    for (c, notes), exp in want.items():
        e = Emu(img)
        held(e, t, notes, c)
        got, same = repeats(e, t, len(exp))
        check(got == exp and same, f"{MODES[c & 7]:4s} {(c >> 3) + 1} oct., notes {notes} : {got}"
              + (" ; le reste de l'événement copié tel quel" if same else " ; COPIE ALTÉRÉE"))
    e = Emu(img)
    held(e, t, (60, 64, 67, 71), 3)
    got, _ = repeats(e, t, 40)
    check(set(got) <= {60, 64, 67, 71} and len(set(got)) == 4 and all(a != b for a, b in zip(got, got[1:])),
          f"RAND : 40 répétitions dans les notes tenues, toutes jouées, jamais deux fois de suite ({got[:10]}…)")
    e = Emu(img)
    held(e, t, (60, 64), 0)
    e.cfg(t, 5)                                   # passé à OFF pendant l'arpège
    got, _ = repeats(e, t, 3)
    check(got == [60, 60, 60], "sens OFF : la répétition rejoue la note gardée (retrig d'origine)")


# --- 3. menu ------------------------------------------------------------------------------------------------------
SEL = 3                                           # piste sélectionnée pendant les changements du menu


def menu(img):
    e = Emu(img)
    e.sel = None
    items, drawn, notes = [], [], []
    o = e.track

    def hook(uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        a = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
        if addr == 0x400734b0:
            fns = []
            for p in a[1:5]:
                st0, _, mgr, inv = struct.unpack(">4I", uc.mem_read(p, 16))
                fns.append((mgr, inv, struct.unpack(">I", uc.mem_read(st0, 4))[0]))
            items.append(fns)
        elif addr == 0x4000f23e:                     # la piste du pattern sélectionné : la nôtre
            e._pop(uc, o.obj)
        elif addr == 0x40012412 and e.sel is not None:   # numéro de la piste sélectionnée
            e._pop(uc, e.sel)
        elif addr == 0x40071a04:
            drawn.append(a[:7])
            e._pop(uc)
        elif addr in (0x40072260, 0x40072080):
            e._pop(uc)
        elif addr == o.f4:
            notes.append(struct.unpack(">I", uc.mem_read(a[1], 4))[0])
    for va in (0x400734b0, 0x4000f23e, 0x40012412, 0x40071a04, 0x40072260, 0x40072080, o.f4):
        e.uc.hook_add(UC_HOOK_CODE, hook, begin=va, end=va)
    view = 0x93000000
    e.uc.mem_write(view, bytes(0x400))
    e.call(0x4002d138, view, count=5_000_000)
    return e, items, drawn, notes, view


def menu_tests(img, stock):
    e, items, drawn, notes, view = menu(img)
    ret_ok = e.uc.reg_read(mk.UC_M68K_REG_PC) == t7.STOP and not e.bad
    check(len(items) == 5 and ret_ok, f"constructeur du menu : {len(items)} lignes, retour normal")
    if len(items) < 5:
        return
    for k, name in enumerate(("Arp", "Oct")):
        lab, press, draw, chg = items[3 + k]
        ok = all(f[0] == 0x4002cf00 for f in items[3 + k]) and press[1:] == (0x4002ccd0, view) \
            and draw[2] == k and chg[2] == k
        s = bytes(e.uc.mem_read(lab[2], 4)).split(b"\0")[0].decode()
        # libellé : l'appel avec a0 = adresse de la std::string, (sp+4) = la std::function
        fn = 0x93600000
        e.uc.mem_write(fn, struct.pack(">IIII", e.heap, 0, 0x4002cf00, lab[1]))
        e.w32(e.heap, lab[2])
        e.heap += 16
        sret = 0x93600100
        e.uc.mem_write(sret, bytes(32))
        e.uc.reg_write(mk.UC_M68K_REG_A0, sret)
        sp = t7.STACK - 0x400
        e.uc.mem_write(sp, struct.pack(">II", t7.STOP, fn))
        e.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        e.uc.emu_start(lab[1], t7.STOP, count=200_000)
        got = std_string(e, sret)
        check(ok and s == name and got == name,
              f"ligne {name} : gestionnaire 0x4002cf00, appui d'origine 0x4002ccd0, libellé « {got} » (std::string)")
    # affichage et changements, sur la piste factice
    data = e.track.data + 512
    fa, fo = make_fn(e, items[3][2]), make_fn(e, items[4][2])
    ca, co = make_fn(e, items[3][3]), make_fn(e, items[4][3])

    def show(fn):
        drawn.clear()
        e.call(items[3 + (fn == fo)][2][1], fn, 0, 0x93700000, 0x93710000, 7)
        d = drawn[-1]
        fmt = cstr(e, d[5])
        val = cstr(e, d[6]) if fmt == "%s" else d[6]
        return fmt, val, d[2] == 0x93710000 + 24 and d[3] == 7 and d[4] == 4

    for byte, mode, octs in ((0, "UP", 1), (2 | 2 << 3, "UPDN", 3), (4 | 3 << 3, "PLAY", 4), (7, "UP", 1)):
        e.uc.mem_write(data, bytes([byte]))
        fa_ = show(fa)
        fo_ = show(fo)
        check(fa_ == ("%s", mode, True) and fo_ == ("%d", octs, True),
              f"affichage, octet +512 = 0x{byte:02x} : Arp {fa_[1]}, Oct {fo_[1]} (formats « %s » et « %d », place de Len)")
    e.uc.mem_write(data, bytes([0x80 | 1 << 3 | 1]))   # bit 7 étranger : gardé
    e.sel = SEL
    seq = []
    for fn, item, delta in ((ca, 3, 1), (ca, 3, 1), (ca, 3, 9), (ca, 3, -20), (co, 4, 1), (co, 4, 5), (co, 4, -1)):
        notes.clear()
        e.call(items[item][3][1], fn, 0, delta & 0xffffffff)
        seq.append((bytes(e.uc.mem_read(data, 1))[0], notes[:], e.uc.mem_read(UI_CFG, 6)[SEL]))
    want = [0x8a, 0x8b, 0x8d, 0x88, 0x90, 0x98, 0x90]
    check([b for b, _, _ in seq] == want and all(n == [0x400ff5ac] for _, n, _ in seq),
          f"changements bornés (Arp 0..5, Oct 1..4), autres bits gardés : {[hex(b) for b, _, _ in seq]} ; "
          "chacun signalé (0x400ff5ac, comme Len)")
    check(all(b == u for b, _, u in seq),
          f"chaque changement est transmis tout de suite au côté audio pour la piste sélectionnée ({SEL + 1})")
    # sans le tweak : trois lignes
    _, items0, _, _, _ = menu(stock)
    check(len(items0) == 3, "OS d'origine : le menu garde ses trois lignes")


def make_fn(e, f):
    """Une std::function comme celles du menu : stockage -> fermeture (4 o) = la valeur gardée."""
    mgr, inv, val = f
    clo = e.heap
    e.heap += 16
    e.w32(clo, val)
    fn = e.heap
    e.heap += 16
    e.uc.mem_write(fn, struct.pack(">IIII", clo, 0, mgr, inv))
    return fn


def cstr(e, a):
    return bytes(e.uc.mem_read(a, 16)).split(b"\0")[0].decode()


def std_string(e, a):
    """Texte d'une std::string de la libstdc++ de l'OS (ancienne ABI à compteur : un pointeur vers les caractères,
    la longueur 12 o avant)."""
    p = struct.unpack(">I", e.uc.mem_read(a, 4))[0]
    n = struct.unpack(">I", e.uc.mem_read(p - 12, 4))[0]
    return bytes(e.uc.mem_read(p, n)).decode() if 0 < n < 64 else ""


# --- 5. de bout en bout : la vraie boucle d'événements de l'interruption audio --------------------------------------
KIT = 0x4f000000                                  # sons du kit factices (à zéro)
POOL3 = 0x4f100000                                # 3e réserve d'objets de la file (allouée par malloc sur la machine)
MSG = 0x4e300000
FRAME = 0x9000f000                                # cadre de l'interruption (fp) ; ses variables en dessous
UIQ = 0x423f0000                                  # file de l'interface (*0x40149250) : une valeur, jamais lue
UIST = 0x423f1000                                 # état de l'interface (*0x40fe4218) : octet +359 = live rec
HEAP = 0x423f2000                                 # tas factice (au-dessus de la BSS de l'OS, 0x423380b0)
BANK = 0x406fa040                                 # banque de patterns du séquenceur (30 710 o par pattern, 0x4008178e)


class Audio:
    """La boucle d'événements de l'interruption audio (0x40058d46 -> 0x400591e4), avec la file et les réserves de
    l'OS (0x40091d94) ; les événements y entrent par 0x4005894a, comme depuis l'interface (0x4008171e)."""

    def __init__(self, img, end=None, payload=None):
        self.e = TM.engine(img, end=end, payload=payload)
        self.uc = self.e.uc
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        w = self.w32
        w(0x40fde8f8, POOL3)
        self.e.call(0x40091d94, 0x42)
        self.img_ = img
        self.fn = self.e.call
        self.track = Track(self, 0x4e400000)
        w(0x800017e4, KIT)                         # sons du kit : déjà chargés (pas de recopie)
        w(0x800017e8, KIT + 628)
        for t in range(6):
            w(0x800015a0 + (153 + t) * 4, KIT)
            w(0x800015a0 + (147 + t) * 4, KIT + 0x1c + 100 * t)
        w(0x40149310, 120 * 120)
        self.now = 1_000_000
        self.heap = HEAP                           # operator new (arp_rate alloue les tampons du live rec)
        self.uc.hook_add(UC_HOOK_CODE, self._new, begin=0x400802e0, end=0x400802e0)

    def _new(self, uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        n = struct.unpack(">I", uc.mem_read(sp + 4, 4))[0]
        a, self.heap = self.heap, (self.heap + n + 15) & ~15
        uc.reg_write(mk.UC_M68K_REG_D0, a)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a, signed=False):
        return struct.unpack(">i" if signed else ">I", self.uc.mem_read(a, 4))[0]

    def cfg(self, t, byte):
        return play_cfg(self, t, byte)

    def send(self, onoff, t, note, rate=9):
        """Un message de note comme ceux de 0x4008171e (retrig, durée 127 : tant que la note est tenue)."""
        m = [0] * 14
        m[0], m[1], m[2], m[3], m[5], m[8] = t, note, 100, onoff, 0xffffffff, 0x40
        if onoff == 1:
            m[4], m[9], m[10] = 0x38081, rate, 127
        self.uc.mem_write(MSG, struct.pack(">14I", *[x & 0xffffffff for x in m]))
        self.w32(0x8000184c, self.now)
        self.e.call(0x4005894a, MSG)

    def run(self, limit=None):
        """Une passe de la boucle : les événements immédiats, et les datés avant limit. Renvoie le masque des pistes
        déclenchées (d4) ; None si la boucle ne finit pas normalement."""
        uc = self.uc
        uc.mem_write(FRAME - 168, bytes(168))
        self.w32(FRAME - 80, self.now if limit is None else limit)
        self.w32(0x8000184c, self.now)
        sp = FRAME - 168 - 0x100
        uc.mem_write(sp, bytes(8))
        for r, v in ((mk.UC_M68K_REG_A6, FRAME), (mk.UC_M68K_REG_A7, sp), (mk.UC_M68K_REG_D2, 0),
                     (mk.UC_M68K_REG_D5, 0), (mk.UC_M68K_REG_D6, 0)):
            uc.reg_write(r, v)
        uc.emu_start(0x40058d46, 0x400591e4, count=2_000_000)
        if uc.reg_read(mk.UC_M68K_REG_PC) != 0x400591e4 or self.e.unmapped:
            return None
        return uc.reg_read(mk.UC_M68K_REG_D4)

    def next_time(self):
        """Heure du prochain lot daté de la file, ou None."""
        b = self.r32(0x40fe15fc)
        while b and self.r32(b) != 0:
            b = self.r32(b + 16)
        return self.r32(b + 4) if b else None

    def tick(self, t):
        """Le prochain lot daté ; renvoie la note jouée sur la piste t (ou None), ou False s'il n'y a plus rien."""
        nt = self.next_time()
        if nt is None:
            return False
        self.now = nt
        mask = self.run(nt + 1)
        return self.state(t)[0] if mask and mask >> t & 1 else None

    def state(self, t):
        return (self.r32(CUR + 4 * t, True), self.r32(0x80001830 + 4 * t, True) >> 16,
                self.r32(RTG + 28 * t + 4, True), self.r32(RTG + 28 * t + 20))


def e2e_tests(img, end=None, payload=None):
    a = Audio(img, end, payload)
    t = 1
    a.cfg(t, 0)                                   # UP, 1 octave
    a.send(1, t, 60)
    mask = a.run()
    cur, pitch, end, copy = a.state(t)
    check(mask is not None and mask >> t & 1 and cur == 60 and pitch == 60 and end == -1 and copy and a.next_time(),
          "note 60 avec retrig : jouée (piste déclenchée, note en cours, hauteur), retrig sans fin en place, "
          "1re répétition programmée")
    a.send(1, t, 64)
    mask = a.run()
    cur, _, end, _ = a.state(t)
    check(mask == 0 and cur == 60 and end == -1, "note 64 ajoutée : pas jouée tout de suite (le rythme continue)")
    played, ticks = [], 0
    while len(played) < 6 and ticks < 3000:
        n = a.tick(t)
        ticks += 1
        if n is False:
            break
        if n is not None:
            played.append(n)
    pitch = a.state(t)[1]
    check(played == [64, 60, 64, 60, 64, 60] and pitch == played[-1],
          f"répétitions par la vraie boucle et la vraie copie : {played} (UP sur 60 et 64, en {ticks} tics), "
          "hauteur suivie")
    a.send(2, t, 60)
    mask = a.run()
    _, _, end, copy = a.state(t)
    check(mask == 0 and end == -1 and copy, "fin de la note 60, la 64 reste tenue : le retrig continue")
    after = []
    for _ in range(3000):
        n = a.tick(t)
        if n is False or len(after) >= 3:
            break
        if n is not None:
            after.append(n)
    check(after == [64, 64, 64], f"ensuite, seule la 64 est répétée : {after}")
    a.send(2, t, 64)
    a.run()
    cur, _, end, copy = a.state(t)
    check(cur == -1 and end == 0 and copy == 0, "fin de la dernière note : l'OS arrête le retrig (copie libérée)")
    left = [a.tick(t) for _ in range(60)]
    check(not any(n not in (None, False) for n in left) and False in left,
          "plus aucune répétition ensuite, la file se vide")
    # DOWN sur 2 octaves, puis passage à UP pendant que les notes sont tenues (comme un changement dans le menu)
    c = Audio(img, end, payload)
    c.cfg(t, 1 | 1 << 3)
    c.send(1, t, 60)
    c.run()
    c.send(1, t, 64)
    c.run()

    def take(a_, n):
        out = []
        for _ in range(3000):
            r = a_.tick(t)
            if r is False or len(out) >= n:
                break
            if r is not None:
                out.append(r)
        return out
    down = take(c, 6)
    check(down == [76, 72, 64, 60, 76, 72], f"DOWN sur 2 octaves (60 et 64), vraie boucle : {down}")
    c.cfg(t, 1 << 3)
    up = take(c, 4)
    check(up == [76, 60, 64, 72], f"passé à UP (2 octaves) pendant que les notes sont tenues : {up}")
    c.cfg(t, 0)
    one = take(c, 3)
    check(one == [60, 64, 60], f"puis 1 octave : {one}")
    # sens OFF : le retrig d'origine, une seule note répétée, la dernière pressée
    b = Audio(img, end, payload)
    b.cfg(t, 5)
    b.send(1, t, 60)
    b.run()
    b.send(1, t, 64)
    b.run()
    rep = []
    for _ in range(3000):
        n = b.tick(t)
        if n is False or len(rep) >= 3:
            break
        if n is not None:
            rep.append(n)
    check(rep == [64, 64, 64], f"sens OFF : la nouvelle note remplace l'autre, comme d'origine : {rep}")


# --- 6. live rec : l'arpège envoie à l'interface les notes qu'il joue (notes/32 §11) -------------------------------
def live(x, on=True, playing=True):
    """Live rec (octet +359 de l'état de l'interface, 0x400cf9a8 déjà construit) et séquenceur en lecture
    (0x4005481a == 1), comme les lit 0x4006ba76."""
    x.w32(0x40fe4218, UIST)
    x.uc.mem_write(UIST + 359, bytes([int(on)]))
    x.w32(0x40a78874, int(playing))
    x.w32(0x40a7883c, 0)


class Ui:
    """L'interface vue de l'arpège : la file 0x40149250 (0x40001fba intercepté, messages gardés), le calcul du pas
    0x40056178 (remplacé : pas = heure / 1000 % 64, micro-décalage = piste + 1), et les messages que l'OS envoie lui-même
    par 0x40080bf6 (intercepté, gardés)."""

    def __init__(self, x):
        self.posted, self.ptrs, self.os = [], [], []
        x.w32(0x40149250, UIQ)
        for va, f in ((0x40001fba, self._post), (0x40056178, self._pos), (0x40080bf6, self._os)):
            x.uc.hook_add(UC_HOOK_CODE, f, begin=va, end=va)

    @staticmethod
    def _args(uc, n):
        return struct.unpack(f">{n}I", uc.mem_read(uc.reg_read(mk.UC_M68K_REG_A7) + 4, 4 * n))

    @staticmethod
    def _ret(uc):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def _post(self, uc, addr, size, ud):
        q, m = self._args(uc, 2)
        if q == UIQ:
            self.posted.append(bytes(uc.mem_read(m, 32)))
            self.ptrs.append(m)
        self._ret(uc)

    def _pos(self, uc, addr, size, ud):
        now, t, buf = self._args(uc, 3)
        uc.mem_write(buf, bytes([now // 1000 % 64, t + 1, 0]))
        self._ret(uc)

    def _os(self, uc, addr, size, ud):
        self.os.append(bytes(uc.mem_read(self._args(uc, 1)[0], 32)))
        self._ret(uc)


def msg(m):
    """Message de note pour l'interface : (ON/OFF, piste, note, vélocité, vitesse du retrig ou durée, pas, micro)."""
    on = struct.unpack_from(">I", m, 4)[0] == 0
    val = struct.unpack_from(">b" if on else ">i", m, 20)[0]
    return ("ON" if on else "OFF", m[8], m[16], m[17], val) + struct.unpack_from(">hh", m, 28)


def live_tests(img):
    t = 2
    hook, copy = target(img, 0x40058e28), target(img, 0x400587f6)

    def scene(cfg, notes, on=True, playing=True):
        e = Emu(img)
        ui = Ui(e)
        live(e, on, playing)
        e.cfg(t, cfg)                             # une note jouée : arp_rate, côté interface
        e.retrig(t, False)
        e.ring = e.r32(RING)
        e.ui = ui
        e.notes = notes
        return e

    def at(e, now):
        e.w32(0x8000184c, now)

    def key(e, n, now, onoff=1):
        at(e, now)
        e.event(EV, onoff, t, n)
        e.w32(EV + 56, 9)
        e.filt(hook)
        e.retrig(t, True)

    def rep(e, now):
        at(e, now)
        e.event(EV2, 1, t, e.notes[0])
        e.w32(EV2 + 56, 9)
        e.uc.mem_write(EV, b"\xee" * 80)
        e.call(copy, EV, EV2)
        return e.r32(EV + 28, True)

    def on_(n, rate, now):
        return ("ON", t, n, 100, rate, now // 1000, t + 1)

    def off(n, t0, now):
        return ("OFF", t, n, 0, (now >> 1) - (t0 >> 1), now // 1000, t + 1)

    # UP : 60 seul (un pas avec retrig), puis 64 ajoutée : chaque note jouée part, la précédente se termine
    e = scene(0, (60, 64))
    check(e.ring != 0, "1re note jouée (arp_rate, côté interface) : les 8 tampons des messages sont alloués")
    key(e, 60, 2000)
    r1 = rep(e, 3000)
    key(e, 64, 3500)
    played = [rep(e, 4000), rep(e, 5000), rep(e, 6000)]
    key(e, 60, 6500, 2)
    key(e, 64, 7000, 2)
    got = [msg(m) for m in e.ui.posted]
    want = [on_(60, 9, 2000), off(60, 2000, 4000), on_(64, -1, 4000), off(64, 4000, 5000), on_(60, -1, 5000),
            off(60, 5000, 6000), on_(64, -1, 6000), off(64, 6000, 7000)]
    check(r1 == 60 and played == [64, 60, 64] and got == want,
          f"UP, 60 puis 64 ajoutée : notes jouées {[r1] + played} ; messages {[g[:3] + g[4:5] for g in got]} "
          "(60 seule : une fois, avec la vitesse 9 ; ensuite chaque note jouée, la précédente terminée avec sa durée)")
    check(not e.ui.os, "aucun message de l'OS lui-même (rien ne passe par 0x40080bf6 côté audio)")
    # une seule note, 1 octave : le retrig d'origine, un seul message
    e = scene(0, (60,))
    key(e, 60, 2000)
    played = [rep(e, n) for n in (3000, 4000, 5000)]
    key(e, 60, 5500, 2)
    got = [msg(m) for m in e.ui.posted]
    check(played == [60, 60, 60] and got == [on_(60, 9, 2000), off(60, 2000, 5500)],
          f"une seule note, 1 octave : un pas avec retrig (vitesse 9), terminé au relâchement : {got}")
    # une seule note, 2 octaves : chaque note jouée
    e = scene(1 << 3, (60,))
    key(e, 60, 2000)
    played = [rep(e, n) for n in (3000, 4000)]
    key(e, 60, 4500, 2)
    got = [msg(m) for m in e.ui.posted]
    check(played == [72, 60] and got == [on_(60, -1, 2000), off(60, 2000, 3000), on_(72, -1, 3000),
                                         off(72, 3000, 4000), on_(60, -1, 4000), off(60, 4000, 4500)],
          f"une note, 2 octaves : chaque note jouée, sans retrig : {[g[:3] for g in got]}")
    # hors du live rec, séquenceur arrêté, sens OFF : rien
    for desc, cfg, on, playing in (("live rec arrêté", 0, False, True), ("séquenceur arrêté", 0, True, False),
                                   ("sens OFF (l'OS enregistre lui-même)", 5, True, True)):
        e = scene(cfg, (60, 64), on, playing)
        key(e, 60, 2000)
        key(e, 64, 2500)
        played = [rep(e, n) for n in (3000, 4000)]
        key(e, 60, 4500, 2)
        key(e, 64, 5000, 2)
        check(not e.ui.posted, f"{desc} : aucun message ({played})")
    # le live rec s'arrête pendant l'arpège : la note en cours se termine, plus rien ensuite
    e = scene(0, (60, 64))
    key(e, 60, 2000)
    key(e, 64, 2500)
    rep(e, 3000)
    live(e, False)
    rep(e, 4000)
    rep(e, 5000)
    key(e, 60, 5500, 2)
    key(e, 64, 6000, 2)
    got = [msg(m) for m in e.ui.posted]
    check(got == [on_(60, 9, 2000), off(60, 2000, 3000), on_(64, -1, 3000), off(64, 3000, 4000)],
          f"live rec arrêté pendant l'arpège : la note en cours se termine, plus rien ensuite : {[g[:3] for g in got]}")
    # plus de 8 messages : les tampons tournent (8 x 32 o)
    e = scene(0, (60, 64))
    key(e, 60, 2000)
    key(e, 64, 2500)
    for k in range(6):
        rep(e, 3000 + 1000 * k)
    want = [e.ring + 32 * (k % 8) for k in range(13)]
    check(len(e.ui.posted) == 13 and all(m[0] == 12 for m in e.ui.posted) and e.ui.ptrs == want,
          f"{len(e.ui.posted)} messages à la suite, tous complets (type 12) : les 8 tampons de 32 o tournent")


def live_e2e(img, end=None, payload=None):
    """Par les vraies fonctions de l'OS : 0x4008171e (touche) et 0x4008145e (relâchement), puis la vraie boucle."""
    t = 1

    def setup(on, cfg=0):
        a = Audio(img, end, payload)
        ui = Ui(a)
        a.w32(0x40a7887c, BANK)                    # pattern en cours (0x40054828) : le 1er de la banque
        a.uc.mem_write(BANK + 722 * t + 710, struct.pack(">H", 0x680))   # drapeaux de la piste : défaut (0x40061438)
        a.uc.mem_write(0x40fb680c, b"\xff" * 4 * 128 * 6)   # heures d'appui des notes : aucune (-1, comme au boot)
        live(a, on)
        a.cfg(t, cfg)
        return a, ui

    def press(a, n, held=0, rate=9):
        a.w32(0x8000184c, a.now)
        a.e.call(0x4008171e, t, n, 100, 0x40, held, 0xffffffff, rate)
        return a.run()

    def release(a, n):
        a.w32(0x8000184c, a.now)
        a.e.call(0x4008145e, t, n, 0x40)
        return a.run()

    # hors du live rec, puis en live rec : mêmes appuis, mêmes heures
    a, ui = setup(False)
    press(a, 60)
    a.now += 40_000
    release(a, 60)
    os_on, os_off = (ui.os + [None, None])[:2]
    check(len(ui.os) == 2 and not ui.posted and msg(os_on)[:3] == ("ON", t, 60) and msg(os_off)[:3] == ("OFF", t, 60),
          "hors du live rec : l'OS envoie lui-même le message de la touche et celui du relâchement ; l'arpège rien")
    b, ui = setup(True)
    press(b, 60)
    b.now += 40_000
    release(b, 60)
    ours = ui.posted + [b"", b""]
    check([msg(m)[0] for m in ui.os] == ["OFF"],
          "live rec : le message de la touche (retrig, arpège UP) ne part plus ; celui du relâchement, si")
    check(len(ui.posted) == 2 and ours[0] == os_on and ours[1] == os_off,
          f"live rec : l'arpège envoie la note puis sa fin, identiques octet pour octet à ceux de l'OS "
          f"({msg(os_on)} ; {msg(os_off)})")
    # les autres messages de touche partent comme d'origine
    for desc, cfg, held, rate in (("pas tenus (la note va à ces pas)", 0, 1, 9), ("sens OFF", 5, 0, 9),
                                  ("sans retrig", 0, 0, 0xffffffff)):
        c, ui = setup(True, cfg)
        press(c, 60, held, rate)
        check([msg(m)[:3] for m in ui.os] == [("ON", t, 60)] and not ui.posted,
              f"live rec, {desc} : le message de la touche part, comme d'origine")
    # un arpège en live rec, par la vraie boucle
    d, ui = setup(True)
    press(d, 60)
    t0 = d.now
    press(d, 64)
    played = []
    for _ in range(3000):
        n = d.tick(t)
        if n is False or len(played) >= 4:
            break
        if n is not None:
            played.append((n, d.now))
    release(d, 60)
    d.now += 1000
    release(d, 64)
    want, prev, pt = [("ON", t, 60, 100, 9)], 60, t0
    for n, now in played:
        want += [("OFF", t, prev, 0, (now >> 1) - (pt >> 1)), ("ON", t, n, 100, -1)]
        prev, pt = n, now
    want.append(("OFF", t, prev, 0, (d.now >> 1) - (pt >> 1)))
    got = [msg(m)[:5] for m in ui.posted]
    check([n for n, _ in played] == [64, 60, 64, 60] and got == want and all(m[0] == 12 for m in ui.posted),
          f"arpège UP 60 + 64 en live rec, vraie boucle : {[n for n, _ in played]} ; à l'interface : "
          f"{[g[0] + ' ' + str(g[2]) for g in got]}, durées = écarts entre les notes jouées")
    check([msg(m)[0] for m in ui.os] == ["OFF", "OFF"],
          "les deux touches : pas de message de note, seulement leurs relâchements")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="",
                    help="autres tweaks appliqués avant (ex. 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    dev = TWEAK.parent
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in dev.glob("*.json") if f.name != "device.json"}
    tweaks = [json.loads(by_id[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    tweaks.append(json.loads(TWEAK.read_text(encoding="utf-8")))
    p, _ = build.apply_writes(stock, tweaks)
    pl, _ = build.build_payload(tweaks, stock, args.syntakt)
    img = bytes(p) + pl
    blob = [t for t in tweaks if t["id"].startswith("model-tg")]
    end = build.BASE + len(stock) + blob[0]["append"]["size"] if blob else None
    syn = [t for t in tweaks if t.get("append", {}).get("syntakt")]
    payload = None
    if syn:
        import syntakt
        payload = (int(syn[0]["append"]["dest"], 16),
                   build.payload_runtime(syn[0], stock, syntakt.dsp_image(args.syntakt)))
    global UI_CFG, RING
    UI_CFG = int(tweaks[-1]["symbols"]["ui_cfg"], 16)
    RING = int(tweaks[-1]["symbols"]["ring"], 16)
    print(f"firmware : {', '.join(t['id'] for t in tweaks)}")
    print("accroches des notes jouées")
    rate_tests(img)
    print("filtre du jeu en direct")
    filter_tests(img)
    print("répétitions")
    repeat_tests(img)
    print("menu FUNC + RETRIG")
    menu_tests(img, stock)
    print("de bout en bout (vraie boucle d'événements de l'interruption audio)")
    e2e_tests(img, end, payload)
    print("live rec : l'arpège envoie à l'interface les notes qu'il joue")
    live_tests(img)
    print("live rec, par les vraies fonctions de l'OS et la vraie boucle")
    live_e2e(img, end, payload)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
