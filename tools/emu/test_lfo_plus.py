#!/usr/bin/env python3
"""Preuve de LFO 2, 3, 4 (notes/56 §3, tweaks/model-cycles_OS1.13/60-lfo-plus.json).

Le vrai code de l'OS sous Unicorn (EMAC exacte de emac.py pour le lissage 0x40058474 et les LFO 0x40091ab2), sur le
MAIN OS sans le tweak (« origine » : l'OS d'origine, ou la combinaison --with) et avec le tweak (« modifié ») :
  0. Écritures : octets d'origine ; masques libérés identiques au masque gardé, désignés par la seule constante de
     leur constructeur, redirigée ; aucun autre tweak n'écrit autre chose sur ces octets ; aucun saut (OS, charges
     utiles) au milieu des instructions remplacées ; mémoire de travail au-dessus du BSS (fin de la remise à zéro en
     0x400004c2) et sous les tampons DMA (0x4a340000, vue sans cache de 0x42340000), sans aucune adresse dedans dans
     l'OS, les tweaks et les charges utiles ; variables à zéro dans l'image.
  1. Bloc audio (vrai lissage 0x40058474 puis l'appel 0x400597ba..0x400597cc), 600 blocs, LFO 1 au hasard sur les
     6 pistes (toutes formes, RND compris, retrigs, deux tempos), sans LFO de plus : mots des pistes, état des LFO,
     générateur aléatoire et adresses écrites identiques à l'origine ; registres et pile rendus ; mémoire de travail
     pas touchée.
  2. LFO 2, 3, 4 : sortie = la fonction des LFO de l'OS réglée pareil (FADE, SPH, MODE de LFO 1), 3 tirages de 400
     blocs (toutes formes, mult synchro et libres, 5 modes, retrigs) ; LFO 1 inchangé ; même destination que LFO 1 :
     ignoré ; deux LFO de plus sur la même destination s'ajoutent, bornés 0..0x7f00 ; LFO 2 -> vitesse de LFO 1 :
     appliqué avant LFO 1 ; destination > 32 : rien ; jeu sans destination : pas calculé ; k = 31 recopié brut ;
     WAVE de LFO 2 lu dans le mot k = 0 des cibles, pas dans obj k = 0, k 30 jamais écrit.
  3. Interface : id -> k (0x4005a4e8) pour tous les identifiants sur les 4 pages, aucun descripteur sur k = 28..32 ;
     touche [LFO] ; get/set des pages 3-4 ; page 2 : le vrai get/set de l'OS écrit SPD, MULT, DEST, DEP en
     k = 28, 29, 31, 32 du son et WAVE en k = 0 ;
     rappels coupés pages 3-4 ; création/destruction de la vue ; dessin du chiffre ; molette DEST (vraie fonction
     de la vtable [20] -> 0x4000c140, vraie liste) : même liste sur les 4 pages, destinations prises sautées.
  4. Son : sauvegarde (formats 2 et 1) -> chargement par les vraies fonctions de l'OS : LFO 2 relu (SPD et DEP au
     multiple de 0x80) avec WAVE en k = 0 et k = 30 remis à 0, tout le reste identique à l'origine ; enregistrement
     de l'ancienne disposition (WAVE en +88) relu de même ; ancien son -> défauts ; son neuf (0x40061866) ->
     défauts ; un OS sans le mod relit un son sauvé avec comme le sien.
  5. p-locks : identifiant de rangée -> k (0x4005aa1a) pour toutes les pistes et tous les identifiants ; aller-retour
     complet 0x4005b95c -> 0x4005b766 de p-locks sur k = 0..32, WAVE par la rangée 29, k 30 jamais sauvé.
  6. Coût : instructions par bloc (appel des LFO) : origine, sans LFO de plus, LFO 2 seul, les trois.
  7. Accroches au milieu d'une fonction : de l'adresse accrochée à la fin des instructions remplacées, mêmes
     registres (hors ceux que la suite réécrit, dits à chacune), même pile, même mémoire que l'origine.
  8. LFO 3/4 par pattern (notes/56 §3.11) : bloc de chacun des 96 kits ; moteur et page sur le bloc du kit joué ;
     vraie sauvegarde (0x4005b2ae) et vrai chargement (0x4005d080) d'un kit : enregistrement = l'origine hors
     +648..+699, aller-retour exact, ancien enregistrement -> défauts, l'OS d'origine relit l'enregistrement du mod
     comme le sien ; vrai son aux défauts (0x40061866) sur le son d'une piste d'un kit ; vrai memcpy (0x4008f1f0) :
     autres tailles = l'origine, kit -> kit, kit -> tampon -> kit ; vrai nouveau projet (0x40061738) ; vrai Clear LFO
     (vtable [12] de l'accesseur, identifiants 0x1e..0x24) sur les pages 3/4.
  (--david) Un son sauvé par le .syx de DavidCaruso se relit ici avec le même LFO 2.

    python3 tools/emu/test_lfo_plus.py --cycles model-cycles_OS1.13.syx \\
        [--with model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,tempo-max --syntakt Syntakt_OS1.42.syx] \\
        [--david Model-TG-VA-DR-v1.syx]
"""
import argparse
import json
import pathlib
import random
import re
import struct
import sys
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import emac                         # noqa: E402
import gen_lfo_plus as G            # noqa: E402
import sprites                      # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAKS = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TWEAK = TWEAKS / "60-lfo-plus.json"
BASE = build.BASE
M32 = 0xffffffff
FAIL = []

STOP, STACK = 0x9f000000, 0x9e000000
FAKE = 0x92000000
THIS, TRACKOBJ, FAKEVT, SOUND, SOUND2, REC = (FAKE + 0x1000 * i for i in range(1, 7))
VIEWOBJ, EVT, BMP, PROJ, SEQ, FCODE = (FAKE + 0x1000 * i for i in range(7, 13))
TGT, ARG = 0x91000000, 0x91001000
PSRC, ROWS, PDST, HEAP = 0x93000000, 0x94000000, 0x95000000, 0x96000000

OBJ, SMOOTH, TEMPO = 0x8000100c, 0x40058474, 0x40149310       # obj lissé (SRAM), lissage, tempo
SITE, SITE_END = 0x400597ba, 0x400597cc                        # 3 arguments empilés puis jsr des LFO
LFO_ST, RNG = 0x40fde838, 0x4014931c
ID2K, PLK_K, PLK_SAVE, PLK_LOAD = 0x4005a4e8, 0x4005aa1a, 0x4005b95c, 0x4005b766
SND_SAVE2, SND_SAVE1, SND_LOAD, SND_INIT = 0x4005afa0, 0x4005b054, 0x4005aecc, 0x40061866
K2ID, KTAB = 0x4005a692, 0x4005a274                            # k -> identifiant (machine), ses tables (BSS)
CUR_PROJ, PROJ_SEQ, SEL_TRACK, NEEDS_REDRAW = 0x400cf866, 0x4000eb90, 0x40012412, 0x40076082
FILL_RECT, TEXT, FONT = 0x40070dea, 0x40071a04, 0x40ea14d4
ORIG_GET, ORIG_SET, ORIG_KEY, ORIG_DRAW, VIEW_CTOR = 0x4000ae20, 0x4000ba7a, 0x40024e86, 0x400426fa, 0x40025798
P_GET, P_SET, P_DELTA, P_KEY, P_DRAW = 0x400fd150, 0x400fd190, 0x400fd148, 0x401016e4, 0x401016ec
ACC_VT = 0x400fd134                                            # vtable de l'accesseur des réglages de la piste
MALLOC, FREE, ASSERT = 0x40080064, 0x4008026a, 0x400c9a7c
EMAC_RANGES = ((0x40058474, 0x40058500), (0x4008f100, 0x40091d50))

D = [getattr(mk, f"UC_M68K_REG_D{i}") for i in range(8)]
A = [getattr(mk, f"UC_M68K_REG_A{i}") for i in range(8)]
SAVED = D[2:8] + A[2:7]
OWN = {0x1d: 0, 0x1e: 1, 0x21: 2, 0x20: 3, 0x24: 4}              # id -> rang : SPD, MULT, WAVE, DEST, DEP
DEFAULTS = [0x7000, 0x0400, 0, 0, 0x4000]                       # LFO 2 par défaut (k = 28..32)
S_LFO1 = G.SCR
ST = {2: G.SCR + 192, 3: G.SCR + 384, 4: G.SCR + 576}            # états des jeux (lfo_plus.S)


def check(ok, msg):
    print(f"  {'ok   ' if ok else 'ECHEC'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def s32(v):
    return v - (1 << 32) if v & 0x80000000 else v


class Rig:
    """Un MAIN OS en mémoire, comme après le démarrage pour ce qu'on en utilise : .data recopiée en SRAM
    (0x4000045c), tables k -> identifiant (0x4005a274), charges utiles à leur adresse d'exécution."""

    def __init__(self, img, runtimes=()):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)              # image + BSS (+ mémoire de travail 0x4233f000)
        uc.mem_map(0x42400000, 0x05c00000)              # charges utiles copiées (0x43000000, 0x46700000)
        uc.mem_map(0x80000000, 0x00020000)              # SRAM
        uc.mem_map(0x90000000, 0x10000000)              # pile, objets factices
        uc.mem_write(BASE, img)
        for dest, data in runtimes:
            uc.mem_write(dest, data)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad, self.asserts, self.fn, self.log, self.heap, self.wlog = [], [], {}, [], HEAP, None
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._write)
        with tempfile.NamedTemporaryFile(suffix=".bin") as f:
            f.write(img)
            f.flush()
            ins = {}
            for lo, hi in EMAC_RANGES:
                ins.update(emac.disasm(f.name, BASE, lo, hi))
        self.emac = emac.EMAC(uc)
        self.emac.install(ins)
        self.emac.macsr = 0x20                          # celui que vérifie 0x400918b0 (fondu)
        self.stub(ASSERT, lambda a: self.asserts.append(a) or 0)
        self.stub(MALLOC, self._malloc)
        self.stub(FREE, lambda a: 0)
        self.call(0x4000045c)
        self.call(KTAB)
        self.rng0 = bytes(uc.mem_read(RNG, 8))

    def _write(self, uc, access, addr, size, value, _):
        if self.wlog is not None and not STACK - 0x2000 <= addr < STACK + 0x100:
            self.wlog.add(addr)

    def _malloc(self, a):
        p, self.heap = self.heap, self.heap + ((a[0] + 15) & ~15)
        return p

    def stub(self, addr, fn):
        """fn(args) remplace la fonction en addr (None : la vraie)."""
        if addr not in self.fn:
            self.uc.hook_add(UC_HOOK_CODE, self._stub, begin=addr, end=addr)
        self.fn[addr] = fn

    def _stub(self, uc, addr, size, _):
        fn = self.fn.get(addr)
        if fn is None:
            return
        sp = uc.reg_read(A[7])
        r = fn(struct.unpack(">6I", uc.mem_read(sp + 4, 24)))
        uc.reg_write(D[0], (r or 0) & M32)
        uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp))
        uc.reg_write(A[7], sp + 4)

    def logged(self, name, ret=0):
        return lambda a: self.log.append((name,) + a) or ret

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & M32))

    def r16(self, a):
        return struct.unpack(">H", self.uc.mem_read(a, 2))[0]

    def w16(self, a, v):
        self.uc.mem_write(a, struct.pack(">H", v & 0xffff))

    def r8(self, a):
        return self.uc.mem_read(a, 1)[0]

    def w8(self, a, v):
        self.uc.mem_write(a, bytes([v & 0xff]))

    def rd(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def call(self, fn, *args, regs=None, check=None):
        """Appelle fn(args) ; check : message, vérifie d2-d7/a2-a6 et la pile rendus."""
        sp = STACK - 4 * (len(args) + 1)
        self.uc.mem_write(sp, struct.pack(">I", STOP) + b"".join(struct.pack(">I", x & M32) for x in args))
        pre = {r: 0x01010101 * (i + 1) for i, r in enumerate(SAVED)}
        pre.update(regs or {})
        for r, v in pre.items():
            self.uc.reg_write(r, v)
        self.uc.reg_write(A[7], sp)
        self.uc.emu_start(fn, STOP, count=50_000_000)
        if check:
            kept = all(self.uc.reg_read(r) == pre[r] for r in SAVED) and self.uc.reg_read(A[7]) == sp + 4
            if not kept:
                check_fail = f"{check} : registres d2-d7/a2-a6 ou pile pas rendus"
                print(f"  ECHEC {check_fail}")
                FAIL.append(check_fail)
        return self.uc.reg_read(D[0])

    def block(self, tg, tempo, mask, smooth=True, obj0=None):
        """Un bloc audio : lissage des cibles tg (ou obj = tg), puis l'appel des LFO tel que la fonction audio le
        fait (0x400597ba..0x400597cc, a2 = obj, a3 = l'argument : (a3) = cibles, 4(a3) = masque des retrigs).
        obj0 : valeur forcée dans le mot k = 0 de obj après le lissage (modulation de LFO 1 / vélocité), les cibles
        k = 0 (WAVE de LFO 2) ne bougent pas. Rend (registres et pile rendus, instructions)."""
        self.uc.mem_write(TGT, tg)
        if smooth:
            self.call(SMOOTH, TGT)
        else:
            self.uc.mem_write(OBJ, tg)
        if obj0 is not None:
            for t in range(6):
                self.w16(OBJ + 14 + 66 * t, obj0)
        self.w32(ARG, TGT)
        self.w32(ARG + 4, mask)
        self.w32(TEMPO, tempo)
        pre = {r: 0x01010101 * (i + 1) for i, r in enumerate(SAVED)}
        pre[A[2]], pre[A[3]] = OBJ, ARG
        for r, v in pre.items():
            self.uc.reg_write(r, v)
        sp = STACK - 0x40
        self.uc.reg_write(A[7], sp)
        self.uc.emu_start(SITE, SITE_END, count=50_000_000)
        return all(self.uc.reg_read(r) == pre[r] for r in SAVED) and self.uc.reg_read(A[7]) == sp - 12

    def counted(self, fn):
        n = [0]
        h = self.uc.hook_add(UC_HOOK_CODE, lambda u, a, s, d: n.__setitem__(0, n[0] + 1))
        r = fn()
        self.uc.hook_del(h)
        return r, n[0]

    def reset_lfo(self, syms=None):
        """État des LFO de l'OS à zéro, générateur aléatoire d'origine ; LFO de plus remis comme au démarrage."""
        self.uc.mem_write(LFO_ST, bytes(192))
        self.uc.mem_write(RNG, self.rng0)
        if syms:
            self.w8(syms["ready"], 0)


# ---------------------------------------------------------------------------------------------- réglages ------

def lfo(spd=0x7000, mult=4, fade=0x4000, dest=0, wave=0, sph=0, mode=0, dep=0x4000):
    return dict(spd=spd, mult=mult, fade=fade, dest=dest, wave=wave, sph=sph, mode=mode, dep=dep)


def tracks(lfo1, lfo2=None, base=None):
    """Cibles (14 o + 7 pistes × 66 o) : LFO 1 en k = 1..8 ; LFO 2 en k = 28, 29, 31, 32 (SPD, MULT, DEST, DEP),
    son WAVE dans le mot k = 0 des cibles (notes/86 §3 ; k 30 reste à Lo-Fi Bits) ; base : {k: mot}."""
    b = bytearray(14 + 7 * 66)
    for t in range(6):
        p = 14 + 66 * t
        for k, v in (base or {}).items():
            struct.pack_into(">H", b, p + 2 * k, v)
        L = lfo1[t]
        words = (L["spd"], L["mult"] << 8, L["fade"], (L["dest"] & 0xff) << 8, L["wave"] << 8, L["sph"],
                 L["mode"] << 8, L["dep"])
        struct.pack_into(">8H", b, p + 2, *words)
        if lfo2:
            M = lfo2[t]
            struct.pack_into(">H", b, p, M["wave"] << 8)
            struct.pack_into(">5H", b, p + 56, M["spd"], M["mult"] << 8, 0, (M["dest"] & 0xff) << 8, M["dep"])
    return bytes(b)


def table34(l3, l4):
    return b"".join(struct.pack(">5H", M["spd"], M["mult"] << 8, M["wave"] << 8, (M["dest"] & 0xff) << 8, M["dep"])
                    for M in l3 + l4)


def words(r, t, ks):
    return [s16(r.r16(OBJ + 14 + 66 * t + 2 * k)) for k in ks]


def masks_schedule(seed, n):
    rnd = random.Random(seed)
    return [sum(1 << t for t in range(6) if rnd.random() < 1 / 40) for _ in range(n)]


# ------------------------------------------------------------------------------------------ 0. écritures -----

def branch_targets(code, base):
    """Cibles des branchements relatifs (Bcc/BRA/BSR .b/.w/.l) et constantes de 32 bits du code."""
    out = set()
    for i in range(0, len(code) - 1, 2):
        op = code[i] << 8 | code[i + 1]
        if op >> 12 == 6:
            d8 = op & 0xff
            if d8 == 0 and i + 4 <= len(code):
                out.add(base + i + 2 + s16(code[i + 2] << 8 | code[i + 3]))
            elif d8 == 0xff and i + 6 <= len(code):
                out.add(base + i + 2 + s32(int.from_bytes(code[i + 2:i + 6], "big")))
            else:
                out.add(base + i + 2 + (d8 - 256 if d8 & 0x80 else d8))
    for i in range(0, len(code) - 3):
        out.add(int.from_bytes(code[i:i + 4], "big"))
    return out


def writes_ok(stock, img, tweak, every, runtimes):
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    for w in tweak["writes"]:
        o, old = w["off"], bytes.fromhex(w["old"])
        if stock[o:o + len(old)] != old:
            check(False, f"octets d'origine en {o + BASE:#x}")
    check(all(stock[w["off"]:w["off"] + len(w["old"]) // 2] == bytes.fromhex(w["old"]) for w in tweak["writes"]),
          f"octets d'origine des {len(tweak['writes'])} écritures")
    used = sorted({m for m in G.MASKS for w in tweak["writes"] if w["off"] + BASE == m})
    for mask in used:
        size, ref, _, kept = sprites.MASKS[mask]
        same = stock[mask - BASE:mask - BASE + size] == stock[kept - BASE:kept - BASE + size]
        refs = [m.start() + BASE for m in re.finditer(re.escape(struct.pack(">I", mask)), stock)]
        check(same and refs == [ref] and img[ref - BASE:ref - BASE + 4] == struct.pack(">I", kept),
              f"masque {mask:#x} : identique au masque gardé {kept:#x}, seule référence {ref:#x}, redirigée")
    clash = []
    for t in every:
        for v in t["writes"]:
            a, b = v["off"], v["off"] + len(v["old"]) // 2
            for w in tweak["writes"]:
                c, d = w["off"], w["off"] + len(w["old"]) // 2
                if a < d and c < b and (v["off"], v["new"]) != (w["off"], w["new"]):
                    clash.append(f"{t['id']}@{a + BASE:#x}")
    check(not clash, f"aucun autre tweak n'écrit autre chose sur ces octets ({len(every)} tweaks) {clash[:4]}")
    # pas de saut au milieu des instructions remplacées (OS d'origine, charges utiles de la combinaison)
    inner = set()
    for addr, old, *_ in G.HOOKS:
        n = len(old) // 2
        first = {0x4005b9c6: 4, 0x4000c140: 4, 0x4005a4ea: 4, 0x4005aa22: 4, 0x40025e10: 4, 0x400d97f8: 4,
                 0x400618e2: 2, 0x4005b2ae: 4, 0x4005d080: 4, 0x4008f1f0: 4}.get(addr, n)
        inner |= {addr + first} if first < n else set()
        inner |= set(range(addr + 1, addr + n)) - {addr + first}
    tg = branch_targets(stock, BASE)
    for dest, data in runtimes:
        tg |= branch_targets(data, dest)
    hit = sorted(a for a in inner if a in tg and a & 1 == 0)
    check(not hit, "aucun branchement ni constante de l'OS ou des charges utiles ne vise l'intérieur des "
                   f"instructions remplacées {[hex(a) for a in hit]}")
    # mémoire de travail
    bss_end = int.from_bytes(stock[0x400004c2 - BASE:0x400004c6 - BASE], "big")
    dma = int.from_bytes(stock[0x40057798 - BASE:0x4005779c - BASE], "big")
    lo, hi = G.SCR, G.SCR + G.SCR_SIZE
    lo2, hi2 = G.SCR34, G.SCR34 + G.SCR34_SIZE
    check(bss_end == 0x423380b0 and dma == 0x4a340000 and bss_end <= lo2 and hi2 <= lo and hi <= dma & 0xf7ffffff,
          f"mémoire de travail {lo:#x}..{hi:#x} et blocs LFO 3/4 {lo2:#x}..{hi2:#x} (sans recouvrement) entre la fin du "
          f"BSS ({bss_end:#x}, 0x400004c2) et les tampons DMA ({dma:#x} = {dma & 0xf7ffffff:#x}, 0x40057798)")
    # Depuis OS 2.0, le trou de RAM libre n'est plus entierement libre : step-rec y range ses
    # 0x4233e800.. (voir son generateur). On exige donc que NOS deux plages soient inoccupees, et
    # seulement elles : le reste du trou appartient a qui le prend.
    def refs_in(data):
        n = 0
        for i in range(0, len(data) - 3):
            v = int.from_bytes(data[i:i + 4], "big") & 0xf7ffffff      # 0x4a.. (sans cache) -> 0x42..
            if ((lo <= v < hi) or (lo2 <= v < hi2)) and i & 1 == 0:
                n += 1
        return n
    own = sum(refs_in(bytes.fromhex(w["new"])) for w in tweak["writes"])
    others = sum(refs_in(bytes.fromhex(w["new"])) for t in every for w in t["writes"])
    # charges utiles de tous les tweaks : leur code à nous (morceaux « hex ») et leurs relocalisations ; les morceaux
    # recopiés de l'OS Cycles sont dans l'OS (déjà vu), ceux du Syntakt ne visent la mémoire du Cycles que par leurs
    # relocalisations
    pay = 0
    for t in every:
        ap_ = t.get("append") or {}
        pay += sum(refs_in(bytes.fromhex(part["hex"])) for part in ap_.get("parts", []) if "hex" in part)
        pay += sum(refs_in(bytes.fromhex(new)) for _, _, new in ap_.get("reloc", []))
    found = (refs_in(stock), others, pay)
    check(found == (0, 0, 0) and own > 0,
          f"aucune adresse de nos plages {lo:#x}..{hi:#x} et {lo2:#x}..{hi2:#x} (ni de leur vue sans cache) dans l'OS, "
          f"les écritures des autres tweaks et le code et les relocalisations de leurs charges utiles {found} ; "
          f"{own} dans ce tweak")
    lo34 = syms["lfo34"] - BASE
    check(img[syms["view"] - BASE:syms["view"] - BASE + 8] == bytes(8)
          and img[lo34:lo34 + 120] == struct.pack(">5H", *DEFAULTS) * 12,
          "variables de la page et kready à zéro, bloc LFO 3/4 de secours aux défauts dans l'image (rechargée à "
          "chaque démarrage)")


# --------------------------------------------------------------------------------- 1. bloc audio, sans plus ---

def audio_identity(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    rnd = random.Random(1)
    sched = masks_schedule(11, 600)
    scr0 = P.rd(G.SCR, G.SCR_SIZE)
    t340 = P.rd(G.SCR34, G.SCR34_SIZE)
    k31 = {OBJ + 14 + 66 * t + 62 + i for t in range(6) for i in (0, 1)}      # recopie brute de k = 31
    same, regs, writes, n_moving = True, True, True, set()
    for blk in range(600):
        if blk % 100 == 0:
            l1 = [lfo(rnd.randrange(0x7f01), rnd.randrange(24), rnd.randrange(0x7f01), rnd.randrange(33),
                      rnd.randrange(7), rnd.randrange(0x7f01), rnd.randrange(5), rnd.randrange(0x7f01))
                  for _ in range(6)]
            l2 = [lfo(rnd.randrange(0x7f01), rnd.randrange(24), 0, 0, rnd.randrange(7), 0, 0, rnd.randrange(0x7f01))
                  for _ in range(6)] if blk % 200 else None
            base = {k: rnd.randrange(0x7f01) for k in list(range(9, 23)) + [23, 24, 25]}
            tg = tracks(l1, l2, base)
        tempo = 14400 if blk < 300 else 9000
        out = []
        for r in (S, P):
            r.wlog = set()
            ok = r.block(tg, tempo, sched[blk])
            out.append((r.rd(OBJ, 476), r.rd(LFO_ST, 192), r.rd(RNG, 8), frozenset(r.wlog)))
            r.wlog = None
            regs &= ok
        same &= out[0][:3] == out[1][:3]
        writes &= out[1][3] - out[0][3] <= k31 and not out[0][3] - out[1][3]
        n_moving.add(out[1][0])
    check(same and len(n_moving) > 300, f"600 blocs : mots des pistes, état des LFO, générateur = origine "
                                        f"({len(n_moving)} états des mots différents)")
    check(writes, "mêmes adresses écrites que l'origine (hors pile), plus le mot k = 31 des 6 pistes (recopié brut des "
                  "cibles, même valeur ici)")
    check(regs, "registres d2-d7/a2-a6 et pile rendus")
    check(P.rd(G.SCR, G.SCR_SIZE) == scr0 and P.r8(syms["ready"]) == 0 and P.rd(G.SCR34, G.SCR34_SIZE) == t340
          and P.r8(syms["kready"]) == 0, "mémoire de travail et blocs LFO 3/4 pas touchés (le moteur n'initialise "
                                         "jamais T34)")
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


# --------------------------------------------------------------------------------- 2. LFO 2, 3, 4 -------------

def run(r, tg, sched, ks, n, syms=None, l34=None, after=None, obj0=None):
    out = []
    for blk in range(n):
        if l34 is not None:
            r.uc.mem_write(syms["lfo34"], l34)
        ok = r.block(tg, 14400, sched[blk], smooth=False, obj0=obj0)
        out.append([words(r, t, ks) for t in range(6)])
        if after:
            after(blk)
        if not ok:
            check(False, "registres ou pile pas rendus par l'appel des LFO")
            break
    return out


def reference(S, cfg, common, base, sched, k, n):
    """La fonction des LFO de l'OS seule, LFO 1 réglé comme cfg (FADE, SPH, MODE : common) : mot k par bloc."""
    S.reset_lfo()
    l1 = [dict(c, fade=common[t]["fade"], sph=common[t]["sph"], mode=common[t]["mode"]) for t, c in enumerate(cfg)]
    out = run(S, tracks(l1, None, base), sched, [k], n)
    return [[o[t][0] for t in range(6)] for o in out]


def audio_extra(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    base = {k: 0x4000 for k in range(9, 23)}
    n = 400
    for seed in (2, 3, 4):
        rnd = random.Random(seed)
        common = [dict(fade=rnd.choice((0x4000, 0x4000, 0x3000, 0x5800)), sph=rnd.randrange(0x7f01),
                       mode=(t + seed) % 5) for t in range(6)]
        sets = {}
        for i, (name, dest) in enumerate((("LFO1", 14), ("LFO2", 11), ("LFO3", 12), ("LFO4", 13))):
            sets[name] = [lfo(spd=rnd.randrange(0x4400, 0x7f01), mult=(3 * t + 5 * i + seed) % 24,
                              wave=(t + 2 * i + seed) % 7, dest=dest, dep=rnd.choice((rnd.randrange(0x7f01), 0x7f00, 0)))
                          for t in range(6)]
        l1 = [dict(sets["LFO1"][t], **common[t]) for t in range(6)]
        sched = masks_schedule(seed, n)
        P.reset_lfo(syms)
        got = run(P, tracks(l1, sets["LFO2"], base), sched, [11, 12, 13, 14], n, syms,
                  table34(sets["LFO3"], sets["LFO4"]))
        for i, (name, k) in enumerate((("LFO2", 11), ("LFO3", 12), ("LFO4", 13), ("LFO1", 14))):
            ref = reference(S, sets[name], common, base, sched, k, n)
            mine = [[got[b][t][i] for t in range(6)] for b in range(n)]
            keep = [t for t in range(6) if sets[name][t]["wave"] != 6]
            rnd_t = [t for t in range(6) if t not in keep]
            same = all([mine[b][t] for t in keep] == [ref[b][t] for t in keep] for b in range(n))
            moving = len({tuple(m) for m in mine})
            waves = sorted({sets[name][t]["wave"] for t in range(6)})
            mults = sorted({sets[name][t]["mult"] for t in range(6)})
            rnd_ok = all(len({mine[b][t] for b in range(n)}) > 2 for t in rnd_t)
            check(same and moving > 50 and rnd_ok,
                  f"tirage {seed}, {name} = fonction des LFO de l'OS réglée pareil, {n} blocs, pistes {keep} "
                  f"(formes {waves}, mult {mults}, modes {[c['mode'] for c in common]}) ; {moving} sorties"
                  + (f" ; RND pistes {rnd_t} : valeurs au hasard (tirage commun, pas comparées)" if rnd_t else ""))
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")
    rules(S, P, base, syms)


def rules(S, P, base, syms):
    n = 200
    sched = masks_schedule(7, n)
    common = [dict(fade=0x4000, sph=0x0800 * t, mode=0) for t in range(6)]
    l1 = [lfo(spd=0x5000 + 0x400 * t, mult=2 + t, wave=t % 6, dest=14, dep=0x6800, **common[t]) for t in range(6)]
    none = [lfo() for _ in range(6)]
    ref1 = reference(S, [dict(c) for c in l1], common, base, sched, 14, n)

    # même destination que LFO 1 : s'additionnent avec saturation
    q = []

    def grab12(blk):
        q.append([(s32(P.r32(ST[2] + 32 * t + 20)), s32(P.r32(LFO_ST + 32 * t + 20))) for t in range(6)])
    l2 = [lfo(spd=0x6000, mult=5, wave=1, dest=14, dep=0x7f00) for _ in range(6)]
    b14 = {**base, 14: 0x7000}
    P.reset_lfo(syms)
    got = run(P, tracks(l1, l2, b14), sched, [14], n, syms, table34(none, none), after=grab12)
    exp = [[min(max(min(max(0x7000 + q2, 0), 0x7f00) + q1, 0), 0x7f00) for q2, q1 in q[b]] for b in range(n)]
    sat = sum(v in (0, 0x7f00) for b in range(n) for v in exp[b])
    check([[g[t][0] for t in range(6)] for g in got] == exp and sat > 0,
          f"LFO 1 et LFO 2 sur la même destination : mot = borne(borne(base + q2) + q1), 0..0x7f00 ({sat} butées)")

    # trois LFO sur la même destination (LFO 2 + LFO 3 + LFO 1) : s'additionnent avec saturation
    q.clear()

    def grab123(blk):
        q.append([(s32(P.r32(ST[2] + 32 * t + 20)),
                   s32(P.r32(ST[3] + 32 * t + 20)),
                   s32(P.r32(LFO_ST + 32 * t + 20))) for t in range(6)])
    l3_stack = [lfo(spd=0x7400, mult=3, wave=(t + 2) % 6, dest=14, dep=0x7800) for t in range(6)]
    P.reset_lfo(syms)
    got3 = run(P, tracks(l1, l2, b14), sched, [14], n, syms, table34(l3_stack, none), after=grab123)
    exp3 = [[min(max(min(max(min(max(0x7000 + q2, 0), 0x7f00) + q3, 0), 0x7f00) + q1, 0), 0x7f00)
             for q2, q3, q1 in q[b]] for b in range(n)]
    sat3 = sum(v in (0, 0x7f00) for b in range(n) for v in exp3[b])
    check([[g[t][0] for t in range(6)] for g in got3] == exp3 and sat3 > 0,
          f"trois LFO (LFO 2, 3 et 1) sur la même destination : mot = borne(borne(borne(base + q2) + q3) + q1), 0..0x7f00 ({sat3} butées)")

    # destination > 32 : rien d'autre que LFO 1
    l2 = [lfo(spd=0x6000, mult=5, wave=1, dest=40, dep=0x7f00) for _ in range(6)]
    P.reset_lfo(syms)
    S.reset_lfo()
    allk = list(range(33))
    got = run(P, tracks(l1, l2, base), sched, allk, n, syms, table34(none, none))
    ref = run(S, tracks(l1, l2, base), sched, allk, n)
    check(got == ref, "LFO 2 sur une destination > 32 : les 33 mots des pistes = l'OS sans le mod")

    # deux LFO de plus sur la même destination : s'ajoutent, bornés
    q = []

    def grab(blk):
        q.append([(s32(P.r32(ST[2] + 32 * t + 20)), s32(P.r32(ST[3] + 32 * t + 20))) for t in range(6)])
    l2 = [lfo(spd=0x6800, mult=3, wave=t % 6, dest=11, dep=0x7f00 if t % 2 else 0) for t in range(6)]
    l3 = [lfo(spd=0x7400, mult=7, wave=(t + 3) % 6, dest=11, dep=0x7800) for t in range(6)]
    b2 = {**base, 11: 0x7000}
    P.reset_lfo(syms)
    got = run(P, tracks(l1, l2, b2), sched, [11], n, syms, table34(l3, none), after=grab)
    exp = [[min(max(min(max(0x7000 + a, 0), 0x7f00) + c, 0), 0x7f00) for a, c in q[b]] for b in range(n)]
    sat = sum(v in (0, 0x7f00) for b in range(n) for v in exp[b])
    check([[g[t][0] for t in range(6)] for g in got] == exp and sat > 0,
          f"LFO 2 et LFO 3 sur la même destination : mot = borne(borne(base + q2) + q3), 0..0x7f00 ({sat} butées)")

    # LFO 2 -> vitesse de LFO 1 (k = 1) : appliqué avant LFO 1
    q.clear()
    l2 = [lfo(spd=0x7000, mult=6, wave=0, dest=1, dep=0x7f00) for _ in range(6)]
    P.reset_lfo(syms)
    got = run(P, tracks(l1, l2, base), sched, [1, 14], n, syms, table34(none, none), after=grab)
    exp = [[min(max(l1[t]["spd"] + q[b][t][0], 0), 0x7f00) for t in range(6)] for b in range(n)]
    diff = sum(got[b][t][1] != ref1[b][t] for b in range(n) for t in range(6))
    check([[g[t][0] for t in range(6)] for g in got] == exp and diff > 100,
          f"LFO 2 -> vitesse de LFO 1 : k1 = borne(SPD + q2) à chaque bloc, LFO 1 tourne avec ({diff} sorties de "
          "LFO 1 différentes de LFO 1 seul)")

    # jeux sans destination : pas calculés
    l2 = [lfo(spd=0x6000, mult=5, wave=1, dest=0, dep=0x7f00) for _ in range(6)]
    l3 = [lfo(spd=0x6000, mult=5, wave=1, dest=12 if t == 4 else 0, dep=0x7f00) for t in range(6)]
    P.reset_lfo(syms)
    run(P, tracks(l1, l2, base), sched, [12], 1, syms, table34(l3, none))
    s2, s4, s3 = P.rd(ST[2], 192), P.rd(ST[4], 192), P.rd(ST[3], 192)
    run(P, tracks(l1, l2, base), sched, [12], 50, syms, table34(l3, none))
    check(P.rd(ST[2], 192) == s2 and P.rd(ST[4], 192) == s4 and P.rd(ST[3], 192) != s3,
          "LFO 2 et LFO 4 sans destination : leurs états ne bougent pas ; LFO 3 (une piste) tourne")

    # k = 31 recopié brut des cibles (pas lissé)
    P.reset_lfo(syms)
    S.reset_lfo()
    P.uc.mem_write(syms["lfo34"], table34(none, none))
    l2 = [lfo(spd=0x6000, mult=5, wave=1, dest=11, dep=0x7f00) for _ in range(6)]
    tg = tracks(l1, l2, base)
    obj = bytearray(tg)
    for t in range(6):
        struct.pack_into(">H", obj, 14 + 66 * t + 62, 0x0a80)       # lissage en cours, entre 10 et 11
    out = {S: set(), P: set()}
    moved = 0
    for blk in range(20):
        for r in (S, P):
            r.uc.mem_write(OBJ, bytes(obj))
            r.uc.mem_write(TGT, tg)
            r.w32(ARG, TGT)
            r.w32(ARG + 4, 0)
            r.uc.reg_write(A[2], OBJ)
            r.uc.reg_write(A[3], ARG)
            r.uc.reg_write(A[7], STACK - 0x40)
            r.uc.emu_start(SITE, SITE_END, count=1_000_000)
            out[r] |= {(r.r16(OBJ + 14 + 66 * t + 62), r.r16(OBJ + 14 + 66 * t + 20)) for t in range(6)}
        moved += sum(P.r16(OBJ + 14 + 66 * t + 22) != 0x4000 for t in range(6))
    check(out[S] == {(0x0a80, 0x4000)} and out[P] == {(0x0b00, 0x4000)} and moved > 0,
          "k = 31 (destination de LFO 2) recopié brut des cibles comme k = 4 : 0x0a80 en cours de lissage -> 0x0b00, "
          f"LFO 2 module k = 11 et jamais k = 10 ({moved} mots modulés) ; l'origine n'y touche pas")

    # WAVE de LFO 2 lu dans les CIBLES k = 0 ; une valeur dans obj k = 0 (LFO 1 / vélocité vers None) n'y change rien
    l2w = [lfo(spd=0x6000, mult=5, wave=3, dest=11, dep=0x7f00) for _ in range(6)]
    tgw = tracks(l1, l2w, base)
    P.reset_lfo(syms)
    refw = run(P, tgw, sched, [11], n, syms, table34(none, none), obj0=0)
    P.reset_lfo(syms)
    junkw = run(P, tgw, sched, [11], n, syms, table34(none, none), obj0=0x0500)
    movingw = len({tuple(x[0] for x in b) for b in refw})
    check(refw == junkw and movingw > 1,
          f"WAVE de LFO 2 lu dans les cibles k = 0 : même sortie k = 11 ({movingw} valeurs) avec 0x0000 ou 0x0500 "
          "dans obj k = 0 (modulation de LFO 1 / vélocité)")
    b30 = {k: 0x4000 for k in range(9, 23)}
    tg30 = bytearray(tracks(l1, l2w, b30))
    for t in range(6):
        struct.pack_into(">H", tg30, 14 + 66 * t + 60, 0x1234)       # k = 30 : Lo-Fi Bits, hors LFO 2
    P.reset_lfo(syms)
    got30 = run(P, bytes(tg30), sched, [30], n, syms, table34(none, none))
    check(all(g[t][0] == 0x1234 for g in got30 for t in range(6)),
          "k = 30 (Lo-Fi Bits) jamais écrit par LFO 2, 3, 4 : 0x1234 des cibles gardé")
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


# --------------------------------------------------------------------------------- 3. interface ----------------

def ui(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    bound = img[0x4005a4e9 - BASE]
    page = syms["page"]
    # id -> k
    ok = {0: True, 1: True, 2: True, 3: True}
    for pg in range(4):
        P.w8(page, pg)
        for i in range(bound + 8):
            ks, kp = s32(S.call(ID2K, i)), s32(P.call(ID2K, i, check="id -> k"))
            exp = ks if pg == 0 or i not in OWN else ((28, 29, 0, 31, 32)[OWN[i]] if pg == 1 else -1)
            ok[pg] &= kp == exp
    P.w8(page, 0)
    check(ok[0], f"page LFO 1 : id -> k = l'origine pour les {bound + 8} identifiants (borne {bound})")
    check(ok[1], "page LFO 2 : SPD, MULT, WAVE, DEST, DEP -> k = 28, 29, 0, 31, 32 (WAVE en k 0, notes/86 §3) ; "
                 "tout le reste = l'origine")
    check(ok[2] and ok[3], "pages LFO 3/4 : ces 5 identifiants -> -1 (aucun mot du son) ; tout le reste = l'origine")
    ks = {s32(S.call(ID2K, i)) for i in range(bound + 1)}
    k2i = {S.call(K2ID, k, m) for k in range(28, 33) for m in range(24)}
    check(not ks & set(range(28, 33)) and k2i == {0},
          f"aucun descripteur ne vise k = 28..32 ({bound + 1} identifiants ; k -> identifiant = 0 pour 24 machines)")

    # touche [LFO]
    view = VIEWOBJ + 56
    P.w32(syms["view"], view)
    P.stub(ORIG_KEY, P.logged("orig", 0x77))
    P.stub(NEEDS_REDRAW, P.logged("redraw"))
    held = view - 56 + 604                              # drapeau « tenue » de la vue (0x40024db6)
    seq = [  # (code, indicateurs, drapeau tenue, rendu attendu, page, pend, original appelé, redessin)
        (8, 0, 0, 0x77, 0, 0, True, False),             # relâchement de l'appui qui a ouvert la page : l'original
        (8, 1, 0, 0x77, 0, 1, True, False),             # appui : l'original (il le prend), noté
        (8, 9, 0, 0x77, 0, 1, True, False),             # répétition : l'original
        (8, 0, 0, 1, 1, 0, False, True),                # relâchement d'un appui bref : LFO 2, redessin
        (8, 1, 0, 0x77, 1, 1, True, False),             # appui...
        (8, 0, 0xff, 0x77, 1, 0, True, False),          # ...potard tourné [LFO] tenue : l'original, la page reste
        (8, 1, 0, 0x77, 1, 1, True, False),             # appui...
        (9, 1, 0, 0x77, 1, 0, True, False),             # ...une autre touche (Clear LFO) : plus d'appui bref
        (9, 0, 0, 0x77, 1, 0, True, False),
        (8, 0, 0, 0x77, 1, 0, True, False),             # ...son relâchement : l'original, la page reste
        (8, 3, 0, 0x77, 1, 0, True, False),             # FUNC + [LFO] : l'original
        (8, 1, 0, 0x77, 1, 1, True, False), (8, 0, 0, 1, 2, 0, False, True),       # LFO 3
        (8, 1, 0, 0x77, 2, 1, True, False), (8, 0, 0, 1, 3, 0, False, True),       # LFO 4
        (8, 1, 0, 0x77, 3, 0, True, False), (8, 0, 0, 0x77, 3, 0, True, False)]   # sur LFO 4 : l'original (ferme)
        # (MACHINES a son propre bloc plus bas : avalée pendant [LFO] tenue seulement)
    good = True
    for code, flags, flag, ret, pg, pend, orig, redraw in seq:
        P.uc.mem_write(EVT, struct.pack(">5I", 0, 0, 0, code, flags))
        P.w8(held, flag)
        P.log.clear()
        r = P.call(P.r32(P_KEY), view, EVT, check="touche")
        names = [x[0] for x in P.log]
        good &= (r == ret and P.r8(page) == pg and P.r8(syms["pend"]) == pend and ("orig" in names) == orig
                 and (("redraw", view) in [x[:2] for x in P.log]) == redraw)
    P.w8(held, 0)
    check(good, "touche [LFO] : appui -> l'original (noté) ; relâchement d'un appui bref (drapeau tenue de la vue à "
                "0) -> LFO 2, 3, 4 (redessin) ; potard tourné [LFO] tenue (drapeau mis) ou autre touche entre-temps "
                "-> l'original, la page reste ; répétition / FUNC / relâchement de l'appui d'ouverture / LFO 4 -> "
                "l'original (il ferme la page au relâchement)")
    # MACHINES : avalée seulement pendant le geste [LFO] tenue + potard (et son relâchement avec elle) ; posée
    # seule sur la page LFO, elle passe à l'original, qui ouvre l'écran des machines (0x40075822)
    P.w8(page, 1)

    def ev(code, down):
        P.uc.mem_write(EVT, struct.pack(">5I", 0, 0, 0, code, 1 if down else 0))
        P.w8(held, 0)
        P.log.clear()
        return P.call(P.r32(P_KEY), view, EVT, check="touche"), [x[0] for x in P.log]

    P.w8(syms["pend"], 1)                       # appui bref de [LFO] en cours
    P.w8(KEY_BITS, 0x08)                        # [LFO] tenue : bit 3 de KEY_BITS (0x4010ae5c[8])
    r1, log1 = ev(5, True)                      # appui de MACHINES : avalé
    ok_held = r1 == 1 and "orig" not in log1 and P.r8(syms["pend"]) == 0 and P.r8(page) == 1
    r2, log2 = ev(5, False)                     # relâchement : avalé aussi
    ok_held &= r2 == 1 and "orig" not in log2 and P.r8(syms["m5"]) == 0
    check(ok_held, "MACHINES pendant [LFO] tenue : la touche est prise (l'original ne la voit pas), son relâchement "
                   "aussi, l'appui bref de [LFO] est annulé, la page ne bouge pas")
    P.w8(syms["pend"], 0)
    P.w8(KEY_BITS, 0)                           # [LFO] relâchée
    r3, log3 = ev(5, True)                      # appui de MACHINES seul : à l'original
    r4, log4 = ev(5, False)
    check(r3 == 0x77 and r4 == 0x77 and "orig" in log3 and "orig" in log4 and P.r8(page) == 1,
          "MACHINES seule sur la page LFO : appui et relâchement à l'original, qui ouvre l'écran des machines "
          "(0x40075822) ; la page ne bouge pas")
    # un appui avalé avale son relâchement même si [LFO] est lâchée entre-temps : l'OS ne voit jamais un
    # relâchement sans appui
    P.w8(KEY_BITS, 0x08)
    r5, log5 = ev(5, True)
    P.w8(KEY_BITS, 0)
    r6, log6 = ev(5, False)
    check(r5 == 1 and r6 == 1 and "orig" not in log5 + log6 and P.r8(syms["m5"]) == 0 and P.r8(page) == 1,
          "appui de MACHINES avalé puis [LFO] lâchée : le relâchement est avalé avec lui (m5 retombé)")
    P.w8(KEY_BITS, 0)
    P.w8(page, 3)

    # création / destruction de la vue
    P.stub(VIEW_CTOR, P.logged("ctor", 0x55))
    P.w8(page, 2)
    P.w8(syms["pend"], 1)
    P.log.clear()
    r = P.call(syms["lfo_ctor"], VIEWOBJ, check="création")
    check(r == 0x55 and P.log == [("ctor", VIEWOBJ, 0, 0, 0, 0, 0)] and P.r32(syms["view"]) == view
          and P.r8(page) == 0 and P.r8(syms["pend"]) == 0,
          "création : constructeur d'origine avec le même argument, vue = objet + 56, page LFO 1")
    P.call(syms["lfo_ctor"], 0)
    check(P.r32(syms["view"]) == 0, "création sur une allocation ratée (0) : pas de vue")
    P.stub(VIEW_CTOR, None)
    for other, cleared in ((VIEWOBJ + 0x400, False), (VIEWOBJ, True)):
        P.w32(syms["view"], view)
        P.w8(page, 3)
        sp = STACK - 0x40
        P.uc.mem_write(sp, struct.pack(">3I", 0x0a0a0a0a, 0x0b0b0b0b, other))
        P.uc.reg_write(A[7], sp)
        P.uc.reg_write(A[2], other)
        P.uc.emu_start(0x400d97f8, 0x400d97fe, count=1000)
        st = (P.r32(syms["view"]), P.r8(page))
        check(st == ((0, 0) if cleared else (view, 3)) and P.uc.reg_read(A[2]) == 0x0a0a0a0a,
              f"destruction {'de la vue LFO : page LFO 1, plus de vue' if cleared else 'd un autre objet : rien'}")
    P.w32(syms["view"], view)

    # rappels coupés sur les pages 3/4
    for addr in (CUR_PROJ, PROJ_SEQ, SEL_TRACK):
        P.stub(addr, P.logged(hex(addr)))
    P.log.clear()
    for pg in (2, 3):
        P.w8(page, pg)
        P.call(0x40025e10, THIS, 0x21, 0x300, check="rappel")
    check(P.log == [], "pages LFO 3/4 : 0x40025e10 (rappels WAVE, MULT, DEST, DEP de la vue) rend la main sans rien "
                       "faire")

    # get / set des pages 3/4
    sel = [0]
    P.stub(CUR_PROJ, lambda a: PROJ)
    P.stub(PROJ_SEQ, lambda a: SEQ)
    P.stub(SEL_TRACK, lambda a: sel[0])
    P.stub(ORIG_GET, P.logged("get", 0x1234))
    P.stub(ORIG_SET, P.logged("set", 0))
    good = True
    rnd = random.Random(5)
    for pg in (2, 3):
        P.w8(page, pg)
        for t in range(7):
            sel[0] = t
            for i in range(0x1b, 0x27):
                P.log.clear()
                v = rnd.randrange(0x7f01)
                P.call(P.r32(P_SET), THIS, i, v, 0, 0, check="set")
                g = s32(P.call(P.r32(P_GET), THIS, i, check="get"))
                mine = t < 6 and i in OWN
                at = syms["lfo34"] + 60 * (pg - 2) + 10 * t + 2 * OWN.get(i, 0)
                if mine:
                    good &= (P.r16(at) == v and g == v and [x[0] for x in P.log] == ["redraw"]
                             and P.log[0][1] == view)
                else:
                    good &= [x[:3] for x in P.log] == [("set", THIS, i), ("get", THIS, i)] and g == 0x1234
    P.w8(page, 1)
    P.log.clear()
    P.call(P.r32(P_SET), THIS, 0x1d, 5, 0, 0)
    P.call(P.r32(P_GET), THIS, 0x1d)
    good &= [x[0] for x in P.log] == ["set", "get"]
    check(good, "pages LFO 3/4 : SPD, MULT, WAVE, DEST, DEP de la piste sélectionnée dans la table LFO 3 / LFO 4, "
                "relus, redessin ; FADE, SPH, MODE, autres réglages, piste FX, page LFO 2 -> l'original")
    for addr in (ORIG_GET, ORIG_SET, CUR_PROJ, PROJ_SEQ, SEL_TRACK):
        P.stub(addr, None)

    # page LFO 2 : le vrai get/set de l'OS sur les mots du son
    for r in (S, P):
        setup_track(r)
    good = True
    for pg in (0, 1):
        P.w8(page, pg)
        for r in (S, P):
            r.uc.mem_write(SOUND + 20, bytes(66))
            r.log.clear()
            for i, v in ((0x1d, 0x5a00), (0x1e, 0x0b00), (0x1f, 0x3100), (0x20, 0x0e00), (0x21, 0x0300),
                         (0x22, 0x1200), (0x23, 0x0200), (0x24, 0x2380)):
                r.call(r.r32(P_SET), THIS, i, v, 0, 0, check="set de l'OS")
        sw = [P.r16(SOUND + 20 + 2 * k) for k in range(33)]
        ref = [S.r16(SOUND + 20 + 2 * k) for k in range(33)]
        if pg == 0:
            good &= sw == ref and P.log == S.log
        else:
            exp = list(ref)
            for k, src in zip((28, 29, 0, 31, 32), (1, 2, 5, 4, 8)):
                exp[k], exp[src] = ref[src], 0
            good &= sw == exp and [x[2] for x in P.log] == [28, 29, 3, 31, 0, 6, 7, 32]
            good &= [s32(P.call(P.r32(P_GET), THIS, i)) for i in (0x1d, 0x1e, 0x21, 0x20, 0x24, 0x1f)] == \
                [0x5a00, 0x0b00, 0x0300, 0x0e00, 0x2380, 0x3100]
    P.w8(page, 0)
    check(good, "page LFO 2 : le get/set de l'OS (0x4000ae20, 0x4000ba7a) lit et écrit k = 28, 29, 0, 31, 32 du son "
                "(SPD, MULT, WAVE, DEST, DEP), WAVE dans le mot k = 0, et notifie ces k ; FADE, SPH, MODE restent ceux "
                "de LFO 1 ; page LFO 1 = l'origine")

    # dessin
    P.stub(ORIG_DRAW, P.logged("draw"))
    P.stub(FILL_RECT, P.logged("fill"))
    P.stub(TEXT, lambda a: P.log.append(("text",) + a[:5] + (P.rd(a[5], 2),)) or 0)
    good = True
    for pg in range(4):
        P.w8(page, pg)
        P.log.clear()
        P.call(P.r32(P_DRAW), view, BMP, check="dessin")
        exp = [("draw", view, BMP)]
        if pg:
            box = ("fill", BMP, 0, 0, 63, 63, M32)
            exp += [box, ("text", BMP, FONT, 32, 34, 2, b"%d\0" % (pg + 1)), box]
        good &= [e[:3] if e[0] == "draw" else e for e in P.log] == exp
    P.w8(page, 0)
    for addr in (ORIG_DRAW, FILL_RECT, TEXT, ORIG_KEY, NEEDS_REDRAW):
        P.stub(addr, None)
    check(good, "dessin : l'original, puis sur LFO 2/3/4 le cadre gauche inversé, « 2 »/« 3 »/« 4 » centré avec la "
                "police du nom de page en (32, 34), cadre réinversé ; rien sur LFO 1")
    dest_wheel(S, P, syms)
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


def setup_track(r, machine=0):
    """this de l'accesseur (vtable de l'OS, + 4 : objet de la piste), objet de la piste (vtable factice : [40] -> le
    son, [16] -> notification « k modifié »), son."""
    r.w32(THIS, ACC_VT)
    r.w32(THIS + 4, TRACKOBJ)
    r.w32(TRACKOBJ, FAKEVT)
    r.w32(FAKEVT + 40, FCODE)
    r.w32(FAKEVT + 16, FCODE + 16)
    r.uc.mem_write(FCODE, b"\x4e\x75" * 16)
    r.stub(FCODE, lambda a: SOUND)
    r.stub(FCODE + 16, lambda a: r.log.append(("notify", a[0], r.r32(a[1] + 4))) or 0)
    r.uc.mem_write(SOUND, bytes(100))
    r.w8(SOUND + 38, machine)


def dest_wheel(S, P, syms):
    """Molette DEST : vtable [20] de l'accesseur (0x4000c264, ou fine_hook de Model-TG) -> 0x4000c140."""
    page, view = syms["page"], VIEWOBJ + 56
    sel = [0]
    for r in (S, P):
        setup_track(r, machine=0)
        r.stub(CUR_PROJ, lambda a: PROJ)
        r.stub(PROJ_SEQ, lambda a: SEQ)
        r.stub(SEL_TRACK, lambda a: sel[0])

    def step(r, v, d):
        return s32(r.call(r.r32(P_DELTA), THIS, 0x20, v, d << 8, check="pas de DEST"))

    def chain(r, start=0):
        seen, v = [start], start
        for _ in range(80):
            n = step(r, v, 1)
            if n == v:
                break
            seen.append(n)
            v = n
        return seen
    ref = chain(S)
    ks = [v >> 8 for v in ref]
    good = len(ref) > 5 and all(v & 0xff == 0 for v in ref)
    P.w32(syms["view"], 0)
    good &= chain(P) == ref
    P.w32(syms["view"], view)
    for pg in range(4):
        P.w8(page, pg)
        good &= chain(P) == ref and P.r8(page) == pg
    check(good, f"liste des destinations (machine 0) : k = {ks} ; modifié, page fermée ou ouverte sur LFO 1..4 sans "
                "destination prise : la même, page rendue (la liste de l'OS ne propose aucun réglage de LFO)")
    # destinations prises par les autres LFO de la piste
    good = True
    tests = 0
    t = 3
    sel[0] = t
    for pg in range(4):
        P.w8(page, pg)
        for start in range(len(ref) - 1):
            for taken_at in ((1, 2), (1, 2, 3), (2,), (1, 3)):
                for d in (1, -1):
                    idx = [start + d * j for j in taken_at]
                    if min(idx) < 1 or max(idx) >= len(ref):
                        continue
                    tk = [ks[j] for j in idx]
                    others = [x for x in range(4) if x != pg]
                    dests = {x: 0 for x in range(4)}
                    for x, k in zip(others, tk):
                        dests[x] = k
                    P.w8(SOUND + 28, dests[0])
                    P.w8(SOUND + 82, dests[1])
                    P.w8(syms["lfo34"] + 10 * t + 6, dests[2])
                    P.w8(syms["lfo34"] + 60 + 10 * t + 6, dests[3])
                    taken = {dests[x] for x in others} - {0}
                    v, exp = ref[start], ref[start]
                    for _ in range(5):
                        n = step(S, v, d)
                        if n == v:
                            exp = ref[start]
                            break
                        v = n
                        if (n >> 8) not in taken:
                            exp = n
                            break
                    else:
                        exp = ref[start]
                    good &= step(P, ref[start], d) == exp and P.r8(page) == pg
                    tests += 1
    for x in (SOUND + 28, SOUND + 82, syms["lfo34"] + 10 * t + 6, syms["lfo34"] + 60 + 10 * t + 6):
        P.w8(x, 0)
    P.w8(page, 0)
    check(good and tests > 100, f"DEST saute les destinations prises par les 3 autres LFO de la piste (LFO 1 = son "
                                f"+ 28, LFO 2 = son + 82, LFO 3/4 = table), dans les deux sens, {tests} cas ; "
                                "None toujours permise ; bout de la liste : inchangée")


# --------------------------------------------------------------------------------- 4. son ---------------------

def sound_bytes(rnd, lfo2):
    b = bytearray(100)
    b[0:4] = b"\x12\x34\x56\x78"
    b[4:20] = bytes(rnd.randrange(65, 91) for _ in range(16))
    for k in range(33):
        struct.pack_into(">H", b, 20 + 2 * k, rnd.randrange(0x7f01) & ~0xff if k in (2, 4, 5, 7, 9) else
                         rnd.randrange(0x7f01))
    struct.pack_into(">H", b, 38, rnd.randrange(6) << 8)               # k = 9 : machine (octet fort)
    struct.pack_into(">H", b, 28, rnd.randrange(33) << 8)              # k = 4 : destination de LFO 1
    struct.pack_into(">H", b, 20, lfo2[2])                             # k = 0 : WAVE de LFO 2 (notes/86 §3)
    struct.pack_into(">5H", b, 76, lfo2[0], lfo2[1], 0x0f00, lfo2[3], lfo2[4])   # k 30 : Lo-Fi Bits, leurre
    struct.pack_into(">IHBBI", b, 88, rnd.randrange(23), 0x4000, rnd.randrange(24), rnd.randrange(128), 0x7f)
    return bytes(b)


def packed(w):
    return ((w[0] >> 7 & 0xff) << 22 | 2 << 30 | (w[1] >> 8 & 0x1f) << 17 | (w[2] >> 8 & 7) << 14
            | (w[3] >> 8 & 0x3f) << 8 | (w[4] >> 7 & 0xff))


def unpacked(p):
    return [(p >> 22 & 0xff) << 7, (p >> 17 & 0x1f) << 8, (p >> 14 & 7) << 8, (p >> 8 & 0x3f) << 8, (p & 0xff) << 7]


def sound(base_img, img, rt, syms, david=None):
    S, P = Rig(base_img, rt), Rig(img, rt)
    rnd = random.Random(9)
    cases = [[0x7000, 0x0400, 0, 0, 0x4000], [0x5a80, 0x0b00, 0x0300, 0x0e00, 0x2380],
             [0x5aff, 0x0b7f, 0x03ff, 0x0eff, 0x23ff], [0x7f00, 0x1700, 0x0600, 0x2000, 0x7f00], [0, 0, 0, 0, 0]]
    cases += [[rnd.randrange(0x7f01), rnd.randrange(24) << 8, rnd.randrange(7) << 8, rnd.randrange(33) << 8,
               rnd.randrange(0x7f01)] for _ in range(20)]
    save_ok = load_ok = old_ok = back_ok = legacy_ok = True
    for c in cases:
        snd = sound_bytes(rnd, c)
        for fn in (SND_SAVE2, SND_SAVE1):
            recs = []
            for r in (S, P):
                r.uc.mem_write(SOUND, snd)
                r.uc.mem_write(REC, b"\xa5" * 100)
                ok = r.call(fn, REC, SOUND, check="sauvegarde du son") & 0xff
                recs.append(r.rd(REC, 100))
            rs, rp = recs
            save_ok &= ok == 1 and rs[:88] == rp[:88] and rs[92:] == rp[92:] and rs[88:92] == bytes(4) \
                and int.from_bytes(rp[88:92], "big") == packed(c)
            if fn == SND_SAVE1:
                continue                    # format 1 : 64 sons vides d'une réserve neuve (0x4005be00), pas relu ici
            outs = []
            for r, rec in ((S, rs), (P, rp), (S, rp), (P, rs)):
                r.uc.mem_write(REC, rec)
                r.uc.mem_write(SOUND2, b"\x55" * 100)
                r.call(SND_LOAD, SOUND2, REC, check="chargement du son")
                outs.append(r.rd(SOUND2, 100))
            ls, lp, ls_new, lp_old = outs
            u = unpacked(packed(c))
            # l'OS sans le mod garde l'ancienne disposition (WAVE en k 30) ; k 0 reçoit la case 18 du son, comme avant
            load_ok &= ls[:20] == lp[:20] and ls[22:76] == lp[22:76] and ls[86:] == lp[86:] \
                and ls[20:22] == rs[64:66] and ls_new[20:22] == rp[64:66] \
                and ls[76:86] == bytes(10) \
                and lp[20:22] == struct.pack(">H", u[2]) \
                and list(struct.unpack(">2H", lp[76:80])) == u[:2] and lp[80:82] == bytes(2) \
                and list(struct.unpack(">2H", lp[82:86])) == u[3:]
            old_ok &= ls[:20] == lp_old[:20] and ls[22:76] == lp_old[22:76] and ls[86:] == lp_old[86:] \
                and list(struct.unpack(">5H", lp_old[76:86])) == DEFAULTS and lp_old[20:22] == bytes(2) \
                and lp_old[80:82] == bytes(2)
            back_ok &= ls_new == ls
            # (a) enregistrement de l'ANCIENNE disposition (WAVE empaqueté en +88, p-lock en rangée 29) : relu ici
            legacy = bytearray(rs)
            legacy[88:92] = struct.pack(">I", packed(c))
            P.uc.mem_write(REC, bytes(legacy))
            P.uc.mem_write(SOUND2, b"\x55" * 100)
            P.call(SND_LOAD, SOUND2, REC, check="chargement d'un ancien son")
            lq = P.rd(SOUND2, 100)
            legacy_ok &= lq[20:22] == struct.pack(">H", u[2]) \
                and list(struct.unpack(">2H", lq[76:80])) == u[:2] and lq[80:82] == bytes(2) \
                and list(struct.unpack(">2H", lq[82:86])) == u[3:]
    check(save_ok, f"sauvegarde (formats 2 et 1), {len(cases)} sons : enregistrement = l'origine sauf +88..+91 = LFO 2 "
                   "empaqueté (marque 10, SPD>>7, MULT, WAVE, DEST, DEP>>7) ; WAVE pris en k 0, k 30 (Lo-Fi Bits) "
                   "ignoré")
    check(load_ok, "chargement (0x4005aecc, enregistrements au format 2, le seul qu'il relit) : son = l'origine sauf "
                   "k = 28, 29, 31, 32 = SPD, MULT, DEST, DEP et k = 0 = WAVE, k = 30 laissé à 0 (SPD et DEP au "
                   "multiple de 0x80 près : 0x5aff -> 0x5a80) ; l'OS sans le mod ne relit pas +88 (k = 28..32 à 0)")
    check(old_ok, "son sauvé sans le mod (+88 = 0) : LFO 2 aux défauts (0x7000, 4, TRI, None, 0), k = 0 et k = 30 "
                  "à 0, le reste = l'origine")
    check(back_ok, "OS sans le mod : relit un son sauvé avec le mod comme le sien (+88..+91 ignorés)")
    check(legacy_ok, "enregistrement de l'ancienne disposition (WAVE empaqueté en +88, comme avant notes/86) : "
                     "WAVE relu en k = 0, k = 30 remis à 0, SPD, MULT, DEST, DEP en k = 28, 29, 31, 32")
    good = True
    for tag in (0x00000000, 0x40ffffff, 0xc0ffffff, 0x3fffffff):
        snd = sound_bytes(rnd, cases[1])
        P.uc.mem_write(SOUND, snd)
        P.call(SND_SAVE2, REC, SOUND)
        P.w32(REC + 88, tag)
        P.uc.mem_write(SOUND2, b"\x55" * 100)
        P.call(SND_LOAD, SOUND2, REC)
        good &= list(struct.unpack(">5H", P.rd(SOUND2 + 76, 10))) == DEFAULTS and P.rd(SOUND2 + 20, 2) == bytes(2) \
            and P.rd(SOUND2 + 80, 2) == bytes(2)
    check(good, "marque autre que 10 en +88 : défauts (k = 28..32), WAVE en k = 0 à 0, k = 30 à 0")
    good = True
    for m in range(6):
        outs = []
        for r in (S, P):
            r.uc.mem_write(SOUND2, b"\x55" * 100)
            r.call(SND_INIT, SOUND2, M32, m, check="son aux défauts")
            outs.append(r.rd(SOUND2, 100))
        good &= outs[0][:76] == outs[1][:76] and outs[0][86:] == outs[1][86:] \
            and list(struct.unpack(">5H", outs[1][76:86])) == DEFAULTS and outs[0][76:86] == bytes(10) \
            and outs[1][80:82] == bytes(2)
    check(good, "son neuf (0x40061866, machines 0..5) : = l'origine, sauf LFO 2 aux défauts (l'origine y met 0), "
                "k = 30 (Lo-Fi Bits) à 0")
    if david:
        Dv = Rig(david)
        good = True
        for c in cases[:6]:
            # l'ancien .syx lit WAVE en k = 30 : on lui donne un son à l'ancienne disposition
            snd = bytearray(sound_bytes(rnd, c))
            snd[20:22] = bytes(2)
            struct.pack_into(">H", snd, 80, c[2])
            Dv.uc.mem_write(SOUND, bytes(snd))
            Dv.uc.mem_write(REC, bytes(100))
            Dv.call(SND_SAVE2, REC, SOUND)
            rec = Dv.rd(REC, 100)
            P.uc.mem_write(REC, rec)
            P.uc.mem_write(SOUND2, b"\x55" * 100)
            P.call(SND_LOAD, SOUND2, REC)
            u = unpacked(packed(c))
            got = P.rd(SOUND2, 100)
            good &= got[20:22] == struct.pack(">H", u[2]) and got[80:82] == bytes(2) \
                and list(struct.unpack(">2H", got[76:80])) == u[:2] \
                and list(struct.unpack(">2H", got[82:86])) == u[3:] \
                and int.from_bytes(rec[88:92], "big") == packed(c)
        check(good, "son sauvé par le .syx de DavidCaruso : même +88..+91, relu ici avec le même LFO 2 (WAVE en k = 0, "
                    "k = 30 à 0)")
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


# --------------------------------------------------------------------------------- 5. p-locks ------------------

def plocks(base_img, img, rt):
    S, P = Rig(base_img, rt), Rig(img, rt)
    plk_k = [23, 24, 25, 28, 29, 0, 31, 32]
    good = True
    for t in range(8):
        for i in range(48):
            ks, kp = s32(S.call(PLK_K, t, i)), s32(P.call(PLK_K, t, i, check="identifiant -> k"))
            good &= kp == (plk_k[i - 24] if t <= 5 and 24 <= i <= 31 else ks)
    check(good, "identifiant de rangée -> k : pistes 0..5, identifiants 24..31 -> k = 23, 24, 25, 28, 29, 0, 31, 32 "
                "(rangée 29 = WAVE de LFO 2, k 0) ; tout le reste (piste FX comprise) = l'origine")
    rnd = random.Random(4)
    src = bytearray(6 * 4385)
    for t in range(6):
        for s in range(64):
            for k in range(33):
                struct.pack_into(">H", src, t * 4385 + s * 68 + 2 * k, 0xffff)
    locked = {}
    for t in (0, 5):
        for k in range(33):
            src[t * 4385 + 4352 + k] = 1
            for s in range(64):
                if rnd.random() < 0.3:
                    v = rnd.randrange(0x7f01)
                    struct.pack_into(">H", src, t * 4385 + s * 68 + 2 * k, v)
                    locked[(t, k, s)] = v
    res = {}
    for name, r in (("origine", S), ("modifié", P)):
        r.uc.mem_write(PSRC, bytes(src))
        r.uc.mem_write(ROWS, bytes(10400))
        r.uc.mem_write(PDST, bytes(6 * 4385))
        a = r.call(PLK_SAVE, ROWS, PSRC, check="enregistrement des p-locks") & 0xff
        b = r.call(PLK_LOAD, PDST, ROWS, check="relecture des p-locks") & 0xff
        dst = r.rd(PDST, 6 * 4385)
        back = {}
        for t in (0, 5):
            for k in range(33):
                for s in range(64):
                    v = struct.unpack_from(">H", dst, t * 4385 + s * 68 + 2 * k)[0]
                    if v != 0xffff:
                        back[(t, k, s)] = v
        ids = sorted({r.r8(ROWS + 130 * i) for i in range(64)})
        res[name] = (a, b, back, ids)
    exp = {key: v for key, v in locked.items() if key[1] not in (26, 27, 30)}
    a, b, back, ids = res["modifié"]
    check(a == b == 1 and back == exp,
          f"aller-retour 0x4005b95c -> 0x4005b766, 2 pistes, k = 0..32 ({len(exp)} p-locks) : tous relus au même k "
          f"et au même pas, WAVE (k 0) par la rangée 29 ; k = 26, 27 (état du Sampler de Model-TG) et k = 30 "
          f"(Lo-Fi Bits, rangée 0xff) ignorés ; identifiants {ids}")
    a, b, back, ids = res["origine"]
    lost = {k for (t, k, s) in locked if back.get((t, k, s)) != locked[(t, k, s)]}
    check(lost == set(range(0, 10)) | set(range(23, 33)),
          "origine, pour mémoire : les rangées de k = 23..32 reviennent sur k = 0..9 et les écrasent (k perdus : "
          f"{sorted(lost)}) ; k = 10..22 relus")
    # (a) p-locks de l'ancienne disposition : WAVE était p-locké en k 30, donc rangée 29 ; relu sur k 0
    rows = bytearray(10400)
    for i in range(64):
        rows[130 * i:130 * i + 2] = b"\xff\xff"
    struct.pack_into(">BBH", rows, 0, 29, 3, 0x0600)
    P.uc.mem_write(ROWS, bytes(rows))
    P.uc.mem_write(PDST, bytes(6 * 4385))
    b = P.call(PLK_LOAD, PDST, ROWS, check="ancien p-lock")
    dst = P.rd(PDST, 6 * 4385)
    check(b == 1 and struct.unpack_from(">H", dst, 3 * 4385)[0] == 0x0600
          and struct.unpack_from(">H", dst, 3 * 4385 + 2 * 30)[0] == 0xffff,
          "p-lock de WAVE de l'ancienne disposition (rangée 29, k 30) : relu sur k = 0, k = 30 laissé libre")
    check(not (S.bad or P.bad), "aucun accès hors mémoire")


# --------------------------------------------------------------------------------- 6. coût ---------------------

def cost(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    base = {k: 0x4000 for k in range(9, 23)}
    l1 = [lfo(spd=0x5800, mult=3 + t, wave=t % 6, dest=14, dep=0x6000, sph=0x1000, mode=t % 2) for t in range(6)]
    on = [lfo(spd=0x6400, mult=5, wave=1, dest=11, dep=0x7000) for _ in range(6)]
    one = [lfo(spd=0x6400, mult=5, wave=1, dest=11 if t == 0 else 0, dep=0x7000) for t in range(6)]
    off = [lfo() for _ in range(6)]
    sched = masks_schedule(3, 100)
    out = {}
    for name, r, l2, l34 in (("origine", S, None, None), ("modifié, sans LFO de plus", P, off, table34(off, off)),
                             ("modifié, LFO 2 (une piste)", P, one, table34(off, off)),
                             ("modifié, LFO 2 (6 pistes)", P, on, table34(off, off)),
                             ("modifié, LFO 2 + 3 + 4", P, on, table34(on, on))):
        r.reset_lfo(syms if r is P else None)
        if l34:
            r.uc.mem_write(syms["lfo34"], l34)
        tg = tracks(l1, l2, base)
        n = [r.counted(lambda: r.block(tg, 14400, sched[b], smooth=False))[1] - 3 for b in range(100)]
        out[name] = (sum(n) / len(n), max(n))
    o = out["origine"][0]
    print("     instructions par bloc (appel des LFO, moyenne / max ; en plus de l'origine, et en part d'un bloc de "
          "166 667 cycles à 1,54 cycle par instruction, hors cache) :")
    for name, (avg, mx) in out.items():
        print(f"       {name:28} {avg:7.0f} / {mx:5}   + {avg - o:5.0f}  ({(avg - o) * 1.54 / 1666.67:4.2f} %)")
    z = out["modifié, sans LFO de plus"][0]
    check(z - o < 200, f"sans LFO de plus : + {z - o:.0f} instructions par bloc ({(z - o) * 1.54 / 1666.67:.2f} % d'un bloc)")


# --------------------------------------------------------------------------------- 7. accroches -----------------

def sites(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    rnd = random.Random(8)
    lfo2 = [0x5a80, 0x0b00, 0x0300, 0x0e00, 0x2380]
    snd = sound_bytes(random.Random(1), lfo2)
    for r in (S, P):
        r.uc.mem_write(SOUND, snd)
    bound = img[0x4005a4e9 - BASE]
    PC = mk.UC_M68K_REG_PC

    def one(start, stop, frame=(), regs=None, clobber=(), page=0, view=0, rec=None, differ=(), extra=None,
            snd2=b"\x77" * 100):
        """De start à stop (les instructions remplacées), origine et modifié, mêmes registres au départ (au hasard,
        sauf regs) : mêmes registres à l'arrivée hors clobber, même pile, mêmes REC / SOUND2 / ROWS
        hors differ ; extra(origine, modifié) en plus. La pile comparée est celle au-dessus de sp (en dessous, la place
        libre où un jsr met son adresse de retour). snd2 : contenu de SOUND2 au départ."""
        init = {k: rnd.getrandbits(32) for k in D + A[:7]}
        init.update(regs or {})
        stack = bytes(rnd.getrandbits(8) for _ in range(128))
        res = []
        for r in (S, P):
            if r is P:
                P.w8(syms["page"], page)
                P.w32(syms["view"], view)
            r.uc.mem_write(STACK - 0x80, stack)
            r.uc.mem_write(STACK - 0x40, b"".join(struct.pack(">I", w & M32) for w in frame))
            r.uc.mem_write(REC, rec or bytes(range(100)))
            r.uc.mem_write(SOUND2, snd2)
            r.uc.mem_write(ROWS, b"\xee" * 130)
            for k, v in init.items():
                r.uc.reg_write(k, v)
            r.uc.reg_write(A[7], STACK - 0x40)
            r.uc.emu_start(start, stop, count=10_000)
            res.append(dict(regs={k: r.uc.reg_read(k) for k in D + A}, pc=r.uc.reg_read(PC), stack=r.rd(STACK - 0x40, 64), REC=r.rd(REC, 100),
                            SOUND2=r.rd(SOUND2, 100), ROWS=r.rd(ROWS, 130)))
        s, p = res
        ok = s["pc"] == p["pc"] == stop and s["stack"] == p["stack"]
        ok &= all(s["regs"][k] == p["regs"][k] for k in D + A if k not in clobber)
        ok &= all(s[m] == p[m] for m in ("REC", "SOUND2", "ROWS") if m not in differ)
        return ok and (extra is None or extra(s, p))

    def outside(s, p, m, lo, hi):
        return s[m][:lo] + s[m][hi:] == p[m][:lo] + p[m][hi:]

    out = {}
    ids = [24, 25, 26, 0xff, 0xff, 27, 28, 0xff, 30, 31]
    # les indicateurs (CCR) de la comparaison remplacée servent à l'instruction suivante : on va jusqu'au retour de
    # la fonction (adresse de retour 0x400a0a0a) pour qu'elle s'en serve
    out["0x4005a4ea id -> k jusqu'au retour, page LFO 1 (tous les identifiants), page LFO 2 (hors LFO) (rien)"] = all(
        one(0x4005a4ea, 0x400a0a0a, (0x400a0a0a, i), {D[1]: bound}, page=pg)
        for pg in (0, 1) for i in range(bound + 3) if pg == 0 or i not in range(0x1d, 0x25))
    out["0x4005aa22 identifiant -> k jusqu'au retour, hors pistes 0..5 x identifiants 24..31 (rien)"] = all(
        one(0x4005aa22, 0x400a0a0a, (0x0d0d0d0d, 0x400a0a0a, t, i), {D[1]: t, D[2]: 6})
        for t, i in ((6, 25), (7, 24), (2, 5), (0, 23), (0, 32), (5, 40), (3, 0), (0, M32), (6, 31), (9, 0),
                     (6, 0), (6, 4), (6, 5)))
    out["0x4005b9c6 rangée de p-locks, k = 1..22 (rien)"] = all(
        one(0x4005b9c6, 0x4005b9ce, (), {A[5]: 0x4010ee4c, D[4]: 4 * k, D[0]: k, D[2]: t, A[3]: ROWS})
        for k in range(1, 23) for t in (0, 5))
    out["0x4005b9c6 rangée de p-locks, k = 0 (WAVE de LFO 2 -> rangée 29)"] = all(
        one(0x4005b9c6, 0x4005b9ce, (), {A[5]: 0x4010ee4c, D[4]: 0, D[0]: 0, D[2]: t, A[3]: ROWS},
            differ=("ROWS",), extra=lambda s, p, t=t: p["ROWS"][:2] == bytes([29, t])
            and s["ROWS"][1:] == p["ROWS"][1:])
        for t in (0, 5))
    out["0x4005b9c6 rangée de p-locks, k = 23..32 (rien ; identifiant de plk_id)"] = all(
        one(0x4005b9c6, 0x4005b9ce, (), {A[5]: 0x4010ee4c, D[4]: 4 * k, D[0]: k, D[2]: t, A[3]: ROWS},
            differ=("ROWS",), extra=lambda s, p, k=k, t=t: p["ROWS"][:2] == bytes([ids[k - 23], t])
            and s["ROWS"][1:] == p["ROWS"][1:])
        for k in range(23, 33) for t in (0, 5))
    for at in (0x4005b028, 0x4005b0dc):
        out[f"{at:#x} sauvegarde du son (d0 ; +88..+91 = LFO 2 empaqueté)"] = all(
            one(at, at + 6, (), {A[2]: REC, A[3]: SOUND}, clobber=(D[0],), differ=("REC",),
                extra=lambda s, p: outside(s, p, "REC", 88, 92) and int.from_bytes(p["REC"][88:92], "big")
                == packed(lfo2) and p["REC"][92:94] == snd[94:96])
            for _ in range(6))
    recs = [bytes(range(100))] + [bytes(100)] + [bytes(rnd.getrandbits(8) for _ in range(88)) + struct.pack(
        ">I", packed([rnd.randrange(0x7f01), rnd.randrange(24) << 8, rnd.randrange(7) << 8,
                      rnd.randrange(33) << 8, rnd.randrange(0x7f01)])) + bytes(8) for _ in range(6)]
    out["0x4005af1c chargement du son (d0, d1, a1 ; k = 28, 29, WAVE en k 30, 31, 32 du son)"] = all(
        one(0x4005af1c, 0x4005af22, (), {A[2]: SOUND2, A[3]: REC}, clobber=(D[0], D[1], A[1]), rec=rec,
            differ=("SOUND2",), extra=lambda s, p, rec=rec: outside(s, p, "SOUND2", 76, 86)
            and s["regs"][A[0]] == 0x4010eea8 and list(struct.unpack(">5H", p["SOUND2"][76:86])) ==
            (unpacked(int.from_bytes(rec[88:92], "big")) if rec[88] >> 6 == 2 else DEFAULTS))
        for rec in recs)
    tail = bytearray(b"\x77" * 100)
    tail[20:22] = b"\x11\x11"                              # k 0 : la case 18 du son, que l'OS vient d'y mettre
    tail[80:82] = b"\x06\x00"                              # k 30 : WAVE, posée par upk5
    out["0x4005af3e fin du chargement du son (a1, a2 ; k 30 -> k 0, k 30 remis à 0)"] = all(
        one(0x4005af3e, 0x4005af46, (), {A[2]: SOUND2, A[1]: 0x4010eea8}, clobber=(D[0],), snd2=bytes(tail),
            differ=("SOUND2",), extra=lambda s, p: s["SOUND2"] == bytes(tail)
            and p["SOUND2"][20:22] == bytes(tail[80:82]) and p["SOUND2"][80:82] == bytes(2)
            and s["SOUND2"][:20] + s["SOUND2"][22:80] + s["SOUND2"][82:]
            == p["SOUND2"][:20] + p["SOUND2"][22:80] + p["SOUND2"][82:])
        for _ in range(4))
    out["0x400618e2 son aux défauts (d0, d1, a0, a1 ; k = 28..32 du son)"] = all(
        one(0x400618e2, 0x400618e8, (), {A[2]: SOUND2, D[3]: m}, clobber=(D[0], D[1], A[0], A[1]),
            differ=("SOUND2",), extra=lambda s, p: outside(s, p, "SOUND2", 76, 86)
            and list(struct.unpack(">5H", p["SOUND2"][76:86])) == DEFAULTS)
        for m in range(6))
    out["0x40025e10 rappels de la vue, pages LFO 1/2 (d0)"] = all(
        one(0x40025e10, 0x40025e16, (0x400a0a0a, THIS, 0x21, 0x300), clobber=(D[0],), page=pg)
        for pg in (0, 1) for _ in range(4))
    out["0x400d97f8 destruction de la vue (a0)"] = all(
        one(0x400d97f8, 0x400d97fe, (0x0a0a0a0a, 0x400a0a0a, o), {A[2]: o}, clobber=(A[0],), view=v)
        for o in (VIEWOBJ, VIEWOBJ + 0x400) for v in (0, VIEWOBJ + 56, VIEWOBJ + 0x400 + 56))
    out["0x4000c140 pas de DEST, page fermée (rien)"] = all(
        one(0x4000c140, 0x4000c148, (0x400a0a0a, THIS, 0x0300, 0x100, 0x600)) for _ in range(4))
    out["0x4001c3dc création de la vue, jusqu'à 0x40025798 (d0)"] = all(
        one(0x4001c3dc, 0x40025798, (VIEWOBJ, 0x260), clobber=(D[0],)) for _ in range(4))
    out["pointeurs get / set / touche, page LFO 1, jusqu'à l'original (d0, d1, a0, a1)"] = all(
        one_ptr(S, P, syms, rnd, ptr, orig, args)
        for ptr, orig, args in ((P_GET, ORIG_GET, (THIS, 0x1d)), (P_GET, ORIG_GET, (THIS, 0x30)),
                                (P_SET, ORIG_SET, (THIS, 0x1d, 0x1234, 0, 0)),
                                (P_KEY, ORIG_KEY, (VIEWOBJ + 56, EVT))))
    for name, ok in out.items():
        check(ok, f"{name} : même pile, mêmes registres hors ceux entre parenthèses (que la suite réécrit), même "
                  "mémoire")
    check(not (S.bad or P.bad), "aucun accès hors mémoire")


def one_ptr(S, P, syms, rnd, ptr, orig, args):
    """Pointeur de vtable réécrit, page LFO 1 : arrive à l'original avec la même pile et les mêmes registres (hors
    d0, d1, a0, a1) ; l'origine pointe sur l'original."""
    P.w8(syms["page"], 0)
    P.uc.mem_write(EVT, struct.pack(">5I", 0, 0, 0, 9, 1))
    for addr in (CUR_PROJ, PROJ_SEQ, SEL_TRACK):
        P.stub(addr, lambda a: 0)
    regs = {k: rnd.getrandbits(32) for k in D + A[:7]}
    sp = STACK - 0x40
    frame = struct.pack(">I", 0x400a0a0a) + b"".join(struct.pack(">I", x) for x in args)
    P.uc.mem_write(sp, frame)
    for k, v in regs.items():
        P.uc.reg_write(k, v)
    P.uc.reg_write(A[7], sp)
    P.uc.emu_start(P.r32(ptr), orig, count=10_000)
    ok = P.uc.reg_read(mk.UC_M68K_REG_PC) == orig and P.uc.reg_read(A[7]) == sp and P.rd(sp, len(frame)) == frame \
        and all(P.uc.reg_read(k) == v for k, v in regs.items() if k not in (D[0], D[1], A[0], A[1]))
    for addr in (CUR_PROJ, PROJ_SEQ, SEL_TRACK):
        P.stub(addr, None)
    return ok and S.r32(ptr) == orig


# --------------------------------------------------------------------------------- 8. LFO 3/4 par pattern ------

KITS, KIT_SZ, CUR_KIT = 0x409c9c80, 7094, 0x40a78888
KIT_SAVE, KIT_LOAD, MEMCPY, NEW_PROJ, PROJECT = 0x4005b2ae, 0x4005d080, 0x4008f1f0, 0x40061738, 0x406fa024
KREC, KREC2, KSCR, KBUF = 0x92100000, 0x92110000, 0x92120000, 0x92130000
MAGIC = 0x4c463334


def kit(n):
    return KITS + n * KIT_SZ


def blk(syms, n):
    return G.SCR34 + 120 * n


def lfo_words(rnd):
    """5 mots d'un LFO que le format de pk5 garde exactement (SPD, DEP au multiple de 0x80)."""
    return [rnd.randrange(0x100) << 7, rnd.randrange(24) << 8, rnd.randrange(7) << 8, rnd.randrange(33) << 8,
            rnd.randrange(0x100) << 7]


def fill_blk(r, a, rnd):
    w = [x for _ in range(12) for x in lfo_words(rnd)]
    r.uc.mem_write(a, struct.pack(">60H", *w))
    return w


def blk_words(r, a):
    return list(struct.unpack(">60H", r.rd(a, 120)))


def kit_bytes(rnd):
    """Un kit plausible : nom, 6 niveaux, les 6 sons et 8 sons de la réserve (sound_bytes), bloc FX à zéro."""
    b = bytearray(KIT_SZ)
    b[0:16] = bytes(rnd.randrange(65, 91) for _ in range(16))
    for i in range(6):
        struct.pack_into(">H", b, 16 + 2 * i, rnd.randrange(0x7f01))
    for i in list(range(6)) + [6 + j for j in range(8)]:
        at = 28 + 100 * i if i < 6 else 694 + 100 * (i - 6)
        b[at:at + 100] = sound_bytes(rnd, lfo_words(rnd))
    return bytes(b)


def no_lfo2(b, rec):
    """Kit (rec = False) ou son enregistrement (rec = True) sans les octets de LFO 2 de ses 70 sons (mots k = 0 et
    28..32 du son, +88..+91 de son enregistrement), que le mod écrit déjà (§4)."""
    b = bytearray(b)
    for i in range(70):
        if rec:
            at = (32 + 100 * i if i < 6 else 712 + 100 * (i - 6)) + 88
            b[at:at + 4] = bytes(4)
        else:
            at = 28 + 100 * i if i < 6 else 694 + 100 * (i - 6)
            b[at + 20:at + 22] = bytes(2)                       # k 0 : WAVE de LFO 2
            b[at + 76:at + 86] = bytes(10)                      # k 28..32
    return bytes(b)


def per_kit(base_img, img, rt, syms):
    S, P = Rig(base_img, rt), Rig(img, rt)
    rnd = random.Random(12)
    D12 = DEFAULTS * 12
    # bloc d'un kit, premier usage
    P.w32(CUR_KIT, kit(9))
    a0 = P.uc
    P.call(syms["cur34"], check="cur34")
    check(P.uc.reg_read(A[0]) == syms["lfo34"] and P.r8(syms["kready"]) == 0,
          "kready = 0 : le kit joué lit le bloc de secours, rien n'est initialisé (le moteur et la page n'écrivent "
          "jamais T34)")
    P.uc.mem_write(G.SCR34, b"\xa5" * G.SCR34_SIZE)       # pas remise à zéro au démarrage
    good = True
    for n in (0, 1, 47, 95):
        d0 = s32(P.call(syms["blk34"], regs={D[0]: kit(n)}, check="blk34"))
        good &= d0 == n and P.uc.reg_read(A[0]) == blk(syms, n)
    for x in (0, kit(0) - 2, kit(3) + 28, kit(96), KSCR):
        d0 = s32(P.call(syms["blk34"], regs={D[0]: x}))
        good &= d0 == -1 and P.uc.reg_read(A[0]) == syms["lfo34"]
    t34 = P.rd(G.SCR34, G.SCR34_SIZE)
    good &= P.r8(syms["kready"]) == 1 and t34[:11520] == struct.pack(">5H", *DEFAULTS) * 1152 \
        and t34[11520:11540] == b"\xff" * 16 + bytes(4)
    P.call(syms["cur34"])
    good &= P.uc.reg_read(A[0]) == blk(syms, 9)
    check(good, "blk34 : chacun des 96 kits -> son bloc (rang 0..95), toute autre adresse -> bloc de secours ; premier "
                "usage : les 96 blocs aux défauts, aucun tampon retenu ; puis cur34 = bloc du kit joué (*0x40a78888)")

    # moteur et page sur le bloc du kit joué
    base = {k: 0x4000 for k in range(9, 23)}
    l1 = [lfo(spd=0x5800, mult=3 + t, wave=t % 6, dest=14, dep=0x6000) for t in range(6)]
    l3 = [lfo(spd=0x6400 - 0x300 * t, mult=5 + t, wave=(t + 1) % 6, dest=11, dep=0x7000) for t in range(6)]
    l4 = [lfo(spd=0x4c00 + 0x200 * t, mult=2 + t, wave=t % 6, dest=12, dep=0x2000) for t in range(6)]
    sched = masks_schedule(5, 150)
    tg = tracks(l1, None, base)
    outs = []
    for cur in (kit(9), kit(10)):
        P.reset_lfo(syms)                               # états à zéro (ready), T34 gardé
        P.w32(CUR_KIT, cur)
        P.uc.mem_write(blk(syms, 9), table34(l3, l4))
        P.uc.mem_write(blk(syms, 10), table34([lfo()] * 6, [lfo()] * 6))
        outs.append(run(P, tg, sched, [11, 12], 150))
    P.reset_lfo(syms)
    P.w32(CUR_KIT, 0)
    P.w8(syms["kready"], 0)
    ref = run(P, tg, sched, [11, 12], 150, syms, table34(l3, l4))
    P.w8(syms["kready"], 1)
    moved = len({tuple(map(tuple, o)) for o in outs[0]})
    check(outs[0] == ref and outs[1] != ref and moved > 50,
          f"moteur : LFO 3/4 tournent depuis le bloc du kit joué (kit 9 = la même sortie que la même table dans le bloc "
          f"de secours, {moved} sorties ; kit 10 aux défauts : rien)")
    sel = [4]
    for addr, fn in ((CUR_PROJ, lambda a: PROJ), (PROJ_SEQ, lambda a: SEQ), (SEL_TRACK, lambda a: sel[0])):
        P.stub(addr, fn)
    P.stub(NEEDS_REDRAW, lambda a: 0)
    P.w32(CUR_KIT, kit(9))
    good = True
    for pg in (2, 3):
        P.w8(syms["page"], pg)
        for i, pid in enumerate((0x1d, 0x1e, 0x21, 0x20, 0x24)):
            v = rnd.randrange(0x7f01)
            P.call(P.r32(P_SET), THIS, pid, v, 0, 0, check="set")
            good &= P.r16(blk(syms, 9) + 60 * (pg - 2) + 40 + 2 * i) == v
            good &= s32(P.call(P.r32(P_GET), THIS, pid)) == v
    check(good, "page : get/set des pages 3/4 lisent et écrivent le bloc du kit joué (piste sélectionnée)")

    # Clear LFO de l'OS (vtable [12] de l'accesseur, 0x4000a5c0 -> 0x4000b30e -> 0x4000b274 -> set) sur les pages 3/4
    setup_track(P)
    P.uc.mem_write(KBUF, struct.pack(">II", 0x401004c0, 0x401004dc))
    notify = P.r32(ACC_VT + 72)                          # 0x4000b942 : suite de 0x4000b274 vers le pattern (bouchon)
    P.stub(notify, lambda a: 0)
    good = True
    for pg in (2, 3):
        P.w8(syms["page"], pg)
        at = blk(syms, 9) + 60 * (pg - 2) + 40
        w = lfo_words(rnd)
        w = [w[0] or 0x80, w[1] | 0x100, w[2] | 0x100, w[3] | 0x100, w[4] or 0x80]
        P.uc.mem_write(at, struct.pack(">5H", *w))
        P.call(P.r32(ACC_VT + 12), THIS, KBUF, check="Clear LFO")
        got = list(struct.unpack(">5H", P.rd(at, 10)))
        good &= got == [w[0]] + DEFAULTS[1:]
    P.w8(syms["page"], 0)
    for addr in (CUR_PROJ, PROJ_SEQ, SEL_TRACK, NEEDS_REDRAW, notify):
        P.stub(addr, None)
    check(good, "Clear LFO de l'OS (identifiants 0x1e..0x24, 0x401004c0) sur les pages 3/4 : MULT, WAVE, DEST, DEP "
                "du LFO affiché aux défauts (SPD gardé, comme pour LFO 1)")

    # sauvegarde / chargement d'un kit
    kb = kit_bytes(rnd)
    for r in (S, P):
        r.uc.mem_write(kit(5), kb)
    vals = fill_blk(P, blk(syms, 5), rnd)
    recs = []
    for r in (S, P):
        r.uc.mem_write(KREC, b"\xa5" * 0x1e00)
        ok = r.call(KIT_SAVE, KREC, kit(5), 0, check="sauvegarde du kit") & 0xff
        recs.append((ok, r.rd(KREC, 0x1e00)))
    (oks, rs), (okp, rp) = recs
    gap = struct.pack(">I", MAGIC) + b"".join(struct.pack(">I", packed(vals[5 * i:5 * i + 5])) for i in range(12))
    ns, np_ = no_lfo2(rs, True), no_lfo2(rp, True)
    check(oks == okp == 1 and ns[:648] == np_[:648] and ns[700:] == np_[700:] and rs[646:700] == b"\xa5" * 54
          and rp[648:700] == gap,
          "vraie sauvegarde d'un kit (0x4005b2ae) : enregistrement = l'origine (hors LFO 2 de ses sons, §4), sauf "
          "+648..+699 = « LF34 » + les 12 LFO empaquetés (l'origine n'écrit rien en +646..+699)")
    loads = {}
    for name, r, rec in (("ss", S, rs), ("pp", P, rp), ("sp", S, rp), ("ps", P, rs)):
        r.uc.mem_write(KREC2, rec)
        r.uc.mem_write(kit(60), b"\x55" * KIT_SZ)
        if r is P:
            P.uc.mem_write(blk(syms, 60), b"\x33" * 120)
        ok = r.call(KIT_LOAD, kit(60), KREC2, check="chargement du kit") & 0xff
        loads[name] = (ok, no_lfo2(r.rd(kit(60), KIT_SZ), False), blk_words(P, blk(syms, 60)) if r is P else None)
    check(loads["ss"][0] == loads["pp"][0] == 1 and loads["ss"][1] == loads["pp"][1] and loads["pp"][2] == vals
          and blk_words(P, blk(syms, 5)) == vals,
          "vrai chargement (0x4005d080) de l'enregistrement du mod dans le kit 60 : kit = l'origine (hors LFO 2), bloc LFO 3/4 = "
          "celui du kit 5 (aller-retour exact)")
    check(loads["sp"][1] == loads["ss"][1],
          "l'OS d'origine relit un kit sauvé avec le mod comme le sien (+648..+699 ignorés)")
    check(loads["ps"][1] == loads["ss"][1] and loads["ps"][2] == D12,
          "enregistrement sauvé sans le mod (trou plein de 0xa5) : kit = l'origine, LFO 3/4 aux défauts")
    good = True
    for g in (bytes(52), b"\xff" * 52, bytes(range(52)), struct.pack(">I", MAGIC ^ 1) + gap[4:]):
        rec = bytearray(rp)
        rec[648:700] = g
        P.uc.mem_write(KREC2, bytes(rec))
        P.uc.mem_write(blk(syms, 60), b"\x33" * 120)
        P.call(KIT_LOAD, kit(60), KREC2)
        good &= blk_words(P, blk(syms, 60)) == D12
    check(good, "sans la marque « LF34 » (trou nul, plein, au hasard, marque voisine) : défauts")
    rec = bytearray(rp)
    rec[0] = 9                                            # version inconnue : chargement refusé
    P.uc.mem_write(KREC2, bytes(rec))
    P.uc.mem_write(blk(syms, 60), b"\x33" * 120)
    okp = P.call(KIT_LOAD, kit(60), KREC2) & 0xff
    S.uc.mem_write(KREC2, bytes(rec))
    oks = S.call(KIT_LOAD, kit(60), KREC2) & 0xff
    check(okp == oks == 0 and P.rd(blk(syms, 60), 120) == b"\x33" * 120,
          "chargement refusé par l'OS (version inconnue) : même résultat, bloc pas touché")
    P.uc.mem_write(KSCR, P.rd(kit(5), KIT_SZ))
    P.uc.mem_write(KREC, b"\xa5" * 0x1e00)
    P.call(KIT_SAVE, KREC, KSCR, 0)
    dgap = struct.pack(">I", MAGIC) + struct.pack(">I", packed(DEFAULTS)) * 12
    t34 = P.rd(G.SCR34, G.SCR34_SIZE)
    P.uc.mem_write(KREC2, rp)
    P.call(KIT_LOAD, KSCR, KREC2)
    check(P.rd(KREC + 648, 52) == dgap and P.rd(G.SCR34, G.SCR34_SIZE) == t34,
          "kit hors des 96 (tampon) : sauvé avec les défauts ; chargé : aucun bloc touché")

    # son remis aux défauts (0x40061866) sur le son d'une piste
    vals7 = fill_blk(P, blk(syms, 7), rnd)
    P.call(SND_INIT, kit(7) + 28 + 300, M32, 0, check="son aux défauts")
    exp = list(vals7)
    for lf in (0, 1):
        exp[30 * lf + 15:30 * lf + 20] = DEFAULTS
    good = blk_words(P, blk(syms, 7)) == exp
    for snd in (kit(7) + 28 + 600, kit(7) + 28 + 202, kit(7) + 10, SOUND2):
        P.call(SND_INIT, snd, M32, 0)
        good &= blk_words(P, blk(syms, 7)) == exp
    check(good, "vrai son aux défauts (0x40061866, effacement du son d'une piste) sur le son de la piste 3 du kit 7 : "
                "ses LFO 3 et 4 aux défauts, le reste du bloc gardé ; son de la réserve, adresse décalée, autre : rien")

    # memcpy
    good = True
    for n in (0, 1, 16, 100, 7093, 7095, 30710):
        src = bytes(rnd.getrandbits(8) for _ in range(n))
        res = []
        for r in (S, P):
            r.uc.mem_write(KBUF, src)
            r.uc.mem_write(KBUF + 0x8000, b"\x11" * (n + 8))
            d0 = r.call(MEMCPY, KBUF + 0x8000, KBUF, n, check="memcpy")
            res.append((d0, r.rd(KBUF + 0x8000, n + 8)))
        good &= res[0] == res[1]
    t34 = P.rd(G.SCR34, G.SCR34_SIZE)
    check(good and P.rd(G.SCR34, G.SCR34_SIZE) == t34, "vrai memcpy (0x4008f1f0), autres tailles que 7 094 : = "
                                                     "l'origine (résultat, octets), registres et pile rendus")
    v0 = fill_blk(P, blk(syms, 0), rnd)
    kb = kit_bytes(rnd)
    for r in (S, P):
        r.uc.mem_write(kit(0), kb)
        r.call(MEMCPY, kit(1), kit(0), KIT_SZ, check="memcpy d'un kit")
    good = S.rd(kit(1), KIT_SZ) == P.rd(kit(1), KIT_SZ) == kb and blk_words(P, blk(syms, 1)) == v0
    P.call(MEMCPY, KBUF, kit(1), KIT_SZ)                  # copie dans un tampon
    fill_blk(P, blk(syms, 1), rnd)                        # modifié entre-temps
    P.call(MEMCPY, kit(20), KBUF, KIT_SZ)                 # collage
    good &= blk_words(P, blk(syms, 20)) == v0
    v21 = fill_blk(P, blk(syms, 21), rnd)
    P.call(MEMCPY, kit(21), KBUF + 0x9000, KIT_SZ)        # source inconnue
    good &= blk_words(P, blk(syms, 21)) == v21
    for i in range(6):
        P.call(MEMCPY, KBUF + 0x10000 + 0x2000 * i, kit(i), KIT_SZ)
    P.call(MEMCPY, kit(30), KBUF, KIT_SZ)                 # tampon oublié (plus de 4 depuis)
    good &= blk_words(P, blk(syms, 30)) != v0
    P.call(MEMCPY, kit(31), KBUF + 0x10000 + 0x2000 * 5, KIT_SZ)
    good &= blk_words(P, blk(syms, 31)) == blk_words(P, blk(syms, 5))
    check(good, "memcpy d'un kit entier : octets = l'origine ; bloc kit -> kit, kit -> tampon -> kit (collage), source "
                "inconnue : gardé ; les 4 derniers tampons retenus")

    # nouveau projet
    for r in (S, P):
        r.uc.mem_write(kit(0), kb)
    for n in (0, 3, 50, 95):
        fill_blk(P, blk(syms, n), rnd)
    try:
        S.call(NEW_PROJ, PROJECT)
    except Exception as e:                                # noqa: BLE001
        print(f"  --    nouveau projet (0x40061738) non émulé avec cette combinaison : l'origine elle-même s'arrête "
              f"sous ce banc ({e}) ; vérifié seul et avec Model-TG")
    else:
        P.call(NEW_PROJ, PROJECT, check="nouveau projet")
        same = all(no_lfo2(S.rd(kit(n), KIT_SZ), False) == no_lfo2(P.rd(kit(n), KIT_SZ), False)
                   for n in (0, 1, 50, 95))
        check(same and all(blk_words(P, blk(syms, n)) == D12 for n in range(96)),
              "vrai nouveau projet (0x40061738) : kits = l'origine (hors LFO 2) ; les 96 blocs LFO 3/4 aux défauts "
              "(kit 0 par ses sons remis aux défauts, kits 1..95 par la copie du kit 0)")
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


# ----------------------------------------------------------------------- 9. [LFO] + potard, diode DEST ------

LEARN, LED_PAINT = 0x4001eaa2, 0x400261aa                     # affectation par potard ; diode de la page LFO
KIT_OF, TRACK_OF, MACHINE_OF, REC_OF = 0x4000eb9c, 0x40009c1a, 0x40014042, 0x4004df76
ACC_OF, KEYS_HELD, SEQ_STATE, TRIG_HELD, TRIG_HELD2 = 0x400097f0, 0x4007faf4, 0x400cf9a8, 0x4006b978, 0x4006b736
LED_CTL, LED_SET, TRIG_SCAN, FN_DTOR = 0x400cfaf4, 0x40005f86, 0x4006be48, 0x400cf044
UI_INIT, KEY_BITS = 0x400de244, 0x40f95744                    # objets d'interface et enregistrements ; MACHINES = bit 0
KIT_OBJ, TRACK_OBJ2, LEDS, FCODE2 = FAKE + 0x20000, FAKE + 0x21000, FAKE + 0x22000, FAKE + 0x23000
ATK, FLT, RES, PITCH, FTUN = 0x0d, 0x0c, 0x0b, 42, 43
# Model-TG : loop_mode, descr_done, sampler_descr, sampler_descr_atk (tools/sampler_mode_filter.py, qui les vérifie,
# et tools/emu/test_sampler_mode_filter.py)
SMF_LOOP_MODE, SMF_DESCR_DONE, SMF_DESCR, SMF_DESCR_ATK = 0x401b2408, 0x401abe98, 0x401abe9a, 0x401abee6


def learn_rig(img, rt, sel, machine, held):
    """Rig dont l'interface tourne : enregistrements et objets d'interface construits (0x400de244), piste sel[0] dans
    le kit 9 (son = kit(9) + 28 + 100 t), machine machine[0] ; held : touches tenues (0x4007faf4)."""
    r = Rig(img, rt)
    for a, ret in ((FN_DTOR, 0), (0x400c9afc, 0), (0x400f4dc6, 1), (0x400f4e22, 0)):
        r.stub(a, lambda x, ret=ret: ret)
    r.call(UI_INIT)
    r.stub(0x400f4dc6, None)
    r.stub(0x400f4e22, None)
    setup_track(r)
    r.w32(CUR_KIT, kit(9))
    r.stub(FCODE, lambda a: kit(9) + 28 + 100 * sel[0])
    r.stub(CUR_PROJ, lambda a: PROJ)
    r.stub(PROJ_SEQ, lambda a: SEQ)
    r.stub(SEL_TRACK, lambda a: sel[0])
    r.stub(KIT_OF, lambda a: KIT_OBJ)
    r.stub(ACC_OF, lambda a: THIS)
    r.stub(TRACK_OF, lambda a: TRACK_OBJ2)
    r.stub(MACHINE_OF, lambda a: machine[0])
    r.stub(KEYS_HELD, lambda a: 1 if a[0] in held else 0)
    r.stub(SEQ_STATE, lambda a: SEQ)
    r.stub(TRIG_HELD, lambda a: 0)
    r.stub(TRIG_HELD2, lambda a: 0)
    r.stub(TRIG_SCAN, lambda a: 0)
    r.stub(NEEDS_REDRAW, lambda a: 0)
    r.stub(LED_CTL, lambda a: LEDS)
    r.stub(LED_SET, lambda a: r.log.append(("led", a[1], a[2])) or 0)
    r.stub(r.r32(ACC_VT + 72), lambda a: 0)            # 0x4000b942 : suite de 0x4000b274 vers le pattern (bouchon)
    r.w32(VIEWOBJ + 56, FAKEVT)
    r.w32(FAKEVT + 128, FCODE2)
    r.stub(FCODE2, lambda a: THIS)
    return r


def learn_led(base_img, img, rt, syms, tg):
    """[LFO] tenue + un potard (0x4001eaa2, le vrai code) et la diode de la destination (0x400261aa, le vrai code), sur
    la machine montée : Attack, Filtre, Résonance sous MACHINES (Model-TG), le lo-fi de MACRO, destinations prises."""
    sel, machine, held = [3], [0], set()
    S, P = learn_rig(base_img, rt, sel, machine, held), learn_rig(img, rt, sel, machine, held)
    P.call(syms["blk34"], regs={D[0]: kit(9)})
    page = syms["page"]
    snd = lambda: kit(9) + 28 + 100 * sel[0]          # noqa: E731
    macro = [m for m in range(6, 16) if P.r32(P.call(REC_OF, m) + 72) == FTUN]
    if macro:
        check(len(macro) == 1 and S.r32(S.call(REC_OF, macro[0]) + 72) == FTUN,
              f"MACRO = machine {macro} : son enregistrement (0x4004df76) porte FINE (43) en entrée 16, la seule")
    macro = macro[0] if macro else None

    def mod(on):
        for r in (S, P):
            r.w8(KEY_BITS, 1 if on else 0)
            if tg:
                r.w32(tg["mod_held"], 1 if on else 0)

    def dest(r, pg):
        r.w8(page, pg) if r is P else None
        return s32(r.call(syms["lfo_get"] if r is P else ORIG_GET, THIS, 0x20)) >> 8

    def set_dest(r, pg, k):
        if pg == 0:
            r.w8(snd() + 28, k)
        elif pg == 1:
            r.w8(snd() + 82, k)
        else:
            r.w8(page, pg)
            r.call(syms["lfo_set"], THIS, 0x20, k << 8)

    def learn(r, pg, knob):
        if r is P:
            r.w8(page, pg)
        r.call(LEARN, VIEWOBJ + 56, knob, 1, check="affectation par potard")
        return dest(r, pg)

    def clear(r):
        r.uc.mem_write(snd(), sound_bytes(random.Random(1), DEFAULTS))
        r.w8(snd() + 38, machine[0])
        r.w8(snd() + 28, 0)
        r.w8(snd() + 82, 0)
        if r is P:
            for pg in (2, 3):
                set_dest(r, pg, 0)

    P.w8(page, 0)
    k_of = {i: s32(P.call(ID2K, i)) for i in (ATK, FLT, RES, PITCH, FTUN)}
    expect_k = {PITCH: 10, FTUN: 17}
    if tg:
        expect_k.update({ATK: 23, FLT: 24, RES: 25})
    check(all(k_of[i] == expect_k[i] for i in expect_k) and all(s32(S.call(ID2K, i)) == expect_k[i] for i in expect_k),
          f"id -> k : {expect_k} ({k_of})")
    # 1. affectation : la destination du LFO affiché
    good, n = True, 0
    for m in list(range(6)) + ([macro] if macro is not None else []):
        machine[0] = m
        for on in (False, True):
            mod(on)
            for knob in range(12):
                ref = None
                for pg in range(4):
                    for r in (S, P):
                        clear(r)
                    got = learn(P, pg, knob)
                    if pg == 0:
                        ref = learn(S, 0, knob)
                        good &= got == ref or (on and knob == 0)
                    others = [dest(P, x) for x in range(4) if x != pg]
                    good &= others == [0, 0, 0] and (got == ref or (on and knob == 0))
                    if on and tg and knob in (1, 4, 5):
                        good &= got == {1: 23, 4: 24, 5: 25}[knob]
                    if on and knob == 0:
                        good &= got == 17          # FINE : le lo-fi de MACRO, l'accord fin ailleurs (id 43 partout)
                    if not on and knob == 0:
                        good &= got == 10
                    n += 1
    P.w8(page, 0)
    mod(False)
    # FUNC + PITCH : reste stock (PITCH, k = 10) même sur MACRO et sous MACHINES
    good_func = True
    for m in list(range(6)) + ([macro] if macro is not None else []):
        machine[0] = m
        for on in (False, True):
            mod(on)
            held.add(2)
            clear(P)
            got = learn(P, 0, 0)
            good_func &= got == 10
            held.discard(2)
    mod(False)
    machine[0] = 0
    check(good and good_func and n > 300, f"[LFO] + potard, machines 0..5 et MACRO, 12 potards, LFO 1..4, MACHINES tenue ou non ({n} cas) : "
                                          "la destination du LFO affiché, celle de l'OS d'origine sur LFO 1, les autres LFO pas "
                                          "touchés ; MACHINES + DECAY / SWEEP / CONTOUR -> Attack / Filtre / Résonance (k 23, 24, 25)"
                                          + ("" if tg else " [sans Model-TG : pas vérifié]")
                                          + " ; MACHINES + PITCH -> FINE (k 17, le lo-fi de MACRO et l'accord fin ailleurs) "
                                          "sur toutes les machines, PITCH (k 10) sans MACHINES ; FUNC + PITCH -> PITCH (k 10)")
    # 2. destination déjà prise par un autre LFO de la piste : admise (cumul de plusieurs LFO)
    machine[0] = 0
    mod(bool(tg))
    good, n = True, 0
    for pg in range(4):
        for other in range(4):
            if other == pg:
                continue
            for knob, k in (((1, 23), (4, 24), (5, 25)) if tg else ((2, 11), (3, 12), (4, 13))):
                clear(P)
                set_dest(P, other, k)
                set_dest(P, pg, 14 if k != 14 else 15)
                got = learn(P, pg, knob)
                good &= got == k and dest(P, other) == k
                n += 1
    clear(S)
    S.w8(snd() + 82, 23 if tg else 11)
    s_dup = learn(S, 0, 1 if tg else 2)
    mod(False)
    check(good and s_dup == (23 if tg else 11),
          f"destination déjà prise par un autre des 4 LFO ({n} cas) : admise (le cumul s'additionne, comme l'OS d'origine)")
    # 3. diode de la page LFO
    good, rows = True, []
    for m in list(range(6)) + ([macro] if macro is not None else []):
        machine[0] = m
        for k in [0] + list(range(9, 26)):
            lit = []
            for pg in range(4):
                for r in (S, P):
                    clear(r)
                set_dest(P, pg, k)
                P.log.clear()
                P.w8(page, pg)
                P.call(LED_PAINT, VIEWOBJ, check="diode de la page LFO")
                lit.append([a for t, a, _ in P.log if t == "led"])
            set_dest(S, 0, k)
            S.log.clear()
            S.call(LED_PAINT, VIEWOBJ)
            ls = [a for t, a, _ in S.log if t == "led"]
            want = ({23: [37], 24: [40], 25: [41]}.get(k) if tg else None) or ([36] if k == 17 and m == macro else ls)
            good &= all(x == want for x in lit)
            if want != ls:
                rows.append((m, k, ls, lit[0]))
    machine[0] = 0
    P.w8(page, 0)
    desc = "; ".join(f"m{m} k{k} : {ls} -> {lp}" for m, k, ls, lp in rows[:3] + [x for x in rows if x[0] == macro])
    nm = 6 + (macro is not None)
    check(good and len(rows) == (3 * nm if tg else 0) + (macro is not None),
          "diode de la destination (0x400261aa), machines 0..5 et MACRO, k = 0, 9..25, LFO 1..4 : Attack -> DECAY (37), "
          "Filtre -> SWEEP (40), Résonance -> CONTOUR (41), lo-fi de MACRO -> PITCH (36) ; tout le reste = l'OS "
          f"d'origine, sur les 4 pages ({len(rows)} différences, avant -> après : {desc})")
    # 3b. le Sampler (machine 6) : SWEEP / CONTOUR sous MACHINES règlent son filtre (k 13/14) en modes 0..2, celui de
    # la piste (k 24/25) en modes 3..6 (sampler_mode_filter, notes/83 §3) ; [LFO] + le même potard doit donner le même
    # k, que la page LFO nomme (paramIdFor, 0x4005a692) et dont elle allume la diode
    if tg:
        lm = SMF_LOOP_MODE + 4 * sel[0]
        machine[0] = 6
        # Les deux descripteurs du Sampler, que sampler_pre construit sur le fil audio (puis descr_done = 1) : ici
        # l'enregistrement que rend l'OS avant cela, avec Attack (0x0d) en position 1 pour la variante MACHINES et
        # Filtre / Résonance du Sampler (0x49 / 0x4a) en positions 4 et 5, comme dans test_sampler_mode_filter.py
        mod(False)
        for r in (S, P):
            rec = r.rd(r.call(0x4004df5c, 7), 76)
            for a, atk in ((SMF_DESCR, False), (SMF_DESCR_ATK, True)):
                r.uc.mem_write(a, rec)
                r.uc.mem_write(a + 24, struct.pack(">II", 0x49, 0x4a))
                if atk:
                    r.w32(a + 12, ATK)
            r.w8(SMF_DESCR_DONE, 1)
        good, bad = True, []
        for mode in range(7):
            for r in (S, P):
                r.w32(lm, mode)
            want = (24, 25) if mode >= 3 else (13, 14)
            for on in (True, False):
                mod(on)
                for pg in range(4):
                    for knob, k in zip((4, 5), want if on else (13, 14)):
                        clear(P)
                        got = learn(P, pg, knob)
                        if got != k:
                            bad.append((mode, on, pg, knob, got))
            mod(False)
            ids = [s32(P.call(K2ID, k, 6)) for k in (24, 25, 13, 14)]
            good &= ids == ([FLT, RES] if mode >= 3 else [0, 0]) + [0x49, 0x4a]
            for k, led in ((24, 40), (25, 41), (13, 40), (14, 41)):
                if k >= 24 and mode < 3:
                    continue
                for pg in range(4):
                    clear(P)
                    set_dest(P, pg, k)
                    P.log.clear()
                    P.w8(page, pg)
                    P.call(LED_PAINT, VIEWOBJ, check="diode de la page LFO")
                    lit = [a for t, a, _ in P.log if t == "led"]
                    if lit != [led]:
                        bad.append(("led", mode, k, pg, lit))
        for r in (S, P):
            r.w32(lm, 0)
            r.w8(SMF_DESCR_DONE, 0)
        machine[0] = 0
        P.w8(page, 0)
        check(good and not bad,
              "Sampler, modes 0..6, LFO 1..4 : [LFO] + MACHINES + SWEEP / CONTOUR -> k 13/14 (son filtre) en modes 0..2, "
              "k 24/25 (filtre de piste) en modes 3..6, k 13/14 sans MACHINES ; DST nomme 24/25 Filtre / Résonance (0x0c / "
              f"0x0b) en modes 3..6 seulement ; diode SWEEP (40) / CONTOUR (41) {bad[:3]}")
    # 4. sauvegarde et rechargement : LFO 1 -> Attack, LFO 2 -> Filtre, LFO 3 -> Résonance
    if tg:
        mod(True)
        clear(P)
        got = [learn(P, 0, 1), learn(P, 1, 4), learn(P, 2, 5)]
        mod(False)
        P.uc.mem_write(KREC, b"\xa5" * 0x1e00)
        ok = P.call(KIT_SAVE, KREC, kit(9), 0, check="sauvegarde du kit") & 0xff
        rec = P.rd(KREC, 0x1e00)
        P.uc.mem_write(kit(9), b"\x55" * KIT_SZ)
        P.uc.mem_write(blk(syms, 9), b"\x33" * 120)
        P.uc.mem_write(KREC2, rec)
        ok2 = P.call(KIT_LOAD, kit(9), KREC2, check="chargement du kit") & 0xff
        back = [dest(P, pg) for pg in range(4)]
        P.w8(page, 0)
        check(ok == ok2 == 1 and got == [23, 24, 25] and back == [23, 24, 25, 0],
              f"par potard sous MACHINES : LFO 1 -> Attack, LFO 2 -> Filtre, LFO 3 -> Résonance (k {got}) ; kit sauvé "
              f"(0x4005b2ae) puis rechargé (0x4005d080) : {back[:3]}, LFO 4 None")
    check(not (S.bad or P.bad or S.asserts or P.asserts), "aucun accès hors mémoire, aucune assertion de l'OS")


# ------------------------------------------------------------------------------------------------ main -----------

def payload_runtimes(tweaks, stock, syntakt_path):
    st_img, out = None, []
    for t in sorted((t for t in tweaks if t.get("append")), key=lambda t: t["order"]):
        if "syntakt" in t["append"] and st_img is None:
            import syntakt                                     # noqa: E402  (tools/emu/syntakt.py)
            st_img = syntakt.dsp_image(syntakt_path)
        out.append((int(t["append"]["dest"], 16), build.payload_runtime(t, stock, st_img)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="autres tweaks appliqués avec (ex. model-tg,arp)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), pour les moteurs du Syntakt")
    ap.add_argument("--david", help="le .syx Model-TG-VA-DR-v1 de DavidCaruso : relire ses sons (facultatif)")
    ap.add_argument("--only", default="", help="sections à passer (ex. 0,2,4)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    files = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in TWEAKS.glob("[0-9]*.json")}
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    every = [json.loads(f.read_text(encoding="utf-8")) for i, f in files.items() if i != tweak["id"]]
    others = [json.loads(files[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    build.check_conflicts(others + [tweak])
    pl, _ = build.build_payload(others, stock, args.syntakt)
    base = build.apply_writes(stock, sorted(others, key=lambda t: t["order"]))[0] + pl
    img = build.apply_writes(stock, sorted(others + [tweak], key=lambda t: t["order"]))[0] + pl
    rt = payload_runtimes(others, stock, args.syntakt)
    syms = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    david = T.main_os_from_syx(args.david) if args.david else None
    only = {int(x) for x in args.only.split(",") if x} or set(range(10))
    tg = next((t["symbols"] for t in others if "mod_held" in t.get("symbols", {})), None)
    tg = {k: int(v, 16) for k, v in tg.items()} if tg else None
    print(f"firmware : {', '.join(t['id'] for t in sorted(others + [tweak], key=lambda t: t['order']))}")
    steps = ((0, "écritures", lambda: writes_ok(stock, img, tweak, every, rt)),
             (1, "bloc audio sans LFO de plus = l'origine", lambda: audio_identity(base, img, rt, syms)),
             (2, "LFO 2, 3, 4", lambda: audio_extra(base, img, rt, syms)),
             (3, "interface", lambda: ui(base, img, rt, syms)),
             (4, "LFO 2 dans le son", lambda: sound(base, img, rt, syms, david)),
             (5, "p-locks dans le pattern", lambda: plocks(base, img, rt)),
             (6, "coût", lambda: cost(base, img, rt, syms)),
             (7, "accroches au milieu des fonctions", lambda: sites(base, img, rt, syms)),
             (8, "LFO 3/4 par pattern", lambda: per_kit(base, img, rt, syms)),
             (9, "[LFO] + potard, diode DEST", lambda: learn_led(base, img, rt, syms, tg)))
    for n, name, fn in steps:
        if n in only:
            print(f"{n}. {name}")
            fn()
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
