#!/usr/bin/env python3
"""Génère 44-chord-keys.json : accords diatoniques sur TRIG 1–16 (notes/40).

Compile les sources ColdFire, les répartit dans des masques de sprites identiques
redirigés vers leur exemplaire conservé, puis vérifie chaque écriture sur l'OS
officiel. Aucun code Elektron n'est incorporé hors des octets attendus des
écritures. Aucun firmware n'est exporté par ce générateur.

    python3 tools/gen_chord_keys.py --cycles firmware/model-cycles_OS1.13.syx [--check]
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile

import build
import sprites
from mtlib import aplib, container
from mtlib.syx import unwrap

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = HERE / "machines/chord_keys"
OUT = ROOT / "tweaks/model-cycles_OS1.13/44-chord-keys.json"
BASE = 0x40000400
# L'ABI Linux attend les retours de pointeur dans a0, l'OS dans d0.
# Ne jamais choisir silencieusement un compilateur Linux pour ces appels C.
CROSS = os.environ.get("M68K_CROSS") or "m68k-elf-"
CFLAGS = ["-mcpu=54418", "-Os", "-ffreestanding", "-fno-builtin", "-nostdlib", "-fno-pic", "-fno-common",
          "-ffunction-sections", "-fdata-sections", "-fomit-frame-pointer", "-fno-stack-protector",
          "-Wall", "-Wextra", "-Werror"]
MASKS = (0x4016b6f8, 0x4016b9e8, 0x40171f30, 0x40172608, 0x40179730,
         0x40182b38, 0x40182e28, 0x40183118, 0x40185018, 0x40185968,
         0x40185c58, 0x4018cd48, 0x4018d1b8, 0x4018d4a8, 0x4018dba8,
         0x4018f4b4, 0x4018fc74, 0x401904b4, 0x40192734)
EXTRA_MASKS = (0x40158744, 0x4016aa28, 0x401699a8, 0x401696a0, 0x40166760,
               0x4016616c, 0x40163fb8, 0x401625bc, 0x40160e6c, 0x40160b6c,
               0x40160864, 0x401601fc, 0x4015f50c, 0x4014d74c,
               0x4015b8f8, 0x401548b4, 0x401542f8, 0x40192ba4,
               0x4018ff64, 0x4018b1a8, 0x4018af88, 0x40189618,
               0x40186238, 0x40185308, 0x401835b8)
MASKS += EXTRA_MASKS
# Adresse, contrat attendu, symbole, opcode (None = pointeur de vtable).
HOOKS = (
    (0x400075f0, "4eb940076be4", "ck_chord_display_dirty", 0x4eb9),
    (0x4008e622, "4fefffd848d71c7c", "ck_chord_display_hook", 0x4ef9),
    (0x4007746c, "4fefffc048d70c04", "ck_ui_pad_dispatch_hook", 0x4ef9),
    (0x400aae88, "4fefffe448d71c3c", "chord_audio_update", 0x4ef9),
    (0x400ab0e4, "d1fc4012142c", "chord_audio_ratios", 0x4ef9),
    (0x4001a0d2, "4fefffd448d77cfc", "ck_ui_key", 0x4ef9),
    (0x40081734, "2e2e001c2c2e0020", "ck_tg_note_on_hook", 0x4ef9),
    (0x4008146c, "262e000c2a2e0010", "ck_tg_note_off_hook", 0x4ef9),
    (0x4010025c, "4001d180", "ck_ui_pad", None),
    (0x401002b0, "4001d3d4", "ck_ui_pad_thunk", None),
    (0x400fd170, "4000a70e", "ck_shape_format", None),
    (0x400fd174, "4000a66a", "ck_shape_draw", None),
    (0x4001e4ca, "4eb94000b22a", "ck_shape_name", 0x4eb9),
    (0x4001cb3e, "4eb94002d138", "ck_ui_menu_ctor", 0x4eb9),
    (0x4005b4a8, "7001156b001c001c", "ck_storage_load_hook", 0x4ef9),
    (0x40061564, "1140001b48780010", "ck_storage_init_hook", 0x4ef9),
    (0x4005b9c6, "16b5480317420001", "ck_plock_save_hook", 0x4ef9),
    (0x4005bad2, "28713c0070ff", "ck_plock_partial_hook", 0x4ef9),
    (0x4005aa1a, "2f027406222f0008", "ck_plock_decode_hook", 0x4ef9),
    (0x40012274, "4eb9400cfd0e", "ck_plock_note_hook", 0x4ef9),
    (0x40058ec6, "222a0028028100000081", "ck_plock_sequence_hook", 0x4ef9),
    (0x40019ee2, "4e922f004eb94000f208", "ck_midi_key_on_hook", 0x4ef9),
    (0x40019cba, "2f044eb940016e90", "ck_midi_key_off_hook", 0x4ef9),
    (0x4001d094, "45f9400cf866", "ck_midi_pad_on_hook", 0x4ef9),
    (0x4001d120, "45f9400cf866", "ck_midi_pad_off_hook", 0x4ef9),
    (0x4005919e, "42b940a78e18", "ck_midi_sequence_hook", 0x4ef9),
)
# Le chargeur stock ignore les identifiants >32 : HARMONY utilise 33 pour
# qu'un retour au firmware officiel ignore ce lock au lieu de modifier LEVEL.
PATCHES = (
    (0x4005b816, "7a20", "7a21"),
    # Diffère le message MIDI jusqu'après les P-locks ; reprise native exacte.
    (0x40058fac, "4a2a00146738", "4ef940058fea"),
)


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def load_stock(path):
    device = json.loads((OUT.parent / "device.json").read_text())
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != device["stock_syx_sha256"]:
        raise ValueError("Le .syx n'est pas l'OS officiel 1.13 attendu")
    stream, _ = unwrap(raw)
    parsed = container.parse(stream)
    section = next(s for s in parsed["sections"] if s["id"] == 3)
    stock = aplib.depack(parsed["blob"][section["off"]:section["off"] + section["size"]])[0]
    if len(stock) != device["section_len"] or build.sha(stock) != device["section_sha256"]:
        raise ValueError("Le MAIN OS n'est pas l'image officielle attendue")
    return stock


def sections(path):
    found = []
    for line in run([CROSS + "objdump", "-h", str(path)]).splitlines():
        match = re.match(r"\s*\d+\s+(\.\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+\S+\s+\S+\s+2\*\*(\d+)", line)
        if match:
            name, size, address, align = match.groups()
            if int(size, 16):
                found.append((name, int(size, 16), int(address, 16), 1 << int(align)))
    return found


def compile_code():
    """Placement déterministe par section, sans casser une fonction entre deux masques."""
    target = run([CROSS + "gcc", "-dumpmachine"]).strip()
    if target != "m68k-elf":
        raise ValueError(
            f"Chord Keys exige la cible m68k-elf (trouvé {target}) : "
            "l'OS renvoie les pointeurs dans d0, voir notes/40 et M68K_CROSS")
    version = run([CROSS + "gcc", "-dumpfullversion"]).strip()
    if version != "16.2.0":
        raise ValueError(
            f"Chord Keys exige m68k-elf-gcc 16.2.0 (trouvé {target} {version}) : "
            "ABI de retour des pointeurs dans d0 et génération reproductible, voir notes/40")
    with tempfile.TemporaryDirectory(prefix="chord-keys-build-") as directory:
        tmp = Path(directory)
        objects, inputs = [], []
        for source in sorted((*SRC.glob("*.c"), *SRC.glob("*.S"))):
            obj = tmp / (source.name + ".o")
            run([CROSS + "gcc", *CFLAGS, "-c", str(source), "-o", str(obj)])
            objects.append(obj)
            for name, size, _, align in sections(obj):
                if name.startswith((".text", ".rodata", ".data", ".bss")):
                    # Le ColdFire exige une adresse paire à chaque entrée. Les tables
                    # locales prennent aussi le type T dans le masque mixte final ;
                    # les aligner évite de confondre leurs symboles avec du code impair.
                    align = max(align, 2)
                    inputs.append((obj, name, size, align))
        bins = [{"at": va, "size": 0, "capacity": sprites.MASKS[va][0], "parts": []}
                for va in MASKS]
        for obj, name, size, align in sorted(inputs, key=lambda s: (-s[2], s[0].name, s[1])):
            for block in bins:
                offset = (block["size"] + align - 1) & -align
                if offset + size <= block["capacity"]:
                    block["parts"].append((obj, name, align))
                    block["size"] = offset + size
                    break
            else:
                raise ValueError(f"Section {obj.name}:{name} ({size} o) trop grande ou place épuisée")
        bins = [block for block in bins if block["parts"]]
        script = ["SECTIONS {"]
        for i, block in enumerate(bins):
            script.append(f"  .ck{i} {block['at']:#x} : {{")
            script.extend(f'    . = ALIGN({align}); "{obj}"({name})' for obj, name, align in block["parts"])
            script.append("  }")
        script.extend(("  /DISCARD/ : { *(.text) *(.data) *(.bss) *(.comment) *(.note*) *(.eh_frame*) }", "}"))
        linker = tmp / "chord_keys.ld"
        linker.write_text("\n".join(script) + "\n")
        elf = tmp / "chord_keys.elf"
        run([CROSS + "ld", "--no-warn-rwx-segments", "--orphan-handling=error", "-T", str(linker),
             "-o", str(elf), *map(str, objects)])
        symbols = {}
        for line in run([CROSS + "nm", str(elf)]).splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[1].upper() in ("T", "D", "B", "R"):
                if fields[1].upper() == "T" and int(fields[0], 16) & 1:
                    raise ValueError(f"Symbole de code non aligné : {fields[2]}")
                symbols[fields[2]] = int(fields[0], 16)
        result = []
        for name, size, address, _ in sections(elf):
            if not name.startswith(".ck"):
                raise ValueError(f"Section imprévue : {name}")
            if address not in MASKS or size > sprites.MASKS[address][0]:
                raise ValueError(f"Section hors masque : {name}, {address:#x}, {size} o")
            binary = tmp / (name + ".bin")
            run([CROSS + "objcopy", "-O", "binary", "-j", name, str(elf), str(binary)])
            # Une section contenant uniquement du BSS doit aussi être initialisée.
            code = binary.read_bytes()
            if len(code) > size:
                raise ValueError("Taille extraite incohérente")
            result.append((address, code.ljust(size, b"\0")))
        return sorted(result), symbols


def build_tweak(stock):
    compiled, symbols = compile_code()
    writes = []
    for address, code in compiled:
        capacity, pointer, _, shared = sprites.MASKS[address]
        old = stock[address - BASE:address - BASE + capacity]
        if old != stock[shared - BASE:shared - BASE + capacity]:
            raise ValueError(f"Masque {address:#x} différent de l'exemplaire conservé")
        encoded = struct.pack(">I", address)
        locations = [m.start() for m in re.finditer(re.escape(encoded), stock)]
        if locations != [pointer - BASE]:
            raise ValueError(f"Références imprévues vers le masque {address:#x}")
        at = pointer - BASE
        width, height = {376: (47, 47), 280: (35, 35), 384: (33, 48), 272: (34, 34)}[capacity]
        dimensions = struct.pack(">HHHH", 0x4878, width, 0x4878, height)
        if (stock[at - 2:at] not in (b"\x48\x79", b"\x2e\xbc") or
                stock[at + 4:at + 6] != b"\x48\x79" or
                stock[at + 10:at + 18] != dimensions):
            raise ValueError(f"Le constructeur du sprite {address:#x} a changé")
        if address in EXTRA_MASKS:
            sure, branches = build.refs_into(stock, [(address - BASE, address - BASE + capacity)])
            if sure != [(pointer, address, "constante 32 bits")] or branches:
                raise ValueError(f"Entrée imprévue dans la nouvelle cave {address:#x}")
        writes.extend(({"off": address - BASE, "old": old[:len(code)].hex(), "new": code.hex()},
                       sprites.redirect_write(address)))
    for address, expected, symbol, opcode in HOOKS:
        old = bytes.fromhex(expected)
        if stock[address - BASE:address - BASE + len(old)] != old:
            raise ValueError(f"Contrat d'accroche inattendu à {address:#x}")
        new = struct.pack(">I", symbols[symbol]) if opcode is None else struct.pack(">HI", opcode, symbols[symbol])
        new += b"\x4e\x71" * ((len(old) - len(new)) // 2)
        writes.append({"off": address - BASE, "old": old.hex(), "new": new.hex()})
    for address, expected, replacement in PATCHES:
        old = stock[address - BASE:address - BASE + len(bytes.fromhex(expected))]
        if old.hex() != expected:
            raise ValueError(f"Instruction stock inattendue à {address:#x}")
        writes.append({"off": address - BASE, "old": old.hex(), "new": replacement})
    tweak = {
        "id": "chord-keys", "order": 44, "name": "Accords de gamme sur TRIG 1–16",
        "description": [
            "Mode Keys dans FUNC + RETRIG : une piste CHORD, gamme et tonique, extensions par degré.",
            "TRIG 1–7 jouent I–VII, 8–14 les mêmes degrés une octave plus haut, 15–16 I–II deux octaves plus haut.",
            "COLOR choisit DIATONIC, JAZZ ou TENSION ; SHAPE dispose et équilibre les voix, sans ancien mode.",
            "Keys actif : T1–T6 transforment temporairement l'accord en HARMONY sans changer de piste.",
            "T1/T2/T3 : 9/11/13 ; T4 : 7sus4 ; T5 : parallèle majeur/mineur ; T6 : dominante V7 de la cible.",
            "TRIG tenu : chaque nouvel appui de pad disponible rejoue l'accord entier à sa vélocité, sans répétition de maintien.",
            "Dernier pad prioritaire ; le relâchement conserve l'accord modifié. Sans préparation, le prochain TRIG retrouve son extension.",
            "Sept modes et quatre voix au plus : 9/11/13 omettent la quinte et les tensions intermédiaires.",
            "Exception m7♭5 étendu : fondamentale, quinte diminuée, septième, tension ; sans tierce. T5/T6 indisponibles.",
            "SHAPE : BASE, CLS0–3, OPN0–3. Les options Controls et Pads sont supprimées.",
            "Anciens et nouveaux patterns utilisent les mêmes contrôles ; gamme et extensions sauvegardées conservées.",
            "L'écran nomme l'accord tenu selon les intervalles audio, les transformations et la basse du voicing.",
            "Les gestes HARMONY s'enregistrent en P-locks natifs : live rec ou pas tenus en grille, puis sauvegarde du pattern.",
            "Chaque attaque reçoit son lock sur le pas choisi par le recorder ; la relecture retrouve chaque accord sans garder le dernier pad.",
            "Sans TRIG tenu, T prépare le prochain TRIG sans toucher la queue ni écrire de lock ; relâcher T annule la préparation.",
            "Un pad T1–T6 encore tenu s'applique à chaque nouveau TRIG de cette piste, jusqu'à son relâchement.",
            "MIDI ROOT conserve la sortie d'origine ; MIDI CHORD émet les trois ou quatre notes disposées, en jeu et au séquenceur.",
            "La sortie CHORD respecte MOut, le canal et la destination natifs ; chaque voix garde sa vélocité et sa fin de note.",
            "Palette, SHAPE et HARMONY sont capturés à l'attaque ; PITCH/FINE et balance restent audio. Notes MIDI au-delà de 127 omises.",
            "Réglages par piste sauvegardés avec le pattern. Dernière touche prioritaire, sans retour à la précédente.",
            "Compatible avec les autres mods, dont Model-TG : Keys garde sa gamme sur CHORD ; Scale Lock reste actif ailleurs.",
            "HARMONY utilise un slot distinct d'Attack, Filter et Resonance. Aucun essai matériel de cette révision.",
            f"Code et état dans {len(compiled)} masques de sprites redirigés, {sum(len(c) for _, c in compiled)} octets.",
            "Généré par tools/gen_chord_keys.py ; sources tools/machines/chord_keys/ ; notes/40.",
        ],
        "device": "Model:Cycles", "os": "1.13", "section": 3,
        "conflicts": [],
        "symbols": {name: f"{value:#x}" for name, value in sorted(symbols.items())},
        "writes": sorted(writes, key=lambda w: w["off"]),
    }
    build.apply_writes(stock, [tweak])
    for path in OUT.parent.glob("*.json"):
        other = json.loads(path.read_text())
        if other.get("id") in (tweak["id"], *tweak["conflicts"]):
            continue
        for a in tweak["writes"]:
            for b in other.get("writes", []):
                lo, hi = max(a["off"], b["off"]), min(a["off"] + len(a["new"]) // 2, b["off"] + len(b["new"]) // 2)
                if lo < hi and bytes.fromhex(a["new"])[lo-a["off"]:hi-a["off"]] != bytes.fromhex(b["new"])[lo-b["off"]:hi-b["off"]]:
                    raise ValueError(f"Chevauchement avec {other['id']} à {BASE + lo:#x}")
    return tweak


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        tweak = build_tweak(load_stock(args.cycles))
        text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
        if args.check:
            if not OUT.exists() or OUT.read_text() != text:
                raise ValueError("Le JSON ne correspond pas aux sources / à cette version du compilateur")
            print("ok 44-chord-keys.json est à jour")
        else:
            OUT.write_text(text)
            print(f"ok {OUT.name} : {len(tweak['writes'])} écritures vérifiées")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"FAIL {error}\n{getattr(error, 'stderr', '')}") from error


if __name__ == "__main__":
    main()
