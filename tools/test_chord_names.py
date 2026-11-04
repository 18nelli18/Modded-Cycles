#!/usr/bin/env python3
"""Vérifie les noms contre les notes des 5 145 harmonies et neuf dispositions.

Les symboles affichés sont relus par un petit interprète musical indépendant :
son ensemble de notes, après les omissions, doit être celui du moteur. Ce test
hôte ne prouve pas l'écran ; emu/chord_display_checks.py exécute son vrai code.

    python3 tools/test_chord_names.py
"""
import ctypes as ct
import itertools
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

from test_chord_harmony import U4, intervals, setup
from test_chord_keys import require


NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def pitch(text):
    return (NOTES[text[0]] + int(text.endswith("#"))) % 12


def packet(note, notes, bass):
    return 0x80000000 | note | (bass % 12) << 27 | sum(n << (7 + 5 * i) for i, n in enumerate(notes))


def name(library, snapshot):
    outputs = [ct.create_string_buffer(b"\xa5" * 32) for _ in range(2)]
    library.ck_chord_name(snapshot, *outputs)
    require(all(bytes(out)[24:32] == b"\xa5" * 8 for out in outputs), "Sortie hors des 24 octets")
    return tuple(out.value.decode("ascii") for out in outputs)


def read_symbol(text, omissions):
    match = re.fullmatch(r"([A-G]#?)([^/]*)(?:/([A-G]#?))?", text)
    require(match is not None, f"Symbole illisible : {text}")
    root_text, quality, bass_text = match.groups()
    root = pitch(root_text)
    if quality == "dim":
        degrees = {1: 0, 3: 3, 5: 6}
    elif quality == "7sus4":
        degrees = {1: 0, 4: 5, 5: 7, 7: 10}
    else:
        extension = re.fullmatch(r"(maj|m)?(7|9|11|13)?(b5)?(?:\((b9|#11|b13)\))?", quality)
        require(extension is not None, f"Qualité inconnue : {quality}")
        family, level, flat_fifth, altered = extension.groups()
        degrees = {1: 0, 3: 3 if family == "m" else 4, 5: 6 if flat_fifth else 7}
        if level:
            degrees[7] = 11 if family == "maj" else 10
            for degree, interval in ((9, 14), (11, 17), (13, 21)):
                if int(level) >= degree:
                    degrees[degree] = interval
        if altered:
            degree, interval = {"b9": (9, 13), "#11": (11, 18), "b13": (13, 20)}[altered]
            degrees[degree] = interval
    if omissions:
        require(omissions.startswith("no"), f"Omission illisible : {omissions}")
        for degree in map(int, omissions[2:].split(",")):
            require(degree in degrees, f"Omission absente de l'accord : {text} {omissions}")
            del degrees[degree]
    return {(root + n) % 12 for n in degrees.values()}, pitch(bass_text) if bass_text else root


def run(library):
    library.ck_chord_name.argtypes = [ct.c_uint, ct.c_void_p, ct.c_void_p]
    library.ck_chord_name.restype = None
    examples = [
        (48, [0, 4, 7, 11], 0, ("Cmaj7", "")),
        (52, [0, 3, 10, 14], 0, ("Em9", "no5")),
        (52, [0, 3, 10, 13], 0, ("Em7(b9)", "no5")),
        (55, [0, 4, 10, 13], 0, ("G7(b9)", "no5")),
        (53, [0, 4, 11, 18], 0, ("Fmaj7(#11)", "no5")),
        (57, [0, 3, 10, 20], 0, ("Am7(b13)", "no5")),
        (59, [0, 6, 10, 14], 0, ("Bm9b5", "no3")),
        (48, [0, 5, 7, 10], 0, ("C7sus4", "")),
        (48, [7, 11, 14, 17], 7, ("G7", "")),
        (48, [7, 11, 14, 17], 2, ("G7/D", "")),
    ]
    for note, notes, bass, expected in examples:
        require(name(library, packet(note, notes, bass)) == expected, f"Exemple {expected}")
    require(name(library, 0) == ("", ""), "Instantané inactif affiché")
    print("ok exemples Cmaj7, Em9, altérations, m7b5 sans tierce, sus et dominante/inversion")
    for note, notes, bass, expected in (
            (72, [0, 4, 7, 11], 11, "Cmaj7/B"),
            (74, [0, 3, 7, 10], 10, "Dm7/C"),
            (48, [0, 3, 10, 14], 0, "Cm9"),
            (48, [7, 11, 14, 17], 7, "G7")):
        require(name(library, packet(note, notes, bass) | 0x400) == (expected, "HIGH LIMIT"),
                f"Protection aiguë sans fausse note ni nom de dominante modifié : {expected}")
    print("ok HIGH LIMIT : fondamentale et V7 préservés, avertissement remplace les omissions")
    count_cases, longest = 0, (0, "")
    for mode, degree, extension, palette, transform in itertools.product(
            range(7), range(7), range(5), range(3), range(7)):
        count, notes = intervals(library, mode, degree, extension, palette, transform)
        if not count:
            count, notes = intervals(library, mode, degree, extension, palette, 0)
        for shape in range(9):
            shaped = U4(*notes)
            library.ck_voicing_apply(shaped, count, shape)
            for root in (48, 49):
                displayed, omissions = name(library, packet(root, notes[:count], shaped[0]))
                actual_notes, bass = read_symbol(displayed, omissions)
                expected_notes = {(root + n) % 12 for n in shaped[:count]}
                context = (mode, degree, extension, palette, transform, shape, root)
                require(actual_notes == expected_notes and bass == (root + shaped[0]) % 12,
                        f"Nom différent des voix : {context} {displayed} {omissions}")
                require(len(displayed) * 8 - 1 <= 128 and len(omissions) * 6 - 1 <= 128,
                        f"Texte trop large : {displayed} {omissions}")
                longest = max(longest, (len(displayed), displayed))
                count_cases += 1
    require(count_cases == 92610, "Balayage incomplet")
    print(f"ok {count_cases:,} noms relus = notes et basse réellement disposées ; largeur maximale {longest[0] * 8 - 1} px")


def main():
    source = Path(__file__).resolve().parent / "machines/chord_keys"
    with tempfile.TemporaryDirectory(prefix="chord-names-") as directory:
        output = Path(directory) / "names.so"
        command = shlex.split(os.environ.get("CC", "cc")) + [
            "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror", "-pedantic", "-fPIC",
            "-dynamiclib" if sys.platform == "darwin" else "-shared",
            *(str(source / name) for name in ("chord_keys.c", "chord_voicing.c", "chord_name.c")),
            "-o", str(output)]
        subprocess.run(command, check=True)
        library = ct.CDLL(str(output))
        setup(library)
        run(library)


if __name__ == "__main__":
    main()
