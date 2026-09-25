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
Deux tweaks déclarés incompatibles (champ « conflicts ») sont refusés ensemble. Un tweak
qui écrit dans une zone 0xFF (cave) est refusé si l'image d'origine pointe dans cette zone,
sauf si cette référence est elle-même réécrite par un des tweaks choisis.
Seule la section 3 est touchée : bootloader et updater sont conservés à l'identique,
donc la récupération par le STARTUP MENU (MIDI IN) reste disponible.

Le moteur bas niveau (mtlib) vient de drumkilla/elektron-model-tweaks (MIT) ; voir tools/mtlib/LICENSE.
"""
import argparse
import array
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
BASE = 0x40000400                             # VA du premier octet de la section 3 (MAIN OS)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_catalog():
    """{ 'model-cycles_OS1.13': (device_dict, {id: tweak_dict}) }"""
    cat = {}
    for d in sorted(TWEAKS.glob("*_OS*")):
        dev = json.loads((d / "device.json").read_text(encoding="utf-8"))
        tweaks = {}
        for f in sorted(d.glob("[0-9]*.json")):
            t = json.loads(f.read_text(encoding="utf-8"))
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
            excl = f"  (incompatible avec : {', '.join(t['conflicts'])})" if t.get("conflicts") else ""
            print(f"  {t['id']:16} {t['name']}{excl}")


def check_conflicts(chosen):
    ids = {t["id"] for t in chosen}
    for t in chosen:
        for other in t.get("conflicts", []):
            if other in ids:
                raise SystemExit(f"!! {t['id']} et {other} sont incompatibles (ils modifient les memes octets) : "
                                 "choisis l'un ou l'autre avec -t")


def cave_zones(main_os, chosen):
    """Zones 0xFF de l'image d'origine ou un tweak ecrit (caves) : [(lo, hi)] en offsets.
    lo recule jusqu'au debut du bloc 0xFF (un objet qui commencerait avant l'ecriture
    serait touche) ; hi s'arrete a la fin des octets ecrits (un objet qui commence
    apres n'est pas touche, meme si ses premiers octets valent 0xFF)."""
    zones = {}                                  # debut du bloc -> fin ecrite la plus haute
    for t in chosen:
        for w in t["writes"]:
            old = bytes.fromhex(w["old"])
            if len(old) < 2 or old.count(0xFF) != len(old):
                continue
            lo, hi = w["off"], w["off"] + len(old)
            while lo > 0 and main_os[lo - 1] == 0xFF:
                lo -= 1
            zones[lo] = max(hi, zones.get(lo, hi))
    return sorted(zones.items())


def refs_into(main_os, zones):
    """References, dans le MAIN OS d'ORIGINE, vers les zones [(lo, hi)] (offsets).
    Renvoie (sures, douteuses) : [(va de la reference, va visee, nature)].
    Sures : constantes 32 bits (pointeurs, jmp/jsr abs.l, lea/move #imm).
    Douteuses : adressages (d16,PC) de lea/pea/jmp/jsr/move et branchements Bcc/BRA/BSR,
    qu'une donnee peut imiter."""
    w = array.array("H", main_os[:len(main_os) & ~1])
    if sys.byteorder == "little":
        w.byteswap()
    vz = [(lo + BASE, hi + BASE) for lo, hi in zones]
    lo_all, hi_all = min(a for a, _ in vz), max(b for _, b in vz)

    def inside(t):
        return lo_all <= t < hi_all and any(a <= t < b for a, b in vz)

    def s16(x):
        return x - 0x10000 if x & 0x8000 else x

    sure, doubt = [], []
    n = len(w)
    for i in range(n - 1):
        x, va = w[i], BASE + 2 * i
        v = (x << 16) | w[i + 1]
        if inside(v):
            sure.append((va, v, "constante 32 bits"))
        t = None
        if (x & 0x3F) == 0x3A and ((x & 0xF1FF) == 0x41FA or x in (0x487A, 0x4EFA, 0x4EBA)
                                    or ((x & 0xC000) == 0 and (x & 0x3000))):
            t, kind = va + 2 + s16(w[i + 1]), "adressage (d16,PC)"
        elif (x & 0xF000) == 0x6000:
            d8 = x & 0xFF
            if d8 == 0:
                t = va + 2 + s16(w[i + 1])
            elif d8 == 0xFF:
                t = va + 2 + ((((w[i + 1] << 16) | (w[i + 2] if i + 2 < n else 0)) ^ 0x80000000) - 0x80000000)
            else:
                t = va + 2 + (d8 - 0x100 if d8 & 0x80 else d8)
            kind = "branchement"
        if t is not None and inside(t):
            doubt.append((va, t, kind))
    return sure, doubt


def check_caves(main_os, chosen, force, dirty=None, patched=None):
    """Refuse d'ecrire dans une zone 0xFF que l'image d'origine reference : elle ne serait pas libre.
    Une reference dont les octets sont eux-memes reecrits par les tweaks choisis (dirty) n'existe
    plus dans l'image patchee (patched) : elle est listee a part et ne bloque pas (ex. : pointeur de
    sprite redirige vers un autre masque identique pour liberer le sien, notes/14). Une constante
    reecrite qui pointe encore dans la zone reste bloquante."""
    zones = cave_zones(main_os, chosen)
    if not zones:
        return
    for lo, hi in zones:
        print(f"  zone 0xFF utilisee : 0x{lo + BASE:08x}..0x{hi + BASE - 1:08x} ({hi - lo} o)")
    sure, doubt = refs_into(main_os, zones)
    if dirty is not None:
        def rewritten(hit):
            o = hit[0] - BASE
            if not any(dirty[o:o + 4]):
                return False
            if patched is not None and hit[2].startswith("constante"):
                v = int.from_bytes(patched[o:o + 4], "big")
                if any(lo + BASE <= v < hi + BASE for lo, hi in zones):
                    return False                    # toujours une reference vers la zone
            return True
        gone = [h for h in sure + doubt if rewritten(h)]
        sure = [h for h in sure if not rewritten(h)]
        doubt = [h for h in doubt if not rewritten(h)]
        for va, t, kind in gone:
            print(f"  reference reecrite par un tweak (neutralisee) : 0x{va:08x} -> 0x{t:08x} ({kind})")
    starts = {lo + BASE for lo, _ in zones}

    def show(hits):
        for va, t, kind in hits:
            z = max(s for s in starts if s <= t)
            note = " (1er octet de la zone : peut aussi etre la fin de l'objet precedent)" if t == z else ""
            print(f"     0x{va:08x} : {kind} -> 0x{t:08x} (zone +0x{t - z:x}){note}")

    if doubt:
        print("  a verifier au desassembleur (peut-etre des donnees qui ressemblent a du code) :")
        show(doubt)
    if not sure:
        print("  references (constantes 32 bits) vers ces zones dans l'image d'origine : aucune")
        return
    print("!! l'image d'origine pointe dans une zone 0xFF ou un tweak veut ecrire :")
    show(sure)
    if not force:
        raise SystemExit("   Cette zone n'est peut-etre pas libre : refus d'ecrire.\n"
                         "   Verifie ces references a la main, puis relance avec --force-cave si elles sont sans danger.")
    print("   --force-cave : on continue quand meme.")


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
    ap.add_argument("--force-cave", action="store_true",
                    help="ecrit meme si l'image d'origine pointe dans une zone 0xFF utilisee (a verifier a la main)")
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
    check_conflicts(chosen)
    for t in chosen:
        print(f"  + {t['name']}")

    patched, dirty = apply_writes(main_os, chosen)
    check_caves(main_os, chosen, args.force_cave, dirty, patched)
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
