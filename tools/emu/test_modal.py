#!/usr/bin/env python3
"""Preuve de la machine MODAL (notes/74, tools/gen_modal.py) dans le Modded Cycles OS : le tweak
31-syntakt-tg-sd-cp-toy-bits-swarm-macro-acid-modal.json (Model-TG, les 5 moteurs du Syntakt, MACRO, ACID, MODAL),
construit comme par build.py. Le vrai code de l'OS, émulé (Unicorn, EMAC exacte : emac.py).

Référence pour ce qui ne change pas : le même OS sans MODAL (31-…-macro-acid.json, celui de la version 2.0.1).

  1. Démarrage : le décompresseur du bootstrap relit l'OS agrandi ; le crochet reconstitue la charge utile
     (test_acid_combos.boot) ; MODAL à sa place, au-dessus d'ACID ; l'image finit sous 0x40200000.
  2. Interface (test_model_tg_syntakt.interface) : 15 machines, 8 ajoutées (gs.ROWS8 : rangées, enregistrements de
     0x50 o), l'écran MACHINES sur 2 lignes de 8 repères, les noms et potards de MODAL.
  2 bis. Model-TG : les trois tests « machine = 6 » qui acceptent aussi MODAL (le sample excitateur, notes/80),
     exécutés depuis le tweak pour les 256 machines contre le code d'origine.
  3. FUNC + SHAPE sur une piste MODAL (lofi_ui, le code de l'interface de l'OS) : FINE, en trois crans (1, 2, 4
     voix), son texte et la fenêtre de valeur ; les autres machines et potards comme sans MODAL ; le lo-fi de MACRO
     (FUNC + PITCH) inchangé.
  4. Son, la boucle des voix (mcengine) : ce que la passerelle de MODAL reçoit à chaque bloc est rejoué sur
     modal.c compilé pour l'ordinateur (modal_machine_host.c) : sortie identique octet pour octet, pour les 4 modèles,
     la polyphonie 1, 2 et 4, les potards qui bougent, le modèle verrouillé par pas, la vélocité, les notes
     extrêmes, les changements de machine (machine locks) ; la note jouée est juste (fondamentale mesurée) ; les gains
     de vélocité remis à 127 (la vélocité règle la frappe, pas le volume).
  4 bis. Le sample comme excitateur (notes/80) : les cases de samples de Model-TG posées comme il le fait, la sortie
     et track_slot / track_pend après chaque render identiques à modal.c sur l'ordinateur : les 4 modèles, la
     polyphonie, un sample court, la vélocité, la case en attente (chargement d'un projet, sample tu, sample qui
     joue), un autre sample sous la note, PEND_SILENT, une case vide ; le son change dès la note.
  5. Les autres machines (les 6 d'origine, les moteurs, MACRO, ACID, le Sampler) : identiques à l'OS sans MODAL.
  6. Régulateur de charge : 6 pistes MODAL sous une surcharge : il les éteint en fondu, jamais le Sampler.
  7. Mémoire : MODAL n'écrit qu'à sa place (ses variables, l'état de ses pistes à 0x46800000..0x46890000, et
     track_slot / track_pend de Model-TG quand il prend une case en attente).
  8. Coût d'une piste MODAL par modèle et polyphonie, et avec un sample en entrée (informatif).

    python3 tools/emu/test_modal.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--quick]

Demande m68k-linux-gnu-objdump (ou m68k-elf-objdump sous ce nom) pour l'EMAC, et un compilateur C pour l'ordinateur.
"""
import argparse
import json
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
POLY_FINE = {1: 64, 2: 80, 3: 96}            # FINE (0..127) -> 0x4000, 0x5000, 0x6000 : 1, 2, 3 voix (notes/81)
RAM = (gmo.MODAL_RAM, gmo.MODAL_RAM + 6 * gmo.TRACK_SIZE)
gs.CATALOG.setdefault("modal", dict(gmo.MACHINE, label="MODAL"))
# les cases de samples de Model-TG (ses symboles), que MODAL lit pour son excitateur (notes/80) ; les samples de la
# preuve dans la zone de Model-TG (vue sans cache), loin de ce qu'il y range lui-même
TG = {k: int(v, 16) for k, v in json.loads((gs.TG_TWEAK).read_text(encoding="utf-8"))["symbols"].items()}
SAMPLE_AT = 0x4b000000
gs.CATALOG.setdefault("macro", dict(gm.MACHINE, label="MACRO"))


class Fw(tac.Fw):
    """test_acid_combos.Fw, plus MODAL : l'EMAC aussi sur son code, et l'état de ses pistes en mémoire."""

    def __init__(self, stock, tweaks, ctx):
        super().__init__(stock, tweaks, ctx)
        self.emac = tuple((v.pay, v.code_end) for k, v in self.views.items() if k in ("acid", "macro", "modal"))

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

    def run(self, recs, slots=()):
        """slots : [(case, empreinte, échantillons int16)] posés dans les cases de Model-TG (le sample excitateur)."""
        head = struct.pack("<i", len(slots))
        for k, h, pcm in slots:
            be = np.asarray(pcm, ">i2").tobytes()
            head += struct.pack("<3i", k, h - (1 << 32) if h >= 1 << 31 else h, len(pcm)) + be + bytes(-len(be) % 4)
        out = subprocess.run([str(self.exe)], input=head + b"".join(recs), capture_output=True, check=True).stdout
        n = len(out) // (37 * 4)
        v = np.frombuffer(out, "<i4").reshape(n, 37).astype(np.int64)
        return v[:, :32], v[:, 32:]


class Probe:
    """Ce que reçoit la passerelle de MODAL (entrées de modal_update), ce qu'elle a écrit après update (gains, marque),
    et ce qu'elle sort (le tampon de modal_render, lu à son retour)."""

    def __init__(self, view, e, tracks=(0,)):
        self.tracks, self.block = tuple(tracks), 0
        self.recs = {t: [] for t in self.tracks}
        self.after = {t: [] for t in self.tracks}
        self.outs = {t: [] for t in self.tracks}
        self.slots = {t: [] for t in self.tracks}        # track_slot, track_pend de Model-TG après render
        self.at = {t: {} for t in self.tracks}           # ... par bloc (MODAL n'est calculée qu'à partir d'un trig)
        self.tg_slots = []                               # cases posées (Host.run)
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
            self.recs[t].append(struct.pack("<9i", t, pmod, r32(v + 0x2c), r32(v + 0x34), r32(v + 0x38),
                                            r16(S.GAIN + 2 * t), r16(S.GAIN_NEXT + 2 * t), r32(TG["track_slot"] + 4 * t),
                                            r32(TG["track_pend"] + 4 * t)) + bytes(uc.mem_read(arg(3), 64)))

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
                self.slots[t].append((r32(TG["track_slot"] + 4 * t), r32(TG["track_pend"] + 4 * t)))
                self.at[t][self.block] = (self.slots[t][-1], self.outs[t][-1])
                self.pending = None
        uc.hook_add(UC_HOOK_CODE, upd, begin=view.upd, end=view.upd)
        uc.hook_add(UC_HOOK_CODE, rnd, begin=view.rnd, end=view.rnd)
        uc.hook_add(UC_HOOK_CODE, back, begin=gs.STUBS, end=gs.DATA - 1)     # l'appel de render : dans nos détours

    def verify(self, host):
        bad, outs = [], {}
        for t in self.tracks:
            if not self.recs[t]:
                continue
            want, back = host.run(self.recs[t], self.tg_slots)
            got = np.array(self.outs[t], np.int64).reshape(-1, 32)
            aft = np.array(self.after[t], np.int64).reshape(-1, 3)
            sl = np.array(self.slots[t], np.int64).reshape(-1, 2)
            back[:, 2] &= 0xffffffff
            aft[:, 2] &= 0xffffffff
            if len(sl) != len(back) or not np.array_equal(sl, back[:, 3:5]):
                bad.append(f"piste {t + 1} : track_slot / track_pend de Model-TG après render différents")
            back = back[:, :3]
            if len(got) != len(want) or not np.array_equal(got, want):
                first = next((i for i in range(min(len(got), len(want))) if not np.array_equal(got[i], want[i])), None)
                bad.append(f"piste {t + 1} : {len(got)} blocs rendus / {len(want)} attendus, 1er bloc différent {first}")
            if not np.array_equal(aft, back):
                bad.append(f"piste {t + 1} : gains et marque après update différents")
            outs[t] = got
        return bad, outs


def tg_put(e, slots=(), track=0, slot=None, pend=None):
    """Les cases de samples de Model-TG, comme les pose son navigateur ou son chargeur (notes/80) : slots
    [(case, empreinte, échantillons int16)] ; la case de la piste (track_slot) et celle qui attend (track_pend)."""
    w32 = lambda a, v: e.uc.mem_write(a, struct.pack(">I", v & 0xffffffff))
    for k, h, pcm in slots:
        base = SAMPLE_AT + 0x100000 * k
        e.uc.mem_write(base, bytes(64) + np.asarray(pcm, ">i2").tobytes())      # l'en-tête de 64 o, puis le PCM
        w32(TG["slot_hash"] + 4 * k, h)
        w32(TG["slot_base"] + 4 * k, base)
        w32(TG["slot_count"] + 4 * k, len(pcm))
    if slot is not None:
        w32(TG["track_slot"] + 4 * track, slot)
    if pend is not None:
        w32(TG["track_pend"] + 4 * track, pend)


def play(fw, kw, blocks, trigs=(1,), changes=None, track=0, gains=None, solo=True, tg=None, tg_at=None):
    """Une piste sur MODAL (ou kw["machine"]), les autres éteintes. changes : {bloc : réglages} ; gains : {bloc : gain
    de vélocité écrit avant le bloc} (0x40fe4c90 et 0x40fe4cd0, ce que l'OS écrit au trig) ; tg : les cases de
    samples de Model-TG au départ (tg_put) ; tg_at : {bloc : (slot, pend)} posés avant le bloc."""
    m = fw.views["modal"]
    e = fw.engine(solo=track if solo else None)
    e.set(track, **dict(dict(machine=m.index), **kw))
    pr = Probe(m, e, (track,))
    if tg:
        tg_put(e, track=track, **tg)
        pr.tg_slots = list(tg.get("slots", ()))
    for b in range(blocks):
        for k, v in (changes or {}).get(b, {}).items():
            e.set(track, **{k: v})
        if b in (gains or {}):
            ta.set_globals(e, track, gain=gains[b])
        if b in (tg_at or {}):
            tg_put(e, track=track, slot=tg_at[b][0], pend=tg_at[b][1])
        pr.block = b
        e.block(1 << track if b in trigs else 0)
    return pr, e.unmapped


def cases(quick):
    """(nom, réglages, extra pour play)."""
    out = []
    for shape in range(len(gmo.MODELS)):
        out.append((f"SHAPE {shape} ({gmo.MODELS[shape]}), 1 voix", dict(KW, shape=shape),
                    dict(trigs=(1, 150), blocks=260, changes={150: dict(note=55)})))
    polys = ((0, 2), (0, 3), (1, 2), (1, 3), (2, 2), (2, 3), (3, 2), (3, 3)) if not quick else ((0, 3), (3, 2))
    for shape, poly in polys:
        notes = {1: dict(note=48), 30: dict(note=52), 60: dict(note=55), 90: dict(note=60)}
        out.append((f"SHAPE {shape}, {poly} voix, 4 notes", dict(KW, shape=shape, finetune=POLY_FINE[poly]),
                    dict(trigs=(1, 30, 60, 90), blocks=200, changes=notes)))
    if not quick:
        for chord in (0, 64, 127):
            out.append((f"cordes en accord, STRUCTURE {chord}, 1 voix", dict(KW, shape=3, contour=chord),
                        dict(trigs=(1,), blocks=120)))
    out += [
        ("potards qui bougent pendant la note (modal)", dict(KW, shape=0),
         dict(trigs=(1,), blocks=160, changes={40: dict(color=110), 60: dict(sweep=100), 80: dict(contour=90),
                                              100: dict(decay=120)})),
        ("potards qui bougent pendant la note (corde)", dict(KW, shape=2),
         dict(trigs=(1,), blocks=160, changes={40: dict(color=20), 60: dict(sweep=5), 80: dict(contour=127),
                                              100: dict(decay=127)})),
        ("modèle verrouillé par pas : 0, 2, 3, 1", dict(KW, shape=0),
         dict(trigs=(1, 40, 80, 120), blocks=180, changes={40: dict(shape=2), 80: dict(shape=3), 120: dict(shape=1)})),
        ("SHAPE au-delà de 3 (un son d'avant) : borné à 3", dict(KW, shape=5), dict(blocks=60)),
        ("polyphonie changée pendant le jeu : 1, 3, 2", dict(KW, shape=1),
         dict(trigs=(1, 40, 80), blocks=140, changes={40: dict(finetune=96), 80: dict(finetune=80)})),
        ("vélocité : gain 127 puis 30", dict(KW, shape=0),
         dict(trigs=(1, 80), blocks=160, gains={0: 127, 79: 30})),
        ("note 0, PITCH 0 : borné en bas", dict(KW, shape=2, note=0, pitch=0), dict(blocks=60)),
        # à 24 kHz (notes/81), le résonateur sonne jusqu'à la note 126 (11,8 kHz) : 127 et au-delà se taisent
        ("note 120 : la plus aiguë qui sonne", dict(KW, shape=0, note=120, pitch=64), dict(blocks=60)),
        ("DAMPING au maximum (cordes : résonance infinie)", dict(KW, shape=1, decay=127), dict(blocks=200)),
        ("BRIGHTNESS 0, POSITION 0, STRUCTURE 0", dict(KW, shape=3, color=0, sweep=0, contour=0), dict(blocks=80)),
        ("BRIGHTNESS 127, POSITION 127, STRUCTURE 127", dict(KW, shape=2, color=127, sweep=127, contour=127),
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


# --- 4 bis. le sample comme excitateur (notes/80) -------------------------------------------------------------------
def sample_pcm(kind, n, seed=1):
    """Des samples de synthèse, int16 : frappe (bruit qui s'éteint), sinus (440 Hz qui s'éteint), plein (carré à
    pleine échelle)."""
    k = np.arange(n)
    if kind == "frappe":
        x = np.random.RandomState(seed).uniform(-1, 1, n) * np.exp(-k / 400.0) * 20000
    elif kind == "sinus":
        x = np.sin(2 * np.pi * 440 * k / 48000) * np.exp(-k / 6000.0) * 24000
    else:
        x = np.where((k // 24) % 2, 32767, -32768)
    return np.clip(np.round(x), -32768, 32767).astype(np.int64).tolist()


HASH5, HASH6 = 0x6809683d, 0x1234567b


def sample_cases():
    """(nom, réglages, extra pour play, contrôle des cases de Model-TG : fonction(slots après chaque render) ou None)."""
    fr, si, co, pl = (sample_pcm("frappe", 2400), sample_pcm("sinus", 9000), sample_pcm("frappe", 20, 3),
                      sample_pcm("plein", 100))
    out = []
    for shape in range(len(gmo.MODELS)):
        out.append((f"SHAPE {shape}, sample « frappe » (2 400 échantillons), 1 voix", dict(KW, shape=shape),
                    dict(trigs=(1, 150), blocks=260, tg=dict(slots=[(5, HASH5, fr)], slot=5)), None))
    out += [
        ("SHAPE 2, sample « sinus » (9 000 échantillons, relancé avant sa fin), 3 voix",
         dict(KW, shape=2, finetune=POLY_FINE[3]), dict(trigs=(1, 30, 60, 90), blocks=200,
                                                       tg=dict(slots=[(5, HASH5, si)], slot=5)), None),
        ("SHAPE 0, sample de 20 échantillons (moins d'un bloc)", dict(KW, shape=0),
         dict(trigs=(1, 40), blocks=120, tg=dict(slots=[(5, HASH5, co)], slot=5)), None),
        ("SHAPE 1, sample à pleine échelle, vélocité 30", dict(KW, shape=1),
         dict(trigs=(1,), blocks=120, gains={0: 30}, tg=dict(slots=[(5, HASH5, pl)], slot=5)), None),
        # la toute première note de MODAL après le démarrage attend ses tables (une vingtaine de blocs) : les cases
        # en attente qui suivent tombent après
        ("case en attente au chargement du projet : prise dès que MODAL joue, la 1re note sur ce sample",
         dict(KW, shape=0), dict(trigs=(1,), blocks=60, tg=dict(slots=[(5, HASH5, fr)], slot=-1, pend=5 | 0x10000)),
         lambda at: (lambda f: all(at[b][0] == (-1, 5 | 0x10000) for b in at if b < f) and at[f][0] == (5, -1))(
             min(b for b in at if np.abs(at[b][1]).max()))),
        ("case en attente, sample tu (la note résonne encore) : prise tout de suite", dict(KW, shape=0, decay=110),
         dict(trigs=(1,), blocks=60, tg=dict(slots=[(5, HASH5, co), (6, HASH6, fr)], slot=5),
              tg_at={50: (5, 6 | 0x10000)}),
         lambda at: at[49][0] == (5, -1) and at[50][0] == (6, -1)),
        ("case en attente pendant que le sample joue : prise au bloc du trig suivant", dict(KW, shape=2),
         dict(trigs=(1, 80), blocks=100, tg=dict(slots=[(5, HASH5, si), (6, HASH6, fr)], slot=5),
              tg_at={50: (5, 6 | 0x10000)}),
         lambda at: all(at[b][0] == (5, 6 | 0x10000) for b in range(50, 80)) and at[80][0] == (6, -1)),
        ("un autre sample posé par le navigateur sous la note : il part au trig suivant", dict(KW, shape=2),
         dict(trigs=(1, 80), blocks=100, tg=dict(slots=[(5, HASH5, si), (6, HASH6, fr)], slot=5),
              tg_at={50: (6, -1)}),
         lambda at: at[49][0] == (5, -1) and all(at[b][0] == (6, -1) for b in range(50, 100))),
        ("plus de sample (PEND_SILENT) : retour à l'excitateur interne", dict(KW, shape=0, decay=110),
         dict(trigs=(1, 120), blocks=200, tg=dict(slots=[(5, HASH5, fr)], slot=5), tg_at={110: (5, 0x1ffff)}),
         lambda at: at[109][0] == (5, -1) and at[110][0] == (-1, -1)),
        ("case vide (empreinte 0) : l'excitateur interne", dict(KW, shape=0),
         dict(trigs=(1,), blocks=60, tg=dict(slots=[(5, 0, fr)], slot=5)), None),
    ]
    return out


def samples(fw, host, label):
    """MODAL avec un sample de Model-TG comme excitateur, octet pour octet contre modal.c sur l'ordinateur ; les cases
    de Model-TG après chaque render aussi ; et le sample change bien le son."""
    for name, kw, extra, want in sample_cases():
        pr, unm = play(fw, kw, **extra)
        bad, outs = pr.verify(host)
        got = outs.get(0, np.zeros((0, 32)))
        peak = int(np.abs(got).max()) if len(got) else 0
        ok = not bad and not unm and len(got) and 0 < peak < 2 ** 31 - 1
        if want is not None:
            ok = ok and want(pr.at[0])
        check(ok, f"{label} : {name} : {len(got)} blocs, identiques à modal.c sur l'ordinateur (cases de Model-TG "
                  f"comprises), crête {peak / 2 ** 31:.3f} {bad[:1]}")
    plain, _ = play(fw, dict(KW, shape=0), trigs=(1,), blocks=60)
    smp, _ = play(fw, dict(KW, shape=0), trigs=(1,), blocks=60,
                  tg=dict(slots=[(5, HASH5, sample_pcm("frappe", 2400))], slot=5))
    a, b = plain.at[0], smp.at[0]
    note = min(k for k in a if np.abs(a[k][1]).max())          # la 1re note sonne (après ses tables)
    check(sorted(a) == sorted(b) and all(np.array_equal(a[k][1], b[k][1]) for k in a if k < note)
          and all(not np.array_equal(a[k][1], b[k][1]) for k in a if k >= note),
          f"{label} : avec un sample, le son change dès la note (bloc {note}), et pas avant : excitateur interne coupé, "
          f"le sample en entrée")


def tg_machine_tests(tg_tw, label):
    """Les trois tests « machine = 6 » de Model-TG qui acceptent aussi MODAL (machine 14, tools/gen_model_tg.py
    ST_PATCHES) : leur code, tiré du tweak, exécuté pour les 256 valeurs de l'octet machine (son + 38), contre le code
    d'origine (le même, ces 6 octets remis comme Model-TG les écrit) : même branche pour toutes les machines sauf 14,
    que seul le code modifié prend pour un Sampler ; et les mêmes registres en sortie, d0 mis à part (relu ensuite)."""
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
    ap = tg_tw["append"]
    base, blob = int(ap["dest"], 16), bytearray(int(ap["size"]))
    for part in ap["parts"]:
        h, o = bytes.fromhex(part["hex"]), int(part["dest"], 16) - base
        blob[o:o + len(h)] = h
    # (nom, motif modifié, octets d'origine, registre d'adresse du son, instructions jusqu'à la branche comprise :
    # d'origine, modifiées) ; le motif commence au chargement de l'octet
    sites = (("any_sampler (navigateur)", "102a00260280000000f70c8000000006", "0280000000ff0c8000000006", "A2",
              4, 4),
             ("name_probe (chargement d'un projet)", "102a00260280000000f70c8000000006", "0280000000ff0c8000000006",
              "A2", 4, 4),
             ("tok_of (préchargement, samples gardés)", "71a80026088000035d80", "0c8000000006", "A0", 3, 4))
    found = {}
    for name, pat, *_ in sites:
        b, i, hits = bytes.fromhex(pat), 0, []
        while (i := blob.find(b, i)) >= 0:
            hits.append(base + i)
            i += 1
        found.setdefault(pat, hits)
    at = {sites[0][0]: found[sites[0][1]][0], sites[1][0]: found[sites[1][1]][1], sites[2][0]: found[sites[2][1]][0]}
    check(len(found[sites[0][1]]) == 2 and len(found[sites[2][1]]) == 1 and at[sites[0][0]] < TG["track_hash"],
          f"{label} : les trois tests modifiés dans le code de Model-TG : "
          f"{', '.join(f'{n.split()[0]} {a:#x}' for n, a in at.items())}")
    regs = [getattr(mk, f"UC_M68K_REG_{r}{i}") for r in "DA" for i in range(8)]

    def run(code, at_, areg, m, count):
        uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        uc.mem_map(base & ~0xfff, (len(blob) + 0x2fff) & ~0xfff)
        uc.mem_map(0x10000000, 0x1000)
        uc.mem_write(base, bytes(code))
        uc.mem_write(0x10000000 + 38, bytes([m]))
        for i, r in enumerate(regs):
            uc.reg_write(r, 0x1234560 + 0x111 * i)
        uc.reg_write(mk.UC_M68K_REG_D0, 0xdeadbe00 | (m ^ 0x5a))       # le haut de d0 : ce qui traînait
        uc.reg_write(getattr(mk, f"UC_M68K_REG_{areg}"), 0x10000000)
        uc.reg_write(mk.UC_M68K_REG_A7, 0x10000800)
        uc.emu_start(at_, base + len(blob), count=count)               # jusqu'à la branche comprise
        return uc.reg_read(mk.UC_M68K_REG_PC), [uc.reg_read(r) for r in regs[1:]]

    for name, pat, orig, areg, n_stock, n_new in sites:
        a = at[name]
        off = a - base + 4
        stock = bytearray(blob)
        stock[off:off + len(bytes.fromhex(orig))] = bytes.fromhex(orig)
        diff, took = [], {}
        for m in range(256):
            pa, ra = run(stock, a, areg, m, n_stock)
            pb, rb = run(blob, a, areg, m, n_new)
            took[m] = pb
            if pa != pb or ra != rb:
                diff.append(m)
        sampler = sorted(m for m in range(256) if took[m] == took[6])
        check(diff == [14] and sampler == [6, 14],
              f"{label} : Model-TG, {name} : 256 machines, même branche et mêmes registres que le code d'origine "
              f"sauf {diff} ; pris pour un Sampler : {sampler}")


def pitch(fw, label):
    """La note jouée : fondamentale mesurée (modal harmonique, corde) pour quelques notes et PITCH."""
    bad, seen = [], []
    for shape, note, p in ((0, 48, 64), (2, 60, 64), (2, 57, 64), (0, 60, 76), (2, 36, 52)):
        kw = dict(KW, shape=shape, note=note, pitch=p, contour=36, decay=100)
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
    gs.set_base(fw.dest)
    fname = gs.DESCN + gs.FTUN * 0x38 + 0x2c         # le nom long de FINE, que montre la fenetre du potard
    seen = []
    for k_, f_ in ((gmo.SHAPE_KNOB, True), (gmo.SHAPE_KNOB, False), (gmo.SHAPE_KNOB, True), (2, True)):
        b.lookup(m, k_, f_)
        seen.append(b.cstr(b.u32(fname)))
    b.lookup(fw.views["macro"].index, 2, True)
    seen.append(b.cstr(b.u32(fname)))
    check(seen == ["Voices", "Pitch", "Voices", "Pitch", "Pitch"],
          f"{label} : nom dans la fenetre du potard : FUNC + SHAPE « Voices », puis « Pitch » des la recherche "
          f"suivante (SHAPE seul, FUNC + PITCH, MACRO FUNC + PITCH) : {seen}")
    names = [b.cstr(b.u32(gs.DESCN + (first + i) * 0x38 + 0x2c)) for i in range(4)]
    check(all(len(w) <= gs.NAME_WORD for n_ in names for w in n_.split(" ")),
          f"{label} : noms des potards {names} : {gs.NAME_WORD} lettres au plus par mot (la fenetre du potard)")
    b.lookup(m, gmo.SHAPE_KNOB, True)           # nos fonctions sur l'objet d'interface de FINE
    steps = {(c, d): b.edit_func(lofi_ui.FTUN, c, d) for c in (0x4000, 0x5000, 0x6000, 0x4080, 0x0, 0x7f00)
             for d in (0x100, -0x100, 0x300, -0x300, 1, -1)}
    want = lambda c, d: 0x4000 + 0x1000 * max(0, min(2, (2 if c >= 0x5800 else 1 if c >= 0x4800 else 0)
                                                       + (1 if d > 0 else -1 if d < 0 else 0)))
    bad = [(hex(c), hex(d), hex(v)) for (c, d), v in steps.items() if v != want(c, d)]
    check(not bad, f"{label} : FUNC + un tour de SHAPE (vrai 0x4000b7d6) : un cran par tour, 1, 2, 3 voix "
                   f"(0x4000, 0x5000, 0x6000), bornés {bad[:3]}")
    shown = {v: b.text(lofi_ui.FTUN, v) for v in (0x4000, 0x5000, 0x6000)}
    check(list(shown.values()) == ["1", "2", "3"], f"{label} : texte de la valeur (vrai sprintf de l'OS) : {shown}")
    shots = {v: (b.popup(lofi_ui.FTUN, v), b.popup(lofi_ui.FTUN, v, text_path=True)) for v in (0x4000, 0x5000, 0x6000)}
    bad = [hex(v) for v, (x, y) in shots.items() if x is None or y is None or x != y or x[1]]
    check(not bad, f"{label} : fenêtre de valeur (vrai 0x4001d818) : 1, 2, 3, pixel pour pixel le texte que l'OS "
                   f"dessine par son chemin texte, pas de jauge {bad}")
    if not bad:
        print("      fenêtre de valeur, FUNC + SHAPE sur 3 voix :")
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
                         or addr in range(S.GAIN, S.GAIN + 12) or addr in range(S.GAIN_NEXT, S.GAIN_NEXT + 12)
                         or addr in range(TG["track_slot"], TG["track_slot"] + 24)       # la case en attente,
                         or addr in range(TG["track_pend"], TG["track_pend"] + 24)):     # prise (notes/80)
            stray.append((hex(pc), hex(addr)))
        if ram and not mine:
            foreign.append((hex(pc), hex(addr)))
    e.uc.hook_add(UC_HOOK_MEM_WRITE, wr)
    for t in range(6):
        e.set(t, **dict(KW, machine=m.index, shape=t % 4, finetune=POLY_FINE[(1, 2, 3)[t % 3]], note=40 + 4 * t))
    for b in range(120):
        e.block(0x3f if b in (1, 60) else 0)
    check(not stray and not foreign and not e.unmapped,
          f"{label} : 6 pistes MODAL (les 4 modèles), 120 blocs : MODAL n'écrit que dans ses variables "
          f"({bss[0]:#x}..), l'état de ses pistes ({RAM[0]:#x}..{RAM[1]:#x}), la voix, les gains et la sortie ; "
          f"personne d'autre dans l'état de ses pistes {stray[:2]} {foreign[:2]}")


# --- 8. coût --------------------------------------------------------------------------------------------------------
def cost(fw, label):
    m = fw.views["modal"]
    res, smp = [], {}
    si = sample_pcm("sinus", 9000)
    for shape in range(len(gmo.MODELS)):
        for poly, tg in ((1, None), (2, None), (3, None), (1, dict(slots=[(5, HASH5, si)], slot=5))):
            e = fw.engine(solo=0)
            e.set(0, **dict(KW, machine=m.index, shape=shape, finetune=POLY_FINE[poly], decay=100))
            if tg:
                tg_put(e, **tg)
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
            if tg:
                smp[shape] = n["i"] // 16
            else:
                res.append((shape, poly, n["i"] // 16))
    for shape in range(len(gmo.MODELS)):
        row = ", ".join(f"{p} voix {i}" for s, p, i in res if s == shape)
        print(f"      {label} : SHAPE {shape} ({gmo.MODELS[shape]}) : {row} instructions par bloc ; 1 voix avec un "
              f"sample en entrée {smp[shape]}")
    check(all(i < 120_000 for _, _, i in res) and all(i < 120_000 for i in smp.values()),
          f"{label} : coût d'une piste MODAL mesuré (instructions de MODAL par bloc, voir ci-dessus), toujours sous "
          f"120 000, avec un sample en entrée compris")


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
        print("Model-TG : une piste MODAL porte un sample")
        tg_machine_tests(tg_tw, f"MODAL dans {label}")
        print("FUNC + SHAPE")
        poly_ui(without, fw, f"MODAL dans {label}")
        lofi_ui.check_lofi(ref_eng.img, fw.img, fw.payload, fw.views["macro"].index, f"MACRO dans {label}", check,
                           end=fw.blob_end, base_end=ref_eng.blob_end, base_payload=ref_eng.payload,
                           base="les mêmes mods sans MACRO, ACID ni MODAL", after=1)
        print("son")
        gs.set_base(fw.dest)
        gs.set_rows(8)
        exact(fw, host, args.quick, f"MODAL dans {label}")
        samples(fw, host, f"MODAL dans {label}")
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
        setup = {t: dict(KW, machine=mv.index, shape=(0, 1, 2, 3, 0, 2)[t], note=40 + 5 * t, decay=110) for t in range(6)}
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
