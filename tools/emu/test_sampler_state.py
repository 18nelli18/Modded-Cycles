#!/usr/bin/env python3
"""L'état du Sampler de Model-TG sur k 26 + sound+86 (notes/86) : le vrai code de Model-TG (30-model-tg-st.json, avec
ST_SPLIT_PATCHES de tools/gen_model_tg.py) et les vraies fonctions de sauvegarde/chargement du son de l'OS.

Le Sampler rangeait ses modes dans un long en sound+72, c'est-à-dire sur les mots k 26 et 27. Le lo-fi de piste prend
k 27 (Lo-Fi Rate) : la moitié haute reste sur k 26, la basse passe en sound+86..+87 (hors des 33 mots, que personne
d'autre ne touche). Vérifications :
  1. sauvegarde du son (0x4005afa0, détour de Model-TG) : les cases 28/29 de l'enregistrement (+84..+87) reçoivent
     k 26 et sound+86, soit exactement le long d'avant ; k 27 n'y va pas ;
  2. chargement (0x4005aecc) : +84 revient sur k 26, +86 sur sound+86, et k 27 reste ce que l'OS y met (0) au lieu de
     recevoir la moitié basse de l'état ; un enregistrement d'avant (le même long) se relit à l'identique ;
  3. state_store puis st_apply (et st_apply_c) : des réglages au hasard, rangés puis relus des deux moitiés, reviennent
     tous ; k 27 n'est jamais écrit ;
  4. le changement de machine (mc_commit_hook) : un état d'étiquette 0x7 (l'actuelle) ou 0xF (samplerIR) est gardé,
     sans état on prend le défaut, en deux moitiés ; k 27 et d1 intacts. Avant, le test du bit 7 ne reconnaissait pas
     l'étiquette 0x7 : un Sampler quitté puis repris perdait ses modes ;
  5. l'écran des machines (restore_hook -> 0x4001416c) : revenir à la machine d'origine sans quitter l'écran remet le
     cliché pris à son ouverture, pour le Sampler comme pour les autres (Model-TG sautait le Sampler, notes/83 §4).

    python3 tools/emu/test_sampler_state.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import random
import struct
import sys

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import lofi_ui                      # noqa: E402
import test_sdvintage as T          # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "30-model-tg-st.json"
SAVE, LOAD = 0x4005afa0, 0x4005aecc
ST_TAG, ST_TAG_OLD, ST_DEFAULT = 0x70000000, 0xF0000000, 0x70000000 + 35280
FAIL = []


def check(ok, msg):
    print(f"  {'ok  ' if ok else 'FAIL'}  {msg}")
    if not ok:
        FAIL.append(msg)


def regcall(u, fn, regs, stop=lofi_ui.STOP, count=2_000_000):
    """Appel d'une routine à registres : regs = {'d0': .., 'a2': ..} ; adresse de retour STOP sur la pile."""
    sp = lofi_ui.STACK - 0x400
    u.uc.mem_write(sp, struct.pack(">I", lofi_ui.STOP))
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    for r, v in regs.items():
        u.uc.reg_write(getattr(mk, f"UC_M68K_REG_{r.upper()}"), v & 0xffffffff)
    u.bad.clear()
    u.uc.emu_start(fn, stop, count=count)
    return {r: u.uc.reg_read(getattr(mk, f"UC_M68K_REG_{r.upper()}")) for r in ("d0", "d1", "a7")}


def w16(u, a):
    return struct.unpack(">H", u.uc.mem_read(a, 2))[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    tw = json.loads(TWEAK.read_text(encoding="utf-8"))
    sym = {k: int(v, 16) for k, v in tw["symbols"].items()}
    pl, _ = build.build_payload([tw], stock, None)
    img = build.apply_writes(stock, [tw])[0] + pl
    u = lofi_ui.UI(img, end=lofi_ui.BASE + len(img))
    check(u.init_ok, "UI de l'OS construite, Model-TG en place")
    S = lofi_ui.SCRATCH + 0x8000
    rt, rec, rt2 = S, S + 0x100, S + 0x200
    rnd = random.Random(86)

    # 1-2. sauvegarde / chargement du son
    bad = []
    for _ in range(64):
        hi = ST_TAG >> 16 | rnd.randrange(0x1000)
        lo = rnd.randrange(0x10000)
        k27 = rnd.randrange(0x7f01)
        u.uc.mem_write(rt, bytes(100))
        u.uc.mem_write(rt + 72, struct.pack(">HH", hi, k27))
        u.uc.mem_write(rt + 86, struct.pack(">H", lo))
        u.uc.mem_write(rec, bytes(100))
        u.call(SAVE, rec, rt)
        r = bytes(u.uc.mem_read(rec, 100))
        if r[84:88] != struct.pack(">HH", hi, lo):
            bad.append(("save", hex(hi), hex(lo), r[84:88].hex()))
        u.uc.mem_write(rt2, b"\xaa" * 100)
        u.call(LOAD, rt2, rec)
        g = bytes(u.uc.mem_read(rt2, 100))
        if g[72:74] != struct.pack(">H", hi) or g[86:88] != struct.pack(">H", lo) or g[74:76] != bytes(2):
            bad.append(("load", hex(hi), hex(lo), g[72:76].hex(), g[86:88].hex()))
    check(not bad, f"son : sauvegarde (cases 28/29 = k 26 | sound+86, le long d'avant) et chargement (k 26, sound+86 ; "
                   f"k 27 laissé à 0) sur 64 états au hasard {bad[:2]}")

    # 3. state_store / st_apply / st_apply_c
    fields = []
    a = sym["st_fields"]
    while True:
        tab, _, _, mx = struct.unpack(">IIII", u.uc.mem_read(a, 16))
        if tab == 0:
            break
        fields.append((tab, mx))
        a += 16
    check(len(fields) == 14, f"st_fields : {len(fields)} réglages (le mode, ses options, les tranches, granulaire)")
    u.hooks[sym["sound_obj"]] = ("sound_obj", rt)
    bad = []
    for n in range(48):
        t = n % 6
        vals = [rnd.randint(0, mx) for _, mx in fields]
        for (tab, _), v in zip(fields, vals):
            u.uc.mem_write(tab + 4 * t, struct.pack(">I", v))
        u.uc.mem_write(rt, bytes(100))
        u.uc.mem_write(rt + 74, b"\xbe\xef")
        regcall(u, sym["state_store"], {"d0": t})
        word = w16(u, rt + 72) << 16 | w16(u, rt + 86)
        if (word & 0xF0000000) != ST_TAG or w16(u, rt + 74) != 0xbeef:
            bad.append(("store", t, hex(word), hex(w16(u, rt + 74))))
            continue
        for tab, _ in fields:
            u.uc.mem_write(tab + 4 * t, struct.pack(">I", 0))
        r = regcall(u, sym["st_apply"], {"d2": t, "a2": rt})
        got = [struct.unpack(">I", u.uc.mem_read(tab + 4 * t, 4))[0] for tab, _ in fields]
        if r["d0"] != 1 or got != vals:
            bad.append(("apply", t, r["d0"], vals, got))
    check(not bad, f"state_store -> st_apply : 48 réglages au hasard (6 pistes) rangés en k 26 + sound+86 et relus "
                   f"à l'identique ; k 27 jamais écrit {bad[:2]}")
    r1 = regcall(u, sym["st_apply_c"], {"d2": 0, "a2": rt})
    u.uc.mem_write(rt + 86, struct.pack(">H", w16(u, rt + 86) ^ 1))
    r2 = regcall(u, sym["st_apply_c"], {"d2": 0, "a2": rt})
    check(r1["d0"] == 1 and r2["d0"] in (0, 1),
          "st_apply_c : décode l'état et voit un changement de la seule moitié basse (sound+86)")

    # 4. le changement de machine : le bloc retouché, de son début à mch_hasst
    blob = bytes(u.uc.mem_read(sym["mc_commit_hook"], sym["mch_hasst"] - sym["mc_commit_hook"]))
    pat = bytes.fromhex("2f01122800480281000000700c8100000070")
    i = blob.find(pat)
    check(i >= 0, f"bloc du changement de machine trouvé (mc_commit_hook + {i})")
    start = sym["mc_commit_hook"] + i
    cases = [("étiquette 0x7 (état actuel)", 0x7123, 0x4567, (0x7123, 0x4567)),
             ("étiquette 0xF (samplerIR)", 0xF123, 0x4567, (0xF123, 0x4567)),
             ("aucun état (zéro)", 0x0000, 0x0000, (ST_DEFAULT >> 16, ST_DEFAULT & 0xffff)),
             ("valeur sans étiquette (0x3)", 0x3456, 0x789a, (ST_DEFAULT >> 16, ST_DEFAULT & 0xffff))]
    for name, hi, lo, want in cases:
        u.uc.mem_write(rt, bytes(100))
        u.uc.mem_write(rt + 72, struct.pack(">HH", hi, 0x2bad))
        u.uc.mem_write(rt + 86, struct.pack(">H", lo))
        sp = lofi_ui.STACK - 0x400
        u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        u.uc.reg_write(mk.UC_M68K_REG_A0, rt)
        u.uc.reg_write(mk.UC_M68K_REG_D1, 0x13572468)
        u.uc.emu_start(start, sym["mch_hasst"], count=200)
        got = (w16(u, rt + 72), w16(u, rt + 86))
        ok = got == want and w16(u, rt + 74) == 0x2bad and u.uc.reg_read(mk.UC_M68K_REG_D1) == 0x13572468 \
            and u.uc.reg_read(mk.UC_M68K_REG_A7) == sp
        check(ok, f"changement de machine, {name} : k 26 / sound+86 = {got[0]:#06x} / {got[1]:#06x} ; k 27, d1 et "
                  f"la pile intacts")

    # 5. l'écran des machines : revenir à la machine d'origine sans le quitter remet le cliché pris à l'ouverture
    # (0x4001416c, par restore_hook), le Sampler compris (Model-TG le sautait : ses Start/End/Filtre/Résonance et
    # le reste de la page revenaient aux défauts)
    obj, vt, vec, pairs = S + 0x300, S + 0x340, S + 0x400, S + 0x420
    snd_fn, notify = S + 0x3e0, S + 0x3e4
    u.uc.mem_write(obj, struct.pack(">I", vt))
    u.uc.mem_write(vt + 40, struct.pack(">I", snd_fn))
    u.uc.mem_write(vt + 16, struct.pack(">I", notify))
    u.hooks[snd_fn] = ("sound_obj", rt)
    u.hooks[notify] = ("notify", 0)
    snap = [(11 + i, 0x1111 * (i + 1)) for i in range(4)] + [(5, 0x0321)]   # (k, valeur) : k 11..14, k 5
    u.uc.mem_write(pairs, b"".join(struct.pack(">IHH", s, v, 0) for s, v in snap))
    u.uc.mem_write(vec, struct.pack(">II", pairs, pairs + 8 * len(snap)))
    for mach in (6, 2):
        u.uc.mem_write(rt, bytes(100))
        u.uc.mem_write(rt + 38, bytes([mach]))
        u.calls.clear()
        u.call(sym["restore_hook"], obj, vec)
        got = [w16(u, rt + 20 + 2 * k) for k, _ in snap]
        sent = bool(u.calls) and u.calls[-1][0] == "notify" and u.calls[-1][1][:2] == (obj, 0)
        check(got == [v for _, v in snap] and sent and u.sp_ok,
              f"retour à la machine d'origine sur l'écran des machines, machine {mach} : les {len(snap)} réglages du "
              f"cliché remis ({[hex(x) for x in got]}), notification envoyée, pile rendue")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
