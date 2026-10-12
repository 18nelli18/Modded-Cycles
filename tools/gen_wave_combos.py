#!/usr/bin/env python3
"""Génère les tweaks où la machine Wave (notes/60) joue avec MACRO (notes/43), ACID (notes/54) et les vrais moteurs du
Syntakt (notes/20), sur la même machine (notes/62), toujours sans Model-TG (Wave a sa propre lecture des fichiers) :

  - 25-macro-wave.json, 26-acid-wave.json, 25-macro-acid-wave.json : MACRO et/ou ACID puis Wave, 7e machine et
    suivantes. Mécanique de gen_macro.added_machine : charge utile rangée en clair, par morceaux (PACK) ;
  - 24-syntakt-<moteurs>[-macro][-acid]-wave.json : les moteurs, MACRO et ACID s'ils sont cochés, puis Wave.
    Mécanique de gen_macro_syntakt.py (notes/50) : passerelle des moteurs reprise octet pour octet de leur tweak
    versionné, charge utile rangée compressée (aPLib), régulateur de charge des moteurs étendu à nos machines.

Wave est toujours la dernière machine : ACID garde son numéro de gen_acid_combos.py. Son moteur est lié à la même place
dans toutes ces combinaisons (WAVE_AT, au-dessus des variables d'ACID ; ses variables à WAVE_BSS) ; notre code (la
glue de gen_wavetable.py) vient juste après lui et compare le son de la piste au numéro de Wave, qui change d'une
combinaison à l'autre. MACRO et ACID gardent leurs places et leurs octets (ceux de gen_acid_combos.py). Avec les
5 moteurs, MACRO, ACID et Wave : 14 machines, dont 8 ajoutées (rangées : gs.ROWS8).

    python3 tools/gen_wave_combos.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx \\
        --eurorack vendor/eurorack [--engines sd,cp | --engines none] [--macro yes|no|both] [--acid yes|no|both] [--check]

Sans --engines : toutes les combinaisons (127 fichiers). De l'OS, ces fichiers ne portent que les courts octets
d'origine (« old ») qui vérifient le fichier officiel ; la table des descripteurs est recopiée au build depuis TON
fichier (recette « cycles »), le code du Syntakt extrait au build de TON Syntakt_OS1.42.syx. Wave, MACRO et ACID sont
compilés par m68k-linux-gnu-gcc/g++ 13.3 (Ubuntu 24.04) : un autre GCC donne d'autres octets, et --check le dit.
"""
import argparse
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import gen_acid_combos as gac      # noqa: E402
import gen_macro as gm             # noqa: E402
import gen_macro_syntakt as gms    # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sdvintage_7th as g7     # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import gen_wavetable as gw         # noqa: E402
import gov_asm                     # noqa: E402
import syntakt                     # noqa: E402
import usb_steady                  # noqa: E402
import voice_loop                  # noqa: E402

DEV = gs.DEV
# Place de Wave dans la charge utile (décalages depuis son début) : au-dessus des variables d'ACID (gac.ACID_BSS + ses
# 6 voix : jusqu'à 0x782e8), son moteur et notre code (8 Ko au plus), puis les variables du moteur.
WAVE_AT = 0x79000
WAVE_BSS = 0x7b000
# Combinaisons testées sur un vrai Model:Cycles : (moteurs, avec MACRO, avec ACID). Ajouter ici après un test réussi
# (règle 3 d'AGENTS.md : seulement sur le retour de Maxime).
HW_TESTED = set()


def order(codes, macro, acid):
    return 24 if codes else (25 if macro else 26)


def wave_part(img, pay, mach):
    """Wave liée à pay + WAVE_AT (variables à pay + WAVE_BSS), machine mach : dict(machine, at, blobs, end, post)."""
    wv = gw.wave_part(pay + WAVE_AT, pay + WAVE_BSS, mach, pay + WAVE_BSS)

    def post(out):                      # nos écritures, avant que la charge utile soit mesurée
        out["writes"] = gw.merge_writes(out["writes"], gw.wave_writes(img, wv["gsyms"]))

    return dict(wv, at=pay + WAVE_AT, post=post)


def lines_end():
    return ["Généré par tools/gen_wave_combos.py. De l'OS, seuls les octets d'origine (old) qui vérifient le fichier",
            "officiel ; la table des descripteurs est recopiée au build (recette cycles)."]


def wave_line(mach):
    return (f"Wave (notes/60, machine {mach + 1}) liée à +{WAVE_AT:#x}, notre code juste après ; son navigateur bloqué, "
            "son chargement par YES, sa table retenue et l'identité Transfer CYC/SMP (notes/61) comme 36-wavetable.json.")


def finish(out, wave, macro_syms, acid):
    """Symboles pour les preuves : ceux de MACRO et d'ACID (gen_acid_combos), puis ceux de Wave."""
    gac.symbols(out, macro_syms, acid) if acid else out.update(symbols={k: f"{macro_syms[n]:#x}" for k, n in (
        ("macro_update", "macro_update"), ("macro_render", "macro_render"), ("braids_render", gm.BRAIDS_RENDER))}
        if macro_syms else {})
    out["symbols"].update(gw.wave_symbols(wave["syms"], wave["gsyms"]))


def build_ours(img, repo, macro, acid_on):
    """MACRO et/ou ACID puis Wave, sans les moteurs du Syntakt."""
    pay = gs.PAY_ALONE
    gs.set_base(pay)
    acid = gac.acid_part(pay) if acid_on else None
    mach = 6 + macro + acid_on
    wave = wave_part(img, pay, mach)
    machines, blobs, end, msyms = [], [], pay, None
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        if macro:
            mblob, msyms, end = gm.compile_machine(tmp, repo, pay)
            machines.append(dict(gm.MACHINE, label="MACRO", update=msyms["macro_update"], render=msyms["macro_render"]))
            blobs.append((pay, mblob))
        if acid:
            if end > acid["at"]:
                raise SystemExit(f"!! MACRO jusqu'à {end:#x} : ACID commence à {acid['at']:#x}")
            machines.append(acid["machine"])
            blobs.append((acid["at"], acid["blob"]))
            end = acid["end"]
        if end > wave["at"]:
            raise SystemExit(f"!! nos machines jusqu'à {end:#x} : Wave commence à {wave['at']:#x}")
        machines.append(wave["machine"])
        writes, append = gm.added_machine(img, None, machines, tmp, blobs + wave["blobs"], wave["end"])
    out = {"writes": writes, "append": append}
    wave["post"](out)
    tid = gw.combo_id((), macro, acid_on)
    names = [n for n, on in (("MACRO (Braids, Émilie Gillet, MIT)", macro),
                             ("ACID (basse acide, d'après Open303, MIT)", acid_on)) if on]
    which = ", ".join(f"{n} (notes/{nt}, machine {7 + i})" for i, (n, nt) in enumerate(
        [x for x, on in ((("MACRO", 43), macro), (("ACID", 54), acid_on)) if on]))
    out = {
        "id": tid,
        "order": order((), macro, acid_on),
        "name": "Machines " + ", ".join(names) + " et Wave (tes tables d'ondes)",
        "description": [
            f"Machines {which} et Wave, ensemble (notes/62).",
        ] + ([f"MACRO compilé comme 25-macro.json ({gm.EURORACK_REPO} {gm.EURORACK_COMMIT[:7]}, licence MIT : "
              "LICENSE-Braids), à la même place."] if macro else [])
          + ([gac.acid_line()] if acid_on else []) + [wave_line(mach)] + lines_end(),
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": sorted(gw.all_ids() - {tid}),
        "writes": out["writes"],
        "append": out["append"],
    }
    finish(out, wave, msyms, acid)
    out = usb_steady.add_to(out)        # comme MACRO, ACID et Wave seules : envoi à l'USB à heure fixe (notes/35),
    out = voice_loop.add_to(out)        # boucle des voix (notes/36)
    segs = sum(n for _, n in out["append"]["pack"])
    at = int(out["append"]["at"], 16)
    return out, dict(ndesc=g7.NDESC + 5 * len(machines), size=out["append"]["size"], packed=segs, end=at + segs)


def build_engines(img, st_img, repo, codes, macro, acid_on):
    """Les moteurs codes, MACRO si macro, ACID si acid_on, puis Wave (gen_macro_syntakt.build_tweak)."""
    pay = gs.PAY_ALONE
    gs.set_base(pay)
    acid = gac.acid_part(pay) if acid_on else None
    mach = 6 + len(codes) + macro + acid_on
    wave = wave_part(img, pay, mach)
    out, info = gms.build_tweak(img, st_img, repo, codes, None, macro=macro, acid=acid, wave=wave)
    macro_syms = gms.compile_macro(repo, pay)[1] if macro else None
    names = [gs.CATALOG[c]["name"] for c in codes]
    which = ", ".join(f"{gs.CATALOG[c]['name']} = {gs.CATALOG[c]['label']} (machine {7 + i})"
                      for i, c in enumerate(codes))
    k = 6 + len(codes)
    for label, on in (("MACRO", macro), ("ACID", acid_on)):
        if on:
            which += f", {label} (machine {k + 1})"
            k += 1
    which += f", Wave (machine {k + 1})"
    tid = gw.combo_id(codes, macro, acid_on)
    versioned = gs.tweak_id(codes)
    gov = [gov_asm.NOTE] if gov_asm.NOTE in out["description"] else []
    out.update({
        "id": tid,
        "order": order(codes, macro, acid_on),
        "name": "Vrais moteurs du Syntakt (" + ", ".join(names) + ")"
                + (", machine MACRO (Braids, Émilie Gillet, MIT)" if macro else "")
                + (", machine ACID (basse acide, d'après Open303, MIT)" if acid_on else "")
                + " et machine Wave (tes tables d'ondes)",
        "description": [
            "Moteurs du Syntakt (OS 1.42 ou 1.41, extraits AU BUILD de TON Syntakt_OS1.42.syx)"
            + (", machine MACRO (notes/43)" if macro else "") + (", machine ACID (notes/54)" if acid_on else "")
            + " et machine Wave (notes/60),",
            "ensemble (notes/62) : " + which + ".",
            "Passerelle des moteurs reprise telle quelle de " + versioned
            + (f" ; MACRO compilé comme 25-macro.json ({gm.EURORACK_REPO} {gm.EURORACK_COMMIT[:7]}, licence MIT : "
               "LICENSE-Braids), à la place des tweaks -macro." if macro else "."),
        ] + ([gac.acid_line()] if acid_on else []) + [
            wave_line(k),
            "Charge utile rangée compressée (aPLib), décompressée au démarrage ; tables d'ondes de CHORD reprises en",
            "SRAM. Le régulateur de charge des moteurs vaut aussi pour nos machines.",
        ] + lines_end() + gov,
        "conflicts": sorted(gw.all_ids() - {tid}),
    })
    finish(out, wave, macro_syms, acid)
    return out, info


def todo_list(args):
    if args.engines is None:
        return gw.combos()
    pick = lambda v: {"yes": [True], "no": [False], "both": [False, True]}[v]
    if args.engines == "none":
        return [((), m, a) for m in pick(args.macro) for a in pick(args.acid) if m or a]
    want = args.engines.split(",")
    if set(want) - set(gs.CATALOG):
        raise SystemExit(f"!! moteurs inconnus : {set(want) - set(gs.CATALOG)}")
    codes = tuple(c for c in gs.CATALOG if c in want)
    return [(codes, m, a) for m in pick(args.macro) for a in pick(args.acid)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--eurorack", required=True, help=f"clone de {gm.EURORACK_REPO} au commit {gm.EURORACK_COMMIT[:7]}")
    ap.add_argument("--engines", help="moteurs, séparés par des virgules, ou none (sinon toutes les combinaisons)")
    ap.add_argument("--macro", choices=("yes", "no", "both"), default="both", help="avec --engines : avec MACRO ou non")
    ap.add_argument("--acid", choices=("yes", "no", "both"), default="both", help="avec --engines : avec ACID ou non")
    ap.add_argument("--check", action="store_true", help="vérifie que les JSON versionnés correspondent")
    args = ap.parse_args()
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    repo = pathlib.Path(args.eurorack).resolve()
    gm.check_sources(repo)
    st_img = syntakt.dsp_image(args.syntakt)
    bad = 0
    for codes, macro, acid in todo_list(args):
        if codes:
            tweak, info = build_engines(img, st_img, repo, list(codes), macro, acid)
        else:
            tweak, info = build_ours(img, repo, macro, acid)
        path = DEV / f"{tweak['order']}-{tweak['id']}.json"
        text = json.dumps(tweak, indent=1) + "\n"
        print(f"  {tweak['id']} : {len(tweak['writes'])} écritures, {info['ndesc']} descripteurs, charge utile "
              f"{info['size']} o, rangée en {info['packed']} o, image jusqu'à {info['end']:#x}")
        bad += gm.emit(path, text, args.check)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
