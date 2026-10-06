"""Vérifications audio réutilisables du mod chord-keys (notes/42).

Appelé par test_chord_keys.py avec les images de référence et modifiée. Le getter
de configuration est seul instrumenté pour isoler le DSP du stockage/menu : les
deux crochets ColdFire, le trampoline et l'update stock s'exécutent réellement.
Les preuves de stockage et de pads doivent compléter ces vérifications.
run_audio_storage_checks ajoute le vrai getter, des changements de pattern et
le coût complet de la boucle native ; aucun getter n'y est instrumenté.
"""
import math
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import mcengine as E
from probe_chord_keys import UPDATE, frequency_ratios

SCALES = (
    (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 9, 10),
    (0, 1, 3, 5, 7, 8, 10), (0, 2, 4, 6, 7, 9, 11),
    (0, 2, 4, 5, 7, 9, 10), (0, 2, 3, 5, 7, 8, 10),
    (0, 1, 3, 5, 6, 8, 10),
)
POSITIONS = ((0, 2, 4), (0, 2, 4, 6), (0, 2, 6, 8),
             (0, 2, 6, 10), (0, 2, 6, 12))


def config_word(root=48, mode=0, extensions=(0,) * 7, enabled=True):
    return ((int(enabled) << 31) | (mode << 28) | (root << 21)
            | sum(ext << (3 * degree) for degree, ext in enumerate(extensions)))


class AudioRunner:
    def __init__(self, image, config_address=None, extra_code=(), setup=None):
        self.engine = E.Engine(image, extra_code=extra_code)
        if setup:
            setup(self.engine)
        self.configs = [0] * 6
        if config_address is not None:
            self.engine.uc.hook_add(UC_HOOK_CODE, self._config,
                                    begin=config_address, end=config_address)

    def _config(self, uc, address, size, userdata):
        """Remplace seulement l'accès au réglage, pas le calcul du DSP."""
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        ret, track = struct.unpack(">II", uc.mem_read(sp, 8))
        assert track < 6, track
        uc.reg_write(mk.UC_M68K_REG_D0, self.configs[track])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        uc.reg_write(mk.UC_M68K_REG_PC, ret)

    def update(self, track=0, root=48, shape=4, color=32, pitch=64, fine=64):
        e = self.engine
        e.machine_defaults(track, "CHORD")
        e.set(track, note=root, pitch=pitch, finetune=fine, shape=shape, color=color)
        e._write_params()
        params = E.PARAMS + 14 + track * 66
        voice = E.VOICE0 + track * E.VSTRIDE
        before = bytes(e.uc.mem_read(params, 66))
        e.emac.macsr = 0xa0
        # Entrée native détournée, même si un autre mod a copié son pointeur.
        e.call(UPDATE, int(root * 65536), voice, params)
        assert e.uc.reg_read(mk.UC_M68K_REG_PC) == E.STOP, "update incomplet"
        assert bytes(e.uc.mem_read(params, 66)) == before, "paramètres natifs modifiés"
        words = lambda off, stride, count: tuple(int.from_bytes(
            e.uc.mem_read(voice + off + i * stride, 4), "big") for i in range(count))
        return words(0x50, 0x78, 4), words(0x70, 0x78, 4), words(12, 4, 3)

    def voices(self):
        return bytes(self.engine.uc.mem_read(E.VOICE0, 6 * E.VSTRIDE))


class NativeAudioConfig:
    """Objets de projet minimaux pour le vrai ck_audio_config, sans callback UI.

    Le getter lit les pointeurs et buffers aux offsets établis dans notes/42.
    Cette fixture ne remplace ni leur sérialisation ni leurs notifications.
    """
    ROOT, ACTIVE, HEADERS = 0x42010000, 0x42050000, 0x42070000

    def __init__(self, engine):
        self.engine = engine
        engine.uc.mem_map(0x40800000, 0x00800000)
        self.write(0x40fe4228, self.ROOT)
        self.write(0x40a7887c, self.ACTIVE)
        self.select(0)

    def write(self, address, value):
        self.engine.uc.mem_write(address, struct.pack(">I", value))

    def select(self, pattern):
        self.write(self.ACTIVE + 30706, pattern)

    def configure(self, words, pattern=0):
        assert len(words) == 6 and 0 <= pattern < 96
        header = self.HEADERS + 256 * pattern
        self.write(self.ROOT + 5192 + 732 * pattern + 60, header)
        self.write(header + 32, 0x434b01a7)
        for track, word in enumerate(words):
            self.write(header + 40 + track * 4, word)


def run_audio_storage_checks(stock, patched, extra_code=(), setup=None):
    """Vrai getter + DSP : patterns, isolation, cas invalides et coût complet."""
    a = AudioRunner(stock)
    b = AudioRunner(patched, extra_code=extra_code, setup=setup)
    config = NativeAudioConfig(b.engine)
    failures = 0

    def check(ok, label):
        nonlocal failures
        failures += not ok
        print(("ok    " if ok else "FAIL  ") + label, flush=True)

    def reset():
        for runner in (a, b):
            for track in range(6):
                runner.engine.call(E.VOICE_RESET, E.VOICE0 + E.VSTRIDE * track)

    # Boot incomplet : pas d'appel d'interface ni d'allocation paresseuse.
    config.write(0x40fe4228, 0)
    check(a.update() == b.update(), "getter natif : boot sans projet, CHORD reste stock")
    config.write(0x40fe4228, config.ROOT)

    valid = True
    # La piste se relit dans le pattern réellement actif, même sans passage par
    # les pads ou le menu ; le dernier objet (95) vérifie aussi le pas de 732 o.
    for pattern in (0, 1, 95):
        config.configure([config_word(mode=(t + pattern) % 7,
                                      extensions=((t + pattern) % 5,) * 7)
                          for t in range(6)], pattern)
        config.select(pattern)
        for track in range(6):
            mode, extension = (track + pattern) % 7, (track + pattern) % 5
            notes = tuple(12 * (p // 7) + SCALES[mode][p % 7] for p in POSITIONS[extension])
            expected = frequency_ratios(notes + ((0,) if len(notes) == 3 else ()))
            ratios, _, gains = b.update(track=track)
            valid &= ratios == expected and (bool(gains[-1]) == (len(notes) == 4))
    check(valid, "getter natif : six pistes, changements de patterns 0/1/95 sans cache ni UI")

    invalid = True
    config.configure([config_word()] * 6)
    for case in ("signature", "mode", "tonique", "extension", "pattern"):
        reset()
        config.configure([config_word()] * 6)
        config.select(0)
        if case == "signature":
            config.write(config.HEADERS + 32, 0)
        elif case == "pattern":
            config.select(96)
        else:
            word = {"mode": config_word(mode=7), "tonique": config_word(root=49),
                    "extension": config_word(extensions=(7,) * 7)}[case]
            config.write(config.HEADERS + 40, word)
        invalid &= a.update(shape=24, color=96) == b.update(shape=24, color=96)
    check(invalid, "getter natif : signature/mode/tonique/extension/index invalides reviennent au stock")

    # Contrat d'appel m68k : les onze registres non volatils doivent traverser
    # le wrapper, son trampoline, le getter et l'update sans changer.
    saved_registers = [getattr(mk, f"UC_M68K_REG_{kind}{n}")
                       for kind, numbers in (("D", range(2, 8)), ("A", range(2, 7)))
                       for n in numbers]
    preserved, depths = True, []
    config.select(0)
    config.configure([config_word(extensions=(2,) * 7)] * 6)
    for runner in (a, b):
        minimum = [E.STACK]

        def stack_depth(uc, address, size, userdata):
            minimum[0] = min(minimum[0], uc.reg_read(mk.UC_M68K_REG_A7))

        hook = runner.engine.uc.hook_add(UC_HOOK_CODE, stack_depth)
        for track in range(6):
            for i, register in enumerate(saved_registers):
                runner.engine.uc.reg_write(register, 0x12340000 + 0x101 * i)
            runner.update(track=track)
            preserved &= all(runner.engine.uc.reg_read(register) == 0x12340000 + 0x101 * i
                             for i, register in enumerate(saved_registers))
            preserved &= runner.engine.uc.reg_read(mk.UC_M68K_REG_A7) == E.STACK - 0x1fc
        runner.engine.uc.hook_del(hook)
        depths.append(E.STACK - 0x200 - minimum[0])
    check(preserved, "ABI audio : d2..d7, a2..a6 et pile restaurés, six pistes, getter natif")
    print(f"info  pile sous l'entrée update : stock {depths[0]} o, mod {depths[1]} o "
          f"(+{depths[1] - depths[0]} o observés)", flush=True)

    reset()
    config.select(0)
    config.configure([config_word(extensions=(2,) * 7, enabled=False)] * 6)
    for runner in (a, b):
        for track, note in enumerate((48, 50, 52, 53, 55, 57)):
            runner.engine.machine_defaults(track, "CHORD")
            runner.engine.set(track, note=note, pitch=64, finetune=64, shape=7, color=32)
    identical = True
    for block in range(8):
        ref = a.engine.block(63 if block == 0 else 0)
        got = b.engine.block(63 if block == 0 else 0)
        identical &= (ref == got).all()
    check(identical, "getter natif : six CHORD désactivés, rendu PCM identique")
    a.engine.count_instructions()
    b.engine.count_instructions()
    a.engine.block()
    b.engine.block()
    off_ref, off_mod = a.engine.instructions, b.engine.instructions
    config.configure([config_word(extensions=(2,) * 7)] * 6)
    a.engine.instructions = b.engine.instructions = 0
    ref = a.engine.block()
    got = b.engine.block()
    check((got != 0).any() and (ref != got).any(),
          "getter natif : activation des six pistes au bloc suivant, PCM changé")
    print(f"info  instructions/bloc, getter natif inclus : inactif {off_ref} → {off_mod} "
          f"(+{off_mod - off_ref}), actif {a.engine.instructions} → {b.engine.instructions} "
          f"(+{b.engine.instructions - a.engine.instructions}) ; pas une mesure de cycles matériels", flush=True)
    check(not a.engine.unmapped and not b.engine.unmapped,
          "getter natif : aucun accès hors mémoire avec le DSP")
    return failures


def run_audio_governor_checks(image, governor_tweak, extra_code=()):
    """CHORD actif + vrai régulateur Syntakt ; minuteur de charge simulé.

    image inclut la charge utile construite à partir du Syntakt officiel.
    Les routines audio/dispatch/getter/régulateur restent natives ; seule
    l'horloge DMA est alimentée avec une charge imposée, comme test_governor.py.
    Cette preuve vérifie la compatibilité, pas la marge CPU réelle du matériel.
    """
    from unicorn import UC_HOOK_MEM_READ
    import numpy as np
    import gov_asm
    from test_governor import TIMER, BLOCK, GAINS, FULL

    symbols = {key: int(value, 16) for key, value in governor_tweak["gov"].items()}
    failures = 0

    def check(ok, label):
        nonlocal failures
        failures += not ok
        print(("ok    " if ok else "FAIL  ") + label, flush=True)

    def play(load):
        engine = E.Engine(image, extra_code=extra_code)
        config = NativeAudioConfig(engine)
        config.configure([config_word(extensions=(2,) * 7)] * 6)
        for track, note in enumerate((48, 50, 52, 53, 55, 57)):
            engine.machine_defaults(track, "CHORD")
            engine.set(track, note=note, shape=7, color=32, decay=100)
            for address in GAINS:
                engine.uc.mem_write(address + 4 * track, struct.pack(">I", FULL))
        clock = {"now": 10_000_000, "fixed": None}

        def timer(uc, access, address, size, value, userdata):
            clock["now"] += 2000
            value = clock["now"] if clock["fixed"] is None else clock["fixed"]
            uc.mem_write(TIMER, struct.pack(">I", value & 0xffffffff))

        engine.uc.hook_add(UC_HOOK_MEM_READ, timer, begin=TIMER, end=TIMER + 3)
        engine.uc.mem_write(gov_asm.x_var(governor_tweak, "X_SLOW"), b"\0" * 4)
        output, fading, stolen = [], [], []
        for block in range(96):
            output.append(engine.block(63 if block in (1, 80) else 0))
            if load is not None:
                start = 10_000_000 + block * BLOCK
                engine.uc.mem_write(symbols["gov_t0_audio"], struct.pack(">I", start))
                clock["fixed"] = start + load(block) * BLOCK // 100
                engine.call(symbols["audio_end"])
                clock["fixed"] = None
            fading.append(bytes(engine.uc.mem_read(symbols["gov_fading"], 6)))
            stolen.append(bytes(engine.uc.mem_read(symbols["gov_stolen"], 6)))
        return np.stack(output), fading, stolen, engine.unmapped

    reference, _, _, unmapped = play(None)
    check(not unmapped and reference.any(), "régulateur + CHORD : six accords natifs audibles dans le dispatch Syntakt")
    normal, _, stolen, unmapped = play(lambda block: 50)
    check(np.array_equal(reference, normal) and not any(map(any, stolen)) and not unmapped,
          "régulateur + CHORD : 50 % simulés, PCM identique et aucune voix volée")
    isolated, _, stolen, unmapped = play(lambda block: 99 if block == 40 else 50)
    check(np.array_equal(reference, isolated) and not any(map(any, stolen)) and not unmapped,
          "régulateur + CHORD : pic isolé à 99 %, PCM identique et aucune voix volée")
    overloaded, fading, stolen, unmapped = play(lambda block: 99 if 40 <= block < 60 else 50)
    first = next((block for block, flags in enumerate(fading) if any(flags)), None)
    check(first == 41 and any(map(any, stolen)) and not unmapped
          and np.array_equal(reference[:first + 1], overloaded[:first + 1])
          and np.abs(overloaded[81:]).max() > 1_000_000,
          "régulateur + CHORD : pic répété, fondu dès le bloc 41, accords rejoués après retrig")
    return failures


def run_audio_checks(stock, patched, config_address, extra_code=(), setup=None):
    """Renvoie le nombre d'échecs ; setup charge uniquement un éventuel code test."""
    a = AudioRunner(stock)
    b = AudioRunner(patched, config_address, extra_code, setup)
    failures = 0

    def check(ok, label):
        nonlocal failures
        failures += not ok
        print(("ok    " if ok else "FAIL  ") + label, flush=True)

    # Des états initiaux identiques donnent les mêmes octets de voix après chaque
    # update, y compris les cas SHAPE unisson et les bornes Pitch/Fine/COLOR.
    identical = True
    for shape in range(38):
        for color in (0, 32, 64, 96, 127):
            for root in (24, 60, 96):
                t = shape % 6
                a.update(t, root, shape, color)
                b.update(t, root, shape, color)
                identical &= a.voices() == b.voices()
    check(identical, "audio désactivé : 570 updates stock/patched, six voix identiques octet par octet")

    # Une note hors gamme et une configuration invalide gardent SHAPE stock.
    passthrough = True
    for word, note in ((config_word(), 49), (config_word(mode=7), 48),
                       (config_word(extensions=(7,) * 7), 48)):
        b.configs[0] = word
        a.update(0, note, 24, 96)
        b.update(0, note, 24, 96)
        passthrough &= a.voices() == b.voices()
    check(passthrough, "audio : note hors gamme/mode invalide/extension invalide restent stock")

    # Références de phase du même moteur OS avec chacune des notes comme racine.
    references = {n: a.update(root=n)[1][0] for n in range(24, 96)}
    worst = 0.0
    count = 0
    for mode, scale in enumerate(SCALES):
        for extension, positions in enumerate(POSITIONS):
            valid = True
            first_error = None
            for tonic in range(24, 49):
                b.configs[0] = config_word(tonic, mode, (extension,) * 7)
                for slot in range(12):
                    notes = tuple(tonic + 12 * ((slot + pos) // 7)
                                  + scale[(slot + pos) % 7] for pos in positions)
                    intervals = tuple(n - notes[0] for n in notes)
                    expected = frequency_ratios(intervals + ((0,) if len(notes) == 3 else ()))
                    ratios, phases, gains = b.update(root=notes[0])
                    cents = max(abs(1200 * math.log2(got / references[n]))
                                for got, n in zip(phases, notes))
                    worst = max(worst, cents)
                    # L'OS quantifie l'incrément entier et sa table exponentielle.
                    # Aux notes graves, comparer deux fondamentales stock donne
                    # jusqu'à 0,877 cent ici ; les rapports Q26 restent exacts.
                    ok = ratios == expected and cents < 1.0 and all(gains[:len(notes) - 1])
                    ok &= len(notes) == 4 or gains[-1] == 0
                    valid &= ok
                    if not ok and first_error is None:
                        first_error = (tonic, slot, ratios, expected, gains, cents)
                    count += 1
            check(valid, f"audio mode {mode}, extension {extension} : 25 toniques × 12 pads"
                  + (f" ; premier écart {first_error}" if first_error else ""))
    check(count == 10500, f"audio : {count} accords, paramètres inchangés, écart maximal {worst:.3f} cent")

    degree_settings = True
    mixed = (0, 1, 2, 3, 4, 0, 1)
    for mode, scale in enumerate(SCALES):
        b.configs[0] = config_word(mode=mode, extensions=mixed)
        for slot in range(12):
            positions = POSITIONS[mixed[slot % 7]]
            notes = tuple(48 + 12 * ((slot + pos) // 7) + scale[(slot + pos) % 7]
                          for pos in positions)
            expected = frequency_ratios(tuple(n - notes[0] for n in notes)
                                        + ((0,) if len(notes) == 3 else ()))
            ratios, _, gains = b.update(root=notes[0])
            degree_settings &= ratios == expected and (bool(gains[-1]) == (len(notes) == 4))
    check(degree_settings, "audio : sept extensions distinctes par degré, retrouvées à l'octave suivante")

    # COLOR conserve exactement les déplacements d'octave de l'update stock.
    color_ok = True
    b.configs[0] = config_word(extensions=(2,) * 7)
    base = frequency_ratios((0, 4, 11, 14))
    for color in range(128):
        expected = list(base)
        for i, (lo, hi, up) in enumerate(((37, 68, 100), (47, 78, 110), (57, 88, 120)), 1):
            if lo <= color <= hi:
                expected[i] >>= 1
            elif color > up:
                expected[i] <<= 1
        ratios, _, gains = b.update(root=48, color=color)
        _, _, stock_gains = a.update(root=48, shape=7, color=color)
        color_ok &= ratios == tuple(expected) and gains == stock_gains
    check(color_ok, "audio : les 128 positions de COLOR conservent gains et inversions stock")

    # Chaque voix reçoit son propre réglage ; aucun écrit dans les cinq autres.
    isolation = True
    b.configs[:] = [config_word(mode=t, extensions=(t % 5,) * 7) for t in range(6)]
    for t in range(6):
        before = b.voices()
        scale, positions = SCALES[t], POSITIONS[t % 5]
        notes = tuple(48 + 12 * (p // 7) + scale[p % 7] for p in positions)
        expected = frequency_ratios(tuple(n - 48 for n in notes) + ((0,) if len(notes) == 3 else ()))
        ratios, _, _ = b.update(track=t)
        after = b.voices()
        start, end = t * E.VSTRIDE, (t + 1) * E.VSTRIDE
        isolation &= (ratios == expected and before[:start] == after[:start]
                      and before[end:] == after[end:])
    check(isolation, "audio : six réglages indépendants, aucun écrit dans les cinq autres voix")

    # Rendu entier de la boucle native : identité inactive, son changé active.
    a = AudioRunner(stock)
    b = AudioRunner(patched, config_address, extra_code, setup)
    for runner in (a, b):
        for t in range(6):
            runner.engine.machine_defaults(t, "CHORD")
            runner.engine.set(t, note=48 + t, pitch=64, finetune=64, shape=7, color=32)
    same_pcm = True
    for block in range(32):
        ref = a.engine.block(63 if block == 0 else 0)
        got = b.engine.block(63 if block == 0 else 0)
        same_pcm &= (ref == got).all()
    check(same_pcm, "rendu : 32 blocs, six CHORD désactivés, PCM identique")

    # Comptage d'instructions, pas mesure de temps réel MCF54415. Le getter est
    # instrumenté et son propre coût doit être ajouté par le test d'intégration.
    a.engine.count_instructions()
    b.engine.count_instructions()
    a.engine.block()
    b.engine.block()
    off_cost = b.engine.instructions - a.engine.instructions
    b.configs[:] = [config_word(extensions=(2,) * 7)] * 6
    # Six notes diatoniques pour mesurer six calculs actifs, sans pass-through.
    for t, note in enumerate((48, 50, 52, 53, 55, 57)):
        a.engine.set(t, note=note)
        b.engine.set(t, note=note)
    a.engine.instructions = b.engine.instructions = 0
    ref = a.engine.block()
    got = b.engine.block()
    on_count = b.engine.instructions
    check((got != 0).any() and (ref != got).any(),
          "rendu : six accords actifs produisent du PCM non nul différent du SHAPE stock")
    print(f"info  instructions/bloc : stock {a.engine.instructions}, supplément inactif {off_cost}, "
          f"six CHORD actifs {on_count} (getter exclu ; pas une mesure CPU matérielle)", flush=True)
    check(not a.engine.unmapped and not b.engine.unmapped,
          "audio : aucun accès mémoire non mappé pendant les rendus")
    return failures
