#!/usr/bin/env python3
"""Vérifie les deux .syx d'essai contre le .syx officiel, comme le dépôt vérifie un firmware :

  - paquets SysEx et leurs sommes (mtlib.syx.unwrap), somme du conteneur, HMAC (clé retrouvée dans le firmware
    lui-même, mtlib.container.find_key) ;
  - sections 1, 2, 4, 5 (bootloader, updater...) identiques octet pour octet à l'officiel : la récupération par le
    STARTUP MENU reste intacte ; seule la section 3 change ;
  - section 3 décompressée = OS officiel + les écritures des tweaks de travail, rien d'autre (empreinte attendue) ;
  - le vérificateur du flasher web (docs/flasher/flasher.js, via tools/webflash_check.js) accepte le fichier et
    refuse une copie dont un octet est abîmé.

    python3 verifier_syx.py [--cycles …] [--out DOSSIER]
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path("/home/user/Modded-Cycles")
sys.path.insert(0, str(REPO / "tools"))
import build                                 # noqa: E402
from mtlib import aplib, container           # noqa: E402
from mtlib.syx import unwrap                 # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import construire                            # noqa: E402

FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def sections(raw):
    stream, info = unwrap(raw)
    c = container.parse(stream)
    plain = {}
    for s in c["sections"]:
        try:
            plain[s["id"]] = aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])[0]
        except Exception:
            plain[s["id"]] = None
    return stream, info, c, plain


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", default=str(REPO / "firmware" / "model-cycles_OS1.13.syx"))
    ap.add_argument("--out", default=str(HERE / "out"))
    args = ap.parse_args()
    off_raw = pathlib.Path(args.cycles).read_bytes()
    _, off_info, off_c, off_plain = sections(off_raw)
    cat = {}
    for f in sorted((HERE / "tweaks" / "model-cycles_OS1.13").glob("[0-9]*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        cat[t["id"]] = t
    for name, ids in construire.FILES.items():
        p = pathlib.Path(args.out) / f"model-cycles_OS1.13_essai-{name}.syx"
        print(f"{p.name}")
        raw = p.read_bytes()
        stream, info, c, plain = sections(raw)          # unwrap vérifie chaque somme de paquet
        check(info["product"] == off_info["product"] and info["name"] == off_info["name"],
              f"paquets SysEx valides, même produit que l'officiel ({info['name']}, {info['count']} paquets)")
        check(int.from_bytes(stream[4:8], "big") == container.content_checksum(c["blob"]),
              "somme du conteneur")
        msg = c["blob"][:len(c["blob"]) - container.DIGEST_LEN]
        dig = c["blob"][len(c["blob"]) - container.DIGEST_LEN:]
        check(container.find_key([x for x in plain.values() if x], msg, dig) is not None,
              "HMAC du conteneur valide (clé du firmware lui-même)")
        ids_off = [s["id"] for s in off_c["sections"]]
        check([s["id"] for s in c["sections"]] == ids_off, f"mêmes sections {ids_off}")
        same = all(c["blob"][s["off"]:s["off"] + s["size"]] == off_c["blob"][o["off"]:o["off"] + o["size"]]
                   for s, o in zip(c["sections"], off_c["sections"]) if s["id"] != 3)
        check(same, "sections autres que 3 (bootloader, updater…) identiques octet pour octet à l'officiel")
        chosen = sorted((cat[i] for i in ids), key=lambda t: t["order"])
        want, dirty = build.apply_writes(off_plain[3], chosen)
        got = plain[3]
        sha = hashlib.sha256(got).hexdigest()
        check(got == want, f"section 3 = OS officiel + {len(ids)} tweaks de travail, rien d'autre "
                           f"({sum(a != b for a, b in zip(got, off_plain[3]))} octets changés) ; MAIN OS {sha}")
        check(sha == (pathlib.Path(args.out) / f"{name}.mainos.sha256").read_text().strip(),
              "empreinte du MAIN OS = celle qu'a imprimée build.py")
        with tempfile.TemporaryDirectory() as d:
            bad = bytearray(raw)
            pos = 0
            for _ in range(5):
                pos = bad.find(0xF0, pos) + 1
            bad[pos + 20] ^= 0x01
            bp = pathlib.Path(d) / "bad.syx"
            bp.write_bytes(bad)
            r = subprocess.run(["node", str(REPO / "tools" / "webflash_check.js"), str(p), str(bp), info["name"],
                                str(info["count"])], capture_output=True, text=True, cwd=REPO)
            print("        " + r.stdout.strip().replace("\n", "\n        "))
            check(r.returncode == 0, "flasher web (flasher.js) : fichier accepté, copie abîmée refusée")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
