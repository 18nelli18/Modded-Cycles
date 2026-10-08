"""Lien séquentiel des vrais gestes UI au vrai DSP CHORD (notes/40).

Le banc UI exécute PadEvent, le routage et les setters persistants. Ses captures
physiques, ses transformations, les captures TRIG et son en-tête passent dans un second banc
DSP possédant la même adresse d'en-tête. Aucun getter musical n'est remplacé.
Ce transfert séquentiel ne simule pas l'ordonnancement concurrent UI/IRQ ; il
prouve que l'état produit par les événements gouverne réellement l'accord tenu.
Les drapeaux de déclenchement sont observés à l'entrée du vrai update CHORD.
Les sorties note-on/off observées à la frontière du relais UI sont traduites en
masques d'entrée de la boucle DSP ; le transport entre ces deux tâches n'est
pas émulé. Les enveloppes et le PCM sont calculés par le véritable OS.
"""
import math

import numpy as np

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import mcengine as E
from chord_audio_checks import NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from chord_ui_checks import HEADER, _ui_rig, _key, _pad, _on
from probe_chord_keys import frequency_ratios


def run_prepare(image, symbols, extra_code, check):
    """Deux DSP natifs : queue laissée seule contre préparation réelle T6."""
    ui, _, _, _, _ = _ui_rig(image, symbols)
    ui.call(symbols["ck_ui_config_set"], 2, config_word(root=24, extensions=(1,) * 7))
    _key(ui, 1, True)
    _pad(ui, 1, True)
    _pad(ui, 1, False)
    _key(ui, 1, False)

    def transfer(engine):
        engine.uc.mem_write(HEADER, bytes(ui.uc.mem_read(HEADER, 64)))
        for name, size in (("held_pads", 6), ("live_modifiers", 48),
                           ("prepared_modifiers", 48), ("held", 256)):
            engine.uc.mem_write(symbols[name], bytes(ui.uc.mem_read(symbols[name], size)))

    twins = []
    for _ in range(2):
        engine = E.Engine(image, extra_code=extra_code)
        config = NativeAudioConfig(engine)
        engine.uc.mem_map(0x93100000, 0x10000)
        config.write(config.ROOT + 5192 + 60, HEADER)
        transfer(engine)
        engine.machine_defaults(2, "CHORD")
        engine.set(2, note=24, pitch=64, finetune=64, shape=3, color=110, decay=110)
        engine.block(4)
        for _ in range(4):
            engine.block(0)
        engine.block(0, 4)
        twins.append(engine)
    reference, changed = twins
    _pad(ui, 6, True)
    transfer(changed)
    exact, audible = not ui.calls, False
    voice = E.VOICE0 + 2 * E.VSTRIDE
    for _ in range(8):
        a, b = reference.block(0), changed.block(0)
        exact &= np.array_equal(a, b)
        audible |= bool(a[2].any())
        exact &= reference.uc.mem_read(voice + 0x230, 36) == changed.uc.mem_read(voice + 0x230, 36)
        exact &= reference.uc.mem_read(symbols["ck_chord_live"], 24) == changed.uc.mem_read(symbols["ck_chord_live"], 24)
    check(exact and audible and changed.call(symbols["ck_audio_controls"], 2) == 1 | (1 << 8),
          "préparer T6 sans TRIG : queue audible, PCM/enveloppe/accord identiques à la queue laissée seule")
    _key(ui, 1, True)
    valid = ui.calls == [_on(2, 24)]
    transfer(changed)
    changed.block(4)
    changed.block(0)
    changed.block(0)
    actual = tuple(int.from_bytes(changed.uc.mem_read(voice + 0x50 + 0x78 * i, 4), "big") for i in range(4))
    expected = frequency_ratios(expected_notes(0, 0, 1, 2, 6))
    valid &= all(abs(a - b) <= 4 for a, b in zip(actual, expected))
    check(valid and changed.call(symbols["ck_audio_controls"], 2) == 1 | (6 << 8),
          "T6 préparé→TRIG : une seule note, rapports V7 natifs dès la nouvelle attaque")
    _pad(ui, 6, False)
    transfer(changed)
    check(not ui.calls and changed.call(symbols["ck_audio_controls"], 2) == 1 | (6 << 8)
          and not ui.bad and not any(t.unmapped for t in twins),
          "T préparé relâché après TRIG : accord conservé, aucun accès mémoire hors du banc")


def run(stock, image, symbols, extra_code, check):
    """Exécute six pads sur six pistes, puis des relâchements sans retour."""
    del stock
    symbols = {name: int(value, 16) if isinstance(value, str) else value
               for name, value in symbols.items()}
    ui, _, selected, _, _ = _ui_rig(image, symbols)
    word = config_word(root=24, extensions=(1,) * 7)
    for track in range(6):
        ui.call(symbols["ck_ui_config_set"], track, word)
    header_before = bytes(ui.uc.mem_read(HEADER, 64))

    engine = E.Engine(image, extra_code=extra_code)
    config = NativeAudioConfig(engine)
    engine.uc.mem_map(0x93100000, 0x10000)
    config.write(config.ROOT + 5192 + 60, HEADER)

    def transfer():
        engine.uc.mem_write(HEADER, bytes(ui.uc.mem_read(HEADER, 64)))
        for name, size in (("held_pads", 6), ("live_modifiers", 48)):
            engine.uc.mem_write(symbols[name], bytes(ui.uc.mem_read(symbols[name], size)))
        engine.uc.mem_write(symbols["held"], bytes(ui.uc.mem_read(symbols["held"], 256)))

    transfer()
    for track in range(6):
        engine.machine_defaults(track, "CHORD")
        engine.set(track, note=24, pitch=64, finetune=64, shape=3,
                   color=(32, 64, 110)[track % 3], decay=100)
    engine.block(63)
    # Le moteur traite le trig avec un bloc de délai avant son enveloppe.
    for _ in range(8):
        engine.block(0)

    flags = []

    def observe_update(uc, address, size, data):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        voice = int.from_bytes(uc.mem_read(sp + 8, 4), "big")
        flags.append(int.from_bytes(uc.mem_read(voice + 0x38, 4), "big"))

    engine.uc.hook_add(UC_HOOK_CODE, observe_update, begin=0x400AAE88, end=0x400AAE88)

    def ratios(track):
        voice = E.VOICE0 + track * E.VSTRIDE
        return tuple(int.from_bytes(engine.uc.mem_read(voice + 0x50 + 0x78 * i, 4), "big")
                     for i in range(4))

    def block_matches(track, modifier, attack=False):
        others = {t: ratios(t) for t in range(6) if t != track}
        transfer()
        actual_control = engine.call(symbols["ck_audio_controls"], track)
        on = off = 0
        for kind, args in ui.calls:
            if kind == "on":
                on |= 1 << args[0]
                engine.set(args[0], note=args[1])
            elif kind == "off":
                off |= 1 << args[0]
        ui.calls.clear()
        flags.clear()
        engine.block(on, off)
        engine.block(0)
        pcm = engine.block(0)
        notes = expected_notes(0, 0, 1, track % 3, modifier)
        target = frequency_ratios(notes)
        actual = ratios(track)
        return (actual_control == 1 | (modifier << 8)
                and all(abs(a - b) <= 4 for a, b in zip(actual, target))
                and all(ratios(t) == before for t, before in others.items())
                and bool(pcm[track].any())
                and on == ((1 << track) if attack else 0)
                and flags == [0] * 6 + [int(attack and t == track) for t in range(6)] + [0] * 6)

    for track in range(6):
        selected[0] = track
        _key(ui, 1, True)
        valid = block_matches(track, 0, attack=True)
        for pad in range(1, 7):
            _pad(ui, pad, True, secondary=True)
            valid &= ui.calls == [("off", (track, 24, 64)), _on(track, 24)]
            valid &= block_matches(track, pad, attack=True)
            _pad(ui, pad, False, secondary=True)
            valid &= not ui.calls and block_matches(track, pad)
        check(valid, f"pads→DSP piste {track + 1} : six gestes réels, nouvelle attaque, notes et PCM conservés au relâchement")
        _key(ui, 1, False)

    selected[0] = 2
    _key(ui, 1, True)
    valid = block_matches(2, 0, attack=True)
    for pad, down, expected in ((1, True, 1), (2, True, 2), (6, True, 6),
                                 (2, False, 6), (6, False, 6), (4, True, 4),
                                 (4, False, 4), (1, False, 4)):
        _pad(ui, pad, down, secondary=True)
        valid &= block_matches(2, expected, attack=down)
    check(valid, "pads→DSP : pile T1/T2/T6 puis SUS7, attaque à chaque appui, aucun retrigger au retrait")

    _pad(ui, 3, True)
    valid = block_matches(2, 3, attack=True)
    ui.call(symbols["ck_ui_clear_modifiers"], 2, HEADER)
    valid &= block_matches(2, 0)
    _pad(ui, 3, False)
    valid &= not ui.calls and block_matches(2, 0)
    check(valid, "pads→DSP : annulation ciblée restaure le repos, relâchement capturé sans note parasite")

    # Régression du retour utilisateur : une modification des rapports seule
    # conserve une queue presque éteinte. Un nouvel événement natif doit rendre
    # une attaque audible, sans modifier le gain ni forcer les états du DSP.
    engine.set(2, decay=16)
    _key(ui, 1, True)
    check(block_matches(2, 0, attack=True), "attaque T : départ du test de décroissance par un vrai TRIG")
    envelope_address = E.VOICE0 + 2 * E.VSTRIDE + 0x230
    initial_envelope = bytes(engine.uc.mem_read(envelope_address, 36))

    def rms():
        samples = np.concatenate([engine.block(0)[2] for _ in range(8)]).astype(float)
        return float(np.sqrt(np.mean(samples * samples)))

    fresh = rms()
    elapsed, tail = 0, fresh
    while elapsed < 1024 and tail > fresh / 100:
        tail = rms()
        elapsed += 8
    _pad(ui, 1, True)
    events = ui.calls[:]
    # Sans transmettre les nouvelles notes, reproduire l'ancien comportement.
    transfer()
    before_attack = rms()
    ui.calls[:] = events
    valid = block_matches(2, 1, attack=True)
    same_envelope = bytes(engine.uc.mem_read(envelope_address, 36)) == initial_envelope
    restarted = rms()
    improvement = 20 * math.log10(max(restarted, 1) / max(before_attack, 1))
    check(valid and fresh > 0 and before_attack < fresh / 20
          and restarted > fresh / 4 and improvement > 20 and same_envelope,
          f"attaque T : après {elapsed * 32 / 48:.1f} ms, rapports seuls RMS={before_attack:.0f}, "
          f"nouvelle attaque RMS={restarted:.0f} (+{improvement:.1f} dB), enveloppe identique au TRIG neuf")
    _pad(ui, 1, True)
    check(not ui.calls and block_matches(2, 1), "attaque T : maintien du pad sans deuxième attaque DSP")
    _pad(ui, 1, False)
    check(not ui.calls and block_matches(2, 1), "attaque T : accord conservé sans deuxième attaque DSP")
    _key(ui, 1, True)
    check(block_matches(2, 0, attack=True), "pads→DSP : rejouer le même TRIG retrouve son accord original")

    # Deux DSP au même instant : l'un garde T6 physiquement tenu, l'autre
    # reçoit son relâchement réel. Le PCM et l'enveloppe doivent être identiques.
    _pad(ui, 6, True)
    twins = []
    for _ in range(2):
        twin = E.Engine(image, extra_code=extra_code)
        native = NativeAudioConfig(twin)
        twin.uc.mem_map(0x93100000, 0x10000)
        native.write(native.ROOT + 5192 + 60, HEADER)
        twin.uc.mem_write(HEADER, bytes(ui.uc.mem_read(HEADER, 64)))
        for name, size in (("held_pads", 6), ("live_modifiers", 48), ("held", 256)):
            twin.uc.mem_write(symbols[name], bytes(ui.uc.mem_read(symbols[name], size)))
        for track in range(6):
            twin.machine_defaults(track, "CHORD")
            twin.set(track, note=24, pitch=64, finetune=64, shape=3, color=110, decay=100)
        twin.block(4)
        for _ in range(8):
            twin.block(0)
        twins.append(twin)
    _pad(ui, 6, False)
    released = twins[1]
    for name, size in (("held_pads", 6), ("live_modifiers", 48), ("held", 256)):
        released.uc.mem_write(symbols[name], bytes(ui.uc.mem_read(symbols[name], size)))
    exact = not ui.calls
    for _ in range(16):
        exact &= np.array_equal(twins[0].block(0), released.block(0))
        exact &= twins[0].uc.mem_read(envelope_address, 36) == released.uc.mem_read(envelope_address, 36)
        exact &= twins[0].uc.mem_read(symbols["ck_chord_live"], 24) == released.uc.mem_read(symbols["ck_chord_live"], 24)
    check(exact and not any(t.unmapped for t in twins),
          "T6 relâché contre T6 tenu : PCM, enveloppe et accord affiché identiques sur 16 blocs natifs")
    check(bytes(ui.uc.mem_read(HEADER, 64)) == header_before
          and not ui.bad and not engine.unmapped,
          "pads→DSP : en-tête identique après retour des réglages, aucun accès mémoire hors du banc")
