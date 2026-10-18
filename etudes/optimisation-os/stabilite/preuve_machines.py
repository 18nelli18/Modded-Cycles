#!/usr/bin/env python3
"""Gel de MACHINES avec une piste sur une machine que le firmware n'a pas : preuve, stock contre correctif.

Le vrai code de l'OS 1.13 (Unicorn), fonction par fonction, comme tools/emu/test_sdvintage_7th.py et
test_syntakt_machines.py (dont on reprend les objets factices et l'empoisonnement des 76 o avant le tableau des
enregistrements : des pointeurs vers une zone non mappée, pour que tout usage se voie).

Correctif proposé (4 octets, OS d'origine) :
  0x4004df66  70ff -> 7006   enregistrement n (0x4004df5c) : hors 0..6 -> CHORD (6) au lieu de -1 (avant le tableau)
  0x4004df80  70ff -> 7006   enregistrement de la machine m (0x4004df76) : hors 0..5 -> CHORD au lieu de -1
Même correctif dans la copie de Model-TG (0x401bf7e2, 0x401bf806, 0x401bf81c), avec --tg.

Vérifié :
  1. accesseurs : 0..6 / 0..5 identiques au stock ; hors limites : stock -> 0x40a714f4 (avant le tableau),
     corrigé -> l'enregistrement de CHORD ;
  2. 0x400148dc (appelée pour chacune des 6 pistes par la lambda 0x400a2404 à l'ouverture de MACHINES) :
     machines 0..5 identiques au stock (mêmes appels, même résultat) ; machine 6, 7, 9, 100, -3 : stock -> lectures
     par les pointeurs empoisonnés ; corrigé -> aucune, résultat = celui de CHORD ;
  3. potards de l'écran principal (0x4001e814) : vecteur de 6 entrées suivi de valeurs quelconques ; stock ->
     descripteurs faux ; corrigé -> ceux de CHORD ;
  4. molette de MACHINES (0x400a2712) depuis la machine 9 : stock et corrigé ramènent sur 5 (CHORD), sans accès faux ;
  5. changement de machine réel (0x40014072) depuis la machine 9.

    python3 preuve_machines.py [--tg]
"""
import argparse
import struct
import sys

sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
sys.path.insert(0, "/home/user/Modded-Cycles/tools")
sys.path.insert(0, "/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/stabilite")

import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402

CYCLES = "/home/user/Modded-Cycles/firmware/model-cycles_OS1.13.syx"
BASE = 0x40000400
REC_BASE, REC_LEN = t7.REC_BASE, t7.REC_LEN
POISON = 0xa0000000
FIX = [(0x4004df66, "70ff", "7006"), (0x4004df80, "70ff", "7006")]
FIX_TG = [(0x401bf7e2, "70ff", "7006"), (0x401bf806, "70ff", "7006"), (0x401bf81c, "70ff", "7006")]
FAIL = []


def check(ok, msg):
    print(f"  {'ok   ' if ok else 'ECHEC'} {msg}", flush=True)
    if not ok:
        FAIL.append(msg)


def patch(img, writes):
    b = bytearray(img)
    for va, old, new in writes:
        o = va - BASE
        assert b[o:o + 2] == bytes.fromhex(old), (hex(va), b[o:o + 2].hex())
        b[o:o + 2] = bytes.fromhex(new)
    return bytes(b)


def poison(u):
    u.uc.mem_write(REC_BASE - REC_LEN, struct.pack(">19I", *[POISON + 16 * k for k in range(19)]))


def new_ui(img):
    u = t7.UI(img)
    if len(img) > t7.E.IMAGE_LEN:                       # charge utile en place (Model-TG) : après l'image d'origine
        u.uc.mem_write(BASE + t7.E.IMAGE_LEN, img[t7.E.IMAGE_LEN:])
    t7.fill_records(u)
    poison(u)
    heap(u)
    return u


def bad_reads(u):
    return [a for a in u.bad if a >= POISON - 0x100]


def heap(u, at=0x93d00000):
    """operator new (0x400802e0) : un tas factice (bump) ; operator delete (0x400802ec) : rien."""
    st = {"p": at}
    mk = t7.mk

    def new(uc, addr, size, ud):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        n = struct.unpack(">I", uc.mem_read(sp + 4, 4))[0]
        uc.reg_write(mk.UC_M68K_REG_D0, st["p"])
        st["p"] += (n + 15) & ~15
        uc.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", uc.mem_read(sp, 4))[0])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
    u.uc.hook_add(t7.UC_HOOK_CODE, new, begin=0x400802e0, end=0x400802e0)
    u.hooks[0x400802ec] = ("delete", 0)


def records(stock, fixed, top_ok):
    a, b = new_ui(stock), new_ui(fixed)
    same = all(a.call(0x4004df5c, i) == b.call(0x4004df5c, i) for i in range(top_ok + 2))
    same &= all(a.call(0x4004df76, m) == b.call(0x4004df76, m) for m in range(top_ok + 1))
    out = [7, 8, 100, -3] if top_ok == 5 else [8, 9, 100, -3]
    s = {i: a.call(0x4004df5c, i) for i in out}
    f = {i: b.call(0x4004df5c, i) for i in out}
    sm = {m: a.call(0x4004df76, m) for m in (top_ok + 1, 9, 100)}
    fm = {m: b.call(0x4004df76, m) for m in (top_ok + 1, 9, 100)}
    chord = REC_BASE + 6 * REC_LEN
    print(f"        stock   : n hors limites -> {sorted({hex(v) for v in s.values()})}, machine -> {sorted({hex(v) for v in sm.values()})}")
    print(f"        corrigé : n hors limites -> {sorted({hex(v) for v in f.values()})}, machine -> {sorted({hex(v) for v in fm.values()})}")
    check(same, f"accesseurs 0x4004df5c (0..{top_ok + 1}) et 0x4004df76 (0..{top_ok}) identiques au stock")
    check(all(v == REC_BASE - REC_LEN for v in list(s.values()) + list(sm.values())),
          "stock : hors limites -> 0x40a714f4, 76 o AVANT le tableau (le défaut)")
    check(all(v == chord for v in list(f.values()) + list(fm.values())), "corrigé : hors limites -> enregistrement de CHORD")


def machine_list(img, m):
    """0x400148dc(piste) : liste (descripteur, valeur) des paramètres de la machine de la piste ; a0 = résultat."""
    u = new_ui(img)
    obj, snd = t7.fake_track(u, m & 0xff)
    for k in range(0x30):                              # des valeurs de son reconnaissables (slot 9 = la machine)
        if k != 9:
            u.uc.mem_write(snd + 0x14 + 2 * k, struct.pack(">h", (k + 1) << 8))
    res = 0x93c00000
    u.uc.mem_write(res, bytes(12))
    u.hooks.pop(0x40014072, None)
    u.uc.reg_write(t7.mk.UC_M68K_REG_A0, res)
    sp = t7.STACK - 0x400
    u.uc.mem_write(sp, struct.pack(">II", t7.STOP, obj))
    u.uc.reg_write(t7.mk.UC_M68K_REG_A7, sp)
    u.bad.clear()
    try:
        u.uc.emu_start(0x400148dc, t7.STOP, count=2_000_000)
        err = None
    except t7.UcError as e:
        err = str(e)
    beg, end = struct.unpack(">II", u.uc.mem_read(res, 8))
    items = []
    if not err and beg and end >= beg and end - beg < 0x1000:
        items = [struct.unpack(">IH", u.uc.mem_read(beg + i, 6)) for i in range(0, end - beg, 8)]
    return items, bad_reads(u), err


def machines_view(stock, fixed, top_ok):
    ref_s = {m: machine_list(stock, m) for m in range(top_ok + 1)}
    ref_f = {m: machine_list(fixed, m) for m in range(top_ok + 1)}
    check(all(ref_s[m] == ref_f[m] and not ref_s[m][1] and not ref_s[m][2] for m in ref_s),
          f"0x400148dc, machines 0..{top_ok} : résultats identiques au stock, aucun accès faux")
    chord = ref_f[5][0]
    for m in (top_ok + 1, top_ok + 2, 9, 100, -3):
        s, f = machine_list(stock, m), machine_list(fixed, m)
        print(f"        machine {m:4d} : stock {len(s[1])} lecture(s) empoisonnée(s){' + ' + s[2] if s[2] else ''} ;"
              f" corrigé {len(f[1])}, {len(f[0])} paramètres{' = CHORD' if f[0] == chord else ''}")
        check((s[1] or s[2]) and not f[1] and not f[2] and f[0] == chord,
              f"0x400148dc machine {m} : stock lit par les pointeurs d'avant le tableau, corrigé = CHORD")


def knobs(stock, fixed, top_ok):
    res = {}
    for name, img in (("stock", stock), ("corrigé", fixed)):
        u = new_ui(img)
        this, vec = 0x93900000, 0x93910000
        n = top_ok + 1
        u.uc.mem_write(vec, struct.pack(f">{n}i", *range(1, n + 1)) + struct.pack(">4I", 0x41234567, 0x7fff0000, 0x13, 0x8000))
        u.uc.mem_write(this + 104, struct.pack(">III", vec, vec + 4 * n, vec + 4 * n))
        out = {}
        for m in list(range(n)) + [n, n + 1, n + 3]:
            u.hooks = {0x4001e318: ("machine", m), 0x400cf9a8: ("app", 0x93a00000), 0x4006b736: ("verrou", 0)}
            u.bad.clear()
            out[m] = ([u.call(0x4001e814, this, k, 0, 0) for k in range(2, 8)], bool(bad_reads(u)))
        res[name] = out
    n = top_ok + 1
    same = all(res["stock"][m] == res["corrigé"][m] for m in range(n))
    print(f"        stock   machine {n}..{n + 3} : {[res['stock'][m][0] for m in (n, n + 1, n + 3)]}")
    print(f"        corrigé machine {n}..{n + 3} : {[res['corrigé'][m][0] for m in (n, n + 1, n + 3)]} (CHORD {res['corrigé'][5][0]})")
    check(same, f"potards (0x4001e814), machines 0..{top_ok} : identiques au stock")
    check(all(res["corrigé"][m] == res["corrigé"][5] for m in (n, n + 1, n + 3)),
          "potards, machine hors limites : corrigé -> descripteurs de CHORD, aucun accès faux")
    check(any(res["stock"][m][0] != res["stock"][5][0] or res["stock"][m][1] for m in (n, n + 1, n + 3)),
          "potards, machine hors limites : stock -> autre chose (lu avant le tableau)")


def wheel_and_change(stock, fixed, top_ok):
    for name, img in (("stock", stock), ("corrigé", fixed)):
        got = {}
        for step in (-1, 1):
            u = new_ui(img)
            obj, snd = t7.fake_track(u, 9)
            del u.hooks[0x40014072]                     # le vrai changement de machine
            this = 0x93900000
            for k in range(6):
                u.uc.mem_write(this + 70 + 4 * k, struct.pack(">i", -1))
            for a_, v in {0x400cf866: 0x93a00000, 0x4000eb90: 0x93a00000, 0x40012412: 0, 0x400cf9a8: 0x93a00000,
                          0x4006bdfe: 0, 0x4000eb9c: 0x93a00000, 0x40009c1a: obj, 0x400f44c6: 0, 0x4001416c: 0}.items():
                u.hooks[a_] = (f"{a_:#x}", v)
            try:
                u.call(0x400a2712, this, step, 0, 0)
                err = None
            except t7.UcError as e:
                err = str(e)
            got[step] = (struct.unpack(">H", u.uc.mem_read(snd + 38, 2))[0] >> 8, len(bad_reads(u)), err)
        print(f"        {name:8s}: molette depuis la machine 9 (-1, +1) -> {got}")
        # la molette borne machine + pas, écrit la machine puis appelle 0x40014072, qui relit la NOUVELLE machine :
        # ce chemin ne lit pas l'enregistrement de l'ancienne (pas le défaut) ; il ramène sur la dernière machine
        check(all(g == (top_ok, 0, None) for g in got.values()),
              f"{name} : molette + vrai changement de machine (0x40014072) depuis 9 -> {top_ok}, aucun accès faux")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", default=CYCLES)
    ap.add_argument("--tg", action="store_true", help="avec Model-TG (7 machines, Sampler = 6)")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    top_ok = 5
    if args.tg:
        import mkimg
        stock = mkimg.make(["model-tg"])
        fixed = patch(stock, FIX_TG)
        top_ok = 6
        print("Model-TG seul (référence : Model-TG sans correctif)")
    else:
        fixed = patch(stock, FIX)
        print("OS d'origine 1.13 (référence : stock)")
    print("1. accesseurs des enregistrements par machine")
    records(stock, fixed, top_ok)
    print("2. ouverture de MACHINES : 0x400148dc pour chaque piste")
    machines_view(stock, fixed, top_ok)
    print("3. potards de l'écran principal")
    knobs(stock, fixed, top_ok)
    print("4-5. molette de MACHINES et changement de machine")
    wheel_and_change(stock, fixed, top_ok)
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
