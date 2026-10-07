"""Palettes et macro SHAPE dans le véritable DSP CHORD (notes/40 §15).

Seuls les deux getters sont instrumentés pour le balayage combinatoire. Une
seconde partie utilise le vrai stockage ; les gestes UI sont prouvés séparément.
Les références ci-dessous sont des intervalles musicaux, jamais du code firmware.
"""
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import mcengine as E
from chord_audio_checks import AudioRunner, NativeAudioConfig, config_word, SCALES, POSITIONS
from probe_chord_keys import frequency_ratios


def expected_notes(mode, degree, extension, palette, transform):
    """Oracle musical indépendant : famille, tension demandée et geste fixe."""
    scale = SCALES[mode]
    interval = lambda step: 12 * ((degree + step) // 7) + scale[(degree + step) % 7] - scale[degree]
    third, fifth, seventh = (interval(step) for step in (2, 4, 6))
    diminished = fifth == 6
    if transform in (5, 6) and diminished:
        transform = 0  # le geste indisponible laisse le réglage de repos
    if transform == 4:
        return (0, 5, 7, 10)
    if transform == 6:
        return (7, 11, 14, 17)
    if 1 <= transform <= 3:
        extension = transform + 1
    if transform == 5:
        third, fifth, seventh = (4, 7, 11) if third == 3 else (3, 7, 10)
    if extension == 0:
        return (0, third, fifth)
    if extension == 1:
        return (0, third, fifth, seventh)
    if palette == 0:
        tension = interval((8, 10, 12)[extension - 2])
        if transform == 5:
            tension = (14, 17, 20 if third == 3 else 21)[extension - 2]
    else:
        dominant = third == 4 and seventh == 10
        tension = (14, 18 if third == 4 else 17, 21)[extension - 2]
        if palette == 2 and dominant:
            tension = (13, 18, 20)[extension - 2]
    return (0, 6 if diminished else third, seventh, tension)


def voiced(notes, index):
    if not index:
        return notes
    result = sorted(n % 12 for n in notes)
    for _ in range((index - 1) % 4):
        result = sorted([result[0] + 12, *result[1:]])
    if index >= 5:
        result = sorted(n + (12 if i % 2 else 0) for i, n in enumerate(result))
    return tuple(result)


def run(stock, patched, symbols, extra_code, check):
    """Vrais hooks, vrai update et vraie boucle audio, sans retrigger ajouté."""
    runner = AudioRunner(patched, symbols['ck_audio_config'], extra_code)
    controls = [1] * 6

    def control_getter(uc, address, size, data):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        ret, track = struct.unpack('>II', uc.mem_read(sp, 8))
        uc.reg_write(mk.UC_M68K_REG_D0, controls[track])
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        uc.reg_write(mk.UC_M68K_REG_PC, ret)

    runner.engine.uc.hook_add(UC_HOOK_CODE, control_getter,
                             begin=symbols['ck_audio_controls'], end=symbols['ck_audio_controls'])

    def snapshot_matches(notes, root, bass):
        packet = int.from_bytes(runner.engine.uc.mem_read(symbols['ck_chord_live'], 4), 'big')
        expected = 0x80000000 | root | ((bass % 12) << 27)
        expected |= sum(n << (7 + 5 * i) for i, n in enumerate(notes))
        return packet == expected

    def matches(notes, ratios, gains):
        reference = frequency_ratios(notes + ((0,) if len(notes) == 3 else ()))
        return (all(abs(a - b) <= 4 for a, b in zip(reference, ratios))
                and all(gains[:len(notes)-1])
                and (len(notes) == 4 or gains[-1] == 0))

    total, first = 0, None
    for mode in range(7):
        valid = True
        for degree in range(7):
            root = 24 + SCALES[mode][degree]
            for ext in range(5):
                runner.configs[0] = config_word(root=24, mode=mode, extensions=(ext,) * 7)
                for palette, color in enumerate((32, 64, 110)):
                    for transform in range(7):
                        controls[0] = 1 | (transform << 8)
                        notes = expected_notes(mode, degree, ext, palette, transform)
                        ratios, _, gains = runner.update(root=root, color=color)
                        ok = matches(notes, ratios, gains) and snapshot_matches(notes, root, notes[0])
                        valid &= ok
                        total += 1
                        if not ok and first is None:
                            first = (mode, degree, ext, palette, transform, notes, ratios, gains)
        check(valid, f'harmonie DSP mode {mode} : 7 degrés × 5 extensions × 3 palettes × 7 gestes'
              + (f' ; premier écart {first}' if not valid else ''))
    check(total == 5145 and first is None, f'harmonie DSP : {total} accords avec racine, famille, tension et instantané écran exacts')

    # Le balayage fait varier simultanément les paramètres effectifs et les
    # gestes ; les gains natifs COLOR ne doivent plus couper les extensions.
    valid, first = True, None
    runner.configs[0] = config_word(root=24, extensions=(4,) * 7)
    weights = ((32,32,32), (30,26,28), (26,32,28), (28,26,32),
               (32,28,26), (22,28,32), (28,22,32), (32,22,28), (28,32,22))
    native = AudioRunner(stock)
    stock_gains = native.update(root=24, shape=7, color=32)[2]
    for index, shape in enumerate((3,4,8,12,16,20,24,28,32)):
        for color in range(128):
            palette = 0 if color < 43 else 1 if color < 86 else 2
            for transform in range(7):
                controls[0] = 1 | (transform << 8)
                base_notes = expected_notes(0,0,4,palette,transform)
                notes = voiced(base_notes, index)
                ratios, _, gains = runner.update(root=24, shape=shape, color=color)
                target_gains = tuple(g if w == 32 else (g >> 15) * (w << 10)
                                     for g, w in zip(stock_gains, weights[index]))
                ok = (matches(notes, ratios, gains) and gains == target_gains
                      and snapshot_matches(base_notes, 24, notes[0]))
                valid &= ok
                if not ok and first is None:
                    first = (index,color,transform,notes,ratios,gains,target_gains)
    check(valid, 'macro SHAPE : 9 dispositions × 128 COLOR × 7 gestes, gains indépendants de la palette, aucune voix coupée'
          + (f' ; premier écart {first}' if first else ''))

    # Deux vraies configurations de pattern : le mot musical reste identique,
    # les deux signatures appliquent désormais les mêmes contrôles COLOR.
    native_runner = AudioRunner(patched, extra_code=extra_code)
    config = NativeAudioConfig(native_runner.engine)
    words = [config_word(root=24, extensions=(2,) * 7)] * 6
    config.configure(words, 0)
    config.configure(words, 1)
    config.write(config.HEADERS + 256 + 32, 0x434b0200)
    valid = True
    for pattern, notes in ((0,(0,3,10,14)), (1,(0,3,10,14)), (0,(0,3,10,14))):
        config.select(pattern)
        for track in range(6):
            ratios, _, gains = native_runner.update(track=track, root=28, color=64)
            valid &= matches(notes, ratios, gains)
    check(valid, 'contrôles permanents : signatures v1/v2 donnent Em9 en JAZZ, six pistes')

    # Le même accord tenu passe d'une palette à l'autre avec trig_mask=0.
    # Les deux appels stock d'enveloppe/trigger ne sont jamais nécessaires.
    e = native_runner.engine
    config.select(1)
    for track in range(6):
        e.machine_defaults(track, 'CHORD')
        e.set(track, note=28, pitch=64, finetune=64, shape=3, color=32, decay=100)
    e.block(63)
    # Le démarrage natif de l'enveloppe comprend des blocs silencieux ; placer
    # les gestes après son attaque, sans réinitialiser ni redéclencher la voix.
    for _ in range(4):
        e.block(0)
    changed, notes_seen, levels = True, [], []
    for color in (32,64,110,32):
        for track in range(6):
            e.set(track, color=color)
        pcm = e.block(0)
        changed &= bool(pcm.any())
        levels.append(int(abs(pcm).max()))
        notes_seen.append(tuple(int.from_bytes(e.uc.mem_read(E.VOICE0 + 0x50 + i*0x78,4),'big')
                                for i in range(4)))
    changed &= notes_seen[0] == notes_seen[3] and notes_seen[0] != notes_seen[1]
    check(changed, 'accord tenu : palette changée et retour exact au bloc suivant sans nouveau trig'
          + (f' ; rapports {notes_seen}, niveaux {levels}' if not changed else ''))
    e.count_instructions()
    costs = []
    for shape in (3, 32):
        for track in range(6):
            e.set(track, shape=shape, color=110)
        e.instructions = 0
        e.block(0)
        costs.append(e.instructions)
    print(f'info  six CHORD / TENSION : BASE {costs[0]}, OPN3 {costs[1]} instructions/bloc ; '
          'getter réel inclus, pas une mesure de cycles matériels', flush=True)
    # Une inversion aiguë peut couper des opérateurs natifs dès TRIG 15/16.
    # Le nom conserve l'harmonie voulue mais signale cette limite réelle, puis
    # efface le marqueur dès que l'on redescend ; aucune fausse alerte de triade.
    limited_ok = True
    controls[0] = 1
    for root, ext, shape, limited in ((72, 1, 32, True), (74, 1, 32, True),
                                      (24, 1, 32, False), (24, 0, 3, False),
                                      (96, 1, 3, True), (24, 1, 3, False)):
        runner.configs[0] = config_word(root=48, extensions=(ext,) * 7)
        _, phases, gains = runner.update(root=root, shape=shape, color=64)
        packet = int.from_bytes(runner.engine.uc.mem_read(symbols['ck_chord_live'], 4), 'big')
        actual_limit = phases[0] == 0x000bd2f1 or not all(gains[:2 if ext == 0 else 3])
        limited_ok &= actual_limit == limited and bool(packet & 0x400) == limited
    check(limited_ok, 'écran DSP : HIGH LIMIT suit les vraies voix coupées/plafonnées, retour grave et triade sans fausse alerte')
    protected = True
    for shape in (3,4,8,12,16,20,24,28,32):
        for color in (0,64,127):
            _, phases, gains = native_runner.update(root=96, shape=shape, color=color)
            protected &= not any(gains) and 0 < phases[0] <= 0x000bd2f1
    check(protected, 'macro SHAPE : protections aiguës stock conservées, aucune voix coupée réactivée')
    check(not e.unmapped and not runner.engine.unmapped, 'nouveaux contrôles : aucun accès hors mémoire dans le DSP')
