#!/usr/bin/env python3
"""Synchronise le flasher de test avec le principal validé (notes/53 §11)."""
import argparse
import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROD = ROOT / "docs/flasher"
OUT = ROOT / "docs/flasher-test"
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles")
    ap.add_argument("--syntakt")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = {p.name:p.read_text() for p in PROD.iterdir() if p.is_file() and p.suffix in (".js", ".css", ".txt", ".html") and p.name != "tweaks.js"}
    files["tweaks.js"] = "/* Catalogue partagé avec le flasher principal. */\n"
    files["index.html"] = files["index.html"].replace('<script src="tweaks.js?', '<script src="../flasher/tweaks.js?')
    files["guide.html"] = (ROOT / "docs/guide/index.html").read_text()
    for name,text in files.items():
        text=text.rstrip()+"\n"
        path=OUT/name
        if args.check:
            assert path.read_text()==text,str(path)
        else:
            path.write_text(text)
    print("ok : flasher de test synchronisé avec le principal")
if __name__ == "__main__":
    main()
