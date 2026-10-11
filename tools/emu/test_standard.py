#!/usr/bin/env python3
"""Preuve du paquet standard (notes/59) : ce que la page du flasher installe par défaut, sans mode avancé.

Le paquet est la liste STANDARD de tools/gen_flasher_tweaks.py, recopiée dans docs/flasher/tweaks.js ; le générateur
vérifie déjà que chaque carte est testée sur la machine, n'en exclut aucune autre et ne demande pas d'autre fichier.
Ce test vérifie que la combinaison existe et tient :

  1. Build : tools/build.py construit le paquet depuis le .syx officiel, et son MAIN OS a l'empreinte que la page
     attend (REF_MAINOS de docs/flasher/app.js, tools/ref_mainos.py).
  2. Chaque mod du paquet : sa preuve en émulation (le code de l'OS, d'origine contre modifié) tourne avec tous les
     autres mods du paquet installés (--with). latching-mute et browser-scroll (tweaks de drumkilla ; Model-TG
     contient le second octet pour octet, une variante du premier) n'ont pas de preuve à eux ; MACRO demande les
     sources de Braids (--eurorack), sans elles sa preuve est sautée et le test le dit.

Un mod ajouté à STANDARD sans preuve dans PROOFS fait échouer le test : on l'y ajoute (ou dans NO_PROOF, avec la raison).
Le Model:Samples est prouvé à part, par tools/emu/test_mods_for_samples.py, qui emballe aussi le paquet standard.

    python3 tools/emu/test_standard.py --cycles model-cycles_OS1.13.syx [--eurorack eurorack/] [--jobs 3] [--quick]

Compter 20 à 30 min avec --jobs 3 (Chord Keys, le filtre et MACRO sont les plus longs) ; --quick saute les mesures
lentes du filtre et ne garde que quelques modèles de MACRO.
"""
import argparse
import concurrent.futures
import pathlib
import re
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))

import ref_mainos                                                    # noqa: E402

# tweak -> ses preuves (scripts de tools/emu/), chacune lancée avec --with les autres tweaks du paquet
PROOFS = {
    "trig-preview": ["test_trig_preview.py"],
    "trig-hold": ["test_trig_hold.py"],
    "arp": ["test_arp.py"],
    "tempo-max": ["test_tempo_max.py"],
    "boot-anim": ["test_boot_anim.py"],
    "multiline-browser": ["test_multiline_browser.py"],
    "level-pan-values": ["test_level_pan.py"],
    "trigless-dim": ["test_trigless_dim.py"],
    "midi-live-both": ["test_midi_thru.py"],
    "macro": ["test_macro.py"],
    "chord-keys": ["test_chord_keys.py", "test_chord_keys_release.py"],
    "track-filter": ["test_track_filter.py"],
}
NO_PROOF = {
    "latching-mute": "tweak de drumkilla, testé par lui ; Model-TG en contient une variante (5 octets diffèrent en "
                     "0x40148696 : trois NOP ici, un jsr vers sa propre fonction dans Model-TG)",
    "browser-scroll": "tweak de drumkilla, octet pour octet celui que contient Model-TG (testé sur la machine)",
}
QUICK = {"test_macro.py", "test_track_filter.py"}                   # ont une option --quick


def ref_mainos_of(key):
    text = (REPO / "docs/flasher/app.js").read_text(encoding="utf-8")
    block = text[text.index("const REF_MAINOS = {"):]
    block = block[:block.index("\n};")]
    return dict(re.findall(r'"([^"]+)": "([0-9a-f]{64})"', block)).get(key)


def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--eurorack", help="clone de pichenettes/eurorack, pour la preuve de MACRO (tools/gen_macro.py)")
    ap.add_argument("--jobs", type=int, default=3, help="preuves lancées en même temps (défaut 3)")
    ap.add_argument("--quick", action="store_true", help="sans les mesures lentes (filtre, tous les modèles de MACRO)")
    ap.add_argument("--only", default="", help="seulement ces tweaks du paquet (ex. arp,macro)")
    ap.add_argument("--log", help="dossier où écrire la sortie de chaque preuve")
    args = ap.parse_args()

    ids = ref_mainos.standard_ids()
    key = "+".join(ids)
    fails = []

    def check(ok, what):
        print(f"  {'ok  ' if ok else 'FAIL'}  {what}")
        if not ok:
            fails.append(what)

    print(f"Paquet standard : {len(ids)} mods : {', '.join(ids)}")
    print("1. Build")
    ref = ref_mainos_of(key)
    check(ref is not None, "la page a son empreinte (REF_MAINOS)")
    if ref:
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "standard.syx"
            code, text, _ = run([sys.executable, "tools/build.py", "-i", args.cycles, "-t", ",".join(ids),
                                 "--expect-mainos", ref, "-o", str(out)])
            check(code == 0 and out.exists(), f"tools/build.py le construit, MAIN OS {ref[:16]}… comme la page"
                  + ("" if code == 0 else "\n" + text[-2000:]))

    print("2. Chaque mod avec tous les autres")
    missing = [i for i in ids if i not in PROOFS and i not in NO_PROOF]
    check(not missing, "chaque mod du paquet a sa preuve (PROOFS) ou une raison de ne pas en avoir (NO_PROOF)"
          + (f" ; manque : {', '.join(missing)}" if missing else ""))
    for i in ids:
        if i in NO_PROOF:
            print(f"  --    {i} : pas de preuve à lui ({NO_PROOF[i]})")
    only = set(filter(None, args.only.split(",")))
    jobs = []
    for i in ids:
        if i not in PROOFS or (only and i not in only):
            continue
        others = ",".join(o for o in ids if o != i)
        for script in PROOFS[i]:
            cmd = [sys.executable, f"tools/emu/{script}", "--cycles", args.cycles, "--with", others]
            if script == "test_macro.py":
                if not args.eurorack:
                    print(f"  --    {i} : {script} sauté, il faut --eurorack (sources de Braids)")
                    continue
                cmd += ["--eurorack", args.eurorack]
            if args.quick and script in QUICK:
                cmd.append("--quick")
            jobs.append((i, script, cmd))
    logdir = pathlib.Path(args.log) if args.log else None
    if logdir:
        logdir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futs = {pool.submit(run, cmd): (i, script) for i, script, cmd in jobs}
        for fut in concurrent.futures.as_completed(futs):
            i, script = futs[fut]
            code, text, dt = fut.result()
            if logdir:
                (logdir / (script[:-3] + ".log")).write_text(text, encoding="utf-8")
            tail = "" if code == 0 else "\n" + "\n".join("        " + ln for ln in text.rstrip().splitlines()[-25:])
            check(code == 0, f"{i} : {script} avec les {len(ids) - 1} autres ({dt:.0f} s){tail}")

    if fails:
        print(f"\n{len(fails)} ÉCHEC(S)")
        sys.exit(1)
    print("\nTOUT OK")


if __name__ == "__main__":
    main()
