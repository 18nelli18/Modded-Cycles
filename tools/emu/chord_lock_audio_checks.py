"""Relecture des P-locks HARMONY dans le séquenceur et le DSP réels.

Le banc fournit les lignes de locks déjà chargées ; extraction des événements,
application, bitmap de présence, lissage, retour au son et update CHORD restent
natifs. Les gestes et l'aller-retour de sauvegarde ont leur preuve séparée.
"""
import struct

import mcengine as E
from chord_audio_checks import AudioRunner, NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from probe_chord_keys import UPDATE, frequency_ratios


RAW, EVENT, SOUND = 0x420c0000, 0x420c2000, 0x420c3000
EXTRACT, APPLY, RESET = 0x4005487c, 0x400583da, 0x40058308
SET_PARAM, SMOOTH = 0x400583ba, 0x40058474
LOCK_MASK = 0x423087f8


def run_lock_audio_checks(stock, patched, symbols, extra_code, check):
    """Suit les vraies valeurs de lock jusqu'aux rapports et à l'instantané."""
    runner = AudioRunner(patched, extra_code=extra_code)
    e = runner.engine
    config = NativeAudioConfig(e)
    active = config_word(root=24, extensions=(1,) * 7)
    config.configure([active] * 6)
    e.uc.mem_write(SOUND, bytes(100))

    def word(address, size=4):
        return int.from_bytes(e.uc.mem_read(address, size), "big")

    def setup(track, color):
        e.machine_defaults(track, "CHORD")
        e.set(track, note=24, pitch=64, finetune=64, shape=3, color=color)
        e._write_params()
        # L'état du lisseur reçoit le même son de base par son setter natif.
        for index in range(238):
            value = int.from_bytes(e.uc.mem_read(E.PARAMS + 2 * index, 2),
                                   "big", signed=True)
            e.call(SET_PARAM, index, value, E.PARAMS)

    def apply(track, modifier):
        e.uc.mem_write(RAW, b"\xff" * 68)
        e.uc.mem_write(RAW + 2 * 23, struct.pack(">H", modifier))
        e.call(EXTRACT, EVENT, RAW, 0, 0)
        e.call(APPLY, track, EVENT, E.PARAMS)

    def update(track):
        e.emac.macsr = 0xa0
        smoothed = e.call(SMOOTH, E.PARAMS)
        params = smoothed + 14 + 66 * track
        voice = E.VOICE0 + E.VSTRIDE * track
        before = bytes(e.uc.mem_read(params, 66))
        e.call(UPDATE, 24 << 16, voice, params)
        assert bytes(e.uc.mem_read(params, 66)) == before, "paramètres lissés modifiés"
        ratios = tuple(word(voice + 0x50 + 0x78 * index) for index in range(4))
        packet = word(symbols["ck_chord_live"] + 4 * track)
        return ratios, packet, word(params + 2 * 23, 2)

    def matches(track, modifier, palette):
        ratios, packet, lane = update(track)
        notes = expected_notes(0, 0, 1, palette, modifier)
        expected_packet = 0x80000000 | 24 | ((notes[0] % 12) << 27)
        expected_packet |= sum(n << (7 + 5 * i) for i, n in enumerate(notes))
        expected_ratios = frequency_ratios(notes)
        return (packet == expected_packet and
                all(abs(a - b) <= 2 for a, b in zip(ratios, expected_ratios))), lane

    replay, reset_ok, count = True, True, 0
    for track in range(6):
        for palette, color in enumerate((32, 64, 110)):
            setup(track, color)
            for modifier in (0, 1, 2, 3, 4, 5, 6, 2, 0):
                apply(track, modifier)
                ok, lane = matches(track, modifier, palette)
                replay &= (ok and lane == modifier and word(EVENT + 8) == 1
                           and word(EVENT + 20, 2) == 23
                           and bool(word(LOCK_MASK + 8 * track) & (1 << 23)))
                count += 1
            apply(track, 6)
            e.call(RESET, track, E.PARAMS, SOUND)
            ok, lane = matches(track, 0, palette)
            reset_ok &= ok and lane == 0 and word(LOCK_MASK + 8 * track) == 0
    check(replay and count == 162,
          "P-lock→DSP : 162 relectures, six pistes × trois palettes, extraction/application/lissage natifs et instantané exact")
    check(reset_ok,
          "P-lock→DSP : retour natif au son sans lock, slot et bitmap remis à zéro, accord EXT restauré")

    # Une valeur parasite sans bit de présence n'est pas un P-lock. Les valeurs
    # hors domaine présentes dans une ligne corrompue restent aussi inactives.
    guarded = True
    setup(0, 32)
    for modifier in range(1, 7):
        e.call(SET_PARAM, 7 + 23, modifier, E.PARAMS)
        ok, lane = matches(0, 0, 0)
        guarded &= ok and lane == modifier and word(LOCK_MASK) == 0
    for modifier in (7, 127, 0x7fff, 0xfffe):
        apply(0, modifier)
        ok, _ = matches(0, 0, 0)
        guarded &= ok
    check(guarded,
          "P-lock→DSP : valeur sans bitmap et lock hors 0..6 ignorés, aucun geste fantôme")

    # Keys OFF doit rester strictement stock même si le pattern contient des
    # locks HARMONY ; ils redeviennent audibles uniquement avec Keys ON.
    reference = AudioRunner(stock)
    setup(0, 32)
    config.configure([active & 0x7fffffff] * 6)
    apply(0, 6)
    ratios, packet, _ = update(0)
    check(ratios == reference.update(root=24, shape=3, color=32)[0] and packet == 0,
          "P-lock→DSP : Keys OFF conserve les rapports stock et efface l'instantané malgré un lock T6")
    config.configure([active] * 6)
    check(matches(0, 6, 0)[0],
          "P-lock→DSP : Keys ON retrouve le lock présent au prochain update")
    check(not e.unmapped and not reference.engine.unmapped,
          "P-lock→DSP : aucun accès mémoire hors du banc")
