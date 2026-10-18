#!/usr/bin/env python3
"""Preuve de l'OS optimisé (notes/70, tweaks/model-cycles_OS1.13/70-os-optimise.json).

« base » = le MAIN OS d'origine avec les mods de --with ; « optimisé » = la même base avec os-optimise. Le vrai code de
l'OS, émulé (Unicorn) sur le banc de l'étage de sortie (outrig.py : vraie interruption audio, séquenceur, voix,
Volume + Dist, envois, mixeur, delay, reverb, master, anneau du codec, copie USB, eDMA simulé), bloc par bloc :

  1. Écritures : octets d'origine, détours et masques, application seule et avec les mods de --with.
  2. Gels (gels_checks.py) : D1, MACHINES sur une machine inconnue ; D2, horloge MIDI sortante, anneau plein.
  Son exact, les deux images en parallèle depuis le démarrage, comparées à chaque bloc : anneau du codec, USB, sortie
  des 6 voix, SRAM entière (sauf 0x8000bc98..0x8000bd98, la sortie du saturateur que le raccourci ne réécrit pas,
  lue x 0), EMAC, lignes du delay et de la reverb ; toute la mémoire tous les 10 blocs (hors pile, octets d'image
  et masques changés par le tweak) :
  3. defaut      6 pistes, un trig sur chaque pas (120 BPM), réglages par défaut (400 blocs) ;
  4. envois      pareil, envois delay 40 et reverb 40 sur les 6 pistes ;
  5. dist        pareil, VOL+DIST 100 sur les pistes 1-3, 80 sur 4-6 ;
  6. glissements trig tous les 40 blocs ; réglages tournés comme des potards : envoi delay 40 piste 3 + VOL+DIST 90
                 piste 1, puis reverb 50 pistes 2 et 5, puis tout revient (envois 0, VOL+DIST 60) ;
     filtre      (avec track-filter dans --with) comme defaut, filtre de piste en marche : cutoff L24 (k 28 = 40),
                 résonance 80 (k 29) sur les 6 pistes, envois delay 30 et reverb 30.
  Arrêt des voix muettes (le seul cas non exact : une voix arrêtée sort 0 au lieu de moins de -108 dB) :
  7. arret       800 blocs sans trig : codec, USB, voix et lignes identiques et exactement nuls ;
  8. silence     DECAY 20 sur les 6 pistes, trig au bloc 100, retrig au bloc 1 750 (toutes les voix arrêtées),
                 1 950 blocs : là où une voix arrêtée sort 0, la base est sous 4 096 après la division par 2 de l'OS
                 (-108 dB) ; ailleurs écart <= 2,5e-6 de la crête ; codec et USB à moins de -100 dBFS de la base.
  Durée (Mac, un cœur) : 2 à 3 min par scénario de 400 blocs, 10 min pour « silence », 25 à 30 min en tout.

    python3 tools/emu/test_os_optimise.py --cycles model-cycles_OS1.13.syx \
        [--scenario defaut,envois,dist,glissements,arret,silence] [--blocks N] [--no-gels] \
        [--with 6ch-usbup,arp,trig-hold,tempo-max,… --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import math
import pathlib
import sys
import time

import numpy as np
from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gels_checks as G             # noqa: E402
import outrig                       # noqa: E402
import seqrig                       # noqa: E402
import test_sdvintage as T          # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TWEAK = DEV / "70-os-optimise.json"
BASE = build.BASE
P1_STALE = (0x8000bc98, 0x8000bd98)      # sortie du saturateur, non réécrite quand il est sauté (lue x 0)
IDLE_N = 64
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def db(x, ref=2 ** 31):
    return -math.inf if x == 0 else 20 * math.log10(x / ref)


def code_regions(tweaks):
    """[(va, taille)] du code que les tweaks ajoutent hors du code de l'OS (masques, caves) : EMAC à intercepter."""
    out = []
    for t in tweaks:
        for w in t["writes"]:
            va, n = w["off"] + BASE, len(w["new"]) // 2
            if va >= 0x40100000 and n >= 16:
                out.append((va, n))
    return out


class Bench:
    """Un banc de sortie et ce qu'on y compte : passages par les chemins courts du tweak."""

    def __init__(self, img, extra, sym=None):
        self.r = outrig.OutRig(img, extra_code=extra)
        self.uc = self.r.uc
        self.sym = sym
        self.n = {}
        if sym:
            for name, key in (("saturateur sauté", "vd_hit"), ("delay endormi", "dz_sleep"),
                              ("reverb endormie", "rz_slept"), ("envoi sauté", "zero_out"),
                              ("PUNCH chemin court", "p_short"), ("PUNCH chemin d'origine", "p_orig")):
                self.n[name] = 0
                a = sym[key]
                self.uc.hook_add(UC_HOOK_CODE, lambda *x, k=name: self._inc(k), begin=a, end=a)

    def _inc(self, k):
        self.n[k] += 1

    def quiet(self):
        return list(self.uc.mem_read(self.sym["QUIET"], 6)) if self.sym else [0] * 6


class Mem:
    """Mémoire comparable de deux bancs : régions mappées sauf pile (0x9000xxxx), périphériques, alias 0x4a, octets
    d'image qui diffèrent entre les deux images, masques où le tweak a son code et ses variables, P1_STALE."""

    def __init__(self, a, b, imga, imgb, regions):
        self.a, self.b, self.regions_ = a, b, regions
        n = min(len(imga), len(imgb))
        self.diffva = np.flatnonzero(np.frombuffer(imga[:n], np.uint8) != np.frombuffer(imgb[:n], np.uint8)) + BASE

    def _regions(self, uc):
        return [(beg, end + 1) for beg, end, _ in uc.mem_regions()
                if not (beg >= 0xfc000000 or 0x90000000 <= beg < 0x91000000 or 0x4a000000 <= beg < 0x4b000000)]

    def _masked(self, uc, beg, end):
        m = np.frombuffer(bytes(uc.mem_read(beg, end - beg)), np.uint8).copy()
        m[self.diffva[(self.diffva >= beg) & (self.diffva < end)] - beg] = 0
        for va, n in self.regions_ + [(P1_STALE[0], P1_STALE[1] - P1_STALE[0])]:
            lo, hi = max(va, beg), min(va + n, end)
            if lo < hi:
                m[lo - beg:hi - beg] = 0
        return m

    def compare_all(self):
        ra, rb = self._regions(self.a.uc), self._regions(self.b.uc)
        if ra != rb:
            return [("régions", ra, rb)]
        bad = []
        for beg, end in ra:
            d = np.flatnonzero(self._masked(self.a.uc, beg, end) != self._masked(self.b.uc, beg, end))
            if len(d):
                bad.append((hex(beg), len(d), [hex(beg + int(i)) for i in d[:6]]))
        return bad

    @staticmethod
    def sram(bench):
        s = np.frombuffer(bytes(bench.uc.mem_read(0x80000000, 0x20000)), np.uint8).copy()
        s[P1_STALE[0] - 0x80000000:P1_STALE[1] - 0x80000000] = 0
        return s


def setup(bench, sc):
    for t in range(6):
        if "sends" in sc:
            bench.r.param(t, 20, sc["sends"][0])
            bench.r.param(t, 21, sc["sends"][1])
        if "dist" in sc:
            bench.r.param(t, 19, sc["dist"][t])
        if "decay" in sc:
            bench.r.param(t, 18, sc["decay"])
        for k, v in sc.get("kset", {}).items():
            bench.r.param(t, k, v)


def glisse(bench, k):
    if k % 100:
        return
    ph = k // 100
    if ph == 1:
        bench.r.target(2, 20, 40)
        bench.r.target(0, 19, 90)
    elif ph == 2:
        bench.r.target(1, 21, 50)
        bench.r.target(4, 21, 50)
    elif ph == 3:
        for t in range(6):
            bench.r.target(t, 20, 0)
            bench.r.target(t, 21, 0)
        bench.r.target(0, 19, 60)


SCEN = {
    "defaut": dict(kind="exact", blocks=400),
    "envois": dict(kind="exact", blocks=400, sends=(40, 40)),
    "dist": dict(kind="exact", blocks=400, dist=(100, 100, 100, 80, 80, 80)),
    "glissements": dict(kind="exact", blocks=400, every=40, glisse=True),
    "filtre": dict(kind="exact", blocks=400, sends=(30, 30), kset={28: 40, 29: 80}, optional=True),
    "arret": dict(kind="arret", blocks=800),
    "silence": dict(kind="tol", blocks=1950, decay=20, trigs=(100, 1750)),
}


def run_exact(name, sc, ctx):
    B = {"base": Bench(ctx["base"], ctx["extra"]), "opt": Bench(ctx["opt"], ctx["extra"], ctx["sym"])}
    for b in B.values():
        setup(b, sc)
    pats = {k: outrig.Pattern(b.r, every=sc.get("every")) for k, b in B.items()}
    mem = Mem(B["base"], B["opt"], ctx["base"], ctx["opt"], ctx["regions"])
    first, peaks, nfull, quiet_max, trigs, first_sound = None, dict(ring=0, usb=0), 0, 0, 0, None
    for k in range(sc["blocks"]):
        info = {}
        for n, b in B.items():
            if sc.get("glisse"):
                glisse(b, k)
            pats[n].tick()
            info[n] = b.r.block()
        ia, ib = info["base"], info["opt"]
        trigs += bin(ia["trig"] & 0x3f).count("1")
        if first_sound is None and np.any(ia["out"]):
            first_sound = k
        peaks["ring"] = max(peaks["ring"], int(np.abs(ia["ring"]).max()))
        peaks["usb"] = max(peaks["usb"], int(np.abs(ia["usb"]).max()))
        quiet_max = max(quiet_max, max(B["opt"].quiet()))
        full = k % 10 == 9 or k == sc["blocks"] - 1
        nfull += full
        if first is None:
            why = [w for w, ok in (
                ("anneau du codec", np.array_equal(ia["ring"], ib["ring"])),
                ("USB", np.array_equal(ia["usb"], ib["usb"])),
                ("voix", np.array_equal(ia["out"], ib["out"])),
                ("SRAM", np.array_equal(Mem.sram(B["base"]), Mem.sram(B["opt"]))),
                ("EMAC", B["base"].r.emac_state() == B["opt"].r.emac_state()),
                ("lignes delay/reverb", B["base"].r.lines() == B["opt"].r.lines())) if not ok]
            if not why and full:
                bad = mem.compare_all()
                if bad:
                    why = [f"mémoire {bad[:3]}"]
            if why:
                first = (k, why)
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    print(f"  {sc['blocks']} blocs, {trigs} trigs ; crêtes : anneau {peaks['ring']}, USB {peaks['usb']} ; mémoire "
          f"entière comparée {nfull} fois ; compteur de blocs faibles des voix <= {quiet_max} (arrêt à {IDLE_N})")
    print("  chemins courts (optimisé) : " + ", ".join(f"{k} {v}" for k, v in B["opt"].n.items()))
    check(first is None, f"{name} : base = optimisé sur {sc['blocks']} blocs (anneau, USB, 6 voix, SRAM, EMAC, lignes "
          "à chaque bloc ; toute la mémoire tous les 10 blocs)" +
          ("" if first is None else f" — premier écart au bloc {first[0]} : {first[1]}"))
    check(peaks["ring"] > 0 and peaks["usb"] > 0, f"{name} : il y a du son (crête de l'anneau {peaks['ring']})")
    check(quiet_max < IDLE_N, f"{name} : aucune voix arrêtée (compteur <= {quiet_max} < {IDLE_N}) : cas exact")
    hz = B["opt"].n
    if "sends" in sc:
        check(np.count_nonzero(np.frombuffer(B["base"].r.lines(), np.uint8)) > 0 and
              hz["delay endormi"] <= first_sound and hz["reverb endormie"] <= first_sound,
              f"{name} : delay et reverb reçoivent du son ; endormis seulement avant le 1er son des voix (bloc "
              f"{first_sound}) : delay {hz['delay endormi']}, reverb {hz['reverb endormie']} blocs")
    elif not sc.get("glisse"):
        check(hz["delay endormi"] == hz["reverb endormie"] == sc["blocks"] and hz["envoi sauté"] > 0,
              f"{name} : envois à 0 : delay et reverb endormis à chaque bloc ({hz['delay endormi']}, "
              f"{hz['reverb endormie']}), envois sautés ({hz['envoi sauté']})")
    if "dist" in sc:
        check(hz["saturateur sauté"] == 0, f"{name} : Dist en service : saturateur calculé ({hz['saturateur sauté']} "
              "sauts)")
    elif not sc.get("glisse"):
        check(hz["saturateur sauté"] == 3 * sc["blocks"], f"{name} : VOL+DIST à 60 : saturateur sauté pour les 3 "
              f"paires à chaque bloc ({hz['saturateur sauté']})")
    check(hz["PUNCH chemin court"] > 0, f"{name} : PUNCH à 0 : chemin court pris ({hz['PUNCH chemin court']} fois)")


def run_arret(name, sc, ctx):
    B = {"base": Bench(ctx["base"], ctx["extra"]), "opt": Bench(ctx["opt"], ctx["extra"], ctx["sym"])}
    same = dict(ring=True, usb=True, out=True, lines=True)
    zero = True
    pages = set()
    for k in range(sc["blocks"]):
        a, b = B["base"].r.block(), B["opt"].r.block()
        same["ring"] &= np.array_equal(a["ring"], b["ring"])
        same["usb"] &= np.array_equal(a["usb"], b["usb"])
        same["out"] &= np.array_equal(a["out"], b["out"])
        if k % 10 == 9:
            same["lines"] &= B["base"].r.lines() == B["opt"].r.lines()
        zero &= not (np.any(a["ring"]) or np.any(a["usb"]) or np.any(a["out"]))
        pages |= set((np.flatnonzero(Mem.sram(B["base"]) != Mem.sram(B["opt"])) & ~0xff).tolist())
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    stopped = B["opt"].quiet()
    print(f"  SRAM base/optimisé : écarts dans {len(pages)} pages de 256 o "
          f"{[hex(0x80000000 + p) for p in sorted(pages)[:12]]} (états des voix et des effets qu'on ne calcule plus)")
    print("  chemins courts (optimisé) : " + ", ".join(f"{k} {v}" for k, v in B["opt"].n.items()))
    check(all(same.values()), f"{name} : base = optimisé pour l'anneau du codec, l'USB, la sortie des 6 voix et les "
          f"lignes delay/reverb sur {sc['blocks']} blocs ({same})")
    check(zero, f"{name} : à l'arrêt, codec, USB et voix valent exactement 0 (base, donc aussi optimisé)")
    if sc["blocks"] > IDLE_N:
        check(all(q >= IDLE_N for q in stopped), f"{name} : les 6 voix sont arrêtées (compteurs {stopped})")


def run_tol(name, sc, ctx):
    B = {"base": Bench(ctx["base"], ctx["extra"]), "opt": Bench(ctx["opt"], ctx["extra"], ctx["sym"])}
    for b in B.values():
        setup(b, sc)
        for t in range(6):
            b.r.rig.set_step(t, 0, vel=100, length=seqrig.LEN_1_16)
    outs, rings, usbs, stopped = {n: [] for n in B}, {n: [] for n in B}, {n: [] for n in B}, []
    for k in range(sc["blocks"]):
        for n, b in B.items():
            if k + 1 in sc["trigs"]:
                for t in range(6):
                    b.r.rig.schedule_step(t, 0, b.r.rig.now + b.r.rig.blk)
            info = b.r.block()
            outs[n].append(info["out"])
            rings[n].append(info["ring"])
            usbs[n].append(info["usb"])
        stopped.append([q >= IDLE_N for q in B["opt"].quiet()])
        if k % 100 == 99:
            print(f"    … bloc {k + 1}", flush=True)
    R, O = np.array(outs["base"]), np.array(outs["opt"])                 # blocs x 6 x 32
    st = np.array(stopped)
    t1, t2 = sc["trigs"]
    peak = np.abs(R).max(axis=(0, 2))
    eq = np.all(R == O, axis=2)
    z = ~eq & np.all(O == 0, axis=2)                                      # optimisé à 0, base pas tout à fait
    worst_zero = int(np.abs(R).max(axis=2)[z].max()) if z.any() else 0
    other = ~eq & ~np.all(O == 0, axis=2)                                 # voix recalculée après un arrêt
    rel = np.abs(R - O).max(axis=2) / np.maximum(peak, 1)[None, :]
    worst_rel = float(rel[other].max()) if other.any() else 0.0
    stop_at = [int(np.argmax(st[t1:, t])) + t1 if st[t1:, t].any() else None for t in range(6)]
    print(f"  crêtes des voix (base) : {peak.tolist()} ; arrêt de chaque voix après le trig du bloc {t1} : {stop_at}")
    print(f"  blocs-pistes : {eq.size} ; identiques {int(eq.sum())} ; optimisé à 0 {int(z.sum())} ; "
          f"autres écarts {int(other.sum())}")
    check(all(s is not None and s < t2 for s in stop_at),
          f"{name} : les 6 voix (DECAY 20) s'arrêtent avant le retrig du bloc {t2}")
    check(bool(np.all(eq[:t1]) and eq[t1:t1 + IDLE_N].all()),
          f"{name} : identique avant le 1er trig et pendant les {IDLE_N} blocs qui le suivent (1re note après un arrêt "
          "au démarrage)")
    check(worst_zero < 4096, f"{name} : voix arrêtée : 0 là où la base sort au plus {worst_zero} après la division "
          f"par 2 ({db(worst_zero, 2 ** 30):.1f} dB de la pleine échelle ; seuil 4 096 = {db(4096, 2 ** 30):.1f} dB)")
    check(worst_rel <= 2.5e-6, f"{name} : voix recalculée après un arrêt (retrig du bloc {t2}) : écart <= "
          f"{worst_rel:.2e} de la crête ({db(worst_rel, 1):.1f} dB ; limite 2,5e-6 = -112 dB)")
    Rr, Or, Ru, Ou = (np.array(x) for x in (rings["base"], rings["opt"], usbs["base"], usbs["opt"]))
    dr, du = int(np.abs(Rr - Or).max()), int(np.abs(Ru - Ou).max())
    check(db(dr, 2 ** 23) < -100 and db(du) < -100, f"{name} : codec et USB à moins de -100 dBFS de la base "
          f"({db(dr, 2 ** 23):.1f} et {db(du):.1f} dBFS)")


def writes_tests(stock, tweak, others, base, opt):
    print("écritures")
    by_off = {w["off"]: w for w in tweak["writes"]}
    for va, old, new in G.D1 + (G.D2,):
        w = by_off.get(va - BASE)
        check(w is not None and w["old"] == old and w["new"] == new and stock[va - BASE:va - BASE + 2].hex() == old,
              f"{va:#x} : {old} -> {new}")
    sym = {k: int(v, 16) for k, v in tweak["symbols"].items()}
    hooks = {0x40057062: "vd_check", 0x40057516: "dz_check", 0x40057ac8: "rz_check", 0x40057dc6: "rz_mod",
             0x40056716: "s6_check", 0x40056698: "s7_check", 0x400a7dfe: "gate", 0x400a7e24: "after"}
    ok = all(opt[va - BASE:va - BASE + 6] == b"\x4e\xf9" + sym[s].to_bytes(4, "big") for va, s in hooks.items())
    check(ok, f"détours : jmp vers {', '.join(hooks.values())}")
    check(all(build.apply_writes(stock, [t])[0] for t in others + [tweak]),
          f"octets d'origine : le tweak seul et {len(others)} autre(s) mod(s) s'appliquent sur l'OS officiel")
    diff = np.flatnonzero(np.frombuffer(base, np.uint8) != np.frombuffer(opt, np.uint8))
    spans = [(w["off"], w["off"] + len(w["new"]) // 2) for w in tweak["writes"]]
    check(all(any(lo <= d < hi for lo, hi in spans) for d in diff.tolist()),
          f"base -> optimisé : {len(diff)} octets changés, tous dans les écritures du tweak")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="", help="autres tweaks appliqués avant (ex. 6ch-usbup,arp)")
    ap.add_argument("--syntakt", help="Syntakt_OS1.42.syx (ou 1.41), si un mod de --with en a besoin")
    ap.add_argument("--scenario", default=",".join(k for k, v in SCEN.items() if not v.get("optional")),
                    help="scénarios, séparés par des virgules (filtre : seulement avec track-filter)")
    ap.add_argument("--blocks", type=int, help="essai rapide : moins de blocs par scénario")
    ap.add_argument("--no-gels", action="store_true", help="sans les preuves D1 et D2")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    by_id = {json.loads(f.read_text(encoding="utf-8"))["id"]: f for f in DEV.glob("*.json") if f.name != "device.json"}
    others = [json.loads(by_id[i].read_text(encoding="utf-8")) for i in args.others.split(",") if i]
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    build.check_conflicts(others + [tweak])
    pl, _ = build.build_payload(others, stock, args.syntakt)
    base = build.apply_writes(stock, others)[0] + pl
    opt = build.apply_writes(stock, others + [tweak])[0] + pl
    print(f"firmware : {', '.join(t['id'] for t in others + [tweak])}")
    writes_tests(stock, tweak, others, base, opt)
    if not args.no_gels:
        print("gels")
        G.d1(base, opt, check)
        G.d2(base, opt, check)
    ctx = dict(base=base, opt=opt, sym={k: int(v, 16) for k, v in tweak["symbols"].items()},
               extra=code_regions(others + [tweak]), regions=code_regions([tweak]))
    for name in [s for s in args.scenario.split(",") if s]:
        sc = dict(SCEN[name])
        if args.blocks:
            sc["blocks"] = args.blocks
            if "trigs" in sc:
                sc["trigs"] = tuple(min(t, args.blocks - 50) for t in sc["trigs"])
        print(f"scénario {name} ({sc['blocks']} blocs)")
        t0 = time.time()
        {"exact": run_exact, "arret": run_arret, "tol": run_tol}[sc["kind"]](name, sc, ctx)
        print(f"  ({time.time() - t0:.0f} s)")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
