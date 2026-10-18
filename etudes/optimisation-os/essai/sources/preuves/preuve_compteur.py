#!/usr/bin/env python3
"""Compteur de charge des fichiers d'essai (src/compteur.S) : preuve en émulation sur les images livrées.

1. Entrée de l'interruption de rendu (0x40058c5e, détournée vers m_entry) : officiel et référence arrivent en
   0x40058c66 avec les mêmes registres (d0-d7, a0-a7) et la même pile octet pour octet ; m_t0 = minuteur.
2. Sonde (0x40059382 : jsr m_probe) avec une fonction audio factice : elle voit la même pile et le même argument
   qu'avec le jsr direct de l'officiel ; au retour en 0x40059388, d2-d7, a2-a6 et sp sont rendus, la pile au-dessus
   de sp est intacte. d0, d1, a0, a1 : détruits comme par la vraie fonction audio (fonction C) ; l'interruption ne
   les relit pas avant de les réécrire (0x40059388 : pea, pea, jsr 0x40002912, une autre fonction C).
3. Fenêtres de 750 blocs sur le minuteur simulé, entrée et sonde réelles à chaque bloc : « --/--/-- » avant la 1re
   fenêtre ; « 90/50/20 » (blocs à 50 %, un à 90 %, temps libre 20 %) ; « 45/30/60 » ; une pause (> 20 blocs) remet
   la fenêtre à zéro sans afficher ; « 7/5/90 » (un chiffre) ; débordement du minuteur (2^32 ticks, 31,8 s) au milieu
   d'une fenêtre ; durée > période : bornée à 99 ; rien n'est écrit au-delà des 9 octets de m_name.
4. Écran MACHINES, vrai code de dessin (0x400a2612 : table des noms, puis 0x40071a04 avec la vraie police
   0x40ea14d4, initialisée par 0x400e7ccc) dans un vrai Bitmap 128 x 64 : les 6 machines affichent m_name ;
   largeur en points du pire cas (8 caractères) contre la moitié gauche de l'écran (0..63) et les noms d'origine.
5. Boucle d'attente (0x4000543a -> m_idle_loop) : le banc de l'étude « système » (idle_proto) sur l'image livrée,
   sans rien réécrire : temps libre compté contre temps libre vrai, écritures et PC hors de la boucle.
6. Même code du compteur, aux mêmes adresses, dans les deux fichiers (référence et optimisé).

    python3 preuve_compteur.py [--out DOSSIER_DES_SYX]
"""
import argparse
import pathlib
import random
import struct
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
import banc_essai as be                     # noqa: E402
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE  # noqa
from unicorn import m68k_const as mk        # noqa: E402

sys.path.insert(0, str(be.REPO / "tools" / "emu"))
import test_sdvintage_7th as t7             # noqa: E402

BASE = 0x40000400
TIMER = be.TIMER
S = be.SYM
V, NAME, ACC = S["V"], S["m_name"], S["idle_acc"]
FAIL = []
R = {n: getattr(mk, f"UC_M68K_REG_{n}") for n in
     ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7"]}
SCR = 0x93000000
FAKE_SRC = f"""
	.text
fake:	lea	{SCR:#x},%a0
	move.l	%sp,(%a0)+
	move.l	(%sp),(%a0)+
	move.l	4(%sp),(%a0)+
	move.l	8(%sp),(%a0)+
	move.l	#0x0d0d0d0d,%d0
	move.l	#0x0d1d1d1d,%d1
	movea.l	#0x0a1a1a1a,%a1
	movea.l	#0x0a0a0a0a,%a0
	rts
"""


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def assemble(src, va):
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d)
        (p / "f.S").write_text(src)
        subprocess.run(["m68k-linux-gnu-as", "-mcpu=54418", "-o", str(p / "f.o"), str(p / "f.S")], check=True)
        subprocess.run(["m68k-linux-gnu-ld", "-Ttext", hex(va), "-o", str(p / "f.elf"), str(p / "f.o")], check=True,
                       capture_output=True)
        subprocess.run(["m68k-linux-gnu-objcopy", "-O", "binary", "-j", ".text", str(p / "f.elf"), str(p / "f.bin")],
                       check=True)
        return (p / "f.bin").read_bytes()


FAKE = assemble(FAKE_SRC, 0x4005979e)


class CPU:
    """L'image seule (sans le banc audio) : pour l'entrée, la sonde et le compteur."""

    def __init__(self, img, fake=True):
        uc = self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x01000000)
        uc.mem_map(0x90000000, 0x00100000)
        uc.mem_map(0x93000000, 0x00010000)
        uc.mem_map(0xfc000000, 0x00100000)
        uc.mem_write(BASE, bytes(img))
        if fake:
            uc.mem_write(0x4005979e, FAKE)
        self.writes = []
        uc.hook_add(UC_HOOK_MEM_WRITE, lambda u, a, ad, sz, v, d: self.writes.append((u.reg_read(mk.UC_M68K_REG_PC),
                                                                                         ad, sz)))

    def w32(self, a, v):
        self.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))

    def r32(self, a):
        return struct.unpack(">I", self.uc.mem_read(a, 4))[0]

    def regs(self):
        return {n: self.uc.reg_read(r) for n, r in R.items()}

    def set_regs(self, d):
        for n, v in d.items():
            self.uc.reg_write(R[n], v)

    def entry(self, timer, regs, sp=0x9000c000):
        """De 0x40058c5e (entrée de l'interruption) à 0x40058c66 (après linkw/moveml)."""
        self.w32(TIMER, timer)
        self.set_regs(dict(regs, A7=sp))
        self.uc.emu_start(0x40058c5e, 0x40058c66, count=1000)
        assert self.uc.reg_read(mk.UC_M68K_REG_PC) == 0x40058c66

    def probe(self, end, regs, arg, sp=0x9000bf00):
        """0x40059382 (jsr de la fonction audio, factice ici) -> 0x40059388 ; minuteur = end à la fin."""
        self.w32(TIMER, end)
        self.uc.mem_write(sp, struct.pack(">IIII", arg, 0x51515151, 0x52525252, 0x53535353))
        self.set_regs(dict(regs, A7=sp))
        self.uc.emu_start(0x40059382, 0x40059388, count=10_000)
        assert self.uc.reg_read(mk.UC_M68K_REG_PC) == 0x40059388

    def name(self):
        return bytes(self.uc.mem_read(NAME, 12)).split(b"\0")[0].decode()


def rnd_regs(rng):
    return {n: rng.getrandbits(32) for n in R if n != "A7"}


def part1(imgs, rng):
    print("1. entrée de l'interruption de rendu (0x40058c5e)")
    ok = True
    for k in range(20):
        regs = rnd_regs(rng)
        regs["A6"] = 0x9000f000 + 4 * k
        timer = rng.getrandbits(32)
        st = {}
        for n in ("officiel", "reference"):
            c = CPU(imgs[n])
            c.uc.mem_write(0x9000bc00, bytes(rng.getrandbits(8) for _ in range(0x500)) if n == "officiel" else st["stk0"])
            if n == "officiel":
                st["stk0"] = bytes(c.uc.mem_read(0x9000bc00, 0x500))
            c.entry(timer, regs)
            st[n] = (c.regs(), bytes(c.uc.mem_read(0x9000bc00, 0x500)))
            if n == "reference":
                ok &= c.r32(V) == timer
        ok &= st["officiel"] == st["reference"]
    check(ok, "20 entrées, registres et minuteur au hasard : en 0x40058c66, d0-d7, a0-a7 et la pile (1,25 Ko autour "
          "de sp) identiques à l'officiel ; m_t0 = minuteur lu à l'entrée")
    print("        (le CCR peut différer : 0x40058c66 « move.l #0x7fffffff,%d0 » le réécrit avant tout test, et le SR "
          "de la tâche interrompue revient du cadre d'exception au rte)")


def part2(imgs, rng):
    print("2. sonde de la fonction audio (0x40059382)")
    ok_same, ok_regs = True, True
    seen_ret = {}
    for k in range(20):
        regs = rnd_regs(rng)
        arg = 0x9000bf80 + 4 * k
        st = {}
        for n in ("officiel", "reference"):
            c = CPU(imgs[n])
            c.uc.mem_write(0x9000be00, bytes(0x200))
            if n == "reference":                       # une entrée réelle d'abord (pile à part), période valable
                c.entry(5_000_000, rnd_regs(rng), sp=0x9000e000)
                c.w32(V + 4, 5_000_000 - 90112)
            c.probe(5_000_000 + 30000 + k, regs, arg)
            after = c.regs()
            seen = struct.unpack(">4I", c.uc.mem_read(SCR, 16))
            st[n] = (seen[0], seen[2:], {r: after[r] for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4",
                                                               "A5", "A6", "A7")},
                     bytes(c.uc.mem_read(0x9000bf00, 0x100)))
            seen_ret[n] = seen[1]
            ok_regs &= all(after[r] == regs[r] for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5",
                                                          "A6")) and after["A7"] == 0x9000bf00
        ok_same &= st["officiel"] == st["reference"]
    check(ok_same, "20 appels : la fonction audio voit le même sp, le même argument (fp-44) et la même pile ; au "
          "retour, mêmes d2-d7, a2-a6, sp et pile au-dessus de sp que l'officiel")
    check(ok_regs, "d2-d7, a2-a6 rendus, sp rendu (0x9000bf00), retour en 0x40059388")
    check(seen_ret["officiel"] == 0x40059388 and S["m_probe"] < seen_ret["reference"] < S["m_probe"] + 0x40,
          f"adresse de retour vue par la fonction : {seen_ret['officiel']:#x} (officiel), {seen_ret['reference']:#x} "
          "(dans m_probe) : seule différence, comme pour tout appel imbriqué")


def part3(img):
    print("3. fenêtres de 750 blocs (entrée et sonde réelles, minuteur simulé)")
    c = CPU(img)
    rng = random.Random(3)
    tail0 = bytes(c.uc.mem_read(NAME + 9, 3))
    shown = []
    state = dict(t=10_000_000, n=0)
    bad_regs = [0]

    def blocks(n, dur, idle=0, special=None, gap=None):
        for k in range(n):
            if gap and k == 0:
                state["t"] += gap
            t = state["t"]
            regs = rnd_regs(rng)
            c.entry(t & 0xffffffff, regs)
            d = special[1] if special and k == special[0] else dur
            c.w32(ACC, c.r32(ACC) + idle)               # ce qu'aurait compté la boucle d'attente
            pr = rnd_regs(rng)
            c.probe((t + d) & 0xffffffff, pr, 0x9000bf80)
            after = c.regs()
            if any(after[r] != pr[r] for r in ("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A4", "A5", "A6")) \
                    or after["A7"] != 0x9000bf00:
                bad_regs[0] += 1
            state["t"] += 90112
            state["n"] += 1

    c.w32(ACC, 0xfffff000)                             # le compteur de temps libre déborde aussi
    blocks(1, 45056)                                   # 1er bloc : remise à zéro
    blocks(749, 45056, 18023, special=(399, 81101))
    shown.append(("749 blocs comptés", c.name()))
    blocks(1, 45056, 18023)
    shown.append(("750 blocs : 50 %, un à 90 %, libre 20 %", c.name()))
    blocks(750, 27034, 54068, special=(10, 40551))
    shown.append(("750 blocs : 30 %, un à 45 %, libre 60 %", c.name()))
    blocks(1, 45056, 0, gap=30 * 90112)                # pause de 30 blocs
    shown.append(("pause de 30 blocs", c.name()))
    blocks(500, 4506, 81101, special=(7, 6308))
    shown.append(("500 blocs après la pause", c.name()))
    blocks(250, 4506, 81101)
    shown.append(("750 blocs : 5 %, un à 7 %, libre 90 %", c.name()))
    state["t"] = 0xffffffff - 300 * 90112             # débordement du minuteur au 300e bloc
    blocks(1, 63079, 9012, gap=0)                      # (écart > 20 blocs : remise à zéro)
    blocks(750, 63079, 9012)
    shown.append(("750 blocs à 70 %, libre 10 %, minuteur qui déborde", c.name()))
    blocks(750, 2 * 90112, 0)
    shown.append(("750 blocs plus longs que la période", c.name()))
    for k, v in shown:
        print(f"        {k:55s} -> « {v} »")
    want = ["--/--/--", "90/50/20", "45/30/60", "45/30/60", "45/30/60", "7/5/90", "70/70/10", "99/99/0"]
    check([v for _, v in shown] == want, f"noms affichés {[v for _, v in shown]} = attendus {want}")
    mine = [(pc, a) for pc, a, n in c.writes if (S["m_entry"] <= pc < S["m_entry"] + 280 or
                                                 S["m_show"] <= pc < S["m_show"] + 192) and not 0x90000000 <= a < 0x90100000]
    check(bytes(c.uc.mem_read(NAME + 9, 3)) == tail0 and mine and all(V <= a < NAME + 9 for pc, a in mine),
          "écritures du compteur : seulement ses variables et les 9 octets de m_name (hors pile)")
    check(bad_regs[0] == 0, f"{state['n']} blocs : d2-d7, a2-a6 et sp rendus par la sonde à chaque bloc")


def font_extent(img, m, text=None):
    """Dessine le nom de la machine m comme l'écran MACHINES (0x400a2612..0x400a2636) ; rend les colonnes allumées."""
    u = t7.UI(img)
    import preuve_machines
    preuve_machines.heap(u)                            # operator new / delete : un tas factice (étude « stabilité »)
    canvas, buf, obj = 0x92000000, 0x92001000, 0x92003000
    u.call(0x400e7ccc)
    u.call(0x40070172, canvas, 128, 64, buf, buf + 0x800)
    if text is not None:
        u.uc.mem_write(NAME, text.encode() + b"\0")
    u.uc.mem_write(obj + 108, struct.pack(">I", 0x40ea14d4))
    sp = t7.STACK - 0x800
    for r, v in ((mk.UC_M68K_REG_D3, m), (mk.UC_M68K_REG_D2, canvas), (mk.UC_M68K_REG_A2, obj),
                 (mk.UC_M68K_REG_A0, 0x40071a04), (mk.UC_M68K_REG_A7, sp)):
        u.uc.reg_write(r, v)
    u.bad.clear()
    u.uc.emu_start(0x400a2612, 0x400a2638, count=2_000_000)
    assert u.uc.reg_read(mk.UC_M68K_REG_PC) == 0x400a2638 and not u.bad, u.bad[:3]
    fb = bytes(u.uc.mem_read(buf, 0x400))
    cols = [x for x in range(128) if any(fb[(x * 2 + y // 32) * 4:(x * 2 + y // 32) * 4 + 4] != b"\0\0\0\0"
                                         for y in (0, 32))]
    rows = [y for y in range(64) if any((struct.unpack(">I", fb[(x * 2 + y // 32) * 4:(x * 2 + y // 32) * 4 + 4])[0]
                                         >> (31 - (y & 31))) & 1 for x in range(128))]
    return (min(cols), max(cols)) if cols else None, (min(rows), max(rows)) if rows else None


def part4(imgs):
    print("4. écran MACHINES (vrai dessin, vraie police)")
    off = [font_extent(imgs["officiel"], m) for m in range(6)]
    print(f"        officiel, noms d'origine : colonnes {[o[0] for o in off]}, lignes {off[0][1]}")
    ref = [font_extent(imgs["reference"], m) for m in range(6)]
    check(all(r == ref[0] for r in ref) and ref[0][0] is not None,
          f"référence : les 6 machines affichent m_name (« --/--/-- » : colonnes {ref[0][0]}, lignes {ref[0][1]})")
    worst = None
    for s in ["99/99/99", "88/88/88", "00/00/00", "44/44/44", "66/66/66", "77/77/77", "22/22/22", "33/33/33",
              "55/55/55", "11/11/11", "90/50/20", "7/5/90", "99/99/0"]:
        ext = font_extent(imgs["reference"], 0, s)
        if worst is None or ext[0][1] - ext[0][0] > worst[1][0][1] - worst[1][0][0]:
            worst = (s, ext)
        print(f"        « {s} » : colonnes {ext[0]}, lignes {ext[1]}")
    lo, hi = worst[1][0]
    check(lo >= 0 and hi <= 63, f"pire cas « {worst[0]} » : colonnes {lo}..{hi}, dans la moitié gauche (0..63) où "
          "l'OS dessine le nom (centré en x = 32) ; l'image de droite est centrée en x = 96")
    for n in ("reference", "optimise"):
        txt = [t7.drum_select(imgs[n], b"", m)[0] for m in range(6)]
        check(all(x == ["--/--/--"] for x in txt), f"{n} : drum_select (0x400a25e0) écrit « --/--/-- » pour les 6 "
              f"machines avant la 1re mesure : {txt}")


def part5(img):
    print("5. temps libre (boucle d'attente 0x4000543a -> m_idle_loop)")
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import idle_proto_orig as ip
    hook = bytes(img[ip.HOOK - BASE:ip.HOOK - BASE + 6])
    check(hook == b"\x4e\xf9" + struct.pack(">I", S["m_idle_loop"]), f"0x4000543a : jmp m_idle_loop ({hook.hex()})")
    stub = S["m_idle_loop"]
    end = stub + 0x26
    acc = ACC

    def run(audio, ui, ms=20, seed=1):
        rng = random.Random(seed)
        uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_map(0xfc000000, 0x100000)
        uc.mem_write(BASE, img)
        span = ip.BUS * ms // 1000
        ev = []
        blk = ip.BUS // 1500
        for k in range(span // blk + 1):
            ev.append((k * blk + rng.randrange(50), int(blk * audio)))
        for k in range(span // (ip.BUS // 12000) + 1):
            ev.append((k * (ip.BUS // 12000) + rng.randrange(100), 60))
        for k in range(span // (ip.BUS // 8000) + 1):
            ev.append((k * (ip.BUS // 8000) + rng.randrange(100), 300))
        for k in range(span // (ip.BUS // 30) + 1):
            ev.append((k * (ip.BUS // 30) + rng.randrange(1000), int(ip.BUS // 30 * ui)))
        ev.sort()
        st = dict(clock=0, stolen=0, i=0, bad_w=[], bad_pc=set(), t0=None)

        def steal():
            while st["i"] < len(ev) and ev[st["i"]][0] <= st["clock"]:
                st["clock"] += ev[st["i"]][1]
                st["stolen"] += ev[st["i"]][1]
                st["i"] += 1

        def hc(u, a, s, d):
            st["clock"] += 1
            if not (a == ip.HOOK or stub <= a < end):
                st["bad_pc"].add(hex(a))
            steal()
            if st["clock"] >= span:
                u.emu_stop()

        def hr(u, ac, a, s, v, d):
            if a == ip.DTIM0:
                st["clock"] += 6
                steal()
                if st["t0"] is None:
                    st["t0"] = (st["clock"], st["stolen"])
                st["t1"] = (st["clock"], st["stolen"])
                u.mem_write(ip.DTIM0, struct.pack(">I", st["clock"] & 0xffffffff))

        def hw(u, ac, a, s, v, d):
            if a != acc and not 0x41ff0000 <= a < 0x42000000:
                st["bad_w"].append(hex(a))
        uc.hook_add(UC_HOOK_CODE, hc)
        uc.hook_add(UC_HOOK_MEM_READ, hr)
        uc.hook_add(UC_HOOK_MEM_WRITE, hw)
        uc.reg_write(mk.UC_M68K_REG_A7, 0x41ffff00 - 24)
        uc.emu_start(ip.HOOK, 0, count=50_000_000)
        counted = struct.unpack(">I", uc.mem_read(acc, 4))[0]
        (c0, s0), (c1, s1) = st["t0"], st["t1"]
        e = c1 - c0
        return 100 * ((c1 - c0) - (s1 - s0)) / e, 100 * counted / e, st["bad_w"][:4], sorted(st["bad_pc"])[:4], \
            uc.reg_read(mk.UC_M68K_REG_A7)

    ok = True
    for audio, ui in ((0.77, 0.05), (0.20, 0.10), (0.61, 0.05), (0.0, 0.0)):
        true, counted, bw, bp, sp = run(audio, ui)
        print(f"        audio {audio:4.0%}, interface {ui:4.0%} : libre vrai {true:6.2f} %, compté {counted:6.2f} % "
              f"(écart {counted - true:+.2f} pt) ; écritures hors compteur {bw or 'aucune'}, PC hors boucle {bp or 'aucun'}")
        ok &= abs(counted - true) < 1.5 and not bw and not bp and sp == 0x41ffff00
    check(ok, "temps libre compté à moins de 1,5 point du vrai ; la boucle n'écrit que idle_acc, ne sort pas, "
          "sp = celui de l'original après lea 24(sp),sp")


def part6(imgs):
    print("6. même compteur dans les deux fichiers")
    a, b = imgs["reference"], imgs["optimise"]
    spots = [(0x40167c50, 280), (0x40171a48, 192), (0x40058c5e, 8), (0x40059382, 6), (0x4000543a, 6),
             (0x401177e4, 24)]
    same = all(a[va - BASE:va - BASE + n] == b[va - BASE:va - BASE + n] for va, n in spots)
    check(same, "masques 0x40167c50 et 0x40171a48, détours 0x40058c5e, 0x40059382, 0x4000543a et table des noms "
          "0x401177e4 : octet pour octet identiques dans la référence et l'optimisé")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(be.OUT))
    args = ap.parse_args()
    imgs = be.images(args.out)
    for k, v in imgs.items():
        print(f"{k:10s} MAIN OS {be.sha(v)}")
    rng = random.Random(7)
    part1(imgs, rng)
    part2(imgs, rng)
    for n in ("reference", "optimise"):
        print(f"   ({n})")
        part3(imgs[n])
    part4(imgs)
    part5(imgs["reference"])
    part6(imgs)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
