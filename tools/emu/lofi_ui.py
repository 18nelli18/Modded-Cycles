"""FINE (accord fin) sous MACHINES + PITCH, sur le code de l'interface de l'OS : la recherche du descripteur d'un
potard (0x4001e814, ou le slot 124 de la vtable de ParameterPageView quand un tweak l'a remplacé), l'application d'un
tour de potard avec FUNC (0x4000b7d6, l'objet des paramètres d'une piste), le texte de la valeur (le formateur de
l'objet d'interface du descripteur, vrai sprintf), et la fenêtre de valeur qui s'ouvre quand on tourne le potard
(0x4001d818, le slot 144 de la vtable de ParameterPageView), dessinée dans un écran de 128 × 64.

Avec Model-TG, l'enregistrement sous MACHINES porte FINE (43) en position 0 sur toutes les machines (notes/86 §8), et
tl_ui (tools/track_lofi.py) pose le pas d'un cran par détent (+0x50) de FINE et le texte / le dessin des descripteurs
1 / 2 (+0x20 / +0x30). Sans Model-TG, FINE n'est sous aucun potard et les 77 objets d'interface restent ceux de l'OS.

Utilisé par test_macro.py, test_macro_syntakt.py, test_acid_combos.py et test_retrosyn.py."""

import re
import struct

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

BASE = 0x40000400
IMAGE_LEN = 0x1a9d40
STOP, STACK, SCRATCH = 0x90000100, 0x90010000, 0x91000000
UI_INIT = 0x400de244                 # construit les objets d'interface des descripteurs
KNOB_LOOKUP = 0x4001e814             # (vue, potard, FUNC, -1) -> descripteur
KNOB_SLOT = 0x401005a8               # slot 124 de la vtable de ParameterPageView
MACHINE_OF = 0x4001e318              # (vue, piste) -> machine de la piste
EDIT = 0x4000b7d6                    # vt[32] de l'objet des paramètres d'une piste (vtable 0x400fd134)
VTABLE = 0x400fd134
UI_REC = 0x40a71754                  # objets d'interface, 100 o par descripteur
PITCH, FTUN = 42, 43
PITCH_KNOB = 2
PARAM_TABLE = 0x4010dce0
KEY_HELD, KEY_TABLE, KEY_BITS = 0x4007faf4, 0x4010ae5c, 0x40f95744   # (code) -> touche tenue ; code -> bit ; état
KEY_MACHINES = 5
PAGE_VT = 0x4010052c                 # vtable de ParameterPageView (slot 124 en 0x401005a8)
POPUP_SLOT = PAGE_VT + 144           # 0x4001d818 : (vue, bitmap, descripteur, valeur, drapeau, 1)
BITMAP = 0x40070172                  # Bitmap(this, largeur, hauteur, image, masque)
DRAW_TEXT = 0x40071a04               # (bitmap, police, x, y, alignement, format, ...)
DRAW_SPRITE = 0x40071da4             # (bitmap, sprite, x, y, mode)
BIG_FONT, FMT_S = 0x401429ec, 0x40124b58     # grande police de la fenêtre de valeur ; « %s »


class UI:
    """Le code de l'interface de l'OS, fonction par fonction : image, charge utile, BSS à zéro, tas factice."""

    def __init__(self, img, payload=None, end=None):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_write(BASE, img[:(end - BASE) if end else IMAGE_LEN])
        if payload:
            dst, data = payload
            uc.mem_map(dst, (len(data) + 0xfffff) & ~0xfffff)
            uc.mem_write(dst, data)
        uc.mem_map(0x90000000, 0x04000000)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad, self.hooks, self.calls, self.heap = [], {}, [], 0x93000000
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_CODE, self._hook)
        self.hooks.update({0x400802e0: ("new", 0), 0x400802ec: ("delete", 0), 0x400cf044: ("atexit", 0),
                           0x400c9afc: ("atexit", 0), 0x400f4dc6: ("guard", 1), 0x400f4e22: ("guard_done", 0)})
        self.call(UI_INIT, count=50_000_000)
        self.init_ok = not self.bad

    def _hook(self, uc, addr, size, ud):
        if addr in self.hooks:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">6I", uc.mem_read(sp + 4, 24))
            name, ret = self.hooks[addr]
            if name == "new":
                ret, self.heap = self.heap, (self.heap + args[0] + 15) & ~15
            self.calls.append((name, args))
            uc.reg_write(mk.UC_M68K_REG_D0, ret)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def u32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def call(self, fn, *args, count=20_000_000):
        sp = STACK - 0x400
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[a & 0xffffffff for a in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.bad.clear()
        self.uc.emu_start(fn, STOP, count=count)
        self.sp_ok = self.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        return self.uc.reg_read(mk.UC_M68K_REG_D0)

    def cstr(self, a):
        return bytes(self.uc.mem_read(a, 64)).split(b"\0")[0].decode("latin-1")

    def hold(self, code, held):
        """La touche de ce code tenue ou non, dans l'état que lit le vrai 0x4007faf4 (bit 0x4010ae5c[code] de
        0x40f95744) : la fonction tourne, ses registres écrasés (d0, d1, a0) avec elle."""
        bit = struct.unpack(">i", self.uc.mem_read(KEY_TABLE + 4 * code, 4))[0]
        v = self.uc.mem_read(KEY_BITS + (bit >> 3), 1)[0]
        v = v | 1 << (bit & 7) if held else v & ~(1 << (bit & 7))
        self.uc.mem_write(KEY_BITS + (bit >> 3), bytes([v]))

    def lookup(self, machine, knob, func, key=0):
        """Descripteur sous un potard pour une piste de cette machine : le vrai 0x4001e814 (par le slot 124, comme
        l'OS l'appelle), la machine de la piste et les singletons de l'écran donnés (pas de popup). key : MACHINES
        tenu (le vrai 0x4007faf4 répond)."""
        view = SCRATCH
        self.uc.mem_write(view + 104, struct.pack(">I", view + 0x200))
        self.uc.mem_write(view + 0x200, b"".join(struct.pack(">I", i) for i in range(1, 7)))   # vecteur [1..6]
        self.hooks.update({MACHINE_OF: ("machine", machine), 0x400cf9a8: ("ui", 0), 0x4006b736: ("popup", 0)})
        self.hooks.pop(KEY_HELD, None)
        self.hold(KEY_MACHINES, key)
        d = self.call(self.u32(KNOB_SLOT), view, knob, 0xffffffff if func else 0, 0xffffffff)
        self.hold(KEY_MACHINES, False)
        return d if self.sp_ok and not self.bad else None

    def edit_func(self, desc, cur, delta, fine=1):
        """Un tour de potard avec FUNC (fine = 1) ou sans (fine = 0) sur ce descripteur : le vrai 0x4000b7d6, sur un objet dont la
        lecture (vt[28]) rend cur et l'écriture (vt[24]) est notée ; rend la valeur écrite (bornée par 0x4000b274), ou sans
        FUNC la suite des valeurs écrites."""
        obj, vt = SCRATCH + 0x400, SCRATCH + 0x800
        self.uc.mem_write(vt, bytes(self.uc.mem_read(VTABLE, 0x80)))
        get, put = SCRATCH + 0xc00, SCRATCH + 0xc10
        self.uc.mem_write(get, b"\x4e\x75"); self.uc.mem_write(put, b"\x4e\x75")
        self.uc.mem_write(vt + 28, struct.pack(">I", get)); self.uc.mem_write(vt + 24, struct.pack(">I", put))
        self.uc.mem_write(obj, struct.pack(">II", vt, 0))
        self.hooks.update({get: ("get", cur & 0xffff if cur >= 0 else cur), put: ("put", 0)})
        self.calls.clear()
        self.call(EDIT, obj, desc, delta, 0, fine, 0, 1, 1)
        puts = [c for c in self.calls if c[0] == "put"]
        if not fine:                     # sans FUNC, l'OS écrit plusieurs fois : toutes les valeurs écrites
            return tuple(c[1][2] for c in puts) if puts and self.sp_ok and not self.bad else None
        return puts[0][1][2] if len(puts) == 1 and self.sp_ok and not self.bad else None

    def popup(self, desc, v, text_path=False):
        """La fenêtre de valeur de ce descripteur à cette valeur : le vrai 0x4001d818 (par le slot 144, comme l'OS),
        dans un écran 128 × 64 neuf ; rend ses pixels (colonne par colonne). La vue rend (vt[128]) un objet des
        paramètres d'une piste (vtable 0x400fd134). text_path : le chemin texte de l'OS pour ce descripteur (sans
        dessin, comme les paramètres sans jauge) : référence de ce que l'OS y écrit."""
        S = SCRATCH + 0x2000
        bmp, fb, view, pvt, stub, obj, ovt, ok = S, S + 0x100, S + 0x800, S + 0xa00, S + 0xe00, S + 0xe10, S + 0xf00, \
            S + 0xff0
        self.uc.mem_write(fb, bytes(0x400))
        self.call(BITMAP, bmp, 128, 64, fb, 0)
        self.uc.mem_write(pvt, bytes(self.uc.mem_read(PAGE_VT, 0x200)))
        self.uc.mem_write(pvt + 128, struct.pack(">I", stub))
        self.uc.mem_write(view, struct.pack(">I", pvt))
        self.uc.mem_write(ovt, bytes(self.uc.mem_read(VTABLE, 0x80)))
        self.uc.mem_write(obj, struct.pack(">II", ovt, 0))
        self.hooks[stub] = ("object", obj)
        r = UI_REC + 100 * desc
        saved = bytes(self.uc.mem_read(r + 0x2c, 4))
        if text_path:                    # sans dessin (+0x2c nul) ; la valeur est acceptée (vt[24], 0x4000c0a6)
            self.uc.mem_write(r + 0x2c, bytes(4))
            self.uc.mem_write(ovt + 24, struct.pack(">I", ok))
            self.hooks[ok] = ("valid", 1)
        self.hooks[DRAW_SPRITE] = ("sprite", 0)          # les jauges : des sprites construits au démarrage, notés
        self.calls.clear()
        self.call(self.u32(POPUP_SLOT), view, bmp, desc, v, 0, 1)
        self.uc.mem_write(r + 0x2c, saved)
        del self.hooks[DRAW_SPRITE]
        good = self.sp_ok and not self.bad
        sprites = [c[1][1] for c in self.calls if c[0] == "sprite"]
        return (bytes(self.uc.mem_read(fb, 0x400)), sprites) if good else None

    def glyph(self, ch):
        """Points allumés par ce caractère seul dans la grande police de la fenêtre de valeur (0x401429ec)."""
        S = SCRATCH + 0x6000
        bmp, fb, font, s = S, S + 0x100, S + 0x600, S + 0x700
        self.uc.mem_write(fb, bytes(0x400))
        self.call(BITMAP, bmp, 128, 64, fb, 0)
        self.call(0x40072260, font, BIG_FONT)
        self.uc.mem_write(s, ch.encode() + b"\0")
        self.call(DRAW_TEXT, bmp, font, 0x60, 0x22, 2, FMT_S, s)
        return sum(bin(x).count("1") for x in self.uc.mem_read(fb, 0x400))

    def text(self, desc, v):
        r = UI_REC + 100 * desc
        self.uc.mem_write(SCRATCH + 0x1000, bytes(32))
        self.call(self.u32(r + 0x20), r + 0x14, v, SCRATCH + 0x1000)
        return self.cstr(SCRATCH + 0x1000)


def pix(fb, x, y):
    w = struct.unpack(">I", fb[(x * 2 + y // 32) * 4:(x * 2 + y // 32) * 4 + 4])[0]
    return (w >> (31 - (y & 31))) & 1


def ascii_popup(fb, x0=64, x1=124, y0=22, y1=57):
    """La moitié droite de la fenêtre (y = 0 en bas de l'écran)."""
    return "\n".join(f"        y={y:2d}  " + "".join("#" if pix(fb, x, y) else "." for x in range(x0, x1))
                     for y in range(y1 - 1, y0 - 1, -1))


def want_text(fine):
    """Ce que macro.cc fait de FINE (notes/55) : RATE à gauche (en kHz), BITS à droite. En majuscules : la grande
    police de la fenêtre de valeur n'a pas de minuscules (sauf m)."""
    if fine == 64:
        return "OFF"
    if fine < 64:
        return f"{round(48 * 2 ** (-86 * (64 - fine) / 1536))}K"
    return f"{12 - (fine - 65) * 10 // 62}B"


def want_step(cur, delta):
    v = (cur + 0x80) & ~0xff
    s = (abs(delta) + 0xff) & ~0xff
    return min(max(v + (s if delta >= 0 else -s), 0), 0x7f00)


MACHINES_KNOBS = {2: FTUN, 3: 0x0d, 4: 1, 5: 2, 6: 0x0c, 7: 0x0b}   # MACHINES + potard -> descripteur
LOAD = re.compile(rb"\x41\xe8\x00\x40\x70\x4a\x61.\x70\x50\x61.\x61")


def load_at(img):
    """tl_load (tools/track_lofi.py), le crochet de snd_load_post de Model-TG, dans cette image : lea 64(%a0), %a0 ;
    moveq #74 ; ... ; None sans Model-TG."""
    m = LOAD.search(img)
    return BASE + m.start() if m else None


def records(u):
    return [bytes(u.uc.mem_read(UI_REC + 100 * d, 100)) for d in range(77)]


def fields(x, y):
    """Les décalages (octets) où deux objets d'interface diffèrent."""
    return tuple(i for i in range(0, 100, 4) if x[i:i + 4] != y[i:i + 4])


def run_load(u, addr):
    """tl_load tel que snd_load_post l'appelle : a0 = enregistrement, a1 = son, pile [d0][son][retour]."""
    rec, snd = SCRATCH + 0x10000, SCRATCH + 0x10100
    u.uc.mem_write(rec, bytes(0x80))
    u.uc.mem_write(snd, bytes(0x80))
    sp = STACK - 0x400
    u.uc.mem_write(sp, struct.pack(">III", 0, snd, STOP))
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.uc.reg_write(mk.UC_M68K_REG_A0, rec)
    u.uc.reg_write(mk.UC_M68K_REG_A1, snd)
    u.bad.clear()
    u.uc.emu_start(addr, STOP, count=20_000)
    return u.uc.reg_read(mk.UC_M68K_REG_PC) == STOP and not u.bad


def check_lofi(base_img, fw_img, payload, top, label, check, end=None, base_end=None, base_payload=None,
               base="l'OS d'origine", after=0, tg=None):
    """MACHINES + PITCH sur une piste MACRO (machine top) : FINE (43) avec Model-TG (tg : sa table de symboles,
    mod_held), PITCH (42) sans ; FINE garde le texte et la jauge de l'OS ; FUNC + un cran : un pas par détent avec
    Model-TG, le défaut de l'OS sans. after : machines ajoutées après MACRO (ACID, RETROSYN), mêmes règles."""
    a = UI(base_img, base_payload, end=base_end)
    b = UI(fw_img, payload, end=end)
    check(a.init_ok and b.init_ok, f"{label} : objets d'interface construits par l'OS (0x400de244)")

    def look(u, m, knob, func, key):
        """Une recherche de descripteur, MACHINES tenue ou non (tg : mod_held de Model-TG, le vrai chemin)."""
        if tg:
            u.uc.mem_write(tg["mod_held"], struct.pack(">I", key))
        try:
            return u.lookup(m, knob, func, key)
        finally:
            if tg:
                u.uc.mem_write(tg["mod_held"], bytes(4))

    # 1. objets d'interface : ceux de l'OS avant tout chargement de son, puis, avec Model-TG, ce que tl_ui y pose
    r0a, r0b = records(a), records(b)
    check(r0a == r0b, f"{label} : objets d'interface des 77 descripteurs identiques à {base} avant le chargement d'un "
                      f"son (l'OS ne les a pas encore touchés)")
    if tg:
        la, lb = load_at(base_img), load_at(fw_img)
        ok = la is not None and lb is not None and run_load(a, la) and run_load(b, lb)
        check(ok, f"{label} : chargement d'un son par Model-TG (tl_load) exécuté sans faute")
        r1a, r1b = records(a), records(b)
        check(r1a == r1b, f"{label} : après le chargement d'un son, les 77 objets de MACRO = ceux de {base} (MACRO "
                          f"n'en ajoute aucun)")
    else:
        r1a, r1b = r0a, r0b
    # 2. la recherche : MACHINES + PITCH -> FINE (43) avec Model-TG, PITCH (42) sans, sur toutes les machines
    got, same = {}, True
    for m in range(top + 1):
        for knob in range(2, 16):
            for func in (False, True):
                for key in (0, 1):                      # key : la touche MACHINES tenue
                    got[m, knob, func, key] = d = look(b, m, knob, func, key)
                    if m < top:
                        same &= d == look(a, m, knob, func, key)
    same &= None not in got.values()
    # le Sampler (machine 6 de Model-TG) n'a pas de PITCH à lui : FINE n'y est que sous MACHINES
    ms = [m for m in range(top + 1) if not (tg and m == 6)]
    if tg:
        bad = [(m, f) for m in ms for f in (False, True) if got[m, PITCH_KNOB, f, 1] != FTUN]
        check(not bad and all(got[m, PITCH_KNOB, f, 0] == PITCH for m in ms for f in (False, True)),
              f"{label} : MACHINES + PITCH -> FINE ({FTUN}) sur les machines 0..{top} (Sampler excepté), PITCH "
              f"({PITCH}) sans MACHINES {bad[:3]}")
        bad = [(m, k, f, got[m, k, f, 1]) for m in range(top + 1) for k in range(2, 8) for f in (False, True)
               if got[m, k, f, 1] != MACHINES_KNOBS[k]]
        check(not bad and all(got[m, k, f, 1] == got[m, k, f, 0] for m in range(top + 1) for k in range(8, 16)
                              for f in (False, True)),
              f"{label} : MACHINES + les potards 2..7 -> {[MACHINES_KNOBS[k] for k in range(2, 8)]} (FINE, Attack, "
              f"Rate, Bits, Filtre, Résonance) sur les machines 0..{top} ; 8..15 comme sans MACHINES {bad[:3]}")
    else:
        check(all(got[m, k, f, 1] == got[m, k, f, 0] for m in range(top + 1) for k in range(2, 16)
                  for f in (False, True)),
              f"{label} : sans Model-TG, MACHINES ne change aucun potard de MACRO (PITCH reste {PITCH})")
    check(all(got[m, PITCH_KNOB, 0, 0] == PITCH and got[m, PITCH_KNOB, 1, 0] == PITCH for m in ms),
          f"{label} : PITCH seul et FUNC + PITCH (sans MACHINES) -> {PITCH} sur les machines 0..{top} (Sampler "
          f"excepté)")
    check(all(got[m, k, True, key] == got[m, k, False, key] for m in range(top + 1) for k in range(2, 14)
              for key in (0, 1)),
          f"{label} : FUNC ne change pas les potards 2..13 de MACRO (14 et 15 : leur 2e paramètre, comme l'OS)")
    check(same, f"{label} : machines 0..{top - 1}, les 14 potards, avec et sans FUNC et MACHINES : le même "
                f"descripteur que {base}")
    # le nom de la plaque : celui de l'OS (FINE n'est plus renommé « Lo-Fi »)
    ptr_a = struct.unpack(">I", a.uc.mem_read(PARAM_TABLE + 56 * FTUN + 0x2c, 4))[0]
    ptr = struct.unpack(">I", b.uc.mem_read(PARAM_TABLE + 56 * FTUN + 0x2c, 4))[0]
    nom = b.cstr(ptr)
    check(nom == a.cstr(ptr_a) and "lo-fi" not in nom.lower(),
          f"{label} : nom de la plaque pour FTUN -> {nom!r} (celui de {base}, pas 'Lo-Fi')")
    if after:
        last = range(top + 1, top + 1 + after)
        later = {(m, k, f, key): look(b, m, k, f, key) for m in last for k in range(2, 16) for f in (False, True)
                 for key in (0, 1)}
        if tg:
            check(None not in later.values()
                  and all(later[m, PITCH_KNOB, f, key] == (FTUN if key else PITCH)
                          for m in last for f in (False, True) for key in (0, 1))
                  and all(later[m, k, f, 1] == MACHINES_KNOBS[k] for m in last for k in range(3, 8)
                          for f in (False, True))
                  and all(later[m, k, f, 1] == later[m, k, f, 0] for m in last for k in range(8, 16)
                          for f in (False, True)),
                  f"{label} : machines {top + 1}..{top + after} (après MACRO) : MACHINES + PITCH -> FINE ({FTUN}) et "
                  f"potards 2..7 -> Attack, Rate, Bits, Filtre, Résonance, comme les autres")
        else:
            check(None not in later.values() and FTUN not in later.values()
                  and all(later[m, PITCH_KNOB, f, key] == PITCH for m in last for f in (False, True)
                          for key in (0, 1))
                  and all(later[m, k, True, key] == later[m, k, False, key] for m in last for k in range(3, 14)
                          for key in (0, 1)),
                  f"{label} : machines {top + 1}..{top + after} (après MACRO) : FUNC + PITCH et MACHINES + PITCH -> "
                  f"PITCH, FINE sous aucun potard, potards 3 à 13 avec FUNC comme sans")
    # 3. le tour de potard avec FUNC : un pas par cran avec Model-TG (tl_step), le défaut de l'OS sans
    cases = [(cur, d) for cur in (0, 0x100, 0x3f00, 0x4000, 0x4080, 0x4100, 0x7e00, 0x7f00, 0x1234)
             for d in (1, 0x100, 0x180, 0x300, -1, -0x100, -0x300, 0x7f00, -0x7f00)]
    if tg:
        bad = [(hex(c), hex(d), b.edit_func(FTUN, c, d)) for c, d in cases
               if b.edit_func(FTUN, c, d) != want_step(c, d) or a.edit_func(FTUN, c, d) != want_step(c, d)]
        check(not bad, f"{label} : FUNC + un cran sur FINE (vrai 0x4000b7d6) : un pas (0x100) par cran, borné à "
                       f"0..0x7f00, comme {base} ({len(cases)} cas) {bad[:3]}")
    else:
        reset = {b.edit_func(FTUN, cur, d) for cur in (0, 0x2000, 0x5f00) for d in (0x100, -0x100)}
        check(reset == {0x4000} and all(b.edit_func(FTUN, c, d) == a.edit_func(FTUN, c, d) for c, d in cases),
              f"{label} : sans Model-TG, FUNC + un tour sur FINE : le défaut de l'OS {sorted(reset)}, comme {base} "
              f"({len(cases)} cas)")
    plain = [(c, d, b.edit_func(FTUN, c, d, fine=0), a.edit_func(FTUN, c, d, fine=0)) for c, d in cases]
    check(all(x == y and x is not None for _, _, x, y in plain),
          f"{label} : MACHINES + un tour sur FINE (sans FUNC, vrai 0x4000b7d6) : le chemin de l'OS, comme {base} "
          f"({len(plain)} cas)")
    pitch = [(b.edit_func(PITCH, c, d), a.edit_func(PITCH, c, d)) for c in (0x4000, 0x4080) for d in (0x100, -0x100)]
    check(all(x == y for x, y in pitch), f"{label} : FUNC + un tour sur PITCH : les demi-tons de l'OS "
                                         f"({', '.join(hex(x) for x, _ in pitch)})")
    # 4. le texte et la fenêtre de valeur de FINE : ceux de l'OS (-64..63, une jauge), aucun texte de lo-fi
    shown = [b.text(FTUN, n << 8) for n in range(128)]
    os_shown = [a.text(FTUN, n << 8) for n in range(128)]
    check(shown == os_shown and all(len(s) <= 3 for s in shown) and "OFF" not in shown,
          f"{label} : texte de FINE (vrai sprintf) = celui de {base} : {shown[0]} .. {shown[127]} (pas OFF / 46K / "
          f"12B)")
    gauge = b.popup(FTUN, 0x2000)
    check(gauge is not None and (not gauge[1] if tg else gauge[1]) and gauge == a.popup(FTUN, 0x2000),
          f"{label} : fenêtre de valeur de FINE (vrai 0x4001d818) = celle de {base} : "
          + ("le nombre et la barre de tl_draw_f (aucun sprite)" if tg else "une jauge (un sprite)")
          + ", aucun texte de lo-fi")
    steps = (0, 1, 31, 63, 64, 65, 100, 127)
    bad = [n for n in steps if b.popup(FTUN, n << 8) != a.popup(FTUN, n << 8)]
    check(not bad, f"{label} : fenêtre de valeur de FINE à {', '.join(str(n) for n in steps)} : pixel pour pixel "
                   f"celle de {base} (jauge, pas de texte) {bad}")
    # 5. les 77 objets : ceux de l'OS avec Model-TG, sauf FINE (+0x50) et les descripteurs 1 / 2 (+0x20, +0x30)
    r2a, r2b = records(a), records(b)
    check(r2a == r1a and r2b == r1b, f"{label} : les vérifications ci-dessus n'ont pas touché aux objets d'interface")
    if tg:
        diff = [d for d in range(77) if r0a[d] != r2b[d]]
        got = {d: fields(r0a[d], r2b[d]) for d in diff}
        shown = {d: tuple(hex(i) for i in f) for d, f in got.items()}
        check(diff == [1, 2, FTUN] and got == {1: (0x20, 0x30), 2: (0x20, 0x30), FTUN: (0x20, 0x30, 0x50)},
              f"{label} : objets d'interface des 77 descripteurs = ceux de l'OS, sauf FINE (+0x20 texte signé, +0x30 "
              f"nombre et barre, +0x50 notre pas) et les "
              f"descripteurs 1 / 2 (+0x20 texte, +0x30 dessin) ({diff} {shown})")
    else:
        check(r2b == r0a, f"{label} : objets d'interface des 77 descripteurs identiques à {base}")
