#!/usr/bin/env python3
"""Preuve du tweak generative (notes/50) : motifs génératifs par-dessus model-tg.

  1. cœur : l'exécutable hôte de tools/machines/generative/core/ (host/gen_cli.c) redonne, octet pour octet, les
     vecteurs dorés de tools/machines/generative/vectors/ (sorties du cœur de référence en JavaScript : tables de
     colliers, trigs, longueurs, vélocités, notes et accords pour des réglages couvrant les trois couches) ;
  2. écritures : sur l'OS d'origine + model-tg, aucun autre tweak n'écrit nos octets ni la zone de notre code,
     sauf ceux déclarés dans `conflicts` ; les combinaisons avec les autres mods se construisent ;
  3. démarrage, accords, Random et Undo (_generative_os.py) ;
  4. la page GEN (_generative_page.py).
Les parties 3 et 4 font tourner le vrai code de l'OS et de Model-TG dans Unicorn, avec nos écritures.

    python3 tools/emu/test_generative.py --cycles model-cycles_OS1.13.syx [--with arp,trig-hold,tempo-max]

Il faut un compilateur C pour l'hôte (`cc`), unicorn et numpy. Environ 10 s.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

import build                    # noqa: E402
import test_sdvintage as T      # noqa: E402

MACH = HERE.parent / "machines" / "generative"
TWEAKS = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
BASE = 0x40000400
FAIL = []
TRACKS, STEPS = 6, 64
CORE = ("prng", "necklace", "nested", "layer1", "layer3", "generate")


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        FAIL.append(msg)


def build_cli(d):
    cli = pathlib.Path(d) / "gen_cli"
    subprocess.run(["cc", "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-o", str(cli), str(MACH / "host" / "gen_cli.c"),
                    *[str(MACH / "core" / f"{f}.c") for f in CORE]], check=True)
    return cli


def run_cli(cli, lines):
    return subprocess.run([str(cli)], input="\n".join(lines) + "\n", capture_output=True, text=True,
                          check=True).stdout.strip().split("\n")


def core_test(cli):
    ref = json.loads((MACH / "vectors" / "necklace-tables.json").read_text(encoding="utf-8"))
    check(int(run_cli(cli, ["tables"])[0]) == ref["fnv1a"], f"tables de colliers : empreinte {ref['fnv1a']:#010x}, "
          f"{ref['entries']} masques")
    files = sorted(f for f in (MACH / "vectors").glob("*.json") if f.name != "necklace-tables.json")
    for f in files:
        v = json.loads(f.read_text(encoding="utf-8"))
        out = run_cli(cli, [f"gen {v['seed']} " + " ".join(map(str, v["controls"])) + " 0 0 0 0 0 0"])[0].split()
        e = v["expected"]
        bad = []
        for t in range(TRACKS):
            written, length, trig, vel, note, chord = out[6 * t:6 * t + 6]
            if written != "1":
                bad.append(f"piste {t + 1} non écrite")
                continue
            sl = slice(t * STEPS, (t + 1) * STEPS)
            hexes = lambda a: "".join(f"{x & 0xff:02x}" for x in a)
            if trig != "".join("1" if x else "0" for x in e["step"]["flags"][sl]):
                bad.append(f"trigs piste {t + 1}")
            if int(length) != e["track"]["length"][t]:
                bad.append(f"longueur piste {t + 1}")
            if vel != hexes(e["step"]["velocity"][sl]) or note != hexes(e["step"]["note"][sl]) \
                    or chord != hexes(e["step"]["chord"][sl]):
                bad.append(f"vélocités/notes/accords piste {t + 1}")
        check(not bad, f"vecteur {f.name} : {', '.join(bad) or 'identique'}")


def writes_test(stock, catalog, ours):
    """Nos octets et la zone de notre code contre ceux de chaque autre tweak. Ceux que model-tg exclut déjà ne se
    combinent pas avec nous (`requires`) : ils sont comptés à part."""
    ranges = [(BASE + w["off"], BASE + w["off"] + len(w["new"]) // 2) for w in ours["writes"]]
    code = (int(ours["append"]["at"], 16), int(ours["symbols"]["ours_end"], 16))
    clash = {}
    tg_out = set(catalog["model-tg"].get("conflicts", []))
    tg_out |= {tid for tid, t in catalog.items() if "model-tg" in t.get("conflicts", [])}
    for tid, t in catalog.items():
        if tid in ("generative", "model-tg") or tid in tg_out:
            continue
        hit = []
        for w in t.get("writes", []):
            a, b = BASE + w["off"], BASE + w["off"] + len(w["new"]) // 2
            hit += [hex(a) for lo, hi in ranges + [code] if a < hi and b > lo]
        ap = t.get("append")
        if ap:
            a = int(ap["at"], 16)
            if a < code[1] and a + int(ap.get("size", 0)) > code[0]:
                hit.append(f"bloc ajouté {ap['at']}")
        if hit:
            clash[tid] = hit
    undeclared = sorted(t for t in clash if t not in ours["conflicts"])
    check(not undeclared, f"aucun chevauchement non déclaré ({len(tg_out)} tweaks déjà exclus par model-tg ; "
          f"{len(clash)} autres en conflit, tous dans `conflicts`)"
          + (f" : {undeclared}" if undeclared else ""))
    combos = [["model-tg", "generative"]]
    others = [t for t in ("arp", "trig-hold", "tempo-max", "boot-anim", "6ch-usbup") if t in catalog]
    combos += [["model-tg", "generative", t] for t in others] + [["model-tg", "generative"] + others]
    for ids in combos:
        try:
            ch = sorted((catalog[i] for i in ids), key=lambda t: t["order"])
            for t in ch:
                bad = [c for c in t.get("conflicts", []) if c in ids]
                if bad:
                    raise SystemExit(f"{t['id']} est en conflit avec {bad}")
            patched, _ = build.apply_writes(stock, ch)
            payload, _ = build.build_payload(ch, stock, None)
            check(True, f"{','.join(ids)} : se construit, MAIN OS {build.sha(patched + payload)[:16]}…")
        except SystemExit as x:
            check(False, f"{','.join(ids)} : {x}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--with", dest="others", default="", help="autres tweaks appliqués avec model-tg et generative")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((TWEAKS / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    _, catalog = build.load_catalog()["model-cycles_OS1.13"]
    others = [t for t in args.others.split(",") if t]
    import _generative_os as OS
    import _generative_page as PG
    with tempfile.TemporaryDirectory() as d:
        cli = build_cli(d)
        for mod in (OS, PG):
            mod.CYCLES, mod.CLI, mod.WITH = args.cycles, cli, others
        print("cœur (vecteurs dorés)")
        core_test(cli)
        print("écritures et combinaisons")
        writes_test(stock, catalog, catalog["generative"])
        if others:
            print(f"avec {','.join(others)}")
        FAIL.extend(OS.run())
        FAIL.extend(PG.run())
    print("TOUT OK" if not FAIL else f"{len(FAIL)} ÉCHEC(S)")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
