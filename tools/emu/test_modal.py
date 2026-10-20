#!/usr/bin/env python3
"""Preuve de la machine MODAL (notes/74, tools/gen_modal.py) dans le Modded Cycles OS : le tweak
31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json (Model-TG, les 5 moteurs du Syntakt, MACRO, ACID, MODAL),
construit comme par build.py. Le vrai code de l'OS, émulé (Unicorn, EMAC exacte : emac.py).

Référence pour ce qui ne change pas : le même OS sans MODAL (31-…-macro-acid.json, celui de la version 2.0.1).

  1. Démarrage : le décompresseur du bootstrap relit l'OS agrandi ; le crochet reconstitue la charge utile
     (test_acid_combos.boot) ; MODAL à sa place, au-dessus d'ACID ; l'image finit sous 0x40200000.
  2. Interface (test_model_tg_syntakt.interface) : 15 machines, 8 ajoutées (gs.ROWS8 : rangées, enregistrements de
     0x50 o), l'écran MACHINES sur 2 lignes de 8 repères, les noms et potards de MODAL.
  3. FUNC + SHAPE sur une piste MODAL (lofi_ui, le code de l'interface de l'OS) : FINE, en trois crans (1, 2, 4
     voix), son texte et la fenêtre de valeur ; les autres machines et potards comme sans MODAL ; le lo-fi de MACRO
     (FUNC + PITCH) inchangé.
  4. Son, la boucle des voix (mcengine) : ce que la passerelle de MODAL reçoit à chaque bloc est rejoué sur
     modal.c compilé pour l'ordinateur (modal_machine_host.c) : sortie identique octet pour octet, pour les 6 modèles,
     la polyphonie 1, 2 et 4, les potards qui bougent, le modèle verrouillé par pas, la vélocité, les notes
     extrêmes, les changements de machine (machine locks) ; la note jouée est juste (fondamentale mesurée) ; les gains
     de vélocité remis à 127 (la vélocité règle la frappe, pas le volume).
  5. Les autres machines (les 6 d'origine, les moteurs, MACRO, ACID, le Sampler) : identiques à l'OS sans MODAL.
  6. Régulateur de charge : 6 pistes MODAL sous une surcharge : il les éteint en fondu, jamais le Sampler.
  7. Mémoire : MODAL n'écrit qu'à sa place (ses variables, l'état de ses pistes à 0x46800000..0x468f0000).
  8. Coût d'une piste MODAL par modèle et polyphonie (informatif).

    python3 tools/emu/test_modal.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--quick]

Demande m68k-linux-gnu-objdump (ou m68k-elf-objdump sous ce nom) pour l'EMAC, et un compilateur C pour l'ordinateur.
"""
import argparse
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import gen_macro as gm              # noqa: E402
import gen_modal as gmo             # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import lofi_ui                      # noqa: E402
import mcengine as E                # noqa: E402
import seqrig as S                  # noqa: E402
import syntakt                      # noqa: E402
import test_acid as ta              # noqa: E402
import test_acid_combos as tac      # noqa: E402
import test_macro as tm             # noqa: E402
import test_macro_syntakt as tmx    # noqa: E402
import test_model_tg_syntakt as tms  # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402

check = t7.check
load = ta.load
FIVE = list(gmo.FIVE)
KW = dict(note=48, pitch=64, color=64, shape=0, sweep=40, contour=36, punch=0, gate=0, finetune=64, decay=64)
POLY_FINE = {1: 64, 2: 80, 4: 96}            # FINE (0..127) -> 0x4000, 0x5000, 0x6000 : 1, 2, 4 voix
RAM = (gmo.MODAL_RAM, gmo.MODAL_RAM + 6 * gmo.TRACK_SIZE)
gs.CATALOG.setdefault("modal", dict(gmo.MACHINE, label="MODAL"))
gs.CATALOG.setdefault("macro", dict(gm.MACHINE, label="MACRO"))


class Fw(tac.Fw):
    """test_acid_combos.Fw, plus MODAL : l'EMAC aussi sur son code, et l'état de ses pistes en mémoire."""

    def __init__(self, stock, tweaks, ctx):
        super().__init__(stock, tweaks, ctx)
        self.emac = tuple((v.pay, v.code_end) for k, v in self.views.items() if k in ("acid", "modal"))

    def engine(self, solo=None):
        e = super().engine(solo)
        S.ensure_map(e.uc, RAM[0], 0x00100000)
        return e


# --- 4. son : MODAL rejouée sur l'ordinateur -----------------------------------------------------------------------
class Host:
    """modal.c (passerelle et cœur) compilé pour l'ordinateur (modal_machine_host.c)."""

    def __init__(self, tmp):
        self.exe = tmp / "modal_machine_host"
        cc = shutil.which("cc") or shutil.which("gcc")
        subprocess.run([cc, "-O2", "-Wall", "-Wextra", "-Werror", f"-I{gmo.SRC}", str(HERE / "modal_machine_host.c"),
                        "-o", str(self.exe)], check=True)

    def run(self, recs):
        out = subprocess.run([str(self.exe)], input=b"".join(recs), capture_output=True, check=True).stdout
        n = len(out) // (35 * 4)
        v = np.frombuffer(out, "<i4").reshape(n, 35).astype(np.int64)
        return v[:, :32], v[:, 32:]


class Probe:
    """Ce que reçoit la passerelle de MODAL (entrées de modal_update), ce qu'elle a écrit après update (gains, marque),
    et ce qu'elle sort (le tampon de modal_render, lu à son retour)."""

    def __init__(self, view, e, tracks=(0,)):
        self.tracks, self.block = tuple(tracks), 0
        self.recs = {t: [] for t in self.tracks}
        self.after = {t: [] for t in self.tracks}
        self.outs = {t: [] for t in self.tracks}
        self.pending = None
        uc = e.uc
        u32 = lambda a: struct.unpack(">I", uc.mem_read(a, 4))[0]
        r16 = lambda a: struct.unpack(">h", uc.mem_read(a, 2))[0]
        r32 = lambda a: struct.unpack(">i", uc.mem_read(a, 4))[0]
        arg = lambda k: u32(uc.reg_read(mk.UC_M68K_REG_A7) + 4 * k)
        track = lambda v: (v - E.VOICE0) // E.VSTRIDE if (v - E.VOICE0) % E.VSTRIDE == 0 else -1

        def upd(uc_, a, s, u):
            v = arg(2)
            t = track(v)
            if t not in self.tracks:
                return
            pmod = struct.unpack(">i", struct.pack(">I", arg(1)))[0]
            self.recs[t].append(struct.pack("<7i", t, pmod, r32(v + 0x2c), r32(v + 0x34), r32(v + 0x38),
                                            r16(S.GAIN + 2 * t), r16(S.GAIN_NEXT + 2 * t)) + bytes(uc.mem_read(arg(3), 64)))

        def rnd(uc_, a, s, u):
            v = arg(2)
            t = track(v)
            if t not in self.tracks:
                return
            self.after[t].append((r16(S.GAIN + 2 * t), r16(S.GAIN_NEXT + 2 * t), r32(v + 0x2c)))
            self.pending = (t, arg(1), arg(0))

        def back(uc_, a, s, u):
            if self.pending and a == self.pending[2]:
                t, out, _ = self.pending
                self.outs[t].append(np.frombuffer(bytes(uc.mem_read(out, 128)), ">i4").astype(np.int64))
                self.pending = None
        uc.hook_add(UC_HOOK_CODE, upd, begin=view.upd, end=view.upd)
        uc.hook_add(UC_HOOK_CODE, rnd, begin=view.rnd, end=view.rnd)
        uc.hook_add(UC_HOOK_CODE, back, begin=gs.STUBS, end=gs.DATA - 1)     # l'appel de render : dans nos détours

    def verify(self, host):
        bad, outs = [], {}
        for t in self.tracks:
            if not self.recs[t]:
                continue
            want, back = host.run(self.recs[t])
            got = np.array(self.outs[t], np.int64).reshape(-1, 32)
            aft = np.array(self.after[t], np.int64).reshape(-1, 3)
            back[:, 2] &= 0xffffffff
            aft[:, 2] &= 0xffffffff
            if len(got) != len(want) or not np.array_equal(got, want):
                first = next((i for i in range(min(len(got), len(want))) if not np.array_equal(got[i], want[i])), None)
                bad.append(f"piste {t + 1} : {len(got)} blocs rendus / {len(want)} attendus, 1er bloc différent {first}")
            if not np.array_equal(aft, back):
                bad.append(f"piste {t + 1} : gains et marque après update différents")
            outs[t] = got
        return bad, outs


def play(fw, kw, blocks, trigs=(1,), changes=None, track=0, gains=None, solo=True):
    """Une piste sur MODAL (ou kw["machine"]), les autres éteintes. changes : {bloc : réglages} ; gains : {bloc : gain
    de vélocité écrit avant le bloc} (0x40fe4c90 et 0x40fe4cd0, ce que l'OS écrit au trig)."""
    m = fw.views["modal"]
    e = fw.engine(solo=track if solo else None)
    e.set(track, **dict(dict(machine=m.index), **kw))
    pr = Probe(m, e, (track,))
    for b in range(blocks):
        for k, v in (changes or {}).get(b, {}).items():
            e.set(track, **{k: v})
        if b in (gains or {}):
            ta.set_globals(e, track, gain=gains[b])
        pr.block = b
        e.block(1 << track if b in trigs else 0)
    return pr, e.unmapped


def cases(quick):
    """(nom, réglages, extra pour play)."""
    out = []
    for model in range(6):
        out.append((f"modèle {model} ({gmo.MODELS[model]}), 1 voix", dict(KW, shape=model),
                    dict(trigs=(1, 150), blocks=260, changes={150: dict(note=55)})))
    polys = ((0, 2), (0, 4), (1, 2), (2, 4), (3, 4), (4, 2), (5, 2)) if not quick else ((0, 4), (4, 2))
    for model, poly in polys:
        notes = {1: dict(note=48), 30: dict(note=52), 60: dict(note=55), 90: dict(note=60)}
        out.append((f"modèle {model}, {poly} voix, 4 notes", dict(KW, shape=model, finetune=POLY_FINE[poly]),
                    dict(trigs=(1, 30, 60, 90), blocks=200, changes=notes)))
    if not quick:
        for chord in (0, 64, 127):
            out.append((f"cordes quantifiées, STRUCTURE {chord}, 1 voix", dict(KW, shape=4, contour=chord),
                        dict(trigs=(1,), blocks=120)))
    out += [
        ("potards qui bougent pendant la note (modal)", dict(KW, shape=0),
         dict(trigs=(1,), blocks=160, changes={40: dict(color=110), 60: dict(sweep=100), 80: dict(contour=90),
                                              100: dict(decay=120)})),
        ("potards qui bougent pendant la note (corde)", dict(KW, shape=2),
         dict(trigs=(1,), blocks=160, changes={40: dict(color=20), 60: dict(sweep=5), 80: dict(contour=127),
                                              100: dict(decay=127)})),
        ("modèle verrouillé par pas : 0, 2, 5, 3", dict(KW, shape=0),
         dict(trigs=(1, 40, 80, 120), blocks=180, changes={40: dict(shape=2), 80: dict(shape=5), 120: dict(shape=3)})),
        ("polyphonie changée pendant le jeu : 1, 4, 2", dict(KW, shape=1),
         dict(trigs=(1, 40, 80), blocks=140, changes={40: dict(finetune=96), 80: dict(finetune=80)})),
        ("vélocité : gain 127 puis 30", dict(KW, shape=0),
         dict(trigs=(1, 80), blocks=160, gains={0: 127, 79: 30})),
        ("note 0, PITCH 0 : borné en bas", dict(KW, shape=2, note=0, pitch=0), dict(blocks=60)),
        ("note 127, PITCH 127 : borné en haut", dict(KW, shape=0, note=127, pitch=127), dict(blocks=60)),
        ("DAMPING au maximum (cordes : résonance infinie)", dict(KW, shape=1, decay=127), dict(blocks=200)),
        ("BRIGHTNESS 0, POSITION 0, STRUCTURE 0", dict(KW, shape=3, color=0, sweep=0, contour=0), dict(blocks=80)),
        ("BRIGHTNESS 127, POSITION 127, STRUCTURE 127", dict(KW, shape=5, color=127, sweep=127, contour=127),
         dict(blocks=80)),
    ]
    if not quick:
        out.append(("machine locks : SNARE, MODAL, ACID, MODAL, KICK", dict(KW, shape=0, machine=1),
                    dict(trigs=(1, 30, 60, 90, 120), blocks=150, changes="locks")))
    return out


def exact(fw, host, quick, label):
    m, acid = fw.views["modal"], fw.views["acid"]
    for name, kw, extra in cases(quick):
        extra = dict(extra)
        if extra.get("changes") == "locks":
            extra["changes"] = {30: dict(machine=m.index), 60: dict(machine=acid.index), 90: dict(machine=m.index),
                                120: dict(machine=0)}
        pr, unm = play(fw, kw, **extra)
        bad, outs = pr.verify(host)
        got = outs.get(0, np.zeros((0, 32)))
        peak = int(np.abs(got).max()) if len(got) else 0
        gains = {(g, n) for g, n, _ in pr.after[0]}
        check(not bad and not unm and len(got) and 0 < peak < 2 ** 31 - 1 and gains <= {(127, 127)},
              f"{label} : {name} : {len(got)} blocs, identiques à modal.c sur l'ordinateur, crête "
              f"{peak / 2 ** 31:.3f} de la pleine échelle, gains de vélocité à 127 {bad[:1]}")


def pitch(fw, label):
    """La note jouée : fondamentale mesurée (modal harmonique, corde, FM) pour quelques notes et PITCH."""
    bad, seen = [], []
    for shape, note, p in ((0, 48, 64), (2, 60, 64), (3, 57, 64), (0, 60, 76), (2, 36, 52)):
        kw = dict(KW, shape=shape, note=note, pitch=p, contour=36 if shape != 3 else 64, decay=100)
        pr, _ = play(fw, kw, 220, trigs=(1,))
        x = np.concatenate(pr.outs[0][20:]).astype(np.float64)
        x = x * np.hanning(len(x))
        sp = np.abs(np.fft.rfft(x, 1 << 18))
        f = np.fft.rfftfreq(1 << 18, 1 / 48000)
        lo = 20
        k = lo + int(np.argmax(sp[lo:]))
        want = 440 * 2 ** ((note + p - 64 - 69) / 12)
        # la plus forte composante est la fondamentale ou un harmonique : on la ramène à la fondamentale attendue
        ratio = f[k] / want
        h = round(ratio)
        ok = h >= 1 and abs(ratio / h - 1) < 0.01
        seen.append(f"{note + p - 64}:{f[k]:.1f}Hz(h{h})")
        if not ok:
            bad.append((shape, note, p, round(f[k], 1), round(want, 1)))
    check(not bad, f"{label} : la note jouée (note du trig + PITCH - 64) : composante la plus forte sur la fondamentale "
                   f"ou un harmonique, à 1 % près ({', '.join(seen)}) {bad}")


# --- 3. FUNC + SHAPE ------------------------------------------------------------------------------------------------
def poly_ui(base, fw, label):
    m = fw.views["modal"].index
    a = lofi_ui.UI(base.img, base.payload, end=base.blob_end)
    b = lofi_ui.UI(fw.img, fw.payload, end=fw.blob_end)
    check(a.init_ok and b.init_ok, f"{label} : objets d'interface construits par l'OS (0x400de244)")
    same = all(b.lookup(x, k, f) == a.lookup(x, k, f) for x in range(m) for k in range(2, 16) for f in (False, True))
    check(same, f"{label} : machines 1..{m}, les 14 potards, avec et sans FUNC : le même descripteur que sans MODAL")
    first = 76 + 5 * 7                          # descripteurs de MODAL : 8e machine ajoutée
    got = {(k, f): b.lookup(m, k, f) for k in range(2, 16) for f in (False, True)}
    check(got[gmo.SHAPE_KNOB, True] == lofi_ui.FTUN and got[gmo.SHAPE_KNOB, False] == first + 1
          and got[2, False] == got[2, True] == lofi_ui.PITCH
          and all(got[k, True] == got[k, False] for k in range(3, 14) if k != gmo.SHAPE_KNOB),
          f"{label} : piste MODAL : FUNC + SHAPE -> {got[gmo.SHAPE_KNOB, True]} (FINE) ; SHAPE seul -> "
          f"{got[gmo.SHAPE_KNOB, False]} (Model, {first + 1}) ; FUNC + PITCH : PITCH ; les autres potards avec FUNC "
          f"comme sans")
    b.lookup(m, gmo.SHAPE_KNOB, True)           # nos fonctions sur l'objet d'interface de FINE
    steps = {(c, d): b.edit_func(lofi_ui.FTUN, c, d) for c in (0x4000, 0x5000, 0x6000, 0x4080, 0x0, 0x7f00)
             for d in (0x100, -0x100, 0x300, -0x300, 1, -1)}
    want = lambda c, d: 0x4000 + 0x1000 * max(0, min(2, (2 if c >= 0x5800 else 1 if c >= 0x4800 else 0)
                                                       + (1 if d > 0 else -1 if d < 0 else 0)))
    bad = [(hex(c), hex(d), hex(v)) for (c, d), v in steps.items() if v != want(c, d)]
    check(not bad, f"{label} : FUNC + un tour de SHAPE (vrai 0x4000b7d6) : un cran par tour, 1, 2, 4 voix "
                   f"(0x4000, 0x5000, 0x6000), bornés {bad[:3]}")
    shown = {v: b.text(lofi_ui.FTUN, v) for v in (0x4000, 0x5000, 0x6000)}
    check(list(shown.values()) == ["1", "2", "4"], f"{label} : texte de la valeur (vrai sprintf de l'OS) : {shown}")
    shots = {v: (b.popup(lofi_ui.FTUN, v), b.popup(lofi_ui.FTUN, v, text_path=True)) for v in (0x4000, 0x5000, 0x6000)}
    bad = [hex(v) for v, (x, y) in shots.items() if x is None or y is None or x != y or x[1]]
    check(not bad, f"{label} : fenêtre de valeur (vrai 0x4001d818) : 1, 2, 4, pixel pour pixel le texte que l'OS "
                   f"dessine par son chemin texte, pas de jauge {bad}")
    if not bad:
        print("      fenêtre de valeur, FUNC + SHAPE sur 4 voix :")
        print(lofi_ui.ascii_popup(shots[0x6000][0][0]))


# --- 7. mémoire -----------------------------------------------------------------------------------------------------
def memory(fw, label):
    """Écritures du code de MODAL : ses variables (BSS) et l'état de ses pistes, rien d'autre (la pile mise à part) ;
    et personne d'autre n'écrit dans l'état de ses pistes."""
    m = fw.views["modal"]
    e = fw.engine()
    bss = (fw.dest + gmo.MODAL_BSS, fw.dest + gmo.MODAL_BSS + 0x4000)
    out_buf = (E.TRACK_BASE, E.TRACK_BASE + 6 * 0x80)
    stray, foreign = [], []

    def wr(uc, access, addr, size, value, ud):
        pc = uc.reg_read(mk.UC_M68K_REG_PC)
        mine = m.pay <= pc < m.code_end
        ram = RAM[0] <= addr < RAM[1]
        if mine and not (ram or bss[0] <= addr < bss[1] or out_buf[0] <= addr < out_buf[1]
                         or 0x90000000 <= addr < 0x90020000 or E.VOICE0 <= addr < E.VOICE0 + 6 * E.VSTRIDE
                         or addr in range(S.GAIN, S.GAIN + 12) or addr in range(S.GAIN_NEXT, S.GAIN_NEXT + 12)):
            stray.append((hex(pc), hex(addr)))
        if ram and not mine:
            foreign.append((hex(pc), hex(addr)))
    e.uc.hook_add(UC_HOOK_MEM_WRITE, wr)
    for t in range(6):
        e.set(t, **dict(KW, machine=m.index, shape=t, finetune=POLY_FINE[(1, 2, 4)[t % 3]], note=40 + 4 * t))
    for b in range(120):
        e.block(0x3f if b in (1, 60) else 0)
    check(not stray and not foreign and not e.unmapped,
          f"{label} : 6 pistes MODAL (les 6 modèles), 120 blocs : MODAL n'écrit que dans ses variables "
          f"({bss[0]:#x}..), l'état de ses pistes ({RAM[0]:#x}..{RAM[1]:#x}), la voix, les gains et la sortie ; "
          f"personne d'autre dans l'état de ses pistes {stray[:2]} {foreign[:2]}")


# --- 8. coût --------------------------------------------------------------------------------------------------------
def cost(fw, label):
    m = fw.views["modal"]
    res = []
    for shape in range(6):
        for poly in (1, 2, 4):
            e = fw.engine(solo=0)
            e.set(0, **dict(KW, machine=m.index, shape=shape, finetune=POLY_FINE[poly], decay=100))
            n = {"i": 0, "on": False}

            def hk(uc, a, s, u):
                if n["on"]:
                    n["i"] += 1
            e.uc.hook_add(UC_HOOK_CODE, hk, begin=m.pay, end=m.code_end - 1)
            for b in range(40):                  # tables, effacements, 1re note : avant la mesure
                e.block(1 if b in (1, 30) else 0)
            n["on"] = True
            for b in range(16):
                e.block(1 if b == 8 else 0)
            res.append((shape, poly, n["i"] // 16))
    for shape in range(6):
        row = ", ".join(f"{p} voix {i}" for s, p, i in res if s == shape)
        print(f"      {label} : modèle {shape} ({gmo.MODELS[shape]}) : {row} instructions par bloc")
    check(all(i < 120_000 for _, _, i in res), f"{label} : coût d'une piste MODAL mesuré (instructions de MODAL par "
                                               f"bloc, voir ci-dessus), toujours sous 120 000")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--eurorack", required=True, help="clone de pichenettes/eurorack (MACRO : Braids)")
    ap.add_argument("--quick", action="store_true", help="moins de cas")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    st_img = syntakt.dsp_image(args.syntakt)
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        ctx = dict(cycles=args.cycles, syntakt=args.syntakt, st_img=st_img, chord=tmx.chord_tables(stock),
                   acid_ref=ta.Ref(tmp))
        repo = pathlib.Path(args.eurorack).resolve()
        gm.check_sources(repo)
        ctx["braids"] = tm.Ref(tmp, repo)
        host = Host(tmp)
        tg_tw = load("30-model-tg-st.json")
        tw = load(f"31-{gmo.TWEAK_ID}.json")
        without_tw = load("31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid.json")
        make = lambda *ts: Fw(stock, sorted([tg_tw, *ts], key=lambda t: t["order"]), ctx)
        fw, without = make(tw), make(without_tw)
        ref_eng = make(load(f"31-{gs.tweak_id(FIVE, tg=True)}.json"))
        label = tw["id"]
        mv = fw.views["modal"]
        print(f"\n== {label} : MODAL en machine {mv.index + 1} sur {fw.nm}")
        print("démarrage")
        t7.X.bootstrap_depack_ok(ctx["cycles"], fw.tweaks, ctx["syntakt"]) or t7.FAIL.append("bootstrap " + label)
        tgs = {k: int(v, 16) for k, v in tg_tw["symbols"].items()}
        tgs["knob_vec"] = tms.knob_vec_at(tw)
        tac.boot(fw, ref_eng, tgs, None)
        check(mv.pay == fw.dest + gmo.MODAL_AT and mv.code_end <= fw.dest + gmo.MODAL_BSS
              and fw.views["acid"].code_end <= mv.pay,
              f"MODAL à {mv.pay:#x}..{mv.code_end:#x} (code et tables), variables à {fw.dest + gmo.MODAL_BSS:#x}, "
              f"après ACID ; l'état de ses pistes à {RAM[0]:#x}")
        print("interface")
        tac.interface(stock, fw, tw, tgs, make())
        print("FUNC + SHAPE")
        poly_ui(without, fw, f"MODAL dans {label}")
        lofi_ui.check_lofi(ref_eng.img, fw.img, fw.payload, fw.views["macro"].index, f"MACRO dans {label}", check,
                           end=fw.blob_end, base_end=ref_eng.blob_end, base_payload=ref_eng.payload,
                           base="les mêmes mods sans MACRO, ACID ni MODAL", after=1)
        print("son")
        gs.set_base(fw.dest)
        gs.set_rows(8)
        exact(fw, host, args.quick, f"MODAL dans {label}")
        pitch(fw, f"MODAL dans {label}")
        print("les autres machines")
        acid, macro = fw.views["acid"], fw.views["macro"]
        for name, setup in (
                ("les 6 d'origine", {t: dict(tm.BASE_KW, machine=t, shape=64, contour=64, decay=60) for t in range(6)}),
                ("SDVtg, SYBit, MACRO, Sampler, ACID, SYSwm",
                 {0: dict(tm.BASE_KW, machine=gs.TG_FIRST, decay=60), 1: dict(tm.BASE_KW, machine=gs.TG_FIRST + 3),
                  2: dict(tm.BASE_KW, machine=macro.index, shape=25, decay=60), 3: dict(KW, machine=6, decay=80),
                  4: dict(ta.KW, machine=acid.index, decay=60), 5: dict(tm.BASE_KW, machine=gs.TG_FIRST + 4)})):
            trigs = {1: 0x3f, 150: 0x3f}
            r, _ = tmx.multi(without, setup, 300, trigs)
            x, unm = tmx.multi(fw, setup, 300, trigs)
            check(np.array_equal(r, x) and np.abs(x).max() > 1e6 and not unm,
                  f"{label} : {name} : sortie des 6 pistes identique à l'OS sans MODAL")
        print("régulateur de charge")
        setup = {t: dict(KW, machine=mv.index, shape=(0, 1, 2, 3, 4, 5)[t], note=40 + 5 * t, decay=110) for t in range(6)}
        setup[2] = dict(KW, machine=6, decay=100)
        tac.governor(fw, tw, f"{label}", sampler=True, setup=setup, what="MODAL")
        print("mémoire")
        memory(fw, f"MODAL dans {label}")
        print("coût")
        cost(fw, f"MODAL dans {label}")
    fail = t7.FAIL + tms.FAIL
    print("\nTOUT OK" if not fail else f"\n{len(fail)} ÉCHEC(S)")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
