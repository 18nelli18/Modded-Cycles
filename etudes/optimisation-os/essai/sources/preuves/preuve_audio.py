#!/usr/bin/env python3
"""Son des deux fichiers d'essai, sur le banc de l'étage de sortie (banc_essai.py : vraie interruption audio, voix,
mixeur, Volume + Dist, envois, delay, reverb, master, anneau du codec, copie USB, eDMA simulé), bloc par bloc,
images relues dans les .syx livrés.

Cas exacts (les trois images en parallèle, du démarrage) :
  defaut       6 pistes, un trig sur chaque pas (120 BPM : 187,5 blocs), réglages par défaut ;
  envois       pareil, envois delay 40 et reverb 40 sur les 6 pistes ;
  dist         pareil, VOL+DIST 100 sur les pistes 1-3, 80 sur 4-6 ;
  glissements  trig tous les 40 blocs ; réglages tournés comme des potards (test_combo de l'étude « sortie ») :
               défaut, puis envoi delay 40 piste 3 + VOL+DIST 90 piste 1, puis reverb 50 pistes 2 et 5, puis tout
               revient (envois 0, VOL+DIST 60).
  Contrôles : officiel = référence (compteur seul) : anneau du codec, USB, sortie des 6 voix, SRAM entière, EMAC,
  lignes du delay et de la reverb en DDR à chaque bloc ; toute la mémoire tous les 10 blocs (sauf la pile, morte
  entre deux blocs, les octets d'image que les tweaks changent et les masques qui portent du code et ses
  variables). Référence = optimisé : les mêmes, sauf 0x8000bc98..bd98 (sortie du saturateur que p1 ne réécrit
  pas, lue x 0 : étude « sortie »).
Cas de l'arrêt des voix muettes (tolérance) :
  arret        800 blocs sans trig, les trois images : codec, USB, voix, lignes identiques ; m_show (bloc 751)
               dans le vrai contexte ; écarts de SRAM listés ;
  silence      DECAY 20 sur les 6 pistes, trig au bloc 100 (après l'arrêt des voix au démarrage), retrig au bloc
               1 750 (après l'arrêt de toutes les voix), 1 950 blocs, référence et optimisé : là où une voix arrêtée
               sort 0, la référence est sous 2^13 (−108 dBFS) ; ailleurs écart ≤ 2,5e-6 de la crête (−112 dB).

    python3 preuve_audio.py SCENARIO [--out DOSSIER_DES_SYX]
"""
import argparse
import math
import sys
import time

sys.dont_write_bytecode = True
import numpy as np                          # noqa: E402
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ   # noqa: E402
from unicorn import m68k_const as mk        # noqa: E402

import banc_essai as be                     # noqa: E402

FAIL = []
LINES = ((0x42400000, 0x400000), (0x42340000, 0x90000), (0x423d0000, 0x8000))   # = 0x4a... (même tampon)


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def db(x, ref=2 ** 31):
    return -math.inf if x == 0 else 20 * math.log10(x / ref)


class Mem:
    """Mémoire comparable d'un banc : régions mappées sauf pile (0x9000xxxx), périphériques, alias 0x4a."""

    def __init__(self, a, b, imga, imgb, p1):
        self.a, self.b = a, b
        self.excl = {}
        diff = np.flatnonzero(np.frombuffer(imga, np.uint8) != np.frombuffer(imgb, np.uint8)) + 0x40000400
        self.static = (len(diff), [hex(int(x)) for x in diff[:3]])
        self.diffva = diff
        self.p1 = p1

    def regions(self, uc):
        out = []
        for beg, end, _ in uc.mem_regions():
            if beg >= 0xfc000000 or 0x90000000 <= beg < 0x91000000 or 0x4a000000 <= beg < 0x4b000000:
                continue
            out.append((beg, end + 1))
        return out

    def _masked(self, uc, beg, end):
        m = np.frombuffer(bytes(uc.mem_read(beg, end - beg)), np.uint8).copy()
        sel = self.diffva[(self.diffva >= beg) & (self.diffva < end)] - beg
        m[sel] = 0
        for va, n in be.CODE_MASKS:
            lo, hi = max(va, beg), min(va + n, end)
            if lo < hi:
                m[lo - beg:hi - beg] = 0
        if self.p1:
            lo, hi = max(be.P1_STALE[0], beg), min(be.P1_STALE[1], end)
            if lo < hi:
                m[lo - beg:hi - beg] = 0
        return m

    def compare_all(self):
        ra, rb = self.regions(self.a.uc), self.regions(self.b.uc)
        if ra != rb:
            return [("régions", ra, rb)]
        bad = []
        for beg, end in ra:
            x, y = self._masked(self.a.uc, beg, end), self._masked(self.b.uc, beg, end)
            d = np.flatnonzero(x != y)
            if len(d):
                bad.append((hex(beg), len(d), [hex(beg + int(i)) for i in d[:6]]))
        return bad

    def sram(self, b):
        s = np.frombuffer(bytes(b.uc.mem_read(0x80000000, 0x20000)), np.uint8).copy()
        if self.p1:
            s[be.P1_STALE[0] - 0x80000000:be.P1_STALE[1] - 0x80000000] = 0
        return s


def lines(b):
    return b"".join(bytes(b.uc.mem_read(a, n)) for a, n in LINES)


def emac(b):
    em = b.e.emac
    return repr((list(em.acc), em.macsr))


class Hits:
    """Passages par les chemins courts des optimisations (image optimisée) et lectures du minuteur."""

    def __init__(self, b, opt):
        self.n = {}
        self.timer_pc = set()
        uc = b.uc
        if opt:
            for name, a in (("p1 saturateur sauté", be.SYM["vd_hit"]), ("p2 delay endormi", be.SYM["dz_sleep"]),
                            ("p2 reverb endormie", be.SYM["rz_slept"]), ("p3 envoi sauté", be.SYM["zero_out"]),
                            ("PUNCH chemin court", 0x40186284), ("PUNCH chemin d'origine", 0x4018628a)):
                self.n[name] = 0
                uc.hook_add(UC_HOOK_CODE, lambda *x, k=name: self._inc(k), begin=a, end=a)

        def rd(uc_, acc, addr, size, value, ud):
            self.timer_pc.add(uc_.reg_read(mk.UC_M68K_REG_PC))
        uc.hook_add(UC_HOOK_MEM_READ, rd, begin=be.TIMER, end=be.TIMER + 3)

    def _inc(self, k):
        self.n[k] += 1


def setup(b, sc):
    for t in range(6):
        if "sends" in sc:
            b.param(t, 20, sc["sends"][0])
            b.param(t, 21, sc["sends"][1])
        if "dist" in sc:
            b.param(t, 19, sc["dist"][t])
        if "decay" in sc:
            b.param(t, 18, sc["decay"])


def glisse(b, k):
    ph = k // 100
    if k % 100:
        return
    if ph == 1:
        b.target(2, 20, 40)
        b.target(0, 19, 90)
    elif ph == 2:
        b.target(1, 21, 50)
        b.target(4, 21, 50)
    elif ph == 3:
        for t in range(6):
            b.target(t, 20, 0)
            b.target(t, 21, 0)
        b.target(0, 19, 60)


SCEN = {
    "defaut": dict(kind="exact", blocks=400),
    "envois": dict(kind="exact", blocks=400, sends=(40, 40)),
    "dist": dict(kind="exact", blocks=400, dist=(100, 100, 100, 80, 80, 80)),
    "glissements": dict(kind="exact", blocks=400, every=40, glisse=True),
    "arret": dict(kind="arret", blocks=800),
    "silence": dict(kind="tol", blocks=1950, decay=20, trigs=(100, 1750)),
}


def run_exact(name, sc, imgs):
    names = ["officiel", "reference", "optimise"]
    B = {k: be.Banc(imgs[k]) for k in names}
    H = {k: Hits(B[k], k == "optimise") for k in names}
    for b in B.values():
        setup(b, sc)
    pats = {k: be.Pattern(B[k], every=sc.get("every")) for k in names} if sc["kind"] == "exact" else {}
    pairs = [("officiel", "reference", False), ("reference", "optimise", True)]
    mems = {(x, y): Mem(B[x], B[y], imgs[x], imgs[y], p1) for x, y, p1 in pairs}
    first = {p: None for p in mems}
    peaks = dict(ring=0, usb=0, out=0)
    nfull = 0
    quiet_max = 0
    trigs = 0
    first_sound = None
    for k in range(sc["blocks"]):
        info = {}
        for n in names:
            if sc.get("glisse"):
                glisse(B[n], k)
            if n in pats:
                pats[n].tick()
            info[n] = B[n].block()
        trigs += bin(info["reference"]["trig"] & 0x3f).count("1")
        if first_sound is None and np.any(info["reference"]["out"]):
            first_sound = k
        peaks["ring"] = max(peaks["ring"], int(np.abs(info["reference"]["ring"]).max()))
        peaks["usb"] = max(peaks["usb"], int(np.abs(info["reference"]["usb"]).max()))
        peaks["out"] = max(peaks["out"], int(np.abs(info["reference"]["out"]).max()))
        quiet_max = max(quiet_max, max(B["optimise"].quiet()))
        full = k % 10 == 9 or k == sc["blocks"] - 1
        nfull += full
        for (x, y), m in mems.items():
            if first[(x, y)] is not None:
                continue
            ia, ib = info[x], info[y]
            why = [w for w, ok in (
                ("anneau du codec", np.array_equal(ia["ring"], ib["ring"])),
                ("USB", np.array_equal(ia["usb"], ib["usb"])),
                ("voix", np.array_equal(ia["out"], ib["out"])),
                ("SRAM", np.array_equal(m.sram(B[x]), m.sram(B[y]))),
                ("EMAC", emac(B[x]) == emac(B[y])),
                ("lignes DDR", lines(B[x]) == lines(B[y]))) if not ok]
            if not why and full:
                bad = m.compare_all()
                if bad:
                    why = [f"mémoire {bad[:3]}"]
            if why:
                first[(x, y)] = (k, why)
                if "SRAM" in why:
                    sa, sb = m.sram(B[x]), m.sram(B[y])
                    d = np.flatnonzero(sa != sb)
                    print(f"    {x}/{y} bloc {k} : SRAM diffère en {len(d)} octets, {[hex(0x80000000 + int(i)) for i in d[:8]]}")
                if "EMAC" in why:
                    print(f"    {x}/{y} bloc {k} : EMAC {emac(B[x])} / {emac(B[y])}")
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    print(f"  {sc['blocks']} blocs, {trigs} trigs (référence) ; crêtes : anneau {peaks['ring']}, USB {peaks['usb']}, "
          f"voix {peaks['out']} ; mémoire entière comparée {nfull} fois ; compteur de blocs faibles de l'arrêt des "
          f"voix ≤ {quiet_max} (arrêt à 64)")
    for (x, y), f in first.items():
        what = ("anneau, USB, 6 voix, SRAM entière" + (" sauf 0x8000bc98..bd98" if mems[(x, y)].p1 else "") +
                ", EMAC, lignes delay/reverb à chaque bloc ; toute la mémoire tous les 10 blocs (hors pile, octets "
                f"d'image changés par les tweaks ({mems[(x, y)].static[0]}), masques de code)")
        check(f is None, f"{name} : {x} = {y} sur {sc['blocks']} blocs ({what})" +
              ("" if f is None else f" — premier écart au bloc {f[0]} : {f[1]}"))
    check(peaks["ring"] > 0 and peaks["usb"] > 0, f"{name} : il y a du son (crête de l'anneau {peaks['ring']})")
    if sc["kind"] == "exact":
        check(quiet_max < 64, f"{name} : aucune voix arrêtée (compteur ≤ {quiet_max} < 64) : cas exact attendu")
    print("  chemins courts (optimisé) : " + ", ".join(f"{k} {v}" for k, v in H["optimise"].n.items()))
    for n in names:
        print(f"  lectures du minuteur DMA 0 ({n}) : {sorted(hex(x) for x in H[n].timer_pc) or 'aucune'}")
    check(not H["officiel"].timer_pc, f"{name} : l'OS officiel ne lit pas le minuteur dans l'interruption audio "
          "(le compteur ne peut pas changer son comportement)")
    if "sends" in sc:
        ln = np.frombuffer(lines(B["reference"]), np.uint8)
        hz = H["optimise"].n
        check(np.count_nonzero(ln) > 0 and hz["p2 delay endormi"] <= first_sound and
              hz["p2 reverb endormie"] <= first_sound,
              f"{name} : delay et reverb reçoivent du son ({np.count_nonzero(ln)} octets non nuls dans leurs lignes) ; "
              f"p2 ne dort qu'avant le 1er son des voix (bloc {first_sound}) : delay {hz['p2 delay endormi']}, "
              f"reverb {hz['p2 reverb endormie']} blocs endormis")
    if "dist" in sc:
        check(H["optimise"].n["p1 saturateur sauté"] == 0, f"{name} : saturateur calculé (Dist en service) : "
              f"{H['optimise'].n['p1 saturateur sauté']} sauts")
    return B


def run_arret(name, sc, imgs):
    names = ["officiel", "reference", "optimise"]
    B = {k: be.Banc(imgs[k]) for k in names}
    H = {k: Hits(B[k], k == "optimise") for k in names}
    m_or = Mem(B["officiel"], B["reference"], imgs["officiel"], imgs["reference"], False)
    m_ro = Mem(B["reference"], B["optimise"], imgs["reference"], imgs["optimise"], True)
    first_or = None
    same_ro = dict(ring=True, usb=True, out=True, lines=True)
    zero = True
    sram_diff = set()
    names_seen = []
    for k in range(sc["blocks"]):
        info = {n: B[n].block() for n in names}
        a, b, c = info["officiel"], info["reference"], info["optimise"]
        if first_or is None:
            why = [w for w, ok in (
                ("anneau", np.array_equal(a["ring"], b["ring"])), ("USB", np.array_equal(a["usb"], b["usb"])),
                ("voix", np.array_equal(a["out"], b["out"])),
                ("SRAM", np.array_equal(m_or.sram(B["officiel"]), m_or.sram(B["reference"]))),
                ("EMAC", emac(B["officiel"]) == emac(B["reference"])),
                ("lignes", lines(B["officiel"]) == lines(B["reference"]))) if not ok]
            if not why and (k % 10 == 9 or k == sc["blocks"] - 1 or k in (749, 750, 751)):
                bad = m_or.compare_all()
                if bad:
                    why = [f"mémoire {bad[:3]}"]
            if why:
                first_or = (k, why)
        same_ro["ring"] &= np.array_equal(b["ring"], c["ring"])
        same_ro["usb"] &= np.array_equal(b["usb"], c["usb"])
        same_ro["out"] &= np.array_equal(b["out"], c["out"])
        if k % 10 == 9:
            same_ro["lines"] &= lines(B["reference"]) == lines(B["optimise"])
        zero &= not (np.any(b["ring"]) or np.any(b["usb"]) or np.any(b["out"]))
        sa, sb = m_ro.sram(B["reference"]), m_ro.sram(B["optimise"])
        sram_diff |= set((np.flatnonzero(sa != sb) & ~0xff).tolist())
        if k in (749, 750, 751, 799):
            names_seen.append((k, B["reference"].meter_name(), B["optimise"].meter_name()))
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    check(first_or is None, f"{name} : officiel = référence sur {sc['blocks']} blocs (anneau, USB, voix, SRAM, EMAC, lignes à "
          "chaque bloc ; toute la mémoire tous les 10 blocs et aux blocs 749-751, où m_show écrit le nom)"
          + ("" if first_or is None else f" — premier écart {first_or}"))
    check(all(same_ro.values()), f"{name} : référence = optimisé pour l'anneau du codec, l'USB, la sortie des 6 voix "
          f"et les lignes delay/reverb ({same_ro})")
    check(zero, f"{name} : à l'arrêt, codec, USB et voix valent exactement 0 dans la référence (donc aussi dans l'optimisé)")
    pages = sorted(sram_diff)
    print(f"  SRAM référence/optimisé : écarts dans {len(pages)} pages de 256 o : "
          f"{[hex(0x80000000 + p) for p in pages[:16]]}")
    print(f"  noms MACHINES (référence, optimisé) : {names_seen}")
    want = f"{100 * be.DUR // be.BLOCK_TICKS}/{be.DUR * 100 // be.BLOCK_TICKS}/0"
    check(names_seen and all(r == "--/--/--" for k, r, o in names_seen if k < 750) and
          all(r == o == want for k, r, o in names_seen if k >= 750),
          f"{name} : nom « --/--/-- » jusqu'au bloc 750, puis « {want} » (minuteur simulé : blocs à "
          f"{be.DUR}/{be.BLOCK_TICKS} ticks, pas de temps libre), dans les deux images")
    print("  chemins courts (optimisé) : " + ", ".join(f"{k} {v}" for k, v in H["optimise"].n.items()))


def run_tol(name, sc, imgs):
    names = ["reference", "optimise"]
    B = {k: be.Banc(imgs[k]) for k in names}
    for b in B.values():
        setup(b, sc)
        for t in range(6):
            b.rig.set_step(t, 0, vel=100, length=be.seqrig.LEN_1_16)
    outs = {n: [] for n in names}
    rings = {n: [] for n in names}
    usbs = {n: [] for n in names}
    stopped = []
    sram_pages = set()
    m = Mem(B["reference"], B["optimise"], imgs["reference"], imgs["optimise"], True)
    for k in range(sc["blocks"]):
        for n in names:
            if k + 1 in sc["trigs"]:
                for t in range(6):
                    B[n].rig.schedule_step(t, 0, B[n].rig.now + B[n].rig.blk)
            info = B[n].block()
            outs[n].append(info["out"])
            rings[n].append(info["ring"])
            usbs[n].append(info["usb"])
        stopped.append([q >= 64 for q in B["optimise"].quiet()])
        sa, sb = m.sram(B["reference"]), m.sram(B["optimise"])
        sram_pages |= set((np.flatnonzero(sa != sb) & ~0xff).tolist())
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    R, O = np.array(outs["reference"]), np.array(outs["optimise"])        # blocs x 6 x 32
    st = np.array(stopped)
    t1, t2 = sc["trigs"]
    peak = np.abs(R).max(axis=(0, 2))                                        # crête par piste
    eq = np.all(R == O, axis=2)                                              # blocs x pistes identiques
    zero_o = np.all(O == 0, axis=2)
    diff_blocks = ~eq
    # 1. là où l'optimisé sort 0 et diffère : la référence est sous le seuil
    z = diff_blocks & zero_o
    ref_under = np.abs(R).max(axis=2)
    worst_zero = int(ref_under[z].max()) if z.any() else 0
    # 2. ailleurs (voix calculée mais état figé pendant l'arrêt) : écart relatif à la crête de la piste
    other = diff_blocks & ~zero_o
    rel = (np.abs(R - O).max(axis=2) / np.maximum(peak, 1)[None, :])
    worst_rel = float(rel[other].max()) if other.any() else 0.0
    print(f"  crêtes des voix (référence) : {peak.tolist()}")
    print(f"  blocs-pistes : {eq.size} ; identiques {int(eq.sum())} ; optimisé à 0 là où la référence ne l'est pas "
          f"{int(z.sum())} ; autres écarts {int(other.sum())} ; arrêtées (compteur ≥ 64) {int(st.sum())}")
    stop_at = [int(np.argmax(st[t1:, t])) + t1 if st[t1:, t].any() else None for t in range(6)]
    print(f"  arrêt de chaque voix après le trig du bloc {t1} : blocs {stop_at}")
    check(all(s is not None and s < t2 for s in stop_at), f"{name} : les 6 voix (DECAY 20) s'arrêtent avant le retrig "
          f"du bloc {t2}")
    first_note = eq[t1:t1 + 64].all()
    check(bool(np.all(eq[:t1]) and first_note),
          f"{name} : identique avant le 1er trig (voix jamais déclenchées) et pendant les 64 blocs qui le suivent "
          "(1re note après un arrêt au démarrage)")
    # sortie de la piste après la division par 2 de l'OS (pleine échelle 2^30) : seuil 4 096 = render < 2^13
    check(worst_zero < 4096, f"{name} : voix arrêtée : 0 là où la référence sort au plus {worst_zero} après la "
          f"division par 2 ({db(worst_zero, 2 ** 30):.1f} dB de la pleine échelle ; seuil 4 096 = "
          f"{db(4096, 2 ** 30):.1f} dB)")
    check(worst_rel <= 2.5e-6, f"{name} : voix recalculée après un arrêt (retrig du bloc {t2}) : écart ≤ "
          f"{worst_rel:.2e} de la crête ({db(worst_rel, 1):.1f} dB ; limite 2,5e-6 = −112 dB)")
    Rr, Or = np.array(rings["reference"]), np.array(rings["optimise"])
    Ru, Ou = np.array(usbs["reference"]), np.array(usbs["optimise"])
    dr, du = int(np.abs(Rr - Or).max()), int(np.abs(Ru - Ou).max())
    pr, pu = int(np.abs(Rr).max()), int(np.abs(Ru).max())
    # anneau du codec : 24 bits (pleine échelle 2^23) ; USB : 32 bits (2^31)
    print(f"  anneau du codec : crête {pr}, écart max {dr} ({db(dr, 2 ** 23):.1f} dBFS) ; "
          f"USB : crête {pu}, écart max {du} ({db(du):.1f} dBFS)")
    check(db(dr, 2 ** 23) < -100 and db(du) < -100, f"{name} : codec et USB à moins de −100 dBFS de la référence "
          f"({db(dr, 2 ** 23):.1f} et {db(du):.1f} dBFS)")
    print(f"  SRAM référence/optimisé : écarts dans {len(sram_pages)} pages de 256 o : "
          f"{[hex(0x80000000 + p) for p in sorted(sram_pages)[:16]]}")
    nr, no = B["reference"].meter_name(), B["optimise"].meter_name()
    want = f"{100 * be.DUR // be.BLOCK_TICKS}/{be.DUR * 100 // be.BLOCK_TICKS}/0"
    check(nr == no == want, f"{name} : nom MACHINES après {sc['blocks']} blocs : « {nr} » / « {no} » (attendu « {want} »)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scen", choices=SCEN)
    ap.add_argument("--out", default=str(be.OUT))
    ap.add_argument("--blocks", type=int, help="essai rapide : moins de blocs")
    args = ap.parse_args()
    imgs = be.images(args.out)
    for k, v in imgs.items():
        print(f"{k:10s} MAIN OS {be.sha(v)}")
    sc = dict(SCEN[args.scen])
    if args.blocks:
        sc["blocks"] = args.blocks
    print(f"scénario {args.scen} : {sc}")
    t0 = time.time()
    {"exact": run_exact, "arret": run_arret, "tol": run_tol}[sc["kind"]](args.scen, sc, imgs)
    print(f"({time.time() - t0:.0f} s)")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
