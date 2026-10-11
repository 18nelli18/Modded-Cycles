#!/usr/bin/env python3
"""Audit reproductible du prototype hors flasher avec les branches upstream.

Réutilise le vérificateur du dépôt, y compris dépendances, conflits et charges
utiles. Les références --git doivent exister dans --upstream (aucun fetch).
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_overlaps as audit

ROOT = HERE.parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", type=pathlib.Path)
    ap.add_argument("--scroll", action="store_true")
    ap.add_argument("--git", action="append", default=[])
    ap.add_argument("--dynamics", action="store_true")
    ap.add_argument("--advanced", action="store_true")
    ap.add_argument("--sequence-only",action="store_true")
    args = ap.parse_args()
    folder = "experimental/sequence-only/" if args.sequence_only else "experimental/advanced/" if args.advanced else ""
    prototypes = [json.loads((ROOT / f"tweaks/model-cycles_OS1.13/{folder}49-{n}.json").read_text())
                  for n in ("scale-gen", "scale-gen-st")]
    dev, tweaks = audit.load_dir(ROOT)
    sources = [("fork", [t for t in tweaks if t["id"] not in ("scale-gen", "scale-gen-st")] + prototypes)]
    if args.git:
        assert args.upstream, "--upstream requis avec --git"
        audit.ROOT = args.upstream.resolve()
        for ref in args.git:
            other, tweaks = audit.load_git(ref)
            assert other["section_len"] == dev["section_len"]
            sources.append((ref, tweaks + prototypes))
    baseline = [(name, [t for t in ts if t["id"] not in ("scale-gen", "scale-gen-st")])
                for name, ts in sources]
    existing, _ = audit.check(audit.merge(baseline), dev["section_len"])
    errors, summary = audit.check(audit.merge(sources), dev["section_len"])
    introduced = sorted(set(errors) - set(existing))
    for error in introduced:
        print("FAIL : " + error)
    assert not introduced, f"{len(introduced)} conflits nouveaux"
    if existing:
        print(f"NOTE : {len(existing)} erreurs préexistantes inchangées ; voir check_overlaps.py sans prototype")
    print("ok : aucun conflit nouveau de masque, crochet, dépendance ou charge utile ; " + summary)


if __name__ == "__main__":
    main()
