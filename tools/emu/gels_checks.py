"""Deux gels de l'OS 1.13 d'origine et leurs correctifs (notes/70 §5), sur le vrai code de l'OS : défaut contre corrigé.

D1 — MACHINES gèle quand une piste porte une machine que le firmware n'a pas (projet fait avec MACRO, ACID ou les
moteurs du Syntakt, rouvert ailleurs). Les accesseurs des enregistrements par machine 0x4004df5c (n, 0..6) et
0x4004df76 (machine m, 0..5) rendent l'entrée -1 hors limites : 0x40a714f4, 76 o AVANT le tableau 0x40a71540.
Correctif : moveq #-1 -> moveq #6 (CHORD) en 0x4004df66 et 0x4004df80. Contrôles (objets factices et empoisonnement
des 76 o avant le tableau de test_sdvintage_7th.py : des pointeurs vers une zone non mappée, pour que tout usage se
voie) : accesseurs ; ouverture de MACHINES (0x400148dc, appelée pour chaque piste par la lambda 0x400a2404) ;
potards de l'écran principal (0x4001e814) ; molette de MACHINES (0x400a2712) et vrai changement de machine
(0x40014072) depuis la machine 9.

D2 — l'interruption du top d'horloge MIDI 0x4005420c (corps à IPL 7) envoie 0xF8 par 0x40082512 -> 0x400824c4 ->
0x40001564 -> 0x40001232. Quand un message part par le DMA (0x4049dca0 non nul), 0x40001232 range l'octet dans
l'anneau de 1 Kio *0x4049dcac ; plein (0x4049dccc > 1023), il attend (0x4000123a..0x40001246) qu'une interruption de
niveau 4 le vide, ce qui ne peut pas arriver à IPL 7 : gel complet après une longue surcharge (1 024 tops sans
service : 4,7 s à 546 BPM, 21 s à 120 BPM). Correctif 0x40001246 : bgt.s 0x4000123a -> bgt.s 0x400012c6 (sortie) :
l'octet est jeté.

    import gels_checks as G
    G.d1(defaut, corrige, check)    # check(ok, message)
    G.d2(defaut, corrige, check)
"""
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UcError   # noqa: E402
from unicorn import m68k_const as mk                               # noqa: E402

import test_sdvintage_7th as t7                                    # noqa: E402

BASE = 0x40000400
REC_BASE, REC_LEN = t7.REC_BASE, t7.REC_LEN
POISON = 0xa0000000
TOP_OK = 5                                       # machines 0..5 de l'OS d'origine (CHORD = 5)
D1 = ((0x4004df66, "70ff", "7006"), (0x4004df80, "70ff", "7006"))
D2 = (0x40001246, "6ef2", "6e7e")
TICK, TICK_RTE = 0x4005420c, 0x40054288
SPIN = (0x4000123a, 0x40001248)
MIDI_RING = 0x4a3e0000


# ---------- D1 : MACHINES ----------

def _heap(u, at=0x93d00000):
    """operator new (0x400802e0) : un tas factice (bump) ; operator delete (0x400802ec) : rien."""
    st = {"p": at}

    def new(uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        n = struct.unpack(">I", uc.mem_read(sp + 4, 4))[0]
        uc.reg_write(mk.UC_M68K_REG_D0, st["p"])
        st["p"] += (n + 15) & ~15
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    u.uc.hook_add(t7.UC_HOOK_CODE, new, begin=0x400802e0, end=0x400802e0)
    u.hooks[0x400802ec] = ("delete", 0)


def _ui(img):
    u = t7.UI(img)
    t7.fill_records(u)
    u.uc.mem_write(REC_BASE - REC_LEN, struct.pack(">19I", *[POISON + 16 * k for k in range(19)]))
    _heap(u)
    return u


def _bad(u):
    return [a for a in u.bad if a >= POISON - 0x100]


def _records(stock, fixed, check):
    a, b = _ui(stock), _ui(fixed)
    same = all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in range(TOP_OK + 2))
    same &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in range(TOP_OK + 1))
    s = [a.call(0x4004df5c, i) for i in (7, 8, 100, -3)] + [a.call(0x4004df76, m) for m in (6, 9, 100)]
    f = [b.call(0x4004df5c, i) for i in (7, 8, 100, -3)] + [b.call(0x4004df76, m) for m in (6, 9, 100)]
    check(same, f"D1 : accesseurs 0x4004df5c (0..{TOP_OK + 1}) et 0x4004df76 (0..{TOP_OK}) identiques au défaut")
    check(all(v == REC_BASE - REC_LEN for v in s), "D1 : défaut, hors limites -> 0x40a714f4, 76 o AVANT le tableau")
    check(all(v == REC_BASE + 6 * REC_LEN for v in f), "D1 : corrigé, hors limites -> enregistrement de CHORD")


def _machine_list(img, m):
    """0x400148dc(piste) : liste (descripteur, valeur) des paramètres de la machine de la piste."""
    u = _ui(img)
    obj, snd = t7.fake_track(u, m & 0xff)
    for k in range(0x30):                              # des valeurs de son reconnaissables (slot 9 = la machine)
        if k != 9:
            u.uc.mem_write(snd + 0x14 + 2 * k, struct.pack(">h", (k + 1) << 8))
    res = 0x93c00000
    u.uc.mem_write(res, bytes(12))
    u.hooks.pop(0x40014072, None)
    u.uc.reg_write(mk.UC_M68K_REG_A0, res)
    sp = t7.STACK - 0x400
    u.uc.mem_write(sp, struct.pack(">II", t7.STOP, obj))
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.bad.clear()
    try:
        u.uc.emu_start(0x400148dc, t7.STOP, count=2_000_000)
        err = None
    except UcError as e:
        err = str(e)
    beg, end = struct.unpack(">II", u.uc.mem_read(res, 8))
    items = []
    if not err and beg and end >= beg and end - beg < 0x1000:
        items = [struct.unpack(">IH", u.uc.mem_read(beg + i, 6)) for i in range(0, end - beg, 8)]
    return items, _bad(u), err


def _machines_view(stock, fixed, check):
    ref_s = {m: _machine_list(stock, m) for m in range(TOP_OK + 1)}
    ref_f = {m: _machine_list(fixed, m) for m in range(TOP_OK + 1)}
    check(all(ref_s[m] == ref_f[m] and not ref_s[m][1] and not ref_s[m][2] for m in ref_s),
          f"D1 : MACHINES (0x400148dc), machines 0..{TOP_OK} : identiques au défaut, aucun accès faux")
    chord = ref_f[TOP_OK][0]
    for m in (TOP_OK + 1, TOP_OK + 2, 9, 100, -3):
        s, f = _machine_list(stock, m), _machine_list(fixed, m)
        check((s[1] or s[2]) and not f[1] and not f[2] and f[0] == chord,
              f"D1 : MACHINES, machine {m} : défaut lit par les pointeurs d'avant le tableau "
              f"({len(s[1])} lecture(s){', ' + s[2] if s[2] else ''}) ; corrigé = CHORD, aucun accès faux")


def _knobs(stock, fixed, check):
    res = {}
    n = TOP_OK + 1
    for name, img in (("défaut", stock), ("corrigé", fixed)):
        u = _ui(img)
        this, vec = 0x93900000, 0x93910000
        u.uc.mem_write(vec, struct.pack(f">{n}i", *range(1, n + 1)) +
                       struct.pack(">4I", 0x41234567, 0x7fff0000, 0x13, 0x8000))
        u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 4 * n, vec + 4 * n))
        out = {}
        for m in list(range(n)) + [n, n + 1, n + 3]:
            u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
            u.bad.clear()
            out[m] = ([u.call(0x4001e814, this, k, 0, 0) for k in range(2, 8)], bool(_bad(u)))
        res[name] = out
    check(all(res["défaut"][m] == res["corrigé"][m] for m in range(n)),
          f"D1 : potards de l'écran principal (0x4001e814), machines 0..{TOP_OK} : identiques au défaut")
    check(all(res["corrigé"][m] == res["corrigé"][TOP_OK] for m in (n, n + 1, n + 3)),
          "D1 : potards, machine hors limites : corrigé -> descripteurs de CHORD, aucun accès faux")
    check(any(res["défaut"][m][0] != res["défaut"][TOP_OK][0] or res["défaut"][m][1] for m in (n, n + 1, n + 3)),
          "D1 : potards, machine hors limites : défaut -> autre chose (lu avant le tableau)")


def _wheel(stock, fixed, check):
    for name, img in (("défaut", stock), ("corrigé", fixed)):
        got = {}
        for step in (-1, 1):
            u = _ui(img)
            obj, snd = t7.fake_track(u, 9)
            del u.hooks[0x40014072]                     # le vrai changement de machine
            this = 0x93900000
            for k in range(6):
                u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
            for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                          0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
                u.hooks[a_] = (f"{a_:#x}", v)
            try:
                u.call(0x400a2712, this, step, 0, 0)
                err = None
            except UcError as e:
                err = str(e)
            got[step] = (struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8, len(_bad(u)), err)
        # la molette borne machine + pas et appelle 0x40014072, qui relit la NOUVELLE machine : ce chemin ne lit pas
        # l'enregistrement de l'ancienne (pas le défaut) ; il ramène sur la dernière machine
        check(all(g == (TOP_OK, 0, None) for g in got.values()),
              f"D1 : {name}, molette de MACHINES et vrai changement de machine depuis la machine 9 -> {TOP_OK} ({got})")


def d1(stock, fixed, check):
    _records(stock, fixed, check)
    _machines_view(stock, fixed, check)
    _knobs(stock, fixed, check)
    _wheel(stock, fixed, check)


# ---------- D2 : horloge MIDI sortante ----------

class ClockRig:
    def __init__(self, img):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x01000000)
        uc.mem_map(0x4a000000, 0x00400000)
        uc.mem_map(0xfc000000, 0x00100000)
        uc.mem_map(0xec000000, 0x00100000)
        uc.mem_map(0x90000000, 0x00010000)
        uc.mem_write(BASE, bytes(img))
        w = self.w32
        w(0x40fe4228, 1)                  # sortie MIDI prête
        uc.mem_write(0x404e9b50, b"\x00\x00\x01")   # OUT (pas THR), 0x404e9b52 : ports = DIN
        w(0x40a70148, 1)                  # envoi d'horloge activé
        w(0x40a78630, 0)
        uc.mem_write(0x40a788e6, b"\x00")
        w(0x4049dcac, MIDI_RING)
        for a in (0x4049dca0, 0x4049dcc4, 0x4049dcc8, 0x4049dccc):
            w(a, 0)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def tick(self, limit=200_000):
        """Une interruption du top d'horloge ; True si elle arrive à son rte."""
        self.uc.reg_write(mk.UC_M68K_REG_SR, 0x2500)     # entrée d'interruption de niveau 5 (SR avant SP)
        self.uc.reg_write(mk.UC_M68K_REG_A7, 0x9000f000)
        try:
            self.uc.emu_start(TICK, TICK_RTE, count=limit)
        except UcError as e:
            return f"erreur {e}"
        return self.uc.reg_read(mk.UC_M68K_REG_PC) == TICK_RTE

    def state(self):
        return (bytes(self.uc.mem_read(MIDI_RING, 1024)), self.r32(0x4049dcc8), self.r32(0x4049dccc),
                bytes(self.uc.mem_read(0xec07400c, 1)), bytes(self.uc.mem_read(0xfc044019, 1)))


def d2(stock, fixed, check):
    for label, img in (("défaut", stock), ("corrigé", fixed)):     # chemin direct : UART libre
        r = ClockRig(img)
        r.uc.mem_write(0xec074004, b"\x04")
        ok = r.tick()
        check(ok is True and r.state()[3] == b"\xf8" and r.r32(0x4049dccc) == 0,
              f"D2 : {label}, UART libre : 0xF8 écrit dans 0xec07400c, anneau vide")
    res = {}
    for label, img in (("défaut", stock), ("corrigé", fixed)):     # surcharge : le niveau 4 n'est jamais servi
        r = ClockRig(img)
        r.w32(0x4049dca0, 2)
        r.uc.mem_write(0xec074004, b"\x00")
        states = []
        for k in range(1, 1027):
            ok = r.tick()
            if ok is not True:
                res[label] = (k, r.uc.reg_read(mk.UC_M68K_REG_PC), r.uc.reg_read(mk.UC_M68K_REG_SR), states)
                break
            states.append(r.state())
        else:
            res[label] = (None, None, None, states)
    k, pc, sr, st = res["défaut"]
    check(k == 1025 and pc is not None and SPIN[0] <= pc < SPIN[1] and (sr >> 8) & 7 == 7,
          f"D2 : défaut, 1 024 tops rangés, le 1 025e ne revient pas (PC dans 0x4000123a..46, IPL 7) : "
          f"top {k}, PC {pc:#x}, SR {sr:#06x}" if pc is not None else f"D2 : défaut inattendu ({k})")
    k2, _, _, st2 = res["corrigé"]
    check(k2 is None and len(st2) == 1026, "D2 : corrigé, les 1 026 tops reviennent (le 1 025e et le 1 026e jettent "
          "leur octet)")
    check(st2[:1024] == st[:1024], "D2 : corrigé, les 1 024 premiers tops laissent anneau, index, compte et registres "
          "identiques au défaut, top après top")
    check(st2[1025][2] == 1024 and st2[1025][0] == st2[1023][0], "D2 : corrigé, anneau plein inchangé (compte 1 024)")
