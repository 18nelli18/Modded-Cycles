#!/usr/bin/env python3
"""Correctifs de gel D1 (MACHINES) et D2 (horloge MIDI) : les preuves de l'étude « stabilité » (preuve_machines.py,
preuve_midi_horloge.py, copiées ici), rejouées sur les images livrées, sans rien réécrire :
  défaut  = OS officiel, puis le fichier `reference` (le compteur seul : il ne touche ni à l'un ni à l'autre) ;
  corrigé = le fichier `optimise` tel qu'il sort de son .syx.

    python3 preuve_gels.py [--out DOSSIER_DES_SYX]
"""
import argparse
import sys

sys.dont_write_bytecode = True
import banc_essai as be                     # noqa: E402
import preuve_machines as PM                # noqa: E402
import preuve_midi_horloge as PH            # noqa: E402
from unicorn import m68k_const as mk        # noqa: E402

BASE = 0x40000400
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def d1(stock, fixed):
    PM.FAIL.clear()
    print("1. accesseurs des enregistrements par machine")
    PM.records(stock, fixed, 5)
    print("2. ouverture de MACHINES : 0x400148dc pour chaque piste")
    PM.machines_view(stock, fixed, 5)
    print("3. potards de l'écran principal")
    PM.knobs(stock, fixed, 5)
    print("4-5. molette de MACHINES et changement de machine")
    PM.wheel_and_change(stock, fixed, 5)
    return list(PM.FAIL)


def d2(stock, fixed):
    """Les contrôles 1 et 2 de preuve_midi_horloge.main, sur deux images données."""
    fails = []

    def ck(ok, msg):
        print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
        if not ok:
            fails.append(msg)
    for label, img in (("défaut", stock), ("corrigé", fixed)):
        r = PH.Rig(img)
        r.uc.mem_write(0xec074004, b"\x04")
        ok = r.tick()
        ck(ok is True and r.state()[3] == b"\xf8" and r.r32(0x4049dccc) == 0,
           f"{label} : UART libre, 0xF8 écrit dans 0xec07400c, anneau vide")
    res = {}
    for label, img in (("défaut", stock), ("corrigé", fixed)):
        r = PH.Rig(img)
        r.w32(0x4049dca0, 2)
        r.uc.mem_write(0xec074004, b"\x00")
        states = []
        for k in range(1, 1027):
            ok = r.tick()
            if ok is not True:
                res[label] = (k, ok, r.uc.reg_read(mk.UC_M68K_REG_PC), r.uc.reg_read(mk.UC_M68K_REG_SR), states)
                break
            states.append(r.state())
        else:
            res[label] = (None, True, None, None, states)
    k, ok, pc, sr, st = res["défaut"]
    ck(k == 1025 and pc is not None and PH.SPIN[0] <= pc < PH.SPIN[1] and (sr >> 8) & 7 == 7,
       f"défaut : 1024 tops rangés, le 1025e ne revient pas (PC {pc:#x} dans 0x4000123a..46, SR {sr:#06x} : IPL 7)"
       if pc else f"défaut : inattendu {res['défaut'][:4]}")
    k2, ok2, _, _, st2 = res["corrigé"]
    ck(k2 is None and len(st2) == 1026, "corrigé : les 1026 tops reviennent (le 1025e et le 1026e jettent leur octet)")
    ck(st2[:1024] == st[:1024], "corrigé : les 1024 premiers tops laissent anneau, index, compte et registres "
       "identiques au défaut, top après top")
    ck(st2[1025][2] == 1024 and st2[1025][0] == st2[1023][0], "corrigé : anneau plein inchangé (compte 1024)")
    return fails


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(be.OUT))
    args = ap.parse_args()
    imgs = be.images(args.out)
    for k, v in imgs.items():
        print(f"{k:10s} MAIN OS {be.sha(v)}")
    opt = imgs["optimise"]
    for va, old, new in PM.FIX:
        check(imgs["officiel"][va - BASE:va - BASE + 2].hex() == old and opt[va - BASE:va - BASE + 2].hex() == new and
              imgs["reference"][va - BASE:va - BASE + 2].hex() == old,
              f"D1 {va:#x} : {old} (officiel, référence) -> {new} (optimisé)")
    va, old, new = PH.FIX
    check(imgs["officiel"][va - BASE:va - BASE + 2] == old and opt[va - BASE:va - BASE + 2] == new and
          imgs["reference"][va - BASE:va - BASE + 2] == old,
          f"D2 {va:#x} : {old.hex()} (officiel, référence) -> {new.hex()} (optimisé)")
    for name in ("officiel", "reference"):
        print(f"\n===== D1, MACHINES : défaut = {name}, corrigé = optimise")
        f = d1(imgs[name], opt)
        check(not f, f"D1 rejouée (défaut {name}, corrigé optimise) : {len(f)} échec(s)")
        print(f"\n===== D2, horloge MIDI : défaut = {name}, corrigé = optimise")
        f = d2(imgs[name], opt)
        check(not f, f"D2 rejouée (défaut {name}, corrigé optimise) : {len(f)} échec(s)")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
