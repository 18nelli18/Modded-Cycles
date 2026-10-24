#!/usr/bin/env python3
"""Inventaire du code exécuté par l'interruption audio du Modded Cycles OS (notes/76, chantier 2 : le code chaud en
SRAM) : pour chaque poste et chaque machine, les lignes de 16 o de code exécutées à chaque bloc (ce que le cache
d'instructions de 8 Ko doit recharger quand il est froid), et où elles sont (OS, masques des mods, Model-TG, charge
utile, SRAM).

Banc : osbanc.OsBanc (le vrai code, étage de sortie compris). Les postes sont délimités par les appels de la fonction
audio (ceux du firmware de mesure, notes/75) ; dans la boucle des voix, chaque piste va de son passage en 0x400a7dfe
(le détour de la boucle : Model-TG, la passerelle) au suivant.

    python3 tools/emu/inventory_code.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--json out]
"""
import argparse
import collections
import contextlib
import io
import json
import pathlib
import struct
import sys

from unicorn import UC_HOOK_CODE

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_mesure as G              # noqa: E402
import mcengine as E                # noqa: E402
import osbanc as O                  # noqa: E402
import seqrig as S                  # noqa: E402
import sprites                      # noqa: E402
import syntakt                      # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_mesure as T             # noqa: E402
import test_modal as tmo            # noqa: E402

VOICE_LOOP, DISPATCH = 0x400a7d4a, 0x400a7dfe
# appels de la fonction audio (site, nom du poste) : comme le firmware de mesure
STAGES = {0x400597a8: "smooth", 0x400597b4: "velmod", 0x400597c6: "lfo", 0x4005981e: "voices",
          0x4005982a: "tgpost", 0x40059840: "gains", 0x40059852: "dist", 0x4005985c: "misc", 0x40059872: "out"}
NAMES = ["KICK", "SNARE", "METAL", "PERC", "TONE", "CHORD", "Sampler", "SDVtg", "CPVtg", "SYToy", "SYBit", "SYSwm",
         "MACRO", "ACID", "MODAL"]


def region(a, masks):
    if 0x80000000 <= a < 0x80010000:
        return "sram"
    if 0x401ab750 <= a < 0x401bf8c0:
        return "tg"
    if 0x46700000 <= a < 0x46800000:
        return "payload"
    if any(m <= a < m + n for m, n in masks):
        return "mods"
    return "os"


class Tracer:
    """Lignes exécutées par poste, bloc par bloc."""

    def __init__(self, b, masks):
        self.b, self.uc, self.masks = b, b.uc, masks
        self.stage, self.stack, self.track, self.lines = "head", [], -1, collections.defaultdict(set)
        self.count = collections.Counter()
        self.seq, self.last = [], None                  # lignes dans l'ordre d'exécution (chaque changement)
        self.ret = {}                                   # adresse de retour d'un appel de poste -> poste précédent
        self.uc.hook_add(UC_HOOK_CODE, self._code)

    def _code(self, uc, addr, size, ud):
        st = self.stage
        if addr in STAGES:
            self.ret[addr + 6] = True
            st = self.stage = STAGES[addr]
        elif addr in self.ret:                          # retour d'un poste : le corps de la fonction audio
            del self.ret[addr]
            st = self.stage = "fn"
        elif addr == O.AUDIO_CALL:
            st = self.stage = "fn"
        elif addr == O.AFTER_CALL:
            st = self.stage = "tail"
        elif addr == VOICE_LOOP:
            self.track = -1
        elif addr == DISPATCH:
            self.track += 1
            m = struct.unpack(">I", uc.mem_read(S.VOICE0 + S.VSTRIDE * self.track, 4))[0]
            st = self.stage = f"voice:{self.track}:{NAMES[m] if m < len(NAMES) else m}"
        line = addr >> 4
        self.lines[st].add(line)
        self.count[st] += 1
        if line != self.last:
            self.seq.append(line)
            self.last = line

    def block(self):
        self.stage, self.track = "head", -1
        self.lines.clear()
        self.count.clear()
        self.ret.clear()
        self.seq, self.last = [], None
        self.b.block()
        out = {}
        for st, ls in self.lines.items():
            by = collections.Counter(region(l << 4, self.masks) for l in ls)
            out[st] = dict(lines=len(ls), instr=self.count[st], where=dict(by), set=ls)
        out["_seq"] = self.seq
        return out


def scenario(fw, machines, params=None, blocks=24, every=6):
    """6 pistes (machines), un trig sur chacune tous les `every` blocs ; rend les relevés des blocs 8.."""
    b = O.OsBanc(fw)
    for t, m in enumerate(machines):
        b.rig.param(t, E.SLOT["machine"], m * 256)
        for k, v in (params or {}).get(t, {}).items():
            b.rig.param(t, E.SLOT[k], v * 256)
    tr = Tracer(b, fw_masks(fw))
    res = []
    for k in range(blocks):
        if k % every == 2:
            for t in range(6):
                b.rig.set_step(t, 0, vel=100, length=S.LEN_1_16)
                b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk // 2)
        r = tr.block()
        if k >= 8:
            res.append(r)
    return res


def fw_masks(fw):
    return [(va, info[0]) for va, info in sprites.MASKS.items()
            if fw.img[va - G.BASE:va - G.BASE + 8] != b"\xff" * 8]


class ICache:
    """Cache d'instructions du ColdFire V4 : 8 Ko, 4 voies, lignes de 16 o (128 ensembles) ; une ligne absente prend
    la voie libre la plus basse, sinon celle du compteur tournant, qui avance (MCF5441x RM §6.3.1, CACR IHLCK). Le
    code en SRAM y passe aussi : le bootstrap y masque les accès au code (RAMBAR 0x80000235, notes/75 §1.2) ; ses
    défauts sont comptés à part (lus par la porte arrière de la SRAM, pas en DDR2). sram : lignes de la SDRAM
    comptées comme si elles étaient en SRAM (budget)."""

    def __init__(self, sets=128, ways=4):
        self.sets, self.ways = sets, ways
        self.clear()

    def clear(self):
        self.s = [[None] * self.ways for _ in range(self.sets)]
        self.rr = 0

    def run(self, seq, sram=frozenset(), per=None):
        """Défauts (en SDRAM, en SRAM)."""
        sd = sr = 0
        for line in seq:
            w = self.s[line & (self.sets - 1)]
            if line in w:
                continue
            if (line >> 24) == 0x8 or line in sram:          # en SRAM (0x8xxxxxxx >> 4 : le haut est 0x8)
                sr += 1
            else:
                sd += 1
                if per is not None:
                    per[line] += 1
            if None in w:
                w[w.index(None)] = line
            else:
                w[self.rr] = line
                self.rr = (self.rr + 1) % self.ways
        return sd, sr


def misses(res, sram=frozenset(), split=False):
    """Défauts par bloc : cache vidé à chaque bloc (l'interface le chasse), et cache gardé d'un bloc à l'autre ; en
    SDRAM seulement, ou (split) ((SDRAM, SRAM) vidé, (SDRAM, SRAM) gardé)."""
    cold, warm, c = [], [], ICache()
    for r in res:
        c.clear()
        cold.append(c.run(r["_seq"], sram))
    c.clear()
    for r in res:
        warm.append(c.run(r["_seq"], sram))
    avg = lambda xs: (sum(x[0] for x in xs) / len(xs), sum(x[1] for x in xs) / len(xs))
    co, wa = avg(cold), avg(warm[2:])
    return (co, wa) if split else (co[0], wa[0])


def per_line(res):
    """Défauts par ligne de code, par bloc (cache vidé à chaque bloc)."""
    per, c = collections.Counter(), ICache()
    for r in res:
        c.clear()
        c.run(r["_seq"], per=per)
    return {k: v / len(res) for k, v in per.items()}


def budget(res, sizes=(2, 4, 8, 12, 16, 24, 30)):
    """Si les lignes les plus manquées allaient en SRAM (ligne à ligne : la borne haute) : défauts restants par bloc
    pour chaque taille de SRAM (Ko)."""
    per = per_line(res)
    order = sorted(per, key=lambda l: -per[l])
    out = {}
    for kb in sizes:
        n = kb * 1024 // 16
        out[kb] = misses(res, frozenset(order[:n]))[0]
    return out


def summary(res):
    """Par poste : lignes par bloc (moyenne), lignes de l'union des blocs, instructions par bloc, où."""
    agg = collections.defaultdict(lambda: dict(lines=0, instr=0, n=0, union=set(), where=collections.Counter()))
    for r in res:
        for st, d in r.items():
            if st == "_seq":
                continue
            key = st if not st.startswith("voice:") else "voice:" + st.split(":")[2]
            a = agg[key]
            a["lines"] += d["lines"]
            a["instr"] += d["instr"]
            a["n"] += 1
            a["union"] |= d["set"]
            a["where"].update(d["where"])
    out = {}
    for k, a in agg.items():
        out[k] = dict(lines=a["lines"] / a["n"], instr=a["instr"] / a["n"], union=len(a["union"]),
                      where={w: round(c / a["n"], 1) for w, c in a["where"].items()}, lineset=sorted(a["union"]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--json", help="écrit l'inventaire (ensembles de lignes compris)")
    args = ap.parse_args()
    stock = T.stock_of(args.cycles)
    ctx = dict(syntakt=args.syntakt, st_img=syntakt.dsp_image(args.syntakt), chord=tmx.chord_tables(stock))
    with contextlib.redirect_stdout(io.StringIO()):
        fw = tmo.Fw(stock, G.os_tweaks(), ctx)
    scen = {
        "origine": ((0, 1, 2, 3, 4, 5), None),
        "ajoutees": ((7, 8, 9, 10, 11, 6), None),
        "nos-machines": ((12, 13, 14, 12, 14, 14), {0: dict(shape=0), 3: dict(shape=25), 4: dict(shape=1),
                                                    5: dict(shape=2)}),
        "macro-modeles": ((12, 12, 12, 12, 12, 12), {t: dict(shape=s) for t, s in enumerate((5, 12, 20, 30, 38, 44))}),
    }
    out = {}
    for name, (mach, params) in scen.items():
        res = scenario(fw, mach, params)
        out[name] = summary(res)
        distinct = sum(len(set(r["_seq"])) for r in res) / len(res)
        cold, warm = misses(res)
        out[name]["_misses"] = dict(distinct=distinct, cold=cold, warm=warm, budget=budget(res))
        out[name]["_perline"] = {str(k): v for k, v in per_line(res).items()}
        print(f"\n== {name} ({', '.join(NAMES[m] for m in mach)}) : {distinct:.0f} lignes distinctes par bloc "
              f"({distinct * 16 / 1024:.1f} Ko) ; défauts du cache d'instructions par bloc : {cold:.0f} cache vidé, "
              f"{warm:.0f} cache gardé")
        print("  si les lignes les plus manquées étaient en SRAM (Ko : défauts restants) :",
              ", ".join(f"{kb} : {m:.0f}" for kb, m in out[name]["_misses"]["budget"].items()))
        for k, d in sorted(((k, d) for k, d in out[name].items() if not k.startswith("_")),
                           key=lambda kv: -kv[1]["lines"]):
            print(f"  {k:16s} {d['lines']:6.0f} lignes/bloc  {d['union']:6d} en tout  {d['instr']:8.0f} instr  {d['where']}")
    if args.json:
        pathlib.Path(args.json).write_text(json.dumps(out))


if __name__ == "__main__":
    main()
