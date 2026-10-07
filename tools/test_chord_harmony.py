#!/usr/bin/env python3
"""Vérifie palettes, gestes et balance SHAPE sur l'hôte (notes/40 §14.7–14.8).

Compilation temporaire du vrai noyau C, sans firmware. Les invariants musicaux
et la comparaison au noyau historique ne prouvent ni boutons ni audio matériel.
Exécution : python3 tools/test_chord_harmony.py
"""

import ctypes as ct
import itertools
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

from test_chord_keys import Config, Result, config, require


DIATONIC, JAZZ, TENSION = range(3)
NONE, NINTH, ELEVENTH, THIRTEENTH, SUS7, PARALLEL, V7 = range(7)
TRIAD, SEVENTH, EXT9, EXT11, EXT13 = range(5)
U4 = ct.c_uint * 4
POISON = 0xA5A5A5A5


def setup(library):
    library.ck_harmony_intervals.argtypes = [ct.c_uint] * 5 + [ct.POINTER(ct.c_uint)]
    library.ck_harmony_intervals.restype = ct.c_uint
    library.ck_palette_index.argtypes = [ct.c_int]
    library.ck_palette_index.restype = ct.c_uint
    library.ck_voicing_index.argtypes = [ct.c_int]
    library.ck_voicing_index.restype = ct.c_uint
    library.ck_voicing_apply.argtypes = [ct.POINTER(ct.c_uint), ct.c_uint, ct.c_uint]
    library.ck_voicing_apply.restype = None
    library.ck_voicing_gain.argtypes = [ct.c_uint] * 3
    library.ck_voicing_gain.restype = ct.c_uint
    library.chord_keys_build.argtypes = [ct.POINTER(Config), ct.c_int, ct.POINTER(Result)]
    library.chord_keys_build.restype = ct.c_int


def intervals(library, mode=0, degree=0, extension=SEVENTH,
              palette=DIATONIC, transform=NONE):
    result = U4(*([POISON] * 4))
    count = library.ck_harmony_intervals(mode, degree, extension, palette, transform, result)
    if count:
        require(count in (3, 4), "Nombre de voix inattendu")
        require(all(n == 0 for n in result[count:]), "Case inutilisée non nulle")
    else:
        require(list(result) == [POISON] * 4, "Refus avec sortie modifiée")
    return count, result


def mode_notes(mode):
    """Gamme reconstruite par rotation des pas, sans reprendre les tables C."""
    steps = (2, 2, 1, 2, 2, 2, 1)
    cycle = steps[mode:] + steps[:mode]
    result = [0]
    for step in itertools.islice(itertools.cycle(cycle), 31):
        result.append(result[-1] + step)
    return result


def family_of(mode, degree):
    notes = mode_notes(mode)
    third, fifth, seventh = [notes[degree + step] - notes[degree] for step in (2, 4, 6)]
    return "dim" if fifth == 6 else "minor" if third == 3 else "major" if seventh == 11 else "dom"


def concrete_examples(library):
    examples = [
        # Em7(b9) → Em9 à fondamentale, tierce et septième identiques.
        ((0, 2, EXT9, DIATONIC, NONE), [0, 3, 10, 13]),
        ((0, 2, EXT9, JAZZ, NONE), [0, 3, 10, 14]),
        ((0, 4, EXT9, TENSION, NONE), [0, 4, 10, 13]),
        ((0, 4, EXT11, JAZZ, NONE), [0, 4, 10, 18]),
        ((0, 4, EXT13, TENSION, NONE), [0, 4, 10, 20]),
        ((0, 0, EXT13, JAZZ, SUS7), [0, 5, 7, 10]),
        ((0, 3, EXT9, JAZZ, PARALLEL), [0, 3, 10, 14]),
        ((0, 1, EXT9, JAZZ, PARALLEL), [0, 4, 11, 14]),
        ((0, 0, EXT13, DIATONIC, PARALLEL), [0, 3, 10, 20]),
        ((0, 1, EXT11, DIATONIC, PARALLEL), [0, 4, 11, 17]),
        ((0, 4, TRIAD, TENSION, PARALLEL), [0, 3, 7]),
        ((0, 0, EXT13, TENSION, V7), [7, 11, 14, 17]),
        # La quinte diminuée reste explicite au prix de la tierce omise.
        ((0, 6, EXT9, DIATONIC, NONE), [0, 6, 10, 13]),
        ((0, 6, EXT9, JAZZ, NONE), [0, 6, 10, 14]),
        ((0, 6, EXT11, JAZZ, NONE), [0, 6, 10, 17]),
        ((0, 6, EXT13, TENSION, NONE), [0, 6, 10, 21]),
    ]
    for args, expected in examples:
        count, actual = intervals(library, *args)
        require(list(actual[:count]) == expected, f"Accord {args}: {list(actual[:count])}")


def legacy_compatibility(library):
    cases = 0
    for mode, degree, extension in itertools.product(range(7), range(7), range(5)):
        settings = config(root=0, mode=mode, extension=extension)
        legacy = Result()
        require(library.chord_keys_build(ct.byref(settings), degree, ct.byref(legacy)) == 0,
                "Référence historique refusée")
        count, actual = intervals(library, mode, degree, extension)
        expected = list(legacy.offsets)
        if family_of(mode, degree) == "dim" and extension >= EXT9:
            expected[1] = 6
        require(count == legacy.count and list(actual) == expected,
                f"DIATONIC changé hors exception m7b5 : {(mode, degree, extension)}")
        cases += 1
    require(cases == 245, "Comparaison historique incomplète")


def exhaustive_harmony(library):
    cases = 0
    for mode, degree, extension, palette, transform in itertools.product(
            range(7), range(7), range(5), range(3), range(7)):
        cases += 1
        family = family_of(mode, degree)
        count, actual = intervals(library, mode, degree, extension, palette, transform)
        context = (mode, degree, extension, palette, transform)
        if family == "dim" and transform in (PARALLEL, V7):
            require(count == 0, f"Transformation diminuée acceptée : {context}")
            continue
        require(count != 0, f"Accord pris en charge refusé : {context}")
        notes = list(actual[:count])
        require(all(a < b for a, b in zip(notes, notes[1:])), f"Doublon : {context}")
        require(len({n % 12 for n in notes}) == count, f"Doublon à l'octave : {context}")
        require(all(0 <= n <= 21 for n in notes), f"Registre de base : {context}")
        saved_count, saved = intervals(library, mode, degree, extension, palette, NONE)
        if transform in (NINTH, ELEVENTH, THIRTEENTH):
            requested_count, requested = intervals(library, mode, degree, transform + 1, palette)
            require(count == requested_count and list(actual) == list(requested),
                    f"Le pad ne suit pas EXT/PALETTE : {context}")
        elif transform == SUS7:
            require(notes == [0, 5, 7, 10], f"SUS7 dépend des settings : {context}")
        elif transform == V7:
            require(notes == [7, 11, 14, 17], f"Dominante de cible incorrecte : {context}")
        elif transform == PARALLEL:
            expected_third = 4 if family == "minor" else 3
            require(notes[0:2] == [0, expected_third], f"Famille parallèle : {context}")
            require(count == saved_count, f"PARALLÈLE change EXT : {context}")
            if extension:
                expected_seventh = 11 if family == "minor" else 10
                require(notes[3 if extension == SEVENTH else 2] == expected_seventh,
                        f"Septième parallèle : {context}")
        else:
            require(actual[0] == 0, f"Fondamentale modifiée : {context}")
            if extension <= SEVENTH:
                _, diatonic = intervals(library, mode, degree, extension)
                require(list(actual) == list(diatonic), f"TRI/7 changé par palette : {context}")
            else:
                _, seventh = intervals(library, mode, degree, SEVENTH)
                require(actual[1] == (6 if family == "dim" else seventh[1])
                        and actual[2] == seventh[3], f"Famille perdue : {context}")
                _, jazz = intervals(library, mode, degree, extension, JAZZ)
                _, tension = intervals(library, mode, degree, extension, TENSION)
                if family != "dom" or extension == EXT11:
                    require(list(jazz) == list(tension), f"Altération superflue : {context}")
                else:
                    require(jazz[3] == tension[3] + 1, f"Tension dominante : {context}")
        # Pas de latch caché : revenir à NONE restitue le même réglage au bit près.
        restored_count, restored = intervals(library, mode, degree, extension, palette, NONE)
        require(saved_count == restored_count and bytes(saved) == bytes(restored),
                f"Geste persistant dans le noyau : {context}")
        for shape in range(9):
            shaped = U4(*actual)
            library.ck_voicing_apply(shaped, count, shape)
            require(sorted(n % 12 for n in shaped[:count]) == sorted(n % 12 for n in notes),
                    f"SHAPE change les notes : {context}, {shape}")
            require(all(a < b for a, b in zip(shaped[:count], shaped[1:count])),
                    f"SHAPE non croissant : {context}, {shape}")
            require(max(shaped[:count]) <= 35, f"SHAPE hors table des rapports : {context}")
            if not shape:
                require(bytes(shaped) == bytes(actual), "BASE transpose un accord")
            for voice in range(count):
                gain = library.ck_voicing_gain(shape, voice, count)
                require(22528 <= gain <= 32768, f"Voix/extension masquée : {context}, {shape}")
    require(cases == 5145, f"Balayage incomplet : {cases}")


def parameter_boundaries(library):
    for value in range(-32768, 32768):
        expected = 0 if value < 43 * 256 else 1 if value < 86 * 256 else 2
        require(library.ck_palette_index(value) == expected, f"COLOR {value}")
        expected_shape = 0 if value < 0 else min(8, value // 1024)
        require(library.ck_voicing_index(value) == expected_shape, f"SHAPE {value}")
    for value, expected in [(-2147483648, 0), (2147483647, 2)]:
        require(library.ck_palette_index(value) == expected, "COLOR extrême invalide")
    for shape in range(9):
        for count in (3, 4):
            require(library.ck_voicing_gain(shape, 0, count) == 32768, "Racine atténuée")
            for voice in range(count, 5):
                require(library.ck_voicing_gain(shape, voice, count) == 0, "Voix inutilisée audible")
            if not shape:
                require(all(library.ck_voicing_gain(shape, voice, count) == 32768
                            for voice in range(count)), "BASE déséquilibré")


def invalid_arguments(library):
    limits = (7, 7, 5, 3, 7)
    for position, limit in enumerate(limits):
        for value in (limit, 0x7FFFFFFF, 0xFFFFFFFF):
            args = [0, 0, 0, 0, 0]
            args[position] = value
            count, _ = intervals(library, *args)
            require(count == 0, f"Argument invalide accepté : {args}")
    require(library.ck_harmony_intervals(0, 0, 0, 0, 0, None) == 0,
            "Pointeur nul accepté")


def main():
    sources = Path(__file__).resolve().parent / "machines/chord_keys"
    families = [
        ("exemples Em9, dominantes tendues, SUS7, parallèle et m7b5", concrete_examples),
        ("245 comparaisons DIATONIC/historique, exception m7b5 explicite", legacy_compatibility),
        ("5 145 harmonies et neuf SHAPE : familles, tensions, retours, audibilité", exhaustive_harmony),
        ("65 536 valeurs COLOR/SHAPE et gains actifs/inutilisés", parameter_boundaries),
        ("arguments invalides et transformations refusées sans sortie modifiée", invalid_arguments),
    ]
    with tempfile.TemporaryDirectory(prefix="chord-harmony-test-") as temporary:
        library_path = Path(temporary) / "chord_harmony.so"
        compiler = shlex.split(os.environ.get("CC", "cc"))
        command = compiler + ["-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                              "-pedantic", "-ffreestanding", "-fno-stack-protector",
                              "-fPIC", "-dynamiclib" if sys.platform == "darwin" else "-shared",
                              str(sources / "chord_keys.c"), str(sources / "chord_voicing.c"),
                              "-o", str(library_path)]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            library = ct.CDLL(str(library_path))
            setup(library)
        except (OSError, subprocess.CalledProcessError) as error:
            print(f"FAIL compilation/chargement du noyau C : {error}")
            if isinstance(error, subprocess.CalledProcessError):
                print(error.stderr, end="")
            return 1
        failures = 0
        for label, test in families:
            try:
                test(library)
            except AssertionError as error:
                print(f"FAIL {label} : {error}")
                failures += 1
            else:
                print(f"ok {label}")
    return int(failures > 0)


if __name__ == "__main__":
    sys.exit(main())
