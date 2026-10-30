#!/usr/bin/env python3
"""Lo-fi de piste (notes/86, tools/track_lofi.py, écrit avec Model-TG) : le geste et l'affichage, sur le vrai code de
l'interface de l'OS et de Model-TG (30-model-tg-st.json) :
  1. descripteurs 1 / 2 : Lo-Fi Rate / Bits, k 27 / 30, groupe 7, drapeaux 0x600, 0..32512, défaut 0 ;
  2. MACHINES + COLOR / SHAPE -> ids 1 / 2 sur les machines 0..5 (dh_pass -> tl_dh) ; DECAY / SWEEP / CONTOUR gardent
     Attack / Filtre / Résonance ; sans MACHINES, les potards de l'OS ;
  3. le descripteur du Sampler sous MACHINES (sampler_pre -> tl_atk) : Attack, Rate, Bits en positions 1, 2, 3 ;
  4. le texte de la valeur : OFF, 46K..4K (les pas de RATE du lo-fi de MACRO), 12B..2B ;
  5. la fenêtre de valeur : ce texte, dessiné comme l'OS dessine le texte d'un paramètre sans jauge (aucun sprite).

    python3 tools/emu/test_track_lofi.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import lofi_ui                      # noqa: E402
import test_sdvintage as T          # noqa: E402
import track_lofi                   # noqa: E402

TWEAK = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13" / "30-model-tg-st.json"
COLOR, SHAPE, DECAY, SWEEP, CONTOUR = 4, 5, 3, 6, 7          # potards de lofi_ui.lookup (PITCH = 2)
FAIL = []


def check(ok, msg):
    print(f"  {'ok  ' if ok else 'FAIL'}  {msg}")
    if not ok:
        FAIL.append(msg)


def khz(r):
    return round(48 * 2 ** (-86 * r / 1536))


def want(desc, v):
    v = min(max((v + 0x80) >> 8, 0), 127)
    if v == 0:
        return "OFF"
    return f"{khz((v + 1) // 2)}K" if desc == 1 else f"{12 - (v - 1) * 10 // 126}B"


TRK, OBJ, VOLDIST, HOOK = 0x80001858, 0x8000100c, 0x40056f58, 0x40059852


def model(blocks, words, side=None):
    """Le lo-fi d'une piste, en Python : blocks = blocs de 32 trames (int32), words = (k 27, k 30) lissés par bloc.
    Rend (blocs, côtés) traités. Phase de départ 0xffff : la première trame est prise."""
    ph, hold, hold_s = 0xffff, 0xffff, 0xffff
    out, out_s = [], []
    for n, (blk, (wr, wb)) in enumerate(zip(blocks, words)):
        q = lambda w: min(max((w + 0x80) >> 8, 0), 127)          # noqa: E731
        vr, vb = q(wr), q(wb)
        inc = round(65536 * 2 ** (-86 * ((vr + 1) // 2) / 1536)) if vr else 65536
        mask = (-1 << (20 + (vb - 1) * 10 // 126)) & 0xffffffff if vb else 0xffffffff
        sb = side[n] if side else [0] * 32
        if not vr and not vb:
            ph = 0xffff
            out.append(list(blk)); out_s.append(list(sb))
            continue
        o, os_ = [], []
        for x, y in zip(blk, sb):
            ph += inc
            if ph >= 65536:
                ph -= 65536
                hold, hold_s = (x & 0xffffffff) & mask, (y & 0xffffffff) & mask
            o.append(hold - (1 << 32) if hold & 0x80000000 else hold)
            os_.append(hold_s - (1 << 32) if hold_s & 0x80000000 else hold_s)
        out.append(o); out_s.append(os_)
    return out, out_s


def audio(u, img, sym):
    """6. Le son : tl_post (le vrai code, appelé comme l'OS l'appelle en 0x40059852, Volume + Dist bouché) contre le
    modèle, piste par piste, bloc après bloc ; bit pour bit éteint ; côté stéréo ; registres et pile ; coût."""
    import random
    hooked = img[HOOK - lofi_ui.BASE:HOOK - lofi_ui.BASE + 6] == b"\x4e\xb9" + struct.pack(">I", track_lofi.SYMS["tl_post"])
    check(hooked, f"0x40059852 : jsr tl_post ({track_lofi.SYMS['tl_post']:#x}) à la place de jsr 0x40056f58")
    try:
        u.uc.mem_map(0x80000000, 0x100000)
    except Exception:
        pass
    u.hooks[VOLDIST] = ("voldist", 0)
    side = track_lofi.SX_SIDE
    check(sym.get("sx_side", side) == side, f"sx_side de Model-TG = {side:#x} (tools/track_lofi.py)")
    rnd = random.Random(86)
    # (Rate, Bits) par piste : éteint, Rate seul, Bits seul, les deux, LFO hors bornes, Rate au plus bas
    cfg = [(0, 0), (0x2000, 0), (0, 0x5000), (0x7f00, 0x7f00), (-0x900, 0x9000), (0x100, 0x100)]
    nblk = 12
    blocks = [[[rnd.randrange(-2 ** 31, 2 ** 31) for _ in range(32)] for _ in range(nblk)] for _ in range(6)]
    sides = [[[rnd.randrange(-2 ** 31, 2 ** 31) for _ in range(32)] for _ in range(nblk)] for _ in range(6)]
    words = [[(wr + (rnd.randrange(-0x300, 0x300) if n % 3 and wr else 0), wb) for n in range(nblk)]
             for wr, wb in cfg]
    words[5][6] = (0, 0)                                          # s'éteint un bloc, repart
    want = [model(blocks[t], words[t], sides[t]) for t in range(6)]
    bad, regs_ok, insns = [], True, []
    sp = lofi_ui.STACK - 0x400
    for n in range(nblk):
        for t in range(6):
            u.uc.mem_write(TRK + 128 * t, struct.pack(">32i", *blocks[t][n]))
            u.uc.mem_write(side + 128 * t, struct.pack(">32i", *sides[t][n]))
            u.uc.mem_write(OBJ + 14 + 66 * t + 54, struct.pack(">h", max(min(words[t][n][0], 32767), -32768)))
            u.uc.mem_write(OBJ + 14 + 66 * t + 60, struct.pack(">h", max(min(words[t][n][1], 32767), -32768)))
        u.uc.mem_write(sp, struct.pack(">III", lofi_ui.STOP, TRK, OBJ))
        u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        marks = {f"d{i}": 0x11110000 + i for i in range(2, 8)}
        marks.update({f"a{i}": 0x22220000 + i for i in range(2, 7)})
        for r, v in marks.items():
            u.uc.reg_write(getattr(mk, f"UC_M68K_REG_{r.upper()}"), v)
        u.bad.clear()
        cnt = [0]
        h = u.uc.hook_add(lofi_ui.UC_HOOK_CODE, lambda *a: cnt.__setitem__(0, cnt[0] + 1))
        u.uc.emu_start(track_lofi.SYMS["tl_post"], lofi_ui.STOP, count=200_000)
        u.uc.hook_del(h)
        insns.append(cnt[0])
        regs_ok &= all(u.uc.reg_read(getattr(mk, f"UC_M68K_REG_{r.upper()}")) == v for r, v in marks.items()) \
            and u.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4 and not u.bad
        for t in range(6):
            got = list(struct.unpack(">32i", u.uc.mem_read(TRK + 128 * t, 128)))
            got_s = list(struct.unpack(">32i", u.uc.mem_read(side + 128 * t, 128)))
            if got != want[t][0][n] or got_s != want[t][1][n]:
                bad.append((n, t, cfg[t]))
    check(not bad, f"tl_post, 6 pistes x {nblk} blocs (éteint ; Rate seul ; Bits seul ; les deux au plus fort ; mots "
                   f"hors bornes ; une piste éteinte un bloc puis rallumée) : sortie et côté = le modèle (S&H Q16, pas "
                   f"de MACRO, masque des b bits forts), piste éteinte bit pour bit {bad[:3]}")
    check(regs_ok, "d2-d7, a2-a6 et la pile rendus, aucun accès hors mémoire")
    check(max(insns) < 2600, f"coût : {min(insns)}..{max(insns)} instructions par bloc avec 5 pistes en lo-fi "
                             f"(Volume + Dist bouché ; un bloc fait environ 108 000 instructions)")


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

    # 1. descripteurs
    rows = {}
    for i in (1, 2):
        r = struct.unpack(">14I", u.uc.mem_read(lofi_ui.PARAM_TABLE + 56 * i, 56))
        rows[i] = (r[0], r[1], r[2], r[3], r[4], r[9], u.cstr(r[11]), u.cstr(r[13]))
    check(rows == {1: (7, 27, 0, 32512, 0, 0x600, "Lo-Fi Rate", "RATE"), 2: (7, 30, 0, 32512, 0, 0x600, "Lo-Fi Bits",
                                                                            "BITS")},
          f"descripteurs 1 / 2 : groupe 7, k 27 / 30, 0..32512, défaut 0, drapeaux 0x600, noms {rows}")

    # 2. le geste, machines 0..5
    held = sym["mod_held"]
    got, bad = {}, []
    for m in range(6):
        for key in (False, True):
            u.uc.mem_write(held, struct.pack(">I", int(key)))
            got[m, key] = [u.lookup(m, kn, False, key) for kn in (DECAY, COLOR, SHAPE, SWEEP, CONTOUR)]
        u.uc.mem_write(held, bytes(4))
        if got[m, True] != [0x0d, 1, 2, 0x0c, 0x0b] or 1 in got[m, False] or 2 in got[m, False] \
                or None in got[m, False]:
            bad.append((m, got[m, False], got[m, True]))
    check(not bad, "MACHINES + DECAY / COLOR / SHAPE / SWEEP / CONTOUR -> Attack / Rate / Bits / Filtre / Résonance "
                   f"(0x0d, 1, 2, 0x0c, 0x0b) sur les machines 0..5 ; sans MACHINES, les potards de l'OS {bad[:2]}")

    # 3. le descripteur du Sampler sous MACHINES : tl_atk, et l'appel à sa place dans sampler_pre
    S = lofi_ui.SCRATCH + 0x9000
    u.uc.mem_write(S, b"\x55" * 76)
    sp = lofi_ui.STACK - 0x400
    u.uc.mem_write(sp, struct.pack(">I", lofi_ui.STOP))
    u.uc.reg_write(mk.UC_M68K_REG_A7, sp)
    u.uc.reg_write(mk.UC_M68K_REG_A0, S)
    u.uc.reg_write(mk.UC_M68K_REG_D2, 0x2468ace0)
    # tl_atk : ce que Model-TG appelle à la place de « moveq #0x0d,d1 ; movel d1,a0@(12) » (track_lofi compile
    # tools/machines/track_lofi avec le même assembleur que gen_model_tg.py)
    tl_atk = track_lofi.ATK
    calls = img.count(b"\x4e\xb9" + struct.pack(">I", tl_atk))
    u.uc.emu_start(tl_atk, lofi_ui.STOP, count=200)
    d = struct.unpack(">19I", u.uc.mem_read(S, 76))
    check(calls == 1 and d[3:6] == (0x0d, 1, 2) and d[:3] == (0x55555555,) * 3 and d[6:] == (0x55555555,) * 13
          and u.uc.reg_read(mk.UC_M68K_REG_D2) == 0x2468ace0 and u.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4,
          f"descripteur du Sampler sous MACHINES (tl_atk, appelé une fois dans Model-TG : {calls}) : positions 1, 2, 3 "
          f"= Attack, Rate, Bits ({[hex(x) for x in d[3:6]]}), le reste intact, pile et d2 rendus")

    # 4. le texte de la valeur (fonctions posées par tl_dh au geste, et par tl_load au chargement)
    bad = []
    for desc in (1, 2):
        for v in list(range(0, 0x7f01, 0x100)) + [0x7f, 0x80, 0x17f, 0x7fff, -5]:
            t = u.text(desc, v)
            if t != want(desc, v):
                bad.append((desc, hex(v), t, want(desc, v)))
    seen = {d: [u.text(d, v << 8) for v in (0, 1, 2, 63, 64, 126, 127)] for d in (1, 2)}
    check(not bad, f"texte : OFF à 0, Rate 46K..4K (pas (v + 1) / 2 de MACRO), Bits 12B..2B, valeurs arrondies au pas "
                   f"{seen} {bad[:3]}")

    # 5. la fenêtre de valeur : notre texte, dessiné comme l'OS dessine le texte d'un paramètre sans jauge
    bad = []
    for desc in (1, 2):
        for v in (0, 0x100, 0x3f00, 0x7f00):
            a, b = u.popup(desc, v), u.popup(desc, v, text_path=True)
            if a is None or b is None or a[0] != b[0] or a[1] or not any(a[0]):
                bad.append((desc, hex(v), a is None, b is None, a and a[1]))
    check(not bad, f"fenêtre de valeur (0x4001d818) : le texte, comme le chemin texte de l'OS, sans sprite {bad[:3]}")

    audio(u, img, sym)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
