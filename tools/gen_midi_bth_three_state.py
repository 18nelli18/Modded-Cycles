#!/usr/bin/env python3
"""Expérimente un vrai sélecteur OUT/THR/BTH sur le Model:Cycles OS 1.13.

Le tweak reste local et expérimental : il n'est pas inscrit dans le flasher.
Il doit être appliqué seul, sans `midi-both` (le mode de secours THR=BTH).
"""
import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DEV = ROOT / "tweaks" / "model-cycles_OS1.13"
BASE = 0x40000400
HELPER = 0x40167C50


def stock_mainos(path):
    sys.path.insert(0, str(HERE))
    from mtlib.syx import unwrap
    from mtlib import aplib, container

    raw = pathlib.Path(path).read_bytes()
    stream, _ = unwrap(raw)
    c = container.parse(stream)
    s = next(s for s in c["sections"] if s["id"] == 3)
    main, _ = aplib.depack(c["blob"][s["off"]:s["off"] + s["size"]])
    device = json.loads((DEV / "device.json").read_text(encoding="utf-8"))
    if hashlib.sha256(raw).hexdigest() != device["stock_syx_sha256"]:
        raise SystemExit("!! ce n'est pas le fichier Model:Cycles OS 1.13 officiel attendu")
    if hashlib.sha256(main).hexdigest() != device["section_sha256"]:
        raise SystemExit("!! la section 3 ne correspond pas à l'OS 1.13 de référence")
    return main


def helper_code():
    """Cycle 0→1→2→0, affiche le libellé et bloque les sorties générées seulement en THR."""
    toggle = bytes.fromhex(
        "4eb940044df8"          # jsr getter brut (clé 0x50)
        "5280"                  # addq.l #1,d0
        "0c8000000003"          # cmpi.l #3,d0
        "6602"                  # bne.s après clr
        "4280"                  # clr.l d0 quand l'ancienne valeur était 2
        "2f400004"              # move.l d0,4(sp), argument du setter
        "4ef940044dc2"          # jmp setter brut (clé 0x50)
    )
    display = bytes.fromhex(
        "4eb940044df8"          # jsr getter brut
        "0c8000000002"          # cmpi.l #2,d0
        "6714"                  # beq BTH
        "4a80"                  # tst.l d0
        "6708"                  # beq OUT
        "263c40127281"          # move.l #THR,d3
        "4e75"                  # rts
        "263c40127bad"          # move.l #OUT,d3
        "4e75"                  # rts
        "263c40167c96"          # move.l #HELPER+70,d3 (BTH string)
        "4e75"                  # rts
        "42544800"              # "BTH\0"
    )
    output_gate = bytes.fromhex(
        "4eb940044df8"          # jsr getter brut
        "0c8000000001"          # cmpi.l #1,d0 (THR seulement)
        "57c0"                  # seq.b d0: nonzero seulement pour THR
        "4e75"                  # rts
    )
    return toggle + display + output_gate


def generate(main):
    import build
    import sprites

    all_helpers = helper_code()
    toggle, display, output_gate = all_helpers[:28], all_helpers[28:74], all_helpers[74:]
    tweak = {
        "id": "midi-bth-three-state", "order": 45,
        "name": "MIDI OUT / THRU / BTH",
        "description": [
            "Ajoute BTH comme troisième valeur : OUT envoie, THR relaie, BTH fait les deux. Expérimental, non proposé dans le flasher ;",
            "test sur machine requis. Généré par tools/gen_midi_bth_three_state.py (note 50).",
        ],
        "device": "Model:Cycles", "os": "1.13", "section": 3,
        "conflicts": ["midi-both"], "writes": [],
    }

    def add(va, old, new, label):
        off = va - BASE
        if main[off:off + len(old)] != old:
            raise SystemExit(f"!! octets inattendus pour {label} à {va:#x}")
        tweak["writes"].append({"off": off, "old": old.hex(), "new": new.hex()})

    # The input callback is a hard-coded boolean inversion. Redirect it to a
    # byte-valued cycle while keeping the stock one-byte setting setter.
    add(0x4003560A, bytes.fromhex("4eb940044df84a8057c0710044802f4000044ef940044dc2"),
        b"\x4e\xf9" + HELPER.to_bytes(4, "big") + b"\x4e\x71" * 9,
        "callback de changement OUT/THRU")

    # The display callback chooses its label from the raw stored byte.
    display_site = 0x40035FD8
    old_display = bytes.fromhex("4eb940044df84a806708263c401272816006263c40127bad")
    new_display = b"\x4e\xb9" + (HELPER + len(toggle)).to_bytes(4, "big") + b"\x4e\x71" * 9
    add(display_site, old_display, new_display, "affichage du réglage")

    # Stock gates block generated MIDI for every nonzero value. Replace their
    # boolean check with an exact THR==1 check; BTH==2 must still transmit.
    for va in (0x4000154A, 0x4000156A, 0x40001590):
        add(va, bytes.fromhex("4eb940044df8"),
            b"\x4e\xb9" + (HELPER + 74).to_bytes(4, "big"),
            f"porte de sortie {va:#x}")

    # The sprite's identical mask is redirected before its 280 bytes are used
    # for executable helper code. This is the same sanctioned code-cave scheme
    # used by the earlier BTH experiment.
    tweak["writes"].append(sprites.redirect_write(HELPER))
    add(HELPER, main[HELPER - BASE:HELPER - BASE + len(all_helpers)], all_helpers,
        "helpers du cycle et du libellé")
    build.apply_writes(main, [tweak])
    return tweak


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    content = json.dumps(generate(stock_mainos(args.cycles)), indent=1, ensure_ascii=False) + "\n"
    out = DEV / "45-midi-bth-three-state.json"
    if args.check:
        ok = out.exists() and out.read_text(encoding="utf-8") == content
        print(f"{out.name}: {'à jour' if ok else 'NE CORRESPOND PAS'}")
        raise SystemExit(0 if ok else 1)
    out.write_text(content, encoding="utf-8")
    print(f"écrit : {out}")


if __name__ == "__main__":
    main()
