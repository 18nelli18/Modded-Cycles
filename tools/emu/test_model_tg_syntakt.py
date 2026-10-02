#!/usr/bin/env python3
"""Preuve de la version combinée Model-TG + moteurs du Syntakt (notes/31 §4) : 30-model-tg-st.json, puis un tweak
31-syntakt-tg-….json par-dessus (tools/gen_syntakt_engines.py --tg).

Références : Model-TG seul (30-model-tg.json, son build officiel ; et 30-model-tg-st.json pour l'interface) et nos
moteurs seuls (24-syntakt-….json).

  1. Démarrage : le jsr de 0x40000530 entre dans notre crochet, qui remet à zéro la zone de la charge utile, y
     recopie ses morceaux depuis l'image, remplit les deux zones de SRAM, puis passe la main à boot_extra_hook de
     Model-TG avec la pile et les registres d0..d1/a0..a1 exceptés intacts.
  2. Interface (le vrai code de l'OS) : rangées de paramètres, recherches (slot, machine) et CC, machine d'un
     descripteur, enregistrements par machine, noms, potards : machines 0..6 (Sampler compris) identiques à
     Model-TG seul, les nôtres (7..) comme SNARE avec leurs propres descripteurs.
  3. Son (la boucle des voix de l'OS) : machines d'origine identiques à Model-TG seul ; Sampler sans échantillon
     muet ; chaque moteur du Syntakt identique, échantillon par échantillon, à nos moteurs seuls ; et tout cela
     ensemble sur les 6 pistes.
  4. Régulateur de charge : en surcharge, il éteint des voix, jamais le Sampler ni la piste dont Model-TG édite les
     tranches (même règle que pour la piste qu'il enregistre).

    python3 tools/emu/test_model_tg_syntakt.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        [--engines sd,cp,toy,bits,swarm]
"""
import argparse
import json
import pathlib
import re
import struct
import sys

import numpy as np
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_sdvintage_7th as g7      # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import syntakt                      # noqa: E402
import test_model_tg as TM          # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402
from test_sdvintage_7th import fill_records, refcount, REC_BASE, REC_LEN  # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = E.BASE
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def load(name):
    return json.loads((DEV / name).read_text(encoding="utf-8"))


class Fw:
    """Un firmware : MAIN OS (avec ce qui est ajouté après) et, s'il y en a une, la charge utile telle qu'en mémoire."""

    def __init__(self, stock, tweaks, st_img, syntakt_path):
        p, _ = build.apply_writes(stock, tweaks)
        pl, _ = build.build_payload(tweaks, stock, syntakt_path)
        self.img = bytes(p) + pl
        self.tweaks = tweaks
        ours = [t for t in tweaks if t.get("append", {}).get("syntakt")]
        self.payload = None
        if ours:
            ap_ = ours[0]["append"]
            self.payload = (int(ap_["dest"], 16), build.payload_runtime(ours[0], stock, st_img))
        tg = [t for t in tweaks if t["id"].startswith("model-tg")]
        self.blob_end = BASE + len(stock) + tg[0]["append"]["size"] if tg else None


# --- 1. démarrage ----------------------------------------------------------------------------------------------
def boot(fw, tg):
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
    bad = []
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: bad.append(addr) or False)
    keep = {r: 0x11110000 + i for i, r in enumerate((mk.UC_M68K_REG_D2, mk.UC_M68K_REG_D3, mk.UC_M68K_REG_D4,
                                                     mk.UC_M68K_REG_D5, mk.UC_M68K_REG_D6, mk.UC_M68K_REG_D7,
                                                     mk.UC_M68K_REG_A2, mk.UC_M68K_REG_A3, mk.UC_M68K_REG_A4,
                                                     mk.UC_M68K_REG_A5, mk.UC_M68K_REG_A6))}
    for r, v in keep.items():
        uc.reg_write(r, v)
    sp0 = 0x90010000
    uc.reg_write(mk.UC_M68K_REG_A7, sp0)
    uc.emu_start(gs.BOOT_CALL, tg["boot_extra_hook"], count=5_000_000)
    pc, sp = uc.reg_read(mk.UC_M68K_REG_PC), uc.reg_read(mk.UC_M68K_REG_A7)
    ret = struct.unpack(">I", uc.mem_read(sp, 4))[0]
    regs = all(uc.reg_read(r) == v for r, v in keep.items())
    check(pc == tg["boot_extra_hook"] and sp == sp0 - 4 and ret == gs.BOOT_CALL + 6 and regs and not bad,
          f"jsr 0x40000530 -> notre crochet -> boot_extra_hook {tg['boot_extra_hook']:#x}, pile et d2..d7/a2..a6 intactes")
    got = bytes(uc.mem_read(dst, len(rt)))
    check(got == rt, f"charge utile reconstituée à {dst:#x} ({len(rt)} o, rangée en "
                     f"{sum(n for _, n in fw.tweaks[-1]['append']['pack'])} o dans l'image)")
    want = bytearray(sram)
    for stage, run, n in E.SRAM_BANKS:
        o = stage - E.PAYLOAD_DST
        want[run - 0x80000000:run - 0x80000000 + n] = rt[o:o + n]
    check(bytes(uc.mem_read(0x80000000, 0x10000)) == bytes(want),
          "SRAM : les deux zones (code et voix du Syntakt) remplies, le reste intact")
    end = BASE + len(fw.img)
    check(end <= gs.END_LIMIT, f"image décompressée jusqu'à {end:#x} (limite {gs.END_LIMIT:#x})")


# --- 2. interface ----------------------------------------------------------------------------------------------
class UI(t7.UI):
    def __init__(self, fw):
        super().__init__(fw.img)
        self.uc.mem_write(BASE + E.IMAGE_LEN, fw.img[E.IMAGE_LEN:])      # Model-TG, puis notre ajout rangé
        if fw.payload:
            self.uc.mem_map(fw.payload[0], 0x00100000)
            self.uc.mem_write(*fw.payload)


def interface(ref, fw, codes, tg):
    first, n = gs.TG_FIRST, len(codes)
    nm, top = first + n, first + n - 1
    ours = {first + i: 76 + 5 * i for i in range(n)}       # machine -> 1er descripteur
    snare = lambda x, m: ours[m] + x - 51 if 51 <= x <= 55 else x
    a, b = UI(ref), UI(fw)
    a.call(0x4005a274)
    b.call(0x4005a274)
    check(not a.bad and not b.bad, "constructeur des tables (0x4005a274) sans accès hors mémoire")
    rows_a = bytes(a.uc.mem_read(g7.ROWS, 6 * 32))
    rows_b = bytes(b.uc.mem_read(gs.ROWSN, nm * 32))
    check(rows_b[:6 * 32] == rows_a and b.u32(t7.ROW_COUNT) == nm and not any(rows_b[6 * 32:7 * 32]),
          f"rangées 0..5 identiques à Model-TG, rangée 6 (Sampler) vide, {nm} rangées")

    diff, bad = set(), []
    for m in range(nm):
        for slot in range(34):
            x, y = a.call(0x4005a692, slot, m), b.call(0x4005a692, slot, m)
            if m <= 6 and x != y:
                bad.append((m, slot, x, y))
            if m in ours and y != snare(b.call(0x4005a692, slot, 1), m):
                bad.append((m, slot, "snare", y))
            if m in ours and x != y:
                diff.add(slot)
    check(not bad and diff == {0xb, 0xc, 0xd, 0xe, 0x12},
          f"(slot, machine) -> descripteur (0x4005a692) : 0..6 identiques (Sampler : ses détours), "
          f"{list(ours)} comme SNARE avec les leurs (slots {sorted(diff)}) {bad[:3]}")

    last = 76 + 5 * n
    dm = [(a.call(0x4005a50a, i), b.call(0x4005a50a, i)) for i in range(last + 9)]
    ok = all(x == y for x, y in dm[:76]) and [y for _, y in dm[76:last]] == [v for i in range(n) for v in [first + i] * 4 + [7]]
    check(ok and all(y == dm[0][1] for _, y in dm[last:]),
          f"machine d'un descripteur (0x4005a50a) : 0..75 identiques, 76..{last - 1} -> {[y for _, y in dm[76:last]]}")

    diff = set()
    for t in range(6):
        for m in range(nm):
            for cc in range(128):
                x, y = a.call(0x4005a8ce, t, m, cc), b.call(0x4005a8ce, t, m, cc)
                if x != y:
                    diff.add((m, cc, y))
    check(diff == {(m, cc, ours[m] + cc - 16) for m in ours for cc in (16, 17, 18, 19)},
          f"CC -> descripteur (0x4005a8ce) : identique à Model-TG sauf les nôtres, CC 16..19 ({len(diff)} écarts)")

    for u in (a, b):
        fill_records(u)
    ok = all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in range(8))
    ok &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in range(7))
    ok &= b.call(0x4004df5c, nm + 1) == a.call(0x4004df5c, 1) and b.call(0x4004df76, nm) == a.call(0x4004df76, 0)
    rc, got = refcount(b), {}
    for m in ours:
        k = m - first
        for r in (mk.UC_M68K_REG_A0, mk.UC_M68K_REG_A1):
            b.uc.reg_write(r, 0x12340000 + r)
        r1 = b.call(0x4004df5c, m + 1)
        kept = b.uc.reg_read(mk.UC_M68K_REG_A1) == 0x12340000 + mk.UC_M68K_REG_A1
        r2 = b.call(0x4004df76, m)
        ids = struct.unpack(">17i", bytes(b.uc.mem_read(r1, REC_LEN))[8:])
        ok &= kept and r1 == r2 == gs.RECS + 0x60 * k and ids[:6] == (42, ours[m] + 4, *range(ours[m], ours[m] + 4))
        got[m] = ids[:6]
    ok &= refcount(b) == rc + 2 * n and not b.bad
    check(ok, f"enregistrements (0x4004df5c / 0x4004df76) : 0..7 et 0..6 identiques à Model-TG (Sampler compris), "
              f"hors limites -> KICK, les nôtres {got}, a1 gardé")
    b.uc.mem_write(tg["mod_held"], struct.pack(">I", 1))
    r = b.call(0x4004df5c, first + 1)
    rec, base_ = bytes(b.uc.mem_read(r, REC_LEN)), bytes(b.uc.mem_read(gs.RECS, REC_LEN))
    sw = struct.unpack_from(">I", rec, 12)[0], struct.unpack_from(">I", rec, 24)[0], struct.unpack_from(">I", rec, 28)[0]
    same = rec[:12] + rec[16:24] + rec[32:] == base_[:12] + base_[16:24] + base_[32:]
    check(r == gs.REC_ATK and sw == (0x0d, 0x0c, 0x0b) and same,
          "touche Attack tenue (mod_held) : DECAY, SWEEP, CONTOUR -> Attack, Filtre, Résonance, comme Model-TG")
    b.uc.mem_write(tg["mod_held"], struct.pack(">I", 0))
    pt = tg["param_table"] + 0x2e * g7.DSTRIDE + 44
    b.uc.mem_write(pt, struct.pack(">III", 0x13572468, 0x2468ace0, 0x369cf258))
    b.call(0x4004df5c, 2)
    check(bytes(b.uc.mem_read(gs.DESCN + 0x2e * g7.DSTRIDE + 44, 12)) == bytes(b.uc.mem_read(pt, 12)),
          "libellés que Model-TG change (apply_names, table d'origine) recopiés dans la table lue par l'OS (DESCN)")

    # changement de machine réel (0x400a2712 -> setMachine -> 0x40014072, où Model-TG a ses détours
    # log_trampoline et mc_commit_hook) : du Sampler à notre 1re machine, puis de l'une à l'autre
    res = {}
    for m_to in ours:
        u = UI(fw)
        fill_records(u)
        obj, snd = t7.fake_track(u, m_to - 1)
        del u.hooks[0x40014072]
        this = 0x93900000
        for k in range(6):
            u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
        for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                      0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
            u.hooks[a_] = (f"{a_:#x}", v)
        u.call(0x400a2712, this, 1, 0, 0)
        mach = struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8
        vals = [struct.unpack(">h", u.uc.mem_read(snd + 0x14 + 2 * sl, 2))[0] >> 8 for sl in (0xb, 0xc, 0xd, 0xe, 0x12)]
        res[m_to] = (mach, vals, bool(u.bad))
    want = {first + i: (first + i, [k[2] for k in gs.CATALOG[c]["knobs"]] + [gs.CATALOG[c]["decay"]], False)
            for i, c in enumerate(codes)}
    check(res == want, "changement de machine réel (0x400a2712, avec les détours de Model-TG) : "
                       + ", ".join(f"{m - 1}->{m} {res[m][1]}" for m in res))

    # écran MACHINES : les nm repères sur 2 lignes dans la moitié droite, le plein sur la machine choisie
    rows_ok, where = True, []
    for m in (0, 6, first, top):
        calls = machines_screen(fw, m)
        marks = [(k, a[1], a[2]) for k, a in calls if k.startswith("repère")]
        filled = [i for i, (k, _, _) in enumerate(marks) if k == "repère plein"]
        ys = [y for _, _, y in marks]
        rows_ok &= len(marks) == nm and filled == [m] and min(x for _, x, _ in marks) >= 64 \
            and sorted(set(ys)) == list(gs.MARKS["y"]) and ys.count(gs.MARKS["y"][0]) == gs.MARKS_ROW
        where.append(marks[m][1:])
    check(rows_ok, f"écran MACHINES : {nm} repères sur 2 lignes dans la moitié droite (x >= 64), le plein sur la "
                   f"machine choisie (1, 7, {first + 1}, {top + 1} : {where})")

    blob = bytes(b.uc.mem_read(tg["sampler_name_table"], 28))
    names = bytes(b.uc.mem_read(gs.DATA, 4 * nm))
    strs = [bytes(b.uc.mem_read(struct.unpack_from(">I", names, 4 * m)[0], 6)).split(b"\0")[0].decode()
            for m in range(first, nm)]
    if re.search("meter|profile", fw.tweaks[-1]["id"]):     # diagnostic : chaque nom est un compteur
        check(len(set(struct.unpack(f">{nm}I", names))) == nm, "noms : un compteur par machine (diagnostic)")
    else:
        check(names[:28] == blob and strs == [gs.CATALOG[c]["name"] for c in codes],
              f"noms : les 7 de Model-TG (le Sampler montre son échantillon), puis {strs}")

    res = []
    for m in range(nm + 2):
        b.uc.reg_write(mk.UC_M68K_REG_A2, 0x93000000)
        b.uc.mem_write(0x93000000 + 104, struct.pack(">I", 0x5a5a0000))
        d0 = b.call(tg["knob_vec"], *([0] * 8), m)
        res.append(b.uc.reg_read(mk.UC_M68K_REG_A1) if d0 == m else None)
    vec = gs.DATA + 12 * nm
    check(res == [0x5a5a0000] * 7 + [vec] * n + [None, None],
          "potards (knob_vec) : machines 0..6 par la table de l'OS, les nôtres par la leur, au-delà KICK")


def machines_screen(fw, m):
    """Appels de dessin de l'écran MACHINES (0x400a25e0..) pour la machine m (comme test_sdvintage_7th.drum_select)."""
    u = UI(fw)
    u.hooks = {0x40071a04: "texte", 0x40071da4: "image", 0x40070c4e: "repère", 0x40070efc: "repère plein",
               0x93000000: "a5", 0x93000010: "a4"}
    for a_ in (0x93000000, 0x93000010):
        u.uc.mem_write(a_, b"\x4e\x75")
    u.uc.mem_write(0x40fe32cc, struct.pack(">I", 0x92000000))
    u.uc.mem_write(0x40fe384c, struct.pack(">I", 0x92100000))
    u.uc.mem_write(0x91001000 + 108, struct.pack(">I", 0x91002000))
    sp = t7.STACK - 0x800
    u.uc.mem_write(sp, struct.pack(">I", t7.STOP) * 64)
    for r, v in {mk.UC_M68K_REG_D3: m, mk.UC_M68K_REG_D2: 0x91000000, mk.UC_M68K_REG_A2: 0x91001000,
                 mk.UC_M68K_REG_A5: 0x93000000, mk.UC_M68K_REG_A4: 0x93000010, mk.UC_M68K_REG_A7: sp}.items():
        u.uc.reg_write(r, v)
    u.uc.emu_start(0x400a25e0, t7.STOP, count=1_000_000)
    return u.calls


# --- 3. son ------------------------------------------------------------------------------------------------------
def engine(fw):
    e = TM.engine(fw.img, end=fw.blob_end, payload=fw.payload)
    return e


def play(fw, setup, blocks, trigs):
    e = engine(fw)
    for t, kw in setup.items():
        e.set(t, **kw)
    out = np.stack([e.block(trigs.get(b, 0)) for b in range(blocks)])
    return out, e.unmapped


def same_or_idle(r, x, retrig):
    """Une piste d'une machine d'origine face à Model-TG seul : identique jusqu'à l'arrêt de la voix muette (notre
    régulateur, comme sans Model-TG : sous IDLE_THR pendant IDLE_BLOCKS blocs), la référence restant ensuite sous le
    seuil jusqu'au trig suivant ; après lui, à 1e-3 de la crête près (la voix reprend où elle s'était arrêtée)."""
    diff = np.nonzero(np.any(r != x, axis=1))[0]
    if not len(diff):
        return True, None
    f = int(diff[0])
    if f >= retrig:
        return np.abs(r[f:] - x[f:]).max() <= 1e-3 * np.abs(r).max(), f
    quiet = np.abs(r[f:retrig]).max() < gs.IDLE_THR and not x[f:retrig].any()
    return quiet and np.abs(r[retrig:] - x[retrig:]).max() <= 1e-3 * np.abs(r).max(), f


def sound(off, alone, fw, codes):
    base = dict(note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0, finetune=64, decay=60)
    trigs = {1: 0x3f, 150: 0x3f}
    setup = {t: dict(base, machine=t) for t in range(6)}
    r, _ = play(off, setup, 300, trigs)
    x, unm = play(fw, setup, 300, trigs)
    res = [same_or_idle(r[:, t], x[:, t], 150) for t in range(6)]
    check(all(ok for ok, _ in res) and not unm,
          "6 machines d'origine : identiques à Model-TG seul (son build officiel), jusqu'à l'arrêt des voix muettes "
          f"(blocs {[f for _, f in res]}), puis sous le seuil jusqu'au trig suivant")
    short = {t: dict(base, machine=t, decay=20) for t in range(6)}
    r, _ = play(off, short, 900, {1: 0x3f, 700: 0x3f})
    x, unm = play(fw, short, 900, {1: 0x3f, 700: 0x3f})
    res = [same_or_idle(r[:, t], x[:, t], 700) for t in range(6)]
    check(all(ok for ok, _ in res) and sum(f is not None for _, f in res) >= 4 and not unm,
          f"DECAY 20 : les voix d'origine s'arrêtent une fois muettes (blocs {[f for _, f in res]} ; aucun : KICK, que "
          "Model-TG éteint lui-même), la référence reste sous le seuil, et le trig du bloc 700 repart comme Model-TG seul")
    setup[2] = dict(base, machine=6)
    r, _ = play(off, setup, 300, trigs)
    x, unm = play(fw, setup, 300, trigs)
    ok = all(same_or_idle(r[:, t], x[:, t], 150)[0] for t in range(6) if t != 2)
    check(ok and np.array_equal(r[:, 2], x[:, 2]) and not x[:, 2].any() and not unm,
          "Sampler (machine 6) sans échantillon sur la piste 3 : muet, et le reste comme Model-TG seul")
    for i, c in enumerate(codes):
        m = gs.CATALOG[c]
        kw = dict(base, color=m["knobs"][0][2], shape=m["knobs"][1][2], sweep=m["knobs"][2][2],
                  contour=m["knobs"][3][2], decay=40)
        t = i % 6
        r, _ = play(alone, {t: dict(kw, machine=6 + i)}, 300, {1: 1 << t, 150: 1 << t})
        x, unm = play(fw, {t: dict(kw, machine=gs.TG_FIRST + i)}, 300, {1: 1 << t, 150: 1 << t})
        peak = np.abs(r[:, t]).max()
        check(np.array_equal(r[:, t], x[:, t]) and peak > 1e7 and not unm,
              f"{m['name']} (machine {gs.TG_FIRST + i + 1}) piste {t + 1} : identique à nos moteurs seuls (crête {peak:.2e})")
    # tout ensemble : KICK, nos 1er et dernier moteurs, le Sampler, CHORD, notre 2e moteur
    k = len(codes)
    mach_tg = [0, gs.TG_FIRST, 6, 5, gs.TG_FIRST + k - 1, gs.TG_FIRST + min(1, k - 1)]
    setup = {t: dict(base, machine=mm) for t, mm in enumerate(mach_tg)}
    x, unm = play(fw, setup, 300, trigs)
    r_off, _ = play(off, {t: dict(base, machine=mm if mm < 7 else 0) for t, mm in enumerate(mach_tg)}, 300, trigs)
    r_al, _ = play(alone, {t: dict(base, machine=mm - 1 if mm >= 7 else 1) for t, mm in enumerate(mach_tg)}, 300, trigs)
    ok = all(np.array_equal(x[:, t], r_al[:, t]) if mm >= 7 else same_or_idle(r_off[:, t], x[:, t], 150)[0]
             for t, mm in enumerate(mach_tg))
    check(ok and not unm, f"6 pistes ensemble (machines {[mm + 1 for mm in mach_tg]}) : chacune identique à sa référence")


# --- 4. régulateur de charge ------------------------------------------------------------------------------------
TIMER, BLOCK = 0xfc07000c, 90112


def governor(fw, ours_tw, codes, tg):
    """Surcharge (comme test_governor.py) : le régulateur éteint des voix, jamais le Sampler ni la piste que
    Model-TG enregistre ou dont il édite les tranches ; les voix épargnées restent identiques à la référence."""
    from unicorn import UC_HOOK_MEM_READ
    sy = {k: int(v, 16) for k, v in ours_tw["gov"].items()}
    cat = [gs.CATALOG[c] for c in codes]

    def eng(i):
        m = cat[i]
        return dict(machine=gs.TG_FIRST + i, note=60, pitch=64, color=m["knobs"][0][2], shape=m["knobs"][1][2],
                    sweep=m["knobs"][2][2], contour=m["knobs"][3][2], punch=0, gate=0, finetune=64, decay=100)
    st_ = lambda m: dict(machine=m, note=60, pitch=64, color=64, shape=64, sweep=64, contour=64, punch=0, gate=0,
                         finetune=64, decay=100)
    setup = {0: eng(0), 1: st_(0), 2: st_(6), 3: eng(1 % len(cat)), 4: st_(4), 5: eng(len(cat) - 1)}
    trigs = {1: 0x3f}

    def play_(load, rec=None):
        e = engine(fw)
        clock = {"t": 10_000_000, "fixed": None}

        def read(uc, access, addr, size, value, ud):
            if clock["fixed"] is None:
                clock["t"] += 2000
                v = clock["t"]
            else:
                v = clock["fixed"]
            uc.mem_write(TIMER, struct.pack(">I", v & 0xffffffff))
        e.uc.hook_add(UC_HOOK_MEM_READ, read, begin=TIMER, end=TIMER + 3)
        for t, kw in setup.items():
            e.set(t, **kw)
        if rec is not None:          # Model-TG édite les tranches de cette piste (même règle que la piste enregistrée,
            e.uc.mem_write(tg["sle_run"], struct.pack(">I", 1))         # rs_src, dont la capture n'est pas émulée)
            e.uc.mem_write(tg["sle_trk"], struct.pack(">I", rec))
        e.uc.mem_write(sy["gov_slow"], struct.pack(">I", 88 * 256 // 100))
        out, stolen, now = [], set(), 10_000_000
        for b in range(300):
            out.append(e.block(trigs.get(b, 0)))
            if load:
                e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", now & 0xffffffff))
                clock["fixed"] = now + (97 if b < 200 else 50) * BLOCK // 100
                e.call(sy["audio_end"])
                clock["fixed"] = None
                now += BLOCK
            stolen |= {t for t, v in enumerate(bytes(e.uc.mem_read(sy["gov_stolen"], 6))) if v}
        return np.stack(out), stolen, e.unmapped
    ref, _, _ = play_(False)
    for rec in (None, 0):
        mod, stolen, unm = play_(True, rec)
        spared = {2} | ({rec} if rec is not None else set())
        same = all(np.array_equal(ref[:, t], mod[:, t]) for t in spared)
        check(stolen and not stolen & spared and same and not unm,
              f"surcharge (97 %) : pistes éteintes {sorted(t + 1 for t in stolen)}, jamais le Sampler (piste 3)"
              + (f" ni la piste dont Model-TG édite les tranches (piste {rec + 1})" if rec is not None else "")
              + ", identiques à la référence")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    ap.add_argument("--engines", default=",".join(gs.CATALOG))
    ap.add_argument("--tweak", help="un autre tweak de ces moteurs (firmware de diagnostic : 91-syntakt-tg-meter.json)")
    args = ap.parse_args()
    codes = [c for c in gs.CATALOG if c in args.engines.split(",")]
    stock = T.main_os_from_syx(args.cycles)
    st_img = syntakt.dsp_image(args.syntakt)
    tg_tw = load("30-model-tg-st.json")
    ours = json.loads(pathlib.Path(args.tweak).read_text(encoding="utf-8")) if args.tweak else \
        load(f"31-{gs.tweak_id(codes, tg=True)}.json")
    fw = Fw(stock, [tg_tw, ours], st_img, args.syntakt)
    ref = Fw(stock, [tg_tw], st_img, None)
    off = Fw(stock, [load("30-model-tg.json")], st_img, None)
    alone = Fw(stock, [load(f"24-{gs.subset_id(codes)}.json")], st_img, args.syntakt)
    tg = {k: int(v, 16) for k, v in tg_tw["symbols"].items()}
    gs.set_base(gs.PAY_TG)
    tg["knob_vec"] = knob_vec_at(ours)
    print(f"démarrage ({ours['id']})")
    boot(fw, tg)
    print("interface")
    interface(ref, fw, codes, tg)
    print("son")
    sound(off, alone, fw, codes)
    print("régulateur de charge")
    governor(fw, ours, codes, tg)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


def knob_vec_at(tw):
    """Adresse de knob_vec : la cible du « jsr » écrit en 0x4001e8da (g7.CALLS)."""
    va = g7.CALLS[0][0]
    w = next(w for w in tw["writes"] if w["off"] == va - BASE)
    return int(w["new"][4:12], 16)


if __name__ == "__main__":
    sys.exit(main())
