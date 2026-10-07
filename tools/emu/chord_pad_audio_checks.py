"""Lien séquentiel des vrais gestes UI au vrai DSP CHORD (notes/40).

Le banc UI exécute PadEvent, le routage et les setters persistants. Ses 72 octets
held_pads et son en-tête sont transférés sans modification dans un second banc
DSP possédant la même adresse d'en-tête. Aucun getter musical n'est remplacé.
Ce transfert séquentiel ne simule pas l'ordonnancement concurrent UI/IRQ ; il
prouve que l'état produit par les événements gouverne réellement l'accord tenu.
Les drapeaux de déclenchement sont observés à l'entrée du vrai update CHORD.
"""
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import mcengine as E
from chord_audio_checks import NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from chord_ui_checks import HEADER, _ui_rig, _key, _pad
from probe_chord_keys import frequency_ratios


def run(stock, image, symbols, extra_code, check):
    """Exécute six pads sur six pistes, puis une pile avec retours successifs."""
    del stock
    symbols = {name: int(value, 16) if isinstance(value, str) else value
               for name, value in symbols.items()}
    ui, _, selected, _, _ = _ui_rig(image, symbols)
    ui.call(symbols["ck_ui_revision_set"], 1)
    word = config_word(root=24, extensions=(1,) * 7)
    for track in range(6):
        ui.call(symbols["ck_ui_config_set"], track, word)
        ui.call(symbols["ck_ui_pad_mode_set"], track, 1)
    header_before = bytes(ui.uc.mem_read(HEADER, 64))

    engine = E.Engine(image, extra_code=extra_code)
    config = NativeAudioConfig(engine)
    engine.uc.mem_map(0x93100000, 0x10000)
    config.write(config.ROOT + 5192 + 60, HEADER)
    state_address = symbols["held_pads"]

    def transfer():
        engine.uc.mem_write(HEADER, bytes(ui.uc.mem_read(HEADER, 64)))
        engine.uc.mem_write(state_address, bytes(ui.uc.mem_read(state_address, 72)))

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

    def block_matches(track, modifier):
        others = {t: ratios(t) for t in range(6) if t != track}
        transfer()
        actual_control = engine.call(symbols["ck_audio_controls"], track)
        flags.clear()
        pcm = engine.block(0)
        notes = expected_notes(0, 0, 1, track % 3, modifier)
        target = frequency_ratios(notes)
        actual = ratios(track)
        return (actual_control == 1 | (modifier << 8)
                and all(abs(a - b) <= 4 for a, b in zip(actual, target))
                and all(ratios(t) == before for t, before in others.items())
                and bool(pcm[track].any())
                and len(flags) == 6 and not any(flags))

    for track in range(6):
        selected[0] = track
        _key(ui, 1, True)
        valid = block_matches(track, 0)
        for pad in range(1, 7):
            _pad(ui, pad, True, secondary=True)
            valid &= not ui.calls and block_matches(track, pad)
            _pad(ui, pad, False, secondary=True)
            valid &= not ui.calls and block_matches(track, 0)
        check(valid, f"pads→DSP piste {track + 1} : six gestes réels, notes attendues, retour, PCM audible, aucun retrigger")
        _key(ui, 1, False)

    selected[0] = 2
    _key(ui, 1, True)
    valid = True
    for pad, down, expected in ((1, True, 1), (2, True, 2), (6, True, 6),
                                 (2, False, 6), (6, False, 1), (4, True, 4),
                                 (4, False, 1), (1, False, 0)):
        _pad(ui, pad, down, secondary=True)
        valid &= not ui.calls and block_matches(2, expected)
    check(valid, "pads→DSP : pile T1/T2/T6 puis SUS7, retrait ancien, précédent restauré et retour sans retrigger")

    _pad(ui, 3, True)
    valid = block_matches(2, 3)
    ui.call(symbols["ck_ui_pad_mode_set"], 2, 0)
    valid &= block_matches(2, 0)
    _pad(ui, 3, False)
    valid &= not ui.calls and block_matches(2, 0)
    check(valid, "pads→DSP : sortie HARMONY vers TRACK restaure le repos, relâchement capturé sans note parasite")
    ui.call(symbols["ck_ui_pad_mode_set"], 2, 1)
    check(bytes(ui.uc.mem_read(HEADER, 64)) == header_before
          and not ui.bad and not engine.unmapped,
          "pads→DSP : en-tête identique après retour des réglages, aucun accès mémoire hors du banc")
