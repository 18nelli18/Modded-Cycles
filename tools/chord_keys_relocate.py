#!/usr/bin/env python3
"""Reloge le code MIT précompilé ChordKeys PR87 sans compilateur C.

Les octets proviennent uniquement des écritures propres de la recette MIT
18nelli18/Modded-Cycles PR87, 770369210cab889fd8642184632d7b9853afd33e.
Les symboles donnent les frontières ; les branches relatives et les chutes
entre frontières interdisent de séparer une même fonction. Toute référence
propre non classée ou adressage PC relatif ambigu provoque un refus.

Ce module ne copie pas les octets « old » du firmware et ne change aucun
hook natif ; le générateur appelant reconstruit ces hooks avec les symboles.
"""
import bisect
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

BASE = 0x40000400
PIN = "770369210cab889fd8642184632d7b9853afd33e"
OWN_DIGEST = "89869577cfe9ea5c645c78f40d8fe890aed137c31c6d52be86fd136a5d5fb714"
# Objets non exécutables identifiés dans les sources MIT de la même révision.
# Les suffixes .0/.1 sont ceux de GCC16.2 ; CSWTCH est sa table de switch.
DATA_SYMBOLS = frozenset((
    "CSWTCH.16", "ck_chord_live", "degrees", "displayed_chord", "expanded",
    "extensions", "families.1", "gains.0", "held", "held_pads", "labels",
    "labels.0", "last_audio_header", "live", "live_modifiers", "modes", "invoke.0",
    "note_names", "notes", "palettes.1", "positions", "prepared_modifiers",
    "scales", "semitone_ratios", "sequenced", "voicings",
))
LINE = re.compile(r"\s*([0-9a-f]+):\t([0-9a-f ]+)\t(\S+)\s*(.*)$")
NUMBER = re.compile(r"0x[0-9a-f]+|#-?\d+")


def _int(value):
    return int(value, 0) if isinstance(value, str) else value


def _objdump():
    requested = os.environ.get("M68K_OBJDUMP")
    candidates = [requested] if requested else []
    candidates += ["m68k-elf-objdump", "m68k-linux-gnu-objdump",
                   str(Path(__file__).resolve().parents[2] / "toolchain/bin/m68k-elf-objdump")]
    for candidate in candidates:
        if candidate and (shutil.which(candidate) or Path(candidate).is_file()):
            return candidate
    raise ValueError("objdump ColdFire introuvable")


def _disassemble(data, address, starts):
    """Décodage séparé à chaque symbole : les tables ne décalent pas le code."""
    result = {}
    with tempfile.TemporaryDirectory(prefix="ck-reloc-") as directory:
        file = Path(directory) / "own-code.bin"
        file.write_bytes(data)
        stops = starts[1:] + [address + len(data)]
        for start, stop in zip(starts, stops):
            command = [_objdump(), "-D", "-z", "-b", "binary", "-m", "m68k:isa-c:emac",
                       f"--adjust-vma={address:#x}", f"--start-address={start:#x}",
                       f"--stop-address={stop:#x}", str(file)]
            out = subprocess.run(command, check=True, text=True, capture_output=True).stdout
            for line in out.splitlines():
                match = LINE.match(line)
                if not match:
                    continue
                at, words, mnemonic, operands = match.groups()
                raw = bytes.fromhex(words)
                at = int(at, 16)
                if data[at-address:at-address+len(raw)] != raw:
                    raise ValueError(f"Désassemblage incohérent en {at:#x}")
                result[at] = (len(raw), mnemonic, operands.strip(), raw)
    return result


def relocate(recipe, layout):
    """Retourne ([(adresse, octets)], symboles relogés, audit JSON).

    layout : [{at, capacity, kind}], adresses hex ou entières. Les clusters
    sont les écritures contenant les symboles de la recette ; les hooks et
    redirections sprite de quatre octets ne sont jamais ingérés comme code.
    """
    symbols = {name: _int(value) for name, value in recipe["symbols"].items()}
    if len(symbols) != 146 or not DATA_SYMBOLS <= symbols.keys():
        raise ValueError("Table de symboles différente de ChordKeys PR87 épinglé")
    clusters = []
    for write in recipe["writes"]:
        at = BASE + write["off"]
        data = bytes.fromhex(write["new"])
        own_symbols = sorted(set(v for v in symbols.values() if at <= v < at + len(data)))
        if own_symbols:
            if len(data) <= 4 or at < 0x40140000:
                raise ValueError("Un symbole pointe un hook ou une écriture native")
            clusters.append({"at": at, "data": data, "symbols": own_symbols})
    clusters.sort(key=lambda c: c["at"])
    if len(clusters) != 58 or sum(len(c["data"]) for c in clusters) != 13335:
        raise ValueError("Clusters différents du précompilé PR87 (58 / 13335 attendus)")
    own_fingerprint = {"symbols": symbols,
                       "clusters": [(c["at"], c["data"].hex()) for c in clusters]}
    own_digest = hashlib.sha256(json.dumps(own_fingerprint, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if own_digest != OWN_DIGEST:
        raise ValueError("Code/symboles différents du précompilé MIT PR87 épinglé")
    ranges = [(c["at"], c["at"] + len(c["data"])) for c in clusters]
    def owned(address):
        return any(lo <= address < hi for lo, hi in ranges)
    if any(not owned(v) for v in symbols.values()):
        raise ValueError("Symbole hors des clusters propres")

    pieces, instructions, cluster_of = [], {}, {}
    function_roots = set(v for name, v in symbols.items() if name not in DATA_SYMBOLS)
    for index, cluster in enumerate(clusters):
        lo, data = cluster["at"], cluster["data"]
        boundaries = sorted({lo, lo + len(data), *cluster["symbols"]})
        for begin, end in zip(boundaries, boundaries[1:]):
            pieces.append({"old": begin, "end": end, "size": end-begin, "cluster": index})
        decoded = _disassemble(data, lo, boundaries[:-1])
        instructions.update(decoded)
        for at in decoded:
            cluster_of[at] = index
    starts = [p["old"] for p in pieces]
    def piece_at(address):
        index = bisect.bisect_right(starts, address) - 1
        if index < 0 or not pieces[index]["old"] <= address < pieces[index]["end"]:
            raise ValueError(f"Adresse propre non couverte {address:#x}")
        return index
    parent = list(range(len(pieces)))
    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    def connect(a, b):
        """Une différence relative exige un intervalle contigu, pas deux îlots."""
        ia, ib = piece_at(a), piece_at(b)
        if pieces[ia]["cluster"] != pieces[ib]["cluster"]:
            raise ValueError(f"Branche/chute relative entre clusters : {a:#x}->{b:#x}")
        low, high = sorted((ia, ib))
        for index in range(low, high):
            parent[root(index+1)] = root(index)

    reached, edges, operand_sites = {}, [], {}
    todo = sorted(function_roots, reverse=True)
    while todo:
        at = todo.pop()
        if at in reached:
            continue
        if at not in instructions:
            raise ValueError(f"Entrée/instruction absente {at:#x}")
        size, mnemonic, operands, raw = instructions[at]
        if mnemonic.startswith(".") or "???" in operands or "%pc" in operands:
            raise ValueError(f"Instruction ambiguë/PC relatif : {at:#x}: {mnemonic} {operands}")
        reached[at] = (size, mnemonic, operands, raw)
        relative = bool(re.match(r"^(?:b(?:ra|sr|hi|ls|cc|cs|ne|eq|vc|vs|pl|mi|ge|lt|gt|le)[swl]?|db\w+)$", mnemonic))
        # Immediats longs et EA absolus : chaque occurrence est prouvée par
        # un nombre explicite de la sortie objdump, puis par ses quatre octets.
        for literal in NUMBER.findall(operands):
            if relative:
                break
            value = int(literal[1:], 10) & 0xffffffff if literal.startswith("#") else int(literal, 16)
            if not owned(value):
                continue
            encoded = struct.pack(">I", value)
            matches = [offset for offset in range(2, size-3, 2) if raw[offset:offset+4] == encoded]
            if not matches:
                raise ValueError(f"Opérande propre sans encodage long : {at:#x}, {value:#x}")
            for offset in matches:
                operand_sites[at+offset] = value
        terminal = mnemonic in ("rts", "rte", "rtr", "illegal", "stop") or mnemonic.startswith("jmp")
        if relative:
            targets = re.findall(r"0x([0-9a-f]+)", operands)
            if len(targets) != 1:
                raise ValueError(f"Destination de branche ambiguë en {at:#x}")
            target = int(targets[0], 16)
            if not owned(target):
                raise ValueError(f"Branche relative hors code propre en {at:#x}")
            connect(at, target)
            edges.append((at, target, "branch"))
            todo.append(target)
            terminal = mnemonic.startswith("bra")
        if not terminal:
            following = at + size
            if not owned(following):
                raise ValueError(f"Chute hors cluster propre en {at:#x}")
            connect(at, following)
            edges.append((at, following, "fallthrough"))
            todo.append(following)

    # Interdire toute instruction chevauchante : un faux symbole de donnée
    # déclaré code ou une cible à l'intérieur d'une instruction est un refus.
    code_bytes = {}
    for at, (size, *_rest) in reached.items():
        for byte in range(at, at+size):
            if byte in code_bytes and code_bytes[byte] != at:
                raise ValueError(f"Instructions chevauchantes en {byte:#x}")
            code_bytes[byte] = at

    data_sites = {}
    for cluster in clusters:
        at, data = cluster["at"], cluster["data"]
        for offset in range(0, len(data)-3, 2):
            value = struct.unpack_from(">I", data, offset)[0]
            if not owned(value):
                continue
            site = at + offset
            coverage = [byte in code_bytes for byte in range(site, site+4)]
            if any(coverage):
                if not all(coverage) or site not in operand_sites:
                    raise ValueError(f"Adresse propre ambiguë dans le code en {site:#x}")
                continue
            # Données seulement, mot aligné et pointeur entièrement dans une
            # seule pièce. Cela inclut les tables de chaînes sans symbole.
            if piece_at(site) != piece_at(site+3):
                raise ValueError(f"Pointeur de donnée coupé par un symbole en {site:#x}")
            data_sites[site] = value

    groups = {}
    for index, piece in enumerate(pieces):
        groups.setdefault(root(index), []).append(piece)
    units = []
    for group in groups.values():
        lo, end = group[0]["old"], group[-1]["end"]
        if sum(p["size"] for p in group) != end-lo:
            raise ValueError("Union non contiguë")
        cluster = clusters[group[0]["cluster"]]
        units.append({"old": lo, "end": end, "size": end-lo,
                      "data": cluster["data"][lo-cluster["at"]:end-cluster["at"]]})
    bins = [dict(at=_int(row["at"]), capacity=_int(row["capacity"]), parts=[], size=0)
            for row in layout]
    for row in bins:
        if row["at"] & 1 or row["capacity"] <= 0:
            raise ValueError("Réserve invalide")
    for i, first in enumerate(bins):
        if any(first["at"] < second["at"]+second["capacity"] and second["at"] < first["at"]+first["capacity"]
               for second in bins[i+1:]):
            raise ValueError("Réserves chevauchantes")
    # First-fit décroissant, comme le compilateur amont ; réserve TG en tête.
    for unit in sorted(units, key=lambda row: (-row["size"], row["old"])):
        for block in bins:
            offset = (block["size"] + 1) & ~1
            if offset + unit["size"] <= block["capacity"]:
                unit["new"] = block["at"] + offset
                block["parts"].append(unit)
                block["size"] = offset + unit["size"]
                break
        else:
            raise ValueError(f"Placement épuisé pour {unit['old']:#x} ({unit['size']} octets)")
    units.sort(key=lambda row: row["old"])
    unit_starts = [row["old"] for row in units]
    def remap(address):
        i = bisect.bisect_right(unit_starts, address)-1
        if i < 0 or not units[i]["old"] <= address < units[i]["end"]:
            raise ValueError(f"Référence hors unité : {address:#x}")
        return units[i]["new"] + address - units[i]["old"]

    sites = {**operand_sites, **data_sites}
    compiled = []
    for block in bins:
        if not block["parts"]:
            continue
        data = bytearray(block["size"])
        for unit in block["parts"]:
            start = unit["new"] - block["at"]
            data[start:start+unit["size"]] = unit["data"]
            for site, value in sites.items():
                if unit["old"] <= site < unit["end"]:
                    if site+4 > unit["end"]:
                        raise ValueError("Opérande coupé par le placement")
                    struct.pack_into(">I", data, start+site-unit["old"], remap(value))
        compiled.append((block["at"], bytes(data)))
    # Chaque branche relative doit conserver sa différence, après placement.
    for source, target, kind in edges:
        if remap(target)-remap(source) != target-source:
            raise ValueError(f"{kind} relative déplacée : {source:#x}->{target:#x}")
    audit = {"upstream_commit": PIN, "own_sha256": own_digest, "clusters": len(clusters),
             "original_bytes": 13335, "units": len(units), "code_instructions": len(reached),
             "absolute_instruction_operands": len(operand_sites), "data_pointers": len(data_sites),
             "relative_edges": len(edges), "capacity": sum(b["capacity"] for b in bins),
             "placed_bytes": sum(len(data) for _, data in compiled),
             "placements": [{key: hex(value) if key in ("old", "end", "new") else value
                             for key, value in unit.items() if key != "data"} for unit in units],
             "references": [{"site": hex(site), "target": hex(value), "new_site": hex(remap(site)),
                             "new_target": hex(remap(value)), "kind": "instruction" if site in operand_sites else "data"}
                            for site, value in sorted(sites.items())]}
    return sorted(compiled), {name: remap(value) for name, value in symbols.items()}, audit


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--audit", required=True)
    args = parser.parse_args()
    compiled, symbols, audit = relocate(json.loads(Path(args.recipe).read_text()), json.loads(Path(args.layout).read_text()))
    Path(args.audit).write_text(json.dumps(audit, indent=1)+"\n")
    print(f"ok : {audit['units']} unités, {audit['placed_bytes']}/{audit['capacity']} octets, "
          f"{audit['absolute_instruction_operands']} opérandes et {audit['data_pointers']} pointeurs relogés")
