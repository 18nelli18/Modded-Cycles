#!/usr/bin/env python3
"""Preuve de Wave avec MACRO, ACID et les moteurs du Syntakt (notes/62, tools/gen_wave_combos.py) : 25-macro-wave,
26-acid-wave, 25-macro-acid-wave et 24-syntakt-<moteurs>[-macro][-acid]-wave. Le vrai code de l'OS, émulé (Unicorn).

Références, construites ici : Wave seule (36-wavetable.json) et la même combinaison sans Wave (25-macro, 26-acid,
25-macro-acid, 24-syntakt-<moteurs>[-macro][-acid]).

  1. Démarrage : le crochet reconstitue la charge utile (en clair par morceaux, ou décompressée avec les moteurs),
     pile et registres intacts ; elle est celle de la combinaison sans Wave, sauf ce qui compte les machines et la
     place de Wave (WAVE_AT..), octet pour octet : les moteurs, MACRO et ACID ne changent pas.
  2. Interface : les vérifications de test_syntakt_machines.py pour toutes les machines ajoutées, Wave comprise
     (jusqu'à 14 machines : rangées déplacées, gs.ROWS8).
  3. Notre code au numéro de Wave dans cette combinaison : chargeur, YES, table retenue, identité Transfer
     (test_wavetable.py).
  4. Son, la boucle des voix seule (mcengine) : la piste Wave identique à Wave seule ; les autres pistes (KICK, moteur
     ou SNARE, MACRO ou TONE, ACID ou CHORD) identiques à la combinaison sans Wave ; avec les moteurs, à l'arrêt
     d'une voix muette par le régulateur près.

    python3 tools/emu/test_wave_combos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        [--engines sd,cp,toy,bits,swarm | --engines none] [--macro yes|no|both] [--acid yes|no|both]

Sans --engines : un échantillon (MACRO, ACID et les deux sans moteurs ; SD seul ; les 5 moteurs avec MACRO et ACID).
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import fenv_ui                      # noqa: E402
import gen_macro as gm              # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import gen_wave_combos as gwc       # noqa: E402
import gen_wavetable as gw          # noqa: E402
import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_acid as ta              # noqa: E402
import test_acid_combos as tac      # noqa: E402
import test_macro as tm             # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_wavetable as tw         # noqa: E402

BASE = E.BASE
DEV = gs.DEV
check = t7.check
KINDS = (("macro", "macro"), ("acid", "acid"), ("wt", "wt"))      # vue, préfixe des symboles


def load(tid):
    return json.loads(next(DEV.glob(f"[0-9][0-9]-{tid}.json")).read_text(encoding="utf-8"))


def engines_of(t):
    return [c for c in t["id"].split("-") if c in gs.CATALOG and c not in ("macro", "acid", "wt")]


class Fw:
    """Un firmware avec une seule charge utile (la combinaison) : comme test_acid_combos.Fw, avec la vue de Wave
    (« wt ») en plus de MACRO et ACID ; l'EMAC posé aussi sur le code de Wave."""

    def __init__(self, stock, tweaks, ctx):
        p, _ = build.apply_writes(stock, tweaks)
        pl, _ = build.build_payload(tweaks, stock, ctx["syntakt"])
        self.stock, self.img, self.tweaks, self.packed = stock, bytes(p) + pl, tweaks, len(pl)
        self.blob_end, self.keep, self.views, self.emac, self.gov_skip = None, [], {}, (), False
        t = self.mine = next(t for t in tweaks if t.get("append"))
        ap_ = t["append"]
        dest = self.dest = self.pay = int(ap_["dest"], 16)
        rt = bytearray(build.payload_runtime(t, stock, ctx["st_img"]))
        if ap_.get("compress"):
            self.chord_at = tmx.chord_at(t, ctx)
            rt[self.chord_at - dest:self.chord_at - dest + len(ctx["chord"])] = ctx["chord"]
        self.runtime = bytes(rt)
        self.payload = (dest, self.runtime)
        self.sym = syms = {k: int(v, 16) for k, v in t.get("symbols", {}).items()}
        self.codes = engines_of(t)
        kinds = [(k, p_) for k, p_ in KINDS if p_ + "_update" in syms]
        self.nm = 6 + len(self.codes) + len(kinds)
        data = dest + gs.LAYOUT["DATA"]
        u32 = lambda va: struct.unpack_from(">I", self.runtime, va - dest)[0]
        for i, (k, p_) in enumerate(kinds):
            index = 6 + len(self.codes) + i
            upd, rnd = u32(data + 4 * self.nm + 4 * index), u32(data + 8 * self.nm + 4 * index)
            check(upd == syms[p_ + "_update"] and rnd == syms[p_ + "_render"],
                  f"{t['id']} : la table des machines appelle {p_}_update et {p_}_render (machine {index + 1})")
            part = next(q for q in ap_["parts"] if "hex" in q
                        and int(q["dest"], 16) <= upd < int(q["dest"], 16) + len(q["hex"]) // 2)
            pay = int(part["dest"], 16)
            end = pay + len(part["hex"]) // 2
            if k == "wt":                       # le moteur, puis notre code (morceau suivant)
                glue = next(q for q in ap_["parts"] if "hex" in q and int(q["dest"], 16) >= end)
                end = int(glue["dest"], 16) + len(glue["hex"]) // 2
            self.views[k] = tac.View(self, index=index, pay=pay, code_end=end, upd=upd, rnd=rnd,
                                     braids_render=syms.get("braids_render"))
        self.emac = tuple((v.pay, v.code_end) for k, v in self.views.items() if k in ("acid", "wt"))
        self.gov_skip = "acid" in self.views
        self.index = self.views["wt"].index

    engine = tac.Fw.engine
    view = tac.Fw.view

    def boot(self):
        """La mémoire après le démarrage (charge utile en place, tampons des tables mappés), pour les essais de notre
        code (test_wavetable) ; le crochet lui-même est vérifié par boot_check."""
        uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(0x40000000, 0x02400000)
        uc.mem_write(BASE, self.img)
        uc.mem_map(self.dest, 0x00100000)
        uc.mem_write(self.dest, self.runtime)
        uc.mem_map(tw.BUF, 0x02000000)
        uc.mem_map(0x80000000, 0x00010000)
        sram = bytearray(0x10000)
        for lo, hi, d in gs.CY_SRAM_INIT:
            sram[d - 0x80000000:d - 0x80000000 + hi - lo] = self.img[lo - BASE:hi - BASE]
        uc.mem_write(0x80000000, bytes(sram))
        uc.mem_map(0x90000000, 0x00020000)
        uc.mem_write(E.STOP, b"\x4e\x71\x4e\x71")
        return uc


# --- 1. démarrage ------------------------------------------------------------------------------------------------
def boot_check(fw, ref, below=0):
    """below : décalage sous lequel la charge utile n'est pas comparée (ACID et Wave sans MACRO : la référence est
    macro-acid, ACID à la même place, MACRO dessous)."""
    gs.set_base(fw.dest)
    n = len(fw.codes) + len(fw.views)
    wave = (gwc.WAVE_AT, gwc.WAVE_BSS + 0x1000)
    allowed = tac.machine_window(n, fw.nm) + [wave] + ([(0, below)] if below else [])
    if fw.mine["append"].get("compress"):
        tmx.boot(fw, ref, None, allowed)
    else:
        ta.boot(fw, None)
        rref = ref.runtime
        diff = [k for k in range(0, min(len(rref), len(fw.runtime)), 4) if rref[k:k + 4] != fw.runtime[k:k + 4]]
        off = [k for k in diff if not any(lo <= k < hi for lo, hi in allowed)]
        check(not off, f"charge utile identique à {ref.mine['id']} ({len(rref)} o), sauf ce qui compte les machines et "
                       f"la place de Wave {[hex(fw.dest + k) for k in off[:4]]}")
    v = fw.views["wt"]
    low = max([fw.dest] + [x.code_end for k, x in fw.views.items() if k != "wt"])
    check(v.pay == fw.dest + gwc.WAVE_AT and v.code_end <= fw.dest + gwc.WAVE_BSS and v.pay >= low,
          f"Wave à {v.pay:#x}..{v.code_end:#x} (moteur et notre code), ses variables à {fw.dest + gwc.WAVE_BSS:#x}, "
          f"au-dessus des autres machines (machine {v.index + 1} sur {fw.nm})")


# --- 2. interface ------------------------------------------------------------------------------------------------
def interface(stock, fw):
    gs.CATALOG.setdefault("macro", dict(gm.MACHINE, label="MACRO"))
    gs.CATALOG.setdefault("acid", dict(tac.ga.MACHINE, label="ACID"))
    gs.CATALOG.setdefault("wt", dict(gw.MACHINE, label="Wave"))
    tac.interface(stock, fw, fw.mine, None, None)


# --- 3. notre code au numéro de Wave -----------------------------------------------------------------------------
def ours(fw, data):
    tw.MACH = fw.index
    print(f"  (Wave = machine {fw.index + 1})")
    uc = fw.boot()
    inode = 0x12345678
    handle, cont = tw.container(data, inode)
    log = tw.loader(uc, fw, 0, handle, cont, inode)
    count = struct.unpack(">i", uc.mem_read(fw.sym["wt_count"], 4))[0]
    check(("open", inode) in log and count == len(data) and tw.name_of(uc, 0) == "W%08X%06X" % (inode, 0x13579b),
          f"chargeur au pad : la table lue ({count} échantillons) et retenue dans le nom du son")
    tw.yes_tests(fw, data)
    tw.tick_tests(fw, data)
    tw.smp_tests(fw, fw.boot())


# --- 4. son ------------------------------------------------------------------------------------------------------
def set_wave(e, fw, t, data, machine, note, color):
    e.uc.mem_write(tw.BUF + 64 + tw.BUF_STRIDE * t, tw.pcm(data))
    e.uc.mem_write(fw.sym["wt_base"] + 4 * t, struct.pack(">i", tw.BUF + tw.BUF_STRIDE * t + 64))
    e.uc.mem_write(fw.sym["wt_count"] + 4 * t, struct.pack(">i", len(data)))
    e.set(t, machine=machine, note=note, color=color, shape=0, sweep=127, contour=0, punch=0, gate=0, finetune=64,
          decay=60)


def wave_engine(fw, solo=None):
    e = fw.engine(solo)
    S.ensure_map(e.uc, tw.BUF, 0x02000000)
    e.uc.mem_write(tw.BUF, b"\0" * 0x02000000)
    return e


def alone_wave(alone, t, data, note, color, blocks, trigs):
    e = tw.eng(alone)
    set_wave(e, alone, t, data, gw.WT_MACH, note, color)
    tw.solo_off(e, {t})
    return np.stack([e.block(trigs.get(b, 0))[t] for b in range(blocks)])


def sound(fw, ref, alone, data, label):
    governed = bool(fw.codes)
    trigs = {1: 0x3f, 150: 0x3f}
    macro, acid = fw.views.get("macro"), fw.views.get("acid")
    mach = [0, 6 if fw.codes else 1, macro.index if macro else ta.TONE, acid.index if acid else 5, fw.index, fw.index]
    kw = {t: dict(ta.KW, color=64, shape=64, decay=40, machine=m) for t, m in enumerate(mach[:4])}
    if fw.codes:
        c = gs.CATALOG[fw.codes[0]]
        kw[1].update(color=c["knobs"][0][2], shape=c["knobs"][1][2], sweep=c["knobs"][2][2], contour=c["knobs"][3][2])
    if macro:
        kw[2] = dict(tm.BASE_KW, shape=0, decay=40, machine=mach[2])     # CSAW : sans le générateur aléatoire
    if acid:
        kw[3] = dict(ta.KW, decay=40, machine=mach[3])
    waves = {4: (48, 64), 5: (36, 100)}

    e = wave_engine(fw)
    for t, k in kw.items():
        e.set(t, **k)
    for t, (note, color) in waves.items():
        set_wave(e, fw, t, data, fw.index, note, color)
    x = np.stack([e.block(trigs.get(b, 0)) for b in range(300)])
    r_e = ref.engine()
    for t, k in kw.items():
        r_e.set(t, **k)
    for t in waves:
        r_e.set(t, machine=tac.OFF)
    r = np.stack([r_e.block(trigs.get(b, 0) & 0x0f) for b in range(300)])
    ok, cut = not e.unmapped and not r_e.unmapped, []
    for t in range(4):
        good, f = tac.same(r[:, t], x[:, t], 150, governed)
        ok &= good and bool(x[:, t].any())
        cut.append(f)
    for t, (note, color) in waves.items():
        y = alone_wave(alone, t, data, note, color, 300, trigs)
        good, f = tac.same(y, x[:, t], 150, governed)
        ok &= good and bool(x[:, t].any())
        cut.append(f)
    names = ["KICK", "moteur" if fw.codes else "SNARE", "MACRO" if macro else "TONE", "ACID" if acid else "CHORD",
             "Wave", "Wave"]
    check(ok, f"{label} : pistes {', '.join(f'{n} ({m + 1})' for n, m in zip(names, mach))} ensemble ; les 4 "
              f"premières identiques à {ref.mine['id']}, les pistes Wave à Wave seule"
              f"{f' (arrêt d une voix muette : {cut})' if governed else ''}")

    e = wave_engine(fw, solo=4)                     # seule sur sa piste : exactement Wave seule
    set_wave(e, fw, 4, data, fw.index, 60, 30)
    x = np.stack([e.block(trigs.get(b, 0) & 0x10)[4] for b in range(200)])
    y = alone_wave(alone, 4, data, 60, 30, 200, {k: v & 0x10 for k, v in trigs.items()})
    good, f = tac.same(y, x, 150, governed)
    check(good and x.any() and not e.unmapped, f"{label} : Wave seule sur sa piste, identique à Wave seule"
                                               f"{f' (arrêt {f})' if governed and f is not None else ''}")


def run(stock, ctx, codes, macro, acid, alone, data):
    tid = gw.combo_id(codes, macro, acid)
    rid = (gs.subset_id(codes) if codes else "") + ("-macro" if macro else "") + ("-acid" if acid else "")
    rid = rid.lstrip("-")
    print(f"== {tid} (référence {rid})")
    fw = Fw(stock, [load(tid)], ctx)
    ref = Fw.__new__(Fw)
    tac.Fw.__init__(ref, stock, [load(rid)], ctx)
    if rid == "acid":                       # ACID seule est liée au début ; ici à ACID_AT, comme dans macro-acid
        bref = Fw.__new__(Fw)
        tac.Fw.__init__(bref, stock, [load("macro-acid")], ctx)
        boot_check(fw, bref, below=tac.gac.ACID_AT)
    else:
        boot_check(fw, ref)
    interface(stock, fw)
    macro = fw.views.get("macro")
    fenv_ui.check_fenv(ref.img, fw.img, fw.payload, fw.index, tid, check, ref.mine["id"], base_payload=ref.payload,
                       macro=macro.index if macro else None)
    ours(fw, data)
    sound(fw, ref, alone, data, tid)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--engines", help="moteurs, séparés par des virgules, ou none")
    ap.add_argument("--macro", choices=("yes", "no", "both"), default="both")
    ap.add_argument("--acid", choices=("yes", "no", "both"), default="both")
    a = ap.parse_args()
    stock = T.main_os_from_syx(a.cycles)
    st_img = syntakt.dsp_image(a.syntakt)
    ctx = dict(syntakt=a.syntakt, st_img=st_img, chord=tmx.chord_tables(stock))
    if a.engines is None:
        todo = [((), True, False), ((), False, True), ((), True, True), (("sd",), False, False),
                (tuple(gs.CATALOG), True, True)]
    else:
        todo = gwc.todo_list(argparse.Namespace(engines=a.engines, macro=a.macro, acid=a.acid))
    data = tw.WC.bake(tw.test_table(frames=8, n=512))
    alone = tw.Fw(stock, [load("wavetable")])
    for codes, macro, acid in todo:
        run(stock, ctx, codes, macro, acid, alone, data)
    fails = len(t7.FAIL) + len(tw.FAIL)
    print("\n" + ("TOUT OK" if not fails else f"{fails} ECHEC(S)"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
