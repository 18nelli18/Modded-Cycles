#!/usr/bin/env python3
"""Construit un firmware Model:Cycles modifié à partir de TA propre copie de l'OS officiel.

Aucune image firmware Elektron n'est distribuée ici. Ce script applique des tables
de patchs (octets) listées dans tweaks/<device>_OS<ver>/*.json à la section 3 (MAIN OS)
de ton .syx, puis reconstruit et re-signe le conteneur (checksums + HMAC-SHA256).

    python3 tools/build.py --list
    python3 tools/build.py -i model-cycles_OS1.13.syx --all
    python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout
    python3 tools/build.py -i model-cycles_OS1.13.syx -t 6ch-multiout --expect-mainos 65e24b50...

Sécurité : chaque octet « old » est vérifié avant écriture ; le SHA-256 de la section 3
d'origine est vérifié ; après build, tous les checksums et le HMAC sont recontrôlés.
Seule la section 3 est touchée : bootloader et updater sont conservés à l'identique,
donc la récupération par le STARTUP MENU (MIDI IN) reste disponible.

Le moteur bas niveau (mtlib) vient de drumkilla/elektron-model-tweaks (MIT) ; voir tools/mtlib/LICENSE.
"""
import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from mtlib import aplib, container            # noqa: E402
from mtlib.syx import unwrap, wrap, BYTES_PER_MSG  # noqa: E402

TWEAKS = ROOT / "tweaks"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_catalog():
    """{ 'model-cycles_OS1.13': (device_dict, {id: tweak_dict}) }"""
    cat = {}
    for d in sorted(TWEAKS.glob("*_OS*")):
        dev = json.loads((d / "device.json").read_text())
        tweaks = {}
        for f in sorted(d.glob("[0-9]*.json")):
            t = json.loads(f.read_text())
            tweaks[t["id"]] = t
        cat[d.name] = (dev, tweaks)
    return cat


def pick_target(cat, syx_sha):
    for name, (dev, tweaks) in cat.items():
        if dev["stock_syx_sha256"] == syx_sha:
            return name, dev, tweaks
    return None, None, None


def cmd_list(cat):
    for name, (dev, tweaks) in cat.items():
        print(f"{dev['device']} OS {dev['os']}  ({name})")
        for t in tweaks.values():
            print(f"  {t['id']:16} {t['name']}")


def apply_writes(main_os, tweaks_selected):
    data = bytearray(main_os)
    dirty = bytearray(len(main_os))
    for t in tweaks_selected:
        for w in t["writes"]:
            off = w["off"]
            old = bytes.fromhex(w["old"])
            new = bytes.fromhex(w["new"])
            cur = bytes(data[off:off + len(old)])
            if cur != old:
                raise SystemExit(
                    f"!! {t['id']} @ {off}: octets 'old' attendus {old.hex()} "
                    f"mais trouves {cur.hex()} — refus d'ecrire")
            data[off:off + len(new)] = new
            for k in range(off, off + len(new)):
                dirty[k] = 1
    return bytes(data), dirty


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-i", "--input", help="ton .syx officiel")
    ap.add_argument("-t", "--tweaks", help="liste d'ids separes par des virgules")
    ap.add_argument("--all", action="store_true", help="applique tous les tweaks du device")
    ap.add_argument("-o", "--output", help="fichier de sortie (defaut: <in>_mod.syx)")
    ap.add_argument("--list", action="store_true", help="liste les tweaks disponibles")
    ap.add_argument("--expect-mainos", help="SHA-256 attendu du MAIN OS patche (verification)")
    args = ap.parse_args()

    cat = load_catalog()
    if args.list or not args.input:
        cmd_list(cat)
        return

    raw = pathlib.Path(args.input).read_bytes()
    stream, info = unwrap(raw)                       # verifie chaque checksum de paquet
    c = container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    main_os, ops = aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])

    name, dev, tweaks = pick_target(cat, sha(raw))
    if not dev:
        # repli : matcher sur le MAIN OS decompresse
        for nm, (d, tw) in cat.items():
            if d["section_sha256"] == sha(main_os):
                name, dev, tweaks = nm, d, tw
                break
    if not dev:
        raise SystemExit("!! image non reconnue (ni .syx ni section 3). Version d'OS differente ?")
    if sha(main_os) != dev["section_sha256"]:
        raise SystemExit("!! la section 3 ne correspond pas a l'image de reference")
    print(f"cible : {dev['device']} OS {dev['os']}")

    if args.all:
        chosen = list(tweaks.values())
    elif args.tweaks:
        chosen = []
        for tid in args.tweaks.split(","):
            tid = tid.strip()
            if tid not in tweaks:
                raise SystemExit(f"!! tweak inconnu : {tid}")
            chosen.append(tweaks[tid])
    else:
        raise SystemExit("!! choisis --all ou -t <ids>")
    for t in chosen:
        print(f"  + {t['name']}")

    patched, dirty = apply_writes(main_os, chosen)
    print(f"  {sum(dirty)} octets changes sur {len(patched)}")
    print(f"  MAIN OS patche SHA-256 : {sha(patched)}")
    if args.expect_mainos and sha(patched) != args.expect_mainos.lower():
        raise SystemExit("!! le MAIN OS patche ne correspond pas au SHA attendu")

    # reconstruction : re-emet le flux aPLib, recalcule checksums + HMAC
    new_s3 = aplib.repack(patched, ops, dirty)
    msg = c["blob"][:len(c["blob"]) - container.DIGEST_LEN]
    expect = c["blob"][len(c["blob"]) - container.DIGEST_LEN:]
    # cle HMAC re-derivee depuis les sections decompressees de l'image d'origine
    plain = []
    for s in c["sections"]:
        try:
            plain.append(aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])[0])
        except Exception:
            pass
    key = container.find_key(plain, msg, expect)
    if not key:
        raise SystemExit("!! cle HMAC introuvable — image inattendue")
    blob = container.rebuild(c, {3: new_s3}, key)
    out_stream = container.build_stream(blob, BYTES_PER_MSG)
    out_raw = wrap(out_stream, info["product"], info["start_seq"])

    out_path = args.output or args.input.replace(".syx", "") + "_mod.syx"
    pathlib.Path(out_path).write_bytes(out_raw)
    print(f"\n  ecrit : {out_path}  ({len(out_raw)} o)")
    print(f"  .syx SHA-256 : {sha(out_raw)}")
    print("  (le hash du .syx depend du packer ; c'est le MAIN OS patche ci-dessus qui fait foi)")
    print("\n  Flash : STARTUP MENU (FUNC + power on, TRIG 4) puis envoi sur le MIDI IN (jack TRS).")


if __name__ == "__main__":
    main()
