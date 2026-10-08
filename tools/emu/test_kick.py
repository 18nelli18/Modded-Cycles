#!/usr/bin/env python3
"""Preuve des machines Kick2 et Kick3 (notes/47) : deux kicks en 7e et 8e machines (26-kick.json), ports de zicBox
(PotKick.h et KickWave.h) en virgule fixe. Le vrai code de l'OS, émulé (Unicorn), avec la charge utile telle que le
crochet de démarrage la reconstitue.

  1. Démarrage : le décompresseur du bootstrap relit l'OS agrandi ; le crochet (stub.S, PACK) remet à zéro la zone de
     la charge utile, y recopie ses morceaux, ne touche pas à la SRAM, puis reprend (remise à zéro du BSS de l'OS).
  2. Interface : les vérifications de test_syntakt_machines.py pour deux machines ajoutées : rangées, recherches,
     descripteurs, écran MACHINES, molette, enregistrements, changement de machine réel, potards, icône.
  3. Son :
     - aucune instruction flottante ni appel à libgcc dans le code des machines (le ColdFire n'a pas de FPU) ;
     - Kick3 suit KickWave.h : sa sortie, avant la chaîne d'ampli, est comparée à un modèle en virgule flottante de
       KickWave.h (calculé ici, mêmes réglages) : corrélation d'au moins 0,93 sur 10 réglages (les 4 formes d'onde,
       skew, harmonique 2, repli d'onde, les 4 caractères de la chute de hauteur ; 0,88 avec PUNCH, dont l'étage de
       l'OS n'est pas dans le modèle) ;
     - Kick2 et Kick3 jouent à tous les réglages (bouts de chaque potard, PUNCH, DECAY), sans accès hors mémoire,
       avec un niveau borné ;
     - les machines d'origine ne changent pas (OS d'origine) et aucune instruction des kicks ne tourne sans piste kick ;
     - machine locks (Kick2, Kick3, SNARE sur la même piste), les 6 pistes en kick, kicks mêlés aux machines d'origine.
  4. Coût : instructions par bloc de chaque machine, comparé à TONE.
  5. Avec les autres mods (--with) : démarrage, machines d'origine identiques aux mêmes mods sans les kicks, et les kicks
     identiques à eux seuls.

    python3 tools/emu/test_kick.py --cycles model-cycles_OS1.13.syx [--with 6ch-usbup,trig-hold,arp,tempo-max,boot-anim]

Durée : environ 6 min, plus 3 min avec --with.
"""
import argparse
import json
import math
import pathlib
import re
import struct
import subprocess
import sys
import tempfile

import numpy as np
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_kick as gk               # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
import test_syntakt_machines as tsm  # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = E.BASE
check = t7.check                    # échecs : t7.FAIL
KICK2, KICK3, TONE = 6, 7, 4
OFF = 9                             # machine hors limites : la voix n'est pas calculée
BASE_KW = dict(note=60, pitch=64, color=0, shape=0, sweep=64, contour=64, punch=0, gate=0, finetune=64, decay=50)


def load(name):
    return json.loads((DEV / name).read_text(encoding="utf-8"))


class Fw:
    """Un firmware : MAIN OS (avec ce qui est ajouté après), et la charge utile des kicks telle qu'en mémoire."""

    def __init__(self, stock, tweaks):
        p, _ = build.apply_writes(stock, tweaks)
        pl, _ = build.build_payload(tweaks, stock, None)
        self.img, self.tweaks = bytes(p) + pl, tweaks
        ours = [t for t in tweaks if t["id"] == "kick"]
        self.payload = None
        if not ours:
            return
        ap_ = ours[0]["append"]
        self.pay = int(ap_["dest"], 16)
        self.runtime = build.payload_runtime(ours[0], stock, None)
        self.payload = (self.pay, self.runtime)
        self.code_end = self.pay + len(ap_["parts"][0]["hex"]) // 2           # code et tables des deux moteurs
        self.syms = {k: int(v, 16) for k, v in ours[0]["symbols"].items()}

    def engine(self, solo=None):
        e = E.Engine(self.img, payload=self.payload)
        if solo is not None:             # les autres pistes : machine hors limites, rien n'est calculé
            for t in range(6):
                if t != solo:
                    e.uc.mem_write(E.VOICE0 + t * E.VSTRIDE, struct.pack(">II", OFF, OFF))
        return e


# --- 1. démarrage ----------------------------------------------------------------------------------------------
def boot(fw):
    """Le crochet de démarrage, exécuté pour de vrai : au début de la remise à zéro du BSS (0x400004b2, jusqu'à son
    retour)."""
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)
    uc.mem_write(BASE, fw.img)
    dst, rt = fw.payload
    uc.mem_map(dst, 0x00100000)
    uc.mem_write(dst, b"\xa5" * 0x00100000)              # ce que la SDRAM contient avant : n'importe quoi
    uc.mem_map(0x80000000, 0x00010000)
    sram = bytearray(0x10000)                             # SRAM après son initialisation par l'OS (0x4000045c)
    for lo, hi, d in gs.CY_SRAM_INIT:
        sram[d - 0x80000000:d - 0x80000000 + hi - lo] = fw.img[lo - BASE:hi - BASE]
    uc.mem_write(0x80000000, bytes(sram))
    uc.mem_map(0x90000000, 0x00020000)
    uc.mem_write(E.STOP, b"\x4e\x71\x4e\x71")
    bad = []
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: bad.append(addr) or False)
    keep = {r: 0x11110000 + i for i, r in enumerate((mk.UC_M68K_REG_D2, mk.UC_M68K_REG_D3, mk.UC_M68K_REG_D4,
                                                     mk.UC_M68K_REG_D5, mk.UC_M68K_REG_D6, mk.UC_M68K_REG_D7,
                                                     mk.UC_M68K_REG_A2, mk.UC_M68K_REG_A3, mk.UC_M68K_REG_A4,
                                                     mk.UC_M68K_REG_A5, mk.UC_M68K_REG_A6))}
    for r, v in keep.items():
        uc.reg_write(r, v)
    sp0 = 0x90010000
    uc.mem_write(sp0, struct.pack(">I", E.STOP))
    uc.reg_write(mk.UC_M68K_REG_A7, sp0)
    uc.emu_start(0x400004b2, E.STOP, count=100_000_000)
    regs = all(uc.reg_read(r) == v for r, v in keep.items())
    tail = BASE + E.IMAGE_LEN
    cleared = not any(uc.mem_read(tail, len(fw.img) - E.IMAGE_LEN)) and not any(uc.mem_read(0x42338000, 0xb0))
    check(uc.reg_read(mk.UC_M68K_REG_PC) == E.STOP and uc.reg_read(mk.UC_M68K_REG_A7) == sp0 + 4 and regs
          and cleared and not bad,
          "0x400004b2 -> notre crochet -> remise à zéro du BSS de l'OS (nos morceaux rangés compris), retour normal, "
          "d2..d7/a2..a6 intacts")
    got = bytes(uc.mem_read(dst, len(rt)))
    packed = sum(n for _, n in next(t for t in fw.tweaks if t["id"] == "kick")["append"]["pack"])
    check(got == rt, f"charge utile reconstituée à {dst:#x} : {len(rt)} o (code et tables, détours, données), "
                     f"rangée en {packed} o dans l'image")
    check(bytes(uc.mem_read(0x80000000, 0x10000)) == bytes(sram), "SRAM intacte")
    end = BASE + len(fw.img)
    check(end <= gs.END_LIMIT, f"image décompressée jusqu'à {end:#x} (limite {gs.END_LIMIT:#x})")


# --- 2. interface ----------------------------------------------------------------------------------------------
def interface(stock, fw):
    """Les vérifications de test_syntakt_machines.py, pour deux machines ajoutées : Kick2 et Kick3."""
    tsm.SAFE = True
    tsm.ADDED = [dict(m, code=m["prefix"], label=m["name"]) for m in gk.MACHINES]
    tsm.N, tsm.NM, tsm.TOP = gk.N, 6 + gk.N, 5 + gk.N
    tsm.FIRST = {m["index"]: f for m, f in zip(gk.MACHINES, gk.FIRSTS)}
    tsm.REC = {m["index"]: gs.RECS + 0x60 * i for i, m in enumerate(gk.MACHINES)}
    tsm.ROWS, tsm.CCROWS = gs.ROWSN, gs.CCROWSN
    tsm.NAMES = ["Kick", "Snare", "Metal", "Perc", "Tone", "Chord"] + [m["name"] for m in gk.MACHINES]
    patched, payload = fw.img, fw.runtime
    a, b = tsm.tables(stock, patched, payload)
    tsm.lookups(a, b)
    tsm.accessors(a, b, stock, patched)
    tsm.screens(stock, patched, payload)
    tsm.setter_and_wheel(stock, patched, payload)
    tsm.records_and_change(stock, patched, payload)
    tsm.out_of_range(stock, patched, payload)
    tsm.small_icon(stock, patched, payload)


# --- 3. son : un modèle en virgule flottante de KickWave.h -------------------------------------------------------
# Les 4 caractères de la chute de hauteur de Kick3 (tools/machines/kick/zic_kick3.cpp) : profondeur, tau en
# échantillons (n1, n2), poids de la 1re exponentielle.
PRESETS = ((1.2, 1440, 2160, 1.0), (3.5, 336, 2160, 1.0), (7.0, 240, 2160, 0.65), (10.0, 4320, 2160, 1.0))


def kickwave_ref(pitch, color, shape, sweep, contour, punch, decay, n):
    """KickWave.h en virgule flottante, 48 kHz, avec les réglages que le port lui donne (notes/47) : triangle et scie
    qui montent depuis 0 comme le sinus, repli d'onde en fondu sur ses 6 premiers %, chute de hauteur en 2 exponentielles."""
    sr = 48000.0
    wave, fold = color / 127, shape / 127
    skew = 0.05 + 0.9 * sweep / 127
    h2 = (contour - 64) / 64
    total = 2400 + decay * 548
    k = pitch / 127 * 3
    seg = min(int(k), 2)
    t = k - seg
    lerp = lambda a, b: a + (b - a) * t
    depth, n1, n2, w1 = (lerp(PRESETS[seg][i], PRESETS[seg + 1][i]) for i in range(4))
    m1, m2 = math.exp(-1 / n1), math.exp(-1 / n2)
    phase = mod = 0.0
    e1 = e2 = 1.0
    comp = 0.0
    inv = 1.0
    out = np.zeros(n)
    base = 52.0
    for i in range(n):
        if i < 32:                       # le trig est au bloc 1
            continue
        env = 0.0
        if inv > 0:
            env = inv ** 5
            inv -= 1.0 / total
        sig = 0.0
        if env > 0.0001:
            e1 *= m1
            e2 *= m2
            pe = w1 * e1 + (1 - w1) * e2
            f = base * (1 + depth * pe)
            mod = (mod + f * 1.5 / sr) % 1
            fm = math.sin(2 * math.pi * mod) * pe * 0.35 * 0.75 * 20 / 2048
            phase = (phase + f / sr + fm) % 1
            pw = 0.5 * phase / skew if phase < skew else 0.5 + 0.5 * (phase - skew) / (1 - skew)
            s = math.sin(2 * math.pi * pw)
            tri = 1 - 2 * abs(2 * (((pw + 0.25) % 1) - 0.5))
            saw = (pw + 0.5) % 1 * 2 - 1
            sq = 1.0 if s > 0 else -1.0
            if wave < 1 / 3:
                m = s + (tri - s) * (wave * 3)
            elif wave < 2 / 3:
                m = tri + (saw - tri) * ((wave - 1 / 3) * 3)
            else:
                m = saw + (sq - saw) * ((wave - 2 / 3) * 3)
            m = max(-1, min(1, m + h2 * math.sin(4 * math.pi * pw)))
            if fold > 0:
                fo = math.sin(m * (1 + fold * 3.5) * math.pi / 2)
                m += (fo - m) * min(fold * 16, 1)
            sig = m * env
        o = sig
        if punch:
            o = math.tanh(o * 6.25) * 6.25
        comp += 0.05 * (abs(o) - comp)
        if comp > 0.65:
            o *= 0.65 / comp
        out[i] = max(-1, min(1, o))
    return out


def play(fw, idx, kw, blocks, trigs=(1,), changes=None, track=0, hook=None):
    """Une piste sur la machine idx, les autres éteintes. changes : {bloc : réglages} (p-locks, potards)."""
    e = fw.engine(solo=track)
    e.set(track, machine=idx, **dict(BASE_KW, **kw))
    if hook:
        e.uc.hook_add(UC_HOOK_CODE, hook[0], begin=hook[1], end=hook[2])
    out = []
    for b in range(blocks):
        for k, v in (changes or {}).get(b, {}).items():
            e.set(track, **{k: v})
        out.append(e.block(1 << track if b in trigs else 0)[track])
    return np.concatenate(out).astype(np.float64) / 2**31, e.unmapped, e


def best_corr(x, r, maxlag=64):
    """Corrélation normalisée de x (sortie de l'OS) et r (modèle), au meilleur décalage : la chaîne d'ampli de l'OS
    retarde la sortie de quelques dizaines d'échantillons."""
    best = (-2.0, 0)
    for d in range(-maxlag, maxlag + 1):
        a, b = x[max(0, d):len(x) + min(0, d)], r[max(0, -d):len(r) + min(0, -d)]
        c = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
        best = max(best, (c, d))
    return best


def sound_reference(fw):
    """Kick3 contre le modèle en virgule flottante de KickWave.h."""
    cases = (("sinus", dict(pitch=64, color=0)),
             ("triangle", dict(pitch=64, color=42)),
             ("scie + skew + harmonique 2 négatif", dict(pitch=64, color=85, sweep=0, contour=20)),
             ("carré", dict(pitch=64, color=127)),
             ("repli d'onde + harmonique 2", dict(pitch=30, color=20, shape=100, sweep=60, contour=100)),
             ("drive (PUNCH)", dict(pitch=100, punch=1)),
             ("chute : glissé doux", dict(pitch=0, color=40)),
             ("chute : classique", dict(pitch=42, color=40)),
             ("chute : gabber", dict(pitch=85, color=40)),
             ("chute : plongeon long", dict(pitch=127, color=40)))
    for name, kw in cases:
        kw = dict(BASE_KW, **kw)
        x, unm, _ = play(fw, KICK3, kw, 250)
        r = kickwave_ref(kw["pitch"], kw["color"], kw["shape"], kw["sweep"], kw["contour"], kw["punch"], kw["decay"], len(x))
        lo, hi = 64, min(len(x), 20000)
        c, lag = best_corr(x[lo:hi], r[lo:hi])
        # avec PUNCH, la chaîne d'ampli de l'OS ajoute son propre étage PUNCH (0x400a967a), que le modèle ne connaît pas :
        # la corrélation est plus basse (0,91 mesuré)
        need = 0.88 if kw["punch"] else 0.93
        check(c >= need and not unm and np.abs(x).max() > 0.05,
              f"Kick3 {name} : corrélation {c:.3f} (au moins {need}) avec KickWave.h en flottant (décalage {lag} échantillons)")


def sound_plays(fw):
    """Les deux machines jouent à tous les réglages, sans accès hors mémoire, avec un niveau borné."""
    knobs = dict(pitch=(0, 64, 127), color=(0, 64, 127), shape=(0, 64, 127), sweep=(0, 64, 127), contour=(0, 64, 127),
                 decay=(0, 64, 127), punch=(0, 1))
    for idx, name in ((KICK2, "Kick2"), (KICK3, "Kick3")):
        bad, runs = [], 0
        for knob, values in knobs.items():
            for v in values:
                kw = dict(BASE_KW, **{knob: v})
                x, unm, _ = play(fw, idx, kw, 80)
                runs += 1
                if unm or not (0.02 < np.abs(x).max() <= 1.0):
                    bad.append((knob, v, float(np.abs(x).max()), len(unm)))
        check(not bad, f"{name} : {runs} réglages (chaque potard à 0, 64, 127 ; PUNCH) jouent, sans accès hors mémoire, "
                       f"niveau entre 0,02 et 1 {bad[:3]}")
        x, unm, _ = play(fw, idx, dict(color=127, shape=127, sweep=127, contour=127, pitch=127, punch=1, decay=127), 120)
        check(not unm and np.abs(x).max() <= 1.0, f"{name} : tous les potards au maximum, PUNCH et DECAY 127")
    # une note plus aiguë et plus grave : la hauteur suit la note
    for idx, name in ((KICK2, "Kick2"), (KICK3, "Kick3")):
        res = []
        for note in (36, 60, 84):
            x, unm, _ = play(fw, idx, dict(note=note, decay=20), 60)
            res.append((len(unm), float(np.abs(x).max())))
        check(all(u == 0 and m > 0.02 for u, m in res), f"{name} : notes 36, 60, 84 jouent {res}")


def no_float(fw):
    """Pas d'instruction flottante, pas d'appel à la libgcc dans les fonctions des deux machines : on désassemble
    l'ELF des moteurs (.text seul, sans leurs tables) et on regarde les mnémoniques et les cibles des appels."""
    cross = next((c for c in ("m68k-linux-gnu-", "m68k-elf-") if subprocess.run(["which", c + "objdump"],
                                                                                 capture_output=True).returncode == 0),
                 None)
    if not cross:
        check(False, "pas d'objdump m68k pour vérifier le code")
        return
    with tempfile.TemporaryDirectory() as d:
        blob, _ = gk.compile_machines(pathlib.Path(d), fw.pay)
        out = subprocess.run([cross + "objdump", "-d", "-m", "m68k:cfv4e", str(pathlib.Path(d) / "kick.elf")],
                             capture_output=True, text=True).stdout
    os_calls = {0x400a9252, 0x400a9430, 0x400a967a}          # chaîne d'ampli de l'OS, comme TONE
    flt, outside, n = [], [], 0
    for line in out.splitlines():
        f = line.split("\t")
        if len(f) < 3 or not re.match(r"\s*[0-9a-f]+:$", f[0]):
            continue
        n += 1
        op = f[2].split()[0] if f[2].split() else ""
        if op.startswith("f") and not op.startswith("fb"):
            flt.append(line)
        m = re.match(r"(?:jsr|bsr\w*|jmp)\s+0x([0-9a-f]+)", f[2].strip())
        if m and not (fw.pay <= int(m.group(1), 16) < fw.pay + len(blob)) and int(m.group(1), 16) not in os_calls:
            outside.append(line)
    check(n > 500 and not flt and not outside,
          f"code des kicks : {n} instructions, aucune flottante, aucun appel hors de la charge utile sauf la chaîne "
          f"d'ampli de l'OS {(flt + outside)[:2]}")


def stock_unchanged(ref_fw, fw, label):
    """6 pistes sur les machines d'origine (2 trigs) : identiques, et rien du code des kicks ne tourne."""
    def run(f, hook):
        e = f.engine()
        for t in range(6):
            e.set(t, **dict(BASE_KW, machine=t, color=64, shape=64, contour=64, decay=60))
        ran = []
        if hook:
            e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: ran.append(a), begin=f.pay, end=f.code_end - 1)
        x = np.stack([e.block(0x3f if b in (1, 150) else 0) for b in range(300)])
        return x, ran, e.unmapped
    r, _, _ = run(ref_fw, False)
    x, ran, unm = run(fw, True)
    check(np.array_equal(r, x) and np.abs(x).max() > 1e7 and not ran and not unm,
          f"6 machines d'origine : identiques à {label}, échantillon par échantillon, sans une instruction des kicks")


def locks(fw, label):
    """Sur une même piste : Kick2, Kick3, SNARE, Kick3, Kick2 : chacune joue."""
    e = fw.engine(solo=0)
    e.set(0, **dict(BASE_KW, machine=KICK2))
    seq = {60: dict(machine=KICK3), 120: dict(machine=1, color=0, shape=127, sweep=8, contour=0),
           180: dict(machine=KICK3), 240: dict(machine=KICK2)}
    x = e.render(310, trig_at=(1, 61, 121, 181, 241), on_block=lambda eng, b: eng.set(0, **seq[b]) if b in seq else None)
    segs = [np.abs(x[32 * a:32 * b]).max() / 2**31 for a, b in ((2, 58), (62, 118), (122, 178), (182, 238), (242, 308))]
    check(all(s > 0.05 for s in segs) and not e.unmapped,
          f"{label} : Kick2 -> Kick3 -> SNARE -> Kick3 -> Kick2 sur une piste : chacune joue "
          f"{[round(float(s), 2) for s in segs]}")


def six_tracks(fw, label):
    """Les 6 pistes en kick (3 + 3), trig en même temps : chaque piste identique à elle seule."""
    solo = []
    for t in range(6):
        idx = KICK2 if t % 2 == 0 else KICK3
        x, _, _ = play(fw, idx, dict(decay=30, color=20 * t), 150, track=t)
        solo.append(x)
    e = fw.engine()
    for t in range(6):
        e.set(t, **dict(BASE_KW, machine=KICK2 if t % 2 == 0 else KICK3, decay=30, color=20 * t))
    x = np.stack([e.block(0x3f if b == 1 else 0) for b in range(150)])        # (blocs, pistes, 32)
    got = [x[:, t, :].reshape(-1).astype(np.float64) / 2**31 for t in range(6)]
    check(all(np.array_equal(g, s) for g, s in zip(got, solo)) and not e.unmapped,
          f"{label} : 6 pistes en kick ensemble (3 Kick2, 3 Kick3), chacune identique à elle seule")


def mixed(fw, ref_fw, label):
    """Kicks mêlés aux machines d'origine : les pistes d'origine restent identiques à celles du firmware sans kicks."""
    def run(f):
        e = f.engine()
        ms = (0, KICK2, 2, KICK3, 4, 5)
        for t in range(6):
            e.set(t, **dict(BASE_KW, machine=ms[t], color=64, shape=64, contour=64, decay=50))
        return np.stack([e.block(0x3f if b == 1 else 0) for b in range(200)]), e.unmapped
    x, unm = run(fw)
    r, _ = run(ref_fw) if ref_fw is not None else (None, None)
    ok = not unm and np.abs(x).max() > 1e7
    if r is not None:
        # un firmware sans kicks ne sait pas jouer les pistes 1 et 3 : seules les pistes d'origine se comparent
        ok &= all(np.array_equal(x[:, t, :], r[:, t, :]) for t in (0, 2, 4, 5))
    check(ok, f"{label} : kicks mêlés à KICK, METAL, TONE, CHORD : les pistes d'origine sont identiques")


def cost(fw):
    """Instructions par bloc de chaque machine (une voix qui joue), comparées à TONE (celle de l'OS)."""
    res = {}
    for idx, name in ((TONE, "TONE"), (KICK2, "Kick2"), (KICK3, "Kick3"), (KICK3, "Kick3 tout au maximum")):
        e = fw.engine(solo=0)
        kw = dict(BASE_KW, machine=idx)
        if name.endswith("maximum"):
            kw.update(color=127, shape=127, sweep=127, contour=127, pitch=127, punch=1)
        e.set(0, **kw)
        for b in range(6):
            e.block(1 if b == 0 else 0)
        n = [0]

        def hk(uc, a, s, u):
            n[0] += 1
        e.uc.hook_add(UC_HOOK_CODE, hk)
        counts = []
        for b in range(6, 14):
            n[0] = 0
            e.block(0)
            counts.append(n[0])
        res[name] = (max(counts), int(np.mean(counts)))
    print("        instructions par bloc (pire, moyenne) : " + ", ".join(f"{k} {v[0]}/{v[1]}" for k, v in res.items()))
    check(all(v[0] > 0 for v in res.values()), "coût mesuré pour chaque machine")


# --- 5. avec les autres mods -------------------------------------------------------------------------------------
def with_others(stock, cycles, ids, alone):
    by_id = {t["id"]: t for t in (load(f.name) for f in sorted(DEV.glob("[0-9]*.json")))}
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        raise SystemExit(f"!! tweaks inconnus : {unknown}")
    others = [by_id[i] for i in ids]
    mine = by_id["kick"]
    clash = [t["id"] for t in others if mine["id"] in t.get("conflicts", []) or t["id"] in mine["conflicts"]]
    if clash:
        raise SystemExit(f"!! incompatibles avec kick : {clash}")
    fw = Fw(stock, sorted(others + [mine], key=lambda t: t["order"]))
    ref_fw = Fw(stock, sorted(others, key=lambda t: t["order"]))
    label = ", ".join(ids)
    print(f"\n== kick avec {label}")
    print("démarrage")
    t7.X.bootstrap_depack_ok(cycles, fw.tweaks, None) or t7.FAIL.append("bootstrap avec " + label)
    boot(fw)
    print("son")
    stock_unchanged(ref_fw, fw, f"{label} sans les kicks")
    for idx, name in ((KICK2, "Kick2"), (KICK3, "Kick3")):
        a, _, _ = play(alone, idx, dict(decay=40, color=64, shape=50), 200, (1, 120))
        b, unm, _ = play(fw, idx, dict(decay=40, color=64, shape=50), 200, (1, 120))
        check(np.array_equal(a, b) and not unm and a.any(), f"{name} avec {label} : sortie identique à celle des kicks seuls")
    locks(fw, f"kick avec {label}")
    mixed(fw, ref_fw, f"kick avec {label}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--with", dest="others", default="", help="ids d'autres tweaks : les kicks avec eux (section 5)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    kick = load("26-kick.json")
    off = Fw(stock, [])
    alone = Fw(stock, [kick])
    print("== kick : Kick2 en machine 7, Kick3 en machine 8")
    print("démarrage")
    t7.X.bootstrap_depack_ok(args.cycles, kick, None) or t7.FAIL.append("bootstrap")
    boot(alone)
    print("interface")
    interface(stock, alone)
    print("son")
    no_float(alone)
    sound_reference(alone)
    sound_plays(alone)
    stock_unchanged(off, alone, "l'OS d'origine")
    locks(alone, "kick seul")
    six_tracks(alone, "kick seul")
    mixed(alone, None, "kick seul")
    print("coût")
    cost(alone)
    if args.others:
        with_others(stock, args.cycles, args.others.split(","), alone)
    print("\nTOUT OK" if not t7.FAIL else f"\n{len(t7.FAIL)} ÉCHEC(S)")
    return 1 if t7.FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
