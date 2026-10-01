#!/usr/bin/env python3
"""Génère tweaks/model-cycles_OS1.13/30-model-tg.json : Model-TG de TinyGregAudio (licence MIT), tel que son
propre build l'exporte pour ce flasher (docs/PAYLOAD.md de Model-TG), depuis un clone de son dépôt au commit
épinglé (MODEL_TG_COMMIT). Notes : notes/31.

Model-TG est un tweak « append » sans Syntakt : ses écritures sur le MAIN OS d'origine, et un seul morceau
ajouté après l'image (l'espace vide jusqu'à 0x401ab750 et son code, qui s'exécute en place, dans des blocs du
cache du système de fichiers). Il est exclusif : il ne se combine pas avec les moteurs du Syntakt (pour
l'instant), ni avec les tweaks de drumkilla, qu'il contient déjà.

    git clone https://github.com/TinyGregAudio/Model-TG vendor/Model-TG
    git -C vendor/Model-TG checkout <MODEL_TG_COMMIT>
    python3 tools/gen_model_tg.py --cycles model-cycles_OS1.13.syx --model-tg vendor/Model-TG [--check]

Son build.py (relu : il n'appelle que l'assembleur, l'éditeur de liens, git et l'outil de dépaquetage, et n'écrit
que dans son dossier build/) est lancé avec la section 3 dépaquetée ici et un outil de dépaquetage qui ne fait
rien : le .syx n'est pas reconstruit par lui. Il vérifie lui-même son image et la réécrit comme ce flasher.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import test_sdvintage as T         # noqa: E402

DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "30-model-tg.json"
LICENSE_OUT = DEV / "LICENSE-Model-TG"
MODEL_TG_REPO = "TinyGregAudio/Model-TG"
MODEL_TG_COMMIT = "454963b78c329e3c4df2f2f3c972abb3db0ce289"     # 01/10/2026, « Export Model-TG as a Modded-Cycles tweak »
STOCK_SHA256 = "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98"


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def export(cycles, repo):
    """Tweak exporté par le build de Model-TG (dictionnaire)."""
    head = git(repo, "rev-parse", "HEAD")
    if head != MODEL_TG_COMMIT:
        raise SystemExit(f"!! {repo} est au commit {head[:7]}, attendu {MODEL_TG_COMMIT[:7]} (git checkout {MODEL_TG_COMMIT})")
    if git(repo, "status", "--porcelain"):
        raise SystemExit(f"!! {repo} a des modifications locales : il faut un clone propre")
    stock = T.main_os_from_syx(cycles)
    if build.sha(stock) != STOCK_SHA256:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    work = repo / "build"
    (work / "stock").mkdir(parents=True, exist_ok=True)
    (work / "stock" / "section_3_MAIN_OS.bin").write_bytes(stock)
    dummy = work / "_unused.syx"
    dummy.write_bytes(b"")                        # son build calcule l'empreinte du .syx qu'il aurait reconstruit
    out = work / "model-tg-modded-cycles.json"
    true = shutil.which("true") or "/usr/bin/true"
    env = {"CROSS": gx.CROSS, "PATH": os.environ["PATH"]}
    r = subprocess.run([sys.executable, "build.py", "--stock", str(cycles), "--tool", true, "--out", str(dummy),
                        "--modded-cycles", str(out)], cwd=repo, env=env, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("!! build de Model-TG :\n" + r.stdout[-2000:] + r.stderr[-2000:])
    tw = json.loads(out.read_text(encoding="utf-8"))
    return tw, stock, r.stdout


def adapt(tw, stock):
    """Format et métadonnées de ce dépôt ; vérifie que le tweak redonne l'image exportée."""
    patched, _ = build.apply_writes(stock, [tw])
    payload, _ = build.build_payload([tw], stock, None)
    if build.sha(bytes(patched) + payload) != tw["result_sha256"]:
        raise SystemExit("!! le tweak exporté ne redonne pas l'empreinte annoncée par Model-TG")
    if BASE + len(stock) + tw["append"]["size"] > 0x40200000:
        raise SystemExit("!! OS agrandi au-delà de la zone de travail du bootstrap (0x40200000)")
    others = sorted(set(tw["conflicts"]) | {gs.subset_id(c) for c in gs.subsets()}
                    | {"sdvintage-snare", "sdvintage-exact", "sdvintage-7th", "syntakt-vintage", "syntakt-meter"})
    return {
        "id": "model-tg",
        "order": 30,
        "name": "Model-TG (TinyGregAudio) : machine Sampler, rééchantillonnage, retrig et effets master",
        "description": [
            f"Model-TG de TinyGregAudio, https://github.com/{MODEL_TG_REPO} (licence MIT, texte dans",
            "LICENSE-Model-TG), commit " + MODEL_TG_COMMIT[:7] + ", exporté par son propre build pour ce flasher.",
            "Machine Sampler (7e machine), rééchantillonnage, retrig et effets master, Attack / Filtre / Résonance sur",
            "les machines d'origine, Scale Lock, envoi d'échantillons par Elektron Transfer, page System, et moins de",
            "charge processeur. Contient déjà les tweaks de drumkilla (mute verrouillé modifié, écoute d'un pas,",
            "défilement des noms). Exclusif : pas avec les moteurs du Syntakt pour l'instant (notes/31).",
            "Généré par tools/gen_model_tg.py. Aucun octet Elektron dans le code de Model-TG.",
        ],
        "version": tw["version"],
        "source": f"https://github.com/{MODEL_TG_REPO}/tree/{MODEL_TG_COMMIT}",
        "result_sha256": tw["result_sha256"],
        "device": tw["device"],
        "os": tw["os"],
        "section": tw["section"],
        "conflicts": others,
        "writes": tw["writes"],
        "append": tw["append"],
    }


BASE = gx.BASE


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--model-tg", required=True, help=f"clone de {MODEL_TG_REPO} au commit {MODEL_TG_COMMIT[:7]}")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    repo = pathlib.Path(args.model_tg).resolve()
    tw, stock, log = export(pathlib.Path(args.cycles).resolve(), repo)
    print("\n".join("  " + x.strip() for x in log.splitlines() if "MAIN OS sha256" in x or "one blob" in x
                    or "Modded-Cycles tweak" in x))
    out = adapt(tw, stock)
    text = json.dumps(out, indent=1) + "\n"
    lic = (repo / "LICENSE").read_text(encoding="utf-8")
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text and LICENSE_OUT.read_text(encoding="utf-8") == lic
        print(f"  {OUT.name} {'est à jour' if ok else 'NE CORRESPOND PAS (autre version des binutils ?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    LICENSE_OUT.write_text(lic, encoding="utf-8")
    print(f"  écrit : {OUT.relative_to(HERE.parent)} ({len(out['writes'])} écritures, {out['append']['size']} o ajoutés, "
          f"MAIN OS {out['result_sha256'][:8]}…) et {LICENSE_OUT.name}")


if __name__ == "__main__":
    main()
