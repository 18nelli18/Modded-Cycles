#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve MCHN sur les vrais accesseurs et le sélecteur DEST de l'OS (notes/58).

Compare origine/modifié, tous les identifiants, chaque machine de la combinaison, pile et registres préservés.
Exécute aussi la fonction LFO de l'OS avec destination k=9 : elle modifie le mot de machine sans changer le calcul.

    python3 tools/emu/test_mchn_lfo.py --cycles model-cycles_OS1.13.syx [--with ids --syntakt Syntakt_OS1.42.syx]
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build
import gen_mchn_lfo as G
import test_lfo_plus as L

DEV = HERE.parent.parent / "tweaks/model-cycles_OS1.13"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--with", dest="others", default="")
    ap.add_argument("--syntakt")
    args = ap.parse_args()
    stock = G.main_os(args.cycles)
    catalog = {t["id"]: t for p in DEV.glob("[0-9]*.json") if (t := json.loads(p.read_text()))}
    tweak = catalog["mchn-lfo"]
    others = [catalog[key] for key in args.others.split(",") if key]
    chosen = sorted(others + [tweak], key=lambda t: t["order"])
    build.check_conflicts(chosen)
    payload, _ = build.build_payload(others, stock, args.syntakt)
    before = build.apply_writes(stock, sorted(others, key=lambda t: t["order"]))[0] + payload
    after = build.apply_writes(stock, chosen)[0] + payload
    runtimes = L.payload_runtimes(others, stock, args.syntakt)
    S, P = L.Rig(before, runtimes), L.Rig(after, runtimes)
    failures = []
    def check(ok, text):
        print(f"{'ok' if ok else 'FAIL'} : {text}", flush=True)
        if not ok:
            failures.append(text)
    check(all(stock[w['off']:w['off'] + len(bytes.fromhex(w['old']))] == bytes.fromhex(w['old'])
              for w in tweak['writes']), "octets d'origine de chaque écriture")
    check(before[len(stock):] == after[len(stock):], "charges utiles identiques")
    # La vraie table de l'accesseur donne les identifiants, y compris la copie en RAM si elle est utilisée.
    flags_ok = labels_ok = True
    for identifier in range(140):
        flags_s = S.call(0x4005a85e, identifier, check="flags origine")
        flags_p = P.call(0x4005a85e, identifier, check="flags MCHN")
        flags_ok &= flags_p == (0x600 if identifier == 41 else flags_s)
        name_s = S.call(0x4000b208, 0, identifier, check="nom origine")
        name_p = P.call(0x4000b208, 0, identifier, check="nom MCHN")
        labels_ok &= (P.rd(name_p, 5) == b'MCHN\0') if identifier == 41 else name_p == name_s
    check(flags_ok, "éligibilité : seul Algorithm devient destination LFO/vélocité")
    check(labels_ok, "libellé court MCHN, autres noms inchangés")
    # Maximum dans la table du vrai accesseur, y compris sa copie relocalisée.
    maximum_s = S.r32(S.r32(0x4005a86a) + 41 * 56 + 12)
    maximum_p = P.r32(P.r32(0x4005a86a) + 41 * 56 + 12)
    check(maximum_s == maximum_p, "borne de machine conservée")
    # La borne maximale se lit dans le descripteur +12.
    count = (maximum_p >> 8) + 1
    for machine in range(count):
        for r in (S, P):
            L.setup_track(r, machine)
        def chain(r):
            value, seen = 0, [0]
            for _ in range(40):
                following = r.call(0x4000c140, L.THIS, value, 0x100, 0x600, check="DEST")
                if following == value:
                    return seen
                seen.append(following)
                value = following
            raise AssertionError("liste DEST sans fin")
        old, new = chain(S), chain(P)
        check(0x900 not in old and 0x900 in new and [v for v in new if v != 0x900] == old,
              f"machine {machine + 1}/{count} : MCHN ajouté, autres destinations identiques")
    # Mapping aller/retour pour les destinations déjà enregistrées : code de l'OS inchangé.
    check(all(S.call(0x4005aa54, 0, k) == P.call(0x4005aa54, 0, k) for k in range(33)),
          "numérotation des destinations enregistrées inchangée")
    target = L.tracks([L.lfo(spd=0x7000, dest=9, wave=1, dep=0x4100, fade=0x4000, mode=1) for _ in range(6)], base={9: 0x200})
    moving, same = set(), True
    for block in range(100):
        mask = 63 if block == 0 else 0
        S.block(target, 14400, mask, smooth=False)
        P.block(target, 14400, mask, smooth=False)
        moving.add(P.r16(L.OBJ + 14 + 18))
        same &= S.rd(L.OBJ, 476) == P.rd(L.OBJ, 476) and S.rd(L.LFO_ST, 192) == P.rd(L.LFO_ST, 192)
    check(same and any(v != 0x200 for v in moving), "vrai LFO de l'OS : machine modulée, calcul identique")
    check(not (S.bad or P.bad or S.asserts or P.asserts or L.FAIL), "aucun accès hors mémoire ni registre/pile perdu")
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
