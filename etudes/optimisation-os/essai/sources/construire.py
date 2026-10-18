#!/usr/bin/env python3
"""Construit les deux fichiers d'essai avec tools/build.py du dépôt, à partir du .syx officiel, et les tweaks de
travail de CE dossier (tweaks/model-cycles_OS1.13/, écrits par gen_essai.py) au lieu de ceux du dépôt.

  reference : OS 1.13 officiel + essai-compteur
  optimise  : le même compteur + D1, D2 + p1, p2, p3, mix2, PUNCH, arrêt des voix muettes

    python3 construire.py [--cycles model-cycles_OS1.13.syx] [--out DOSSIER]
Seul changement par rapport à `tools/build.py -i … -t …` : le catalogue lu (build.TWEAKS).
"""
import argparse
import contextlib
import io
import pathlib
import re
import sys

REPO = pathlib.Path("/home/user/Modded-Cycles")
sys.path.insert(0, str(REPO / "tools"))
import build                     # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
FILES = {
    "reference": ["essai-compteur"],
    "optimise": ["essai-compteur", "essai-gel-machines", "essai-gel-horloge", "essai-dist", "essai-effets",
                 "essai-envois", "essai-mix2", "essai-punch", "essai-voix-muettes"],
}


def run(cycles, ids, out):
    build.TWEAKS = HERE / "tweaks"
    sys.argv = ["build.py", "-i", cycles, "-t", ",".join(ids), "-o", str(out)]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        build.main()
    log = buf.getvalue()
    sha = re.search(r"MAIN OS patche SHA-256 : ([0-9a-f]{64})", log).group(1)
    return log, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", default=str(REPO / "firmware" / "model-cycles_OS1.13.syx"))
    ap.add_argument("--out", default=str(HERE / "out"))
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, ids in FILES.items():
        p = out / f"model-cycles_OS1.13_essai-{name}.syx"
        log, sha = run(args.cycles, ids, p)
        print(f"===== {name} : {', '.join(ids)}\n{log}")
        (out / f"{name}.mainos.sha256").write_text(sha + "\n")


if __name__ == "__main__":
    main()
