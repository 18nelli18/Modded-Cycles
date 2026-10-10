#!/usr/bin/env python3
"""Compare une optimisation CHORD Keys à son JSON de référence (notes/40).

Exécute les deux versions du vrai DSP, avec le getter de stockage natif : voix
entières, instantanés d'accords et blocs PCM doivent rester identiques. La matrice
réduite croise modes/degrés/extensions/palettes et distribue SHAPE, HARMONY et les
six pistes ; ce n'est pas la suite exhaustive. Les états live/lock sont préparés
en mémoire, sans prétendre tester les gestes UI ou le transport du séquenceur.
Les compteurs portent sur les instructions exécutées, pas les cycles matériels.

    python3 tools/emu/chord_cpu_checks.py \\
        --cycles firmware/model-cycles_OS1.13.syx \\
        --before-tweak build/chord-cpu-before/44-chord-keys.json

Aucune image ou sortie PCM n'est sauvegardée. Durée attendue : environ une minute.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import build
from gen_chord_keys import load_stock
from chord_audio_checks import AudioRunner, NativeAudioConfig, SCALES, config_word
import mcengine as E

SHAPES = (3, 4, 8, 12, 16, 20, 24, 28, 32)
COLORS = (32, 64, 110)
SLOT, LOCK_MASK, EVENT = 28, 0x423087f8, 0x420c0000
DEFAULT_TWEAK = HERE.parents[1] / "tweaks/model-cycles_OS1.13/44-chord-keys.json"


class Version:
    """Un firmware et ses objets minimaux, sans interception des getters."""

    def __init__(self, stock, path):
        raw = path.read_bytes()
        self.digest = hashlib.sha256(raw).hexdigest()
        self.tweak = json.loads(raw)
        assert self.tweak["id"] == "chord-keys", path
        self.symbols = {name: int(value, 0)
                        for name, value in self.tweak["symbols"].items()}
        patched, _ = build.apply_writes(stock, [self.tweak])
        extra = [(build.BASE + w["off"], len(w["new"]) // 2)
                 for w in self.tweak["writes"] if len(w["new"]) // 2 > 32]
        self.runner = AudioRunner(bytes(patched), extra_code=extra)
        self.engine = self.runner.engine
        self.config = NativeAudioConfig(self.engine)
        self.engine.count_instructions()

    def controls(self, track, transform=0, source="lock", locked=None,
                 present=True, pattern=0):
        """Prépare l'état publié ; l'arbitrage audio réel reste exécuté.

        Un événement natif choisit l'origine ; seul l'état UI final est fourni
        directement, comme le bitmap et la lane d'un lock déjà chargés.
        """
        e, symbols = self.engine, self.symbols
        header = self.config.HEADERS + 256 * pattern
        live = source in ("live", "live-zero", "sequenced-live")
        e.uc.mem_write(symbols["live_modifiers"] + 8 * track,
                       struct.pack(">II", header if live else 0,
                                   0 if source == "live-zero" else transform if live else 0))
        event = [0] * 11
        event[1], event[3] = 1, int(source in ("lock", "sequenced-live"))
        e.uc.mem_write(EVENT, struct.pack(">11I", *event))
        e.call(symbols["ck_audio_event"], track, EVENT)
        value = transform if locked is None else locked
        e.uc.mem_write(E.PARAMS + 14 + track * 66 + 2 * SLOT,
                       struct.pack(">H", value))
        e.uc.mem_write(LOCK_MASK + 8 * track,
                       struct.pack(">I", (1 << SLOT) if present else 0))

    def snapshots(self):
        return bytes(self.engine.uc.mem_read(self.symbols["ck_chord_live"], 24))

    def configure(self, word, pattern=0, signature=0x434b01a7):
        self.config.configure([word] * 6, pattern)
        self.config.select(pattern)
        self.config.write(self.config.HEADERS + 256 * pattern + 32, signature)


def first_difference(a, b):
    """Premier octet différent, sans masquer de données musicales."""
    return next((f"+0x{i:x}: {x:02x}/{y:02x}"
                 for i, (x, y) in enumerate(zip(a, b)) if x != y), "taille")


class Comparison:
    def __init__(self, before, after):
        self.versions = (before, after)
        self.failures = []
        self.updates = []

    def check(self, condition, label, detail=""):
        print(("ok    " if condition else "FAIL  ") + label + detail, flush=True)
        if not condition:
            self.failures.append(label + detail)

    def equal_state(self):
        a, b = self.versions
        voices = a.runner.voices(), b.runner.voices()
        if voices[0] != voices[1]:
            return " voix " + first_difference(*voices)
        snapshots = a.snapshots(), b.snapshots()
        if snapshots[0] != snapshots[1]:
            return " instantané " + first_difference(*snapshots)
        return ""

    def update(self, *, word, track=0, root=48, shape=3, color=32,
               pitch=64, fine=64, transform=0, source="lock", locked=None,
               present=True, pattern=0, signature=0x434b01a7, invalid=None):
        counts = []
        for version in self.versions:
            version.configure(word, pattern, signature)
            version.controls(track, transform, source, locked, present, pattern)
            config = version.config
            if invalid == "project":
                config.write(0x40fe4228, 0)
            elif invalid == "active":
                config.write(0x40a7887c, 0)
            elif invalid == "pattern":
                config.select(96)
            elif invalid == "header":
                config.write(config.ROOT + 5192 + 732 * pattern + 60, 0)
            version.engine.instructions = 0
            version.runner.update(track, root, shape, color, pitch, fine)
            counts.append(version.engine.instructions)
            config.write(0x40fe4228, config.ROOT)
            config.write(0x40a7887c, config.ACTIVE)
        self.updates.append(tuple(counts))
        return self.equal_state()

    def matrix(self):
        first = ""
        coverage = [set() for _ in range(8)]
        start = len(self.updates)
        for mode in range(7):
            for degree in range(7):
                for extension in range(5):
                    for palette, color in enumerate(COLORS):
                        shape_index = (mode + 3 * degree + extension + 2 * palette) % 9
                        transform = (mode + degree + 2 * extension + 3 * palette) % 7
                        track = (mode + 2 * degree + extension + palette) % 6
                        tonic = (24, 36, 48)[(mode + extension + palette) % 3]
                        word = config_word(tonic, mode, (extension,) * 7)
                        root = tonic + SCALES[mode][degree] + 12 * ((degree + palette) % 3)
                        error = self.update(word=word, track=track, root=root,
                                            shape=SHAPES[shape_index], color=color,
                                            transform=transform)
                        values = (mode, degree, extension, palette, shape_index,
                                  transform, track, tonic)
                        for seen, value in zip(coverage, values):
                            seen.add(value)
                        if error and not first:
                            first = f" ; cas {values}{error}"
        count = len(self.updates) - start
        self.check(not first and count == 735 and
                   [len(s) for s in coverage] == [7, 7, 5, 3, 9, 7, 6, 3],
                   f"équivalence : {count} updates, 7 modes × 7 degrés × 5 extensions × 3 palettes ; "
                   "9 SHAPE, HARMONY 0..6 et six pistes répartis", first)

    def boundaries(self):
        first, start = "", len(self.updates)
        fine_values = (0, 64 - 1 / 256, 64, 64 + 1 / 256, 127 + 255 / 256)
        for index, root in enumerate((0, 24, 95, 96, 97, 127)):
            for fine in fine_values:
                for pitch in (0, 32, 64, 127):
                    error = self.update(word=config_word(24, extensions=(4,) * 7),
                                        track=index, root=root, shape=32, color=110,
                                        pitch=pitch, fine=fine, transform=index % 7)
                    if error and not first:
                        first = f" ; note/FINE/PITCH {(root, fine, pitch)}{error}"
        # Les seuils Q8 de SHAPE et COLOR restent identiques, y compris les
        # valeurs négatives possibles après modulation native.
        edges = (-128, -1 / 256, 0, 37, 127 + 255 / 256)
        edges += tuple(edge + delta for edge in range(4, 33, 4)
                       for delta in (-1 / 256, 0, 1 / 256))
        for index, shape in enumerate(edges):
            color = (43 - 1 / 256, 43, 86 - 1 / 256, 86)[index % 4]
            error = self.update(word=config_word(24, extensions=(2,) * 7),
                                track=index % 6, root=24, shape=shape, color=color)
            if error and not first:
                first = f" ; SHAPE/COLOR {(shape, color)}{error}"
        self.check(not first,
                   f"limites : {len(self.updates) - start} updates MIDI aigu, PITCH/FINE et seuils Q8", first)
        first, start = "", len(self.updates)
        for mode in range(7):
            for tonic in range(24, 36):
                relative = (tonic + 5 * mode) % 12
                error = self.update(word=config_word(tonic, mode, (2,) * 7),
                                    track=tonic % 6, root=tonic + relative,
                                    shape=32, color=110, transform=mode)
                if error and not first:
                    first = f" ; mode/tonique/classe {(mode, tonic, relative)}{error}"
        self.check(not first,
                   f"classes chromatiques : {len(self.updates) - start} updates, "
                   "12 toniques et 12 classes relatives par mode, notes hors gamme incluses", first)

    def storage_controls(self):
        active = config_word(24, extensions=(2,) * 7)
        first, start = "", len(self.updates)
        invalids = (
            {"word": active & 0x7fffffff},
            {"word": config_word(24, mode=7)},
            {"word": config_word(49)},
            {"word": config_word(24, extensions=(7,) * 7)},
            {"word": active, "signature": 0},
            *({"word": active, "invalid": value}
              for value in ("project", "active", "pattern", "header")),
            {"word": active, "root": 25},
        )
        for track in range(6):
            for case in invalids:
                error = self.update(track=track, shape=32, color=110,
                                    transform=6, **case)
                if error and not first:
                    first = f" ; piste {track}, {case}{error}"
        self.check(not first,
                   f"stockage : {len(self.updates) - start} updates OFF/hors gamme/configurations invalides", first)
        first, start = "", len(self.updates)
        for track in range(6):
            for transform in range(7):
                for source in ("lock", "live", "live-zero", "sequenced-live"):
                    error = self.update(word=active, track=track, root=24,
                                        shape=SHAPES[(track + transform) % 9],
                                        color=COLORS[track % 3], transform=transform,
                                        source=source, locked=(transform + 1) % 7,
                                        pattern=(0, 1, 95)[track % 3],
                                        signature=(0x434b01a7, 0x434b023f, 0x434b033f)[track % 3])
                    if error and not first:
                        first = f" ; piste/geste/source {(track, transform, source)}{error}"
            for locked, present in ((6, False), (7, True), (127, True), (65534, True)):
                error = self.update(word=active, track=track, root=24,
                                    locked=locked, present=present)
                if error and not first:
                    first = f" ; lock/présence {(locked, present)}{error}"
        self.check(not first,
                   f"contrôles : {len(self.updates) - start} updates live/locks, priorité séquenceur, "
                   "patterns 0/1/95 et signatures v1/v2/v3", first)

    def pcm(self):
        """Six voix dans le dispatch natif, avec changements sans retrigger."""
        first, rendered = "", 0
        scenes = (
            ("OFF", False, 3, 32, "lock", 0),
            ("BASE", True, 3, 32, "lock", 0),
            ("OPN3", True, 32, 32, "lock", 0),
            ("JAZZ", True, 20, 64, "lock", 3),
            ("TENSION", True, 28, 110, "lock", 6),
            ("live", True, 8, 110, "live", 5),
            ("live EXT", True, 12, 64, "live-zero", 0),
            ("séquenceur prioritaire", True, 32, 110, "sequenced-live", 4),
        )
        for scene, (label, enabled, shape, color, source, transform) in enumerate(scenes):
            for version in self.versions:
                pattern = (0, 1, 95)[scene % 3]
                word = config_word(24, scene % 7, (scene % 5,) * 7, enabled)
                version.configure(word, pattern)
                for track in range(6):
                    version.controls(track, transform, source, (transform + 2) % 7,
                                     pattern=pattern)
                    version.engine.machine_defaults(track, "CHORD")
                    version.engine.set(track, note=24 + SCALES[scene % 7][track],
                                       pitch=64, finetune=64, shape=shape,
                                       color=color, decay=100)
            counts, audible = [], False
            for block in range(4):
                pcm, instructions = [], []
                for version in self.versions:
                    if block == 2:
                        for track in range(6):
                            version.engine.set(track, shape=SHAPES[(track + scene) % 9],
                                               color=COLORS[(track + scene) % 3])
                    version.engine.instructions = 0
                    pcm.append(version.engine.block(63 if block == 0 else 0,
                                                    63 if block == 3 else 0))
                    instructions.append(version.engine.instructions)
                counts.append(tuple(instructions))
                error = self.equal_state()
                if not (pcm[0] == pcm[1]).all():
                    error += " PCM"
                audible |= bool(pcm[0].any())
                if error and not first:
                    first = f" ; scène {label}, bloc {block}{error}"
                rendered += 1
            if not audible and not first:
                first = f" ; scène {label} entièrement silencieuse"
            old, new = counts[1]
            print(f"info  instructions/bloc, six CHORD, {label} : {old} → {new} "
                  f"({100 * (new - old) / old:+.2f} %), getter natif inclus", flush=True)
        self.check(not first, f"PCM : {rendered} blocs complets identiques, six voix, "
                   "attaques/queues/relâchements et paramètres changés sans retrigger", first)

    def report(self):
        old, new = map(sum, zip(*self.updates))
        worst = max(b - a for a, b in self.updates)
        print(f"info  {len(self.updates)} updates : {old} → {new} instructions au total "
              f"({100 * (new - old) / old:+.2f} %), moyenne "
              f"{old / len(self.updates):.1f} → {new / len(self.updates):.1f}, "
              f"plus grand delta individuel {worst:+d}", flush=True)
        print("info  instructions émulées ≠ cycles CPU : mémoire, cache et latence des "
              "instructions exigent une mesure matérielle ; aucun résultat matériel revendiqué", flush=True)
        self.check(not any(v.engine.unmapped for v in self.versions),
                   "aucun accès mémoire hors du banc")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles", required=True, type=Path)
    parser.add_argument("--before-tweak", required=True, type=Path)
    parser.add_argument("--after-tweak", type=Path, default=DEFAULT_TWEAK)
    args = parser.parse_args()
    stock = load_stock(args.cycles)
    versions = (Version(stock, args.before_tweak), Version(stock, args.after_tweak))
    for label, version in zip(("avant", "après"), versions):
        print(f"info  JSON {label} SHA-256 {version.digest}", flush=True)
    comparison = Comparison(*versions)
    comparison.matrix()
    comparison.boundaries()
    comparison.storage_controls()
    comparison.pcm()
    comparison.report()
    print("TOUT OK" if not comparison.failures else
          f"FAIL : {len(comparison.failures)} groupes en échec", flush=True)
    return int(bool(comparison.failures))


if __name__ == "__main__":
    sys.exit(main())
