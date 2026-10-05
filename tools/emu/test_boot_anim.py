#!/usr/bin/env python3
"""Preuve de l'animation de démarrage « modded-cycles » (notes/39, tweaks/model-cycles_OS1.13/43-boot-anim.json).

On exécute la tâche d'animation (0x40053a6c) de l'OS d'origine et de l'OS modifié avec le vrai code de l'écran :
0x4008e728 (tampon de dessin), 0x4008e622 (envoi des blocs changés, échange des tampons), 0x4008e6ba (effacement),
0x4008e580 / 0x40053f64 / 0x40053fb0 / 0x40053e74 (position, données, registres du DSPI1). Chaque mot écrit dans
le registre d'envoi du DSPI1 (0xfc03c034, bit 8 = donnée / commande) est rejoué sur un modèle de l'écran
(commandes de page 0xb0..0xb7 et de colonne 0x0X / 0x1X, page de l'OS = 7 - page de l'écran, bit 7 = ligne du haut,
comme Bitmap::setPixel 0x400701b8) ; sa mémoire part de valeurs quelconques.
Interceptés : le minuteur (0x40002144, 0x40002200), les sémaphores (0x40001aca : une image ; 0x40001c80 ; 0x40001b3e :
fin de la tâche), et pour l'animation d'origine, l'allocation (0x400802e0, 0x400802e6, 0x400802ec), le verrou des LED
(0x40001cc4, 0x40001df6) et ses carreaux (descripteurs chargés au démarrage, *0x40fe3840 : de faux carreaux pleins).

  1. Écriture : octets d'origine, dans le corps de la tâche seulement, aucun autre tweak n'y écrit, la création de la
     tâche pointe toujours dessus.
  2. Repère de l'écran : un pixel posé par le vrai Bitmap::setPixel arrive au bon endroit après le vrai envoi.
  3. Même contrat que l'original : minuteur (0x400539b8, 2 ticks) posé au début et retiré à la fin, 10 ticks d'attente
     après la dernière image, signal 0x40a78620 (attendu par la tâche principale), puis attente sans fin.
  4. Chaque image envoyée à l'écran est celle du modèle (tools/gen_boot_anim.py, frames()), pixel pour pixel.
  5. Aucune écriture hors des deux tampons de l'écran, des pointeurs qui les échangent, de la pile et du DSPI1.

  6. Avec les autres mods (--with) : mêmes images.

    python3 tools/emu/test_boot_anim.py --cycles model-cycles_OS1.13.syx [--gif anim.gif] [--png fin.png] \
        [--with 6ch-usbup,model-tg-st,syntakt-tg-sd-cp-toy-bits-swarm,arp,trig-hold,tempo-max]
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_boot_anim as G           # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAKS = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = build.BASE
FAIL = []

TASK = 0x40053a6c
TIMER_ADD, TIMER_DEL = 0x40002144, 0x40002200
SEM_WAIT, SEM_POST1, SEM_TAKE = 0x40001aca, 0x40001c80, 0x40001b3e
TICK_CB, SEM_TICK, SEM_DONE = 0x400539b8, 0x40a78618, 0x40a78620
BUF_PTRS = 0x401492f0                # tampon de dessin, tampon affiché
SET_PIXEL, FLUSH = 0x400701b8, 0x4008e622
PUSHR = 0xfc03c034
TILES = 0x40fe3840                   # *TILES : 10 descripteurs Bitmap de 28 o (animation d'origine)
MALLOC = (0x400802e0, 0x400802e6)
FREE = 0x400802ec
LED_LOCK = (0x40001cc4, 0x40001df6)

STOP = 0x9f000000
STACK = 0x9e000000
HEAP, FAKE = 0x93000000, 0x92000000


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Panel:
    """L'écran : 8 pages de 128 octets, adressées par les commandes reçues sur le DSPI1."""

    def __init__(self):
        self.ram = [[0xa5 ^ (p * 37 + c) & 0xff for c in range(128)] for p in range(8)]
        self.page = self.col = 0

    def push(self, v):
        b = v & 0xff
        if v & 0x100:                                   # donnée
            if self.col < 128:
                self.ram[self.page][self.col] = b
            self.col += 1
        elif b & 0xf0 == 0xb0:
            self.page = b & 0x0f
        elif b & 0xf0 == 0x00:
            self.col = self.col & 0xf0 | b
        elif b & 0xf0 == 0x10:
            self.col = self.col & 0x0f | (b & 0x0f) << 4

    def image(self):
        """Lignes de pixels, dans le repère de l'OS (page de l'OS = 7 - page de l'écran, bit 7 en haut)."""
        img = [[0] * G.W for _ in range(G.H)]
        for pp in range(8):
            for x in range(128):
                b = self.ram[pp][x]
                for k in range(8):
                    img[(7 - pp) * 8 + k][x] = b >> (7 - k) & 1
        return img


class Rig:
    def __init__(self, img, stock_tiles=False):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        uc.mem_map(0x40000000, 0x02400000)              # image + BSS
        uc.mem_write(BASE, img)
        uc.mem_map(0x90000000, 0x10000000)              # pile, tas, faux carreaux
        uc.mem_map(0xfc000000, 0x00100000)              # registres (DSPI1)
        uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.bad, self.calls, self.frames, self.writes = [], [], [], set()
        self.panel = Panel()
        self.heap = HEAP
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: self.bad.append(addr) or False)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._write)
        stubs = {
            TIMER_ADD: lambda a: self._log("minuteur+", a[0], a[1]),
            TIMER_DEL: lambda a: self._log("minuteur-", a[0]),
            SEM_WAIT: self._wait,
            SEM_POST1: lambda a: self._log("signal", a[0]),
            SEM_TAKE: self._take,
            FREE: lambda a: 0,
        }
        for m in MALLOC:
            stubs[m] = self._malloc
        for m in LED_LOCK:
            stubs[m] = lambda a: 0
        for addr, fn in stubs.items():
            uc.hook_add(UC_HOOK_CODE, self._stub(fn), begin=addr, end=addr)
        if stock_tiles:                                 # carreaux de 16 x 16 pleins, masque opaque
            pix, mask = FAKE + 0x1000, FAKE + 0x2000
            uc.mem_write(pix, b"\xff\xff\x00\x00" * 16)
            uc.mem_write(mask, b"\xff\xff\x00\x00" * 16)
            for n in range(10):
                uc.mem_write(FAKE + 28 * n, struct.pack(">IiiiIIB3x", 0x401117c8, 16, 16, 1, pix, mask, 0))
            self.w32(TILES, FAKE)

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def _stub(self, fn):
        def hook(uc, addr, size, ud):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">4I", uc.mem_read(sp + 4, 16))
            r = fn(args)
            if r is None:
                return
            uc.reg_write(mk.UC_M68K_REG_D0, r & 0xffffffff)
            uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        return hook

    def _log(self, *what):
        self.calls.append(what)
        return 0

    def _malloc(self, a):
        p = self.heap
        self.heap += (a[0] + 15) & ~15
        return p

    def _wait(self, a):
        self.calls.append(("attente", a[0]))
        if a[0] == SEM_TICK:
            self.frames.append(self.panel.image())       # ce qui est à l'écran à ce tick
        return 0

    def _take(self, a):
        self.calls.append(("fin", a[0]))
        self.uc.emu_stop()
        return None

    def _write(self, uc, access, addr, size, value, ud):
        if addr == PUSHR:
            self.panel.push(value)
        self.writes.add(addr & ~3)

    def run(self, entry, count=60_000_000):
        sp = STACK - 0x100
        self.uc.mem_write(sp, struct.pack(">I", STOP))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(entry, STOP, count=count)

    def call(self, fn, *args):
        sp = STACK - 0x100
        self.uc.mem_write(sp, struct.pack(">I" + "I" * len(args), STOP, *[x & 0xffffffff for x in args]))
        self.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        self.uc.emu_start(fn, STOP, count=2_000_000)
        return self.uc.reg_read(mk.UC_M68K_REG_D0)


def contract(calls):
    """Les appels au système, les attentes de tick regroupées : [(quoi, arg, …, nombre)]."""
    out = []
    for c in calls:
        if out and c == out[-1][0]:
            out[-1] = (c, out[-1][1] + 1)
        else:
            out.append((c, 1))
    return out


def show(img):
    return "\n".join("".join("#" if v else "." for v in row) for row in img)


def save(frames, gif, png):
    from PIL import Image
    on, off, scale = (0x1f, 0x24, 0x57), (0xb2, 0xb6, 0xe2), 4      # couleurs de l'écran sur le site (site.css)

    def pic(img):
        im = Image.new("RGB", (G.W, G.H), off)
        im.putdata([on if v else off for row in img for v in row])
        return im.resize((G.W * scale, G.H * scale), Image.NEAREST)
    if gif:
        pics = [pic(f) for f in frames]
        pics[0].save(gif, save_all=True, append_images=pics[1:], duration=[20] * (len(pics) - 1) + [1500], loop=0)
        print(f"  écrit : {gif}")
    if png:
        pic(frames[-1]).save(png)
        print(f"  écrit : {png}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--gif", help="écrit l'animation reçue par l'écran (GIF, x4)")
    ap.add_argument("--png", help="écrit sa dernière image (PNG, x4)")
    ap.add_argument("--with", dest="others", default="", help="ids de tweaks appliqués avec (écritures seulement)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads((TWEAKS / "43-boot-anim.json").read_text(encoding="utf-8"))
    patched, _ = build.apply_writes(stock, [tw])
    patched = bytes(patched)

    print("1. écriture")
    (w,) = tw["writes"]
    lo, n = BASE + w["off"], len(bytes.fromhex(w["new"]))
    check(stock[w["off"]:w["off"] + n].hex() == w["old"], "octets d'origine")
    check(lo == G.BODY and lo + n <= G.BODY_END, f"dans le corps de la tâche : {lo:#x}..{lo + n:#x} (fin {G.BODY_END:#x})")
    others = []
    for f in sorted(TWEAKS.glob("*.json")):
        if f.name in ("device.json", "43-boot-anim.json"):
            continue
        for ow in json.loads(f.read_text(encoding="utf-8")).get("writes", []):
            a = BASE + ow["off"]
            if a < G.BODY_END and a + len(bytes.fromhex(ow["new"])) > G.BODY:
                others.append(f.name)
    check(not others, f"aucun autre tweak n'écrit dans 0x{G.BODY:x}..0x{G.BODY_END:x} {others or ''}")
    va, old = G.TASK_PEA
    check(patched[va - BASE:va - BASE + 4].hex() == old, "la création de la tâche (0x40053a2e) pointe toujours dessus")

    print("2. repère de l'écran (vrai Bitmap::setPixel, vrai envoi)")
    r = Rig(patched)
    bmp = 0x91000000
    draw = r.r32(BUF_PTRS)
    r.uc.mem_write(bmp, struct.pack(">IiiiIIB3x", 0x401117c8, 128, 64, 2, draw, 0, 0))
    pts = ((3, 10), (127, 0), (64, 63), (0, 33))
    for x, y in pts:
        r.call(SET_PIXEL, bmp, x, y, 1)
    r.call(FLUSH)
    img = r.panel.image()
    check(all(img[y][x] for x, y in pts), f"pixels {pts} à leur place")
    check(sum(map(sum, img)) > len(pts), "(les autres blocs gardent la mémoire quelconque de l'écran)")

    print("3. même contrat que l'original")
    rs = Rig(stock, stock_tiles=True)
    rs.run(TASK)
    rp = Rig(patched)
    rp.run(TASK)
    cs, cp = contract(rs.calls), contract(rp.calls)
    print(f"        origine : {cs}")
    print(f"        modifié : {cp}")
    shape = lambda c: [(k[0], *k[1:]) if k[0] != "attente" else ("attente",) for k, _ in c]
    check(shape(cs) == shape(cp), "mêmes appels, dans le même ordre")
    check(cs[0][0] == ("minuteur+", TICK_CB, 2) and cp[0][0] == ("minuteur+", TICK_CB, 2),
          "minuteur 0x400539b8 toutes les 2 ticks de 10 ms (20 ms par image)")
    check(cs[1] == (("attente", SEM_TICK), 80 + 10), "origine : 80 images (carreaux allumés ou éteints) + 10 ticks")
    check(cp[1] == cs[1], f"modifié : {G.NF} images + 10 ticks, même durée ({(G.NF + 10) * 20} ms)")
    check(cp[2:] == [(("signal", SEM_DONE), 1), (("minuteur-", TICK_CB), 1), (("fin", SEM_TICK), 1)],
          "puis signal 0x40a78620, retrait du minuteur, attente sans fin")
    check(not rs.bad and not rp.bad, f"aucun accès hors mémoire {[hex(a) for a in (rs.bad + rp.bad)[:4]]}")

    print("4. images envoyées à l'écran")
    sent = rp.frames[1:G.NF + 1]                        # à l'attente k+1, l'écran montre l'image k
    want = G.frames()
    bad = [k for k in range(G.NF) if sent[k] != want[k]]
    check(len(sent) == G.NF and not bad, f"{G.NF} images identiques au modèle, pixel pour pixel"
          + (f" ; différentes : {bad[:8]}" if bad else ""))
    check(all(f == want[-1] for f in rp.frames[G.NF + 1:]), "la dernière reste affichée pendant les 10 ticks")
    check(rp.frames[0] == [[0] * G.W for _ in range(G.H)], "l'écran est entièrement effacé avant la 1re image")
    lit = sum(map(sum, want[-1]))
    check(lit > 1000, f"dernière image : logo et texte ({lit} pixels allumés)")
    if bad:
        print(show(sent[bad[0]]))
        print()
        print(show(want[bad[0]]))

    print("5. écritures")
    bufs = {r.r32(BUF_PTRS), r.r32(BUF_PTRS + 4)}
    ok_ranges = [(b, b + 1024) for b in bufs] + [(BUF_PTRS, BUF_PTRS + 8), (0xfc03c000, 0xfc03c040),
                                                    (STACK - 0x10000, STACK)]
    stray = sorted(a for a in rp.writes if not any(lo <= a < hi for lo, hi in ok_ranges))
    check(not stray, f"seulement les tampons de l'écran, leurs pointeurs, la pile, le DSPI1 "
          f"{[hex(a) for a in stray[:6]] if stray else ''}")

    if args.others:
        print("6. avec " + args.others)
        byid = {json.loads(f.read_text(encoding="utf-8"))["id"]: json.loads(f.read_text(encoding="utf-8"))
                for f in TWEAKS.glob("*.json") if f.name != "device.json"}
        combo, _ = build.apply_writes(stock, [byid[i] for i in args.others.split(",")] + [tw])
        rc = Rig(bytes(combo))
        rc.run(TASK)
        check(contract(rc.calls) == cp, "mêmes appels")
        check(rc.frames == rp.frames and not rc.bad, "mêmes images, aucun accès hors mémoire")

    save(rp.frames[1:G.NF + 1], args.gif, args.png)
    print("RÉSULTAT :", "ÉCHEC " + str(len(FAIL)) if FAIL else "tout est ok")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
