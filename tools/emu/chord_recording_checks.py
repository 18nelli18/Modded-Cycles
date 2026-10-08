"""Prise TRIG→T puis relecture dans la vraie file audio OS (notes/40 §21).

Le banc choisit le pas quantifié et transfère l'état UI entre deux émulateurs.
Recorder, sauvegarde, file audio, arbitrage, locks et DSP restent natifs.
L'ordonnancement concurrent et les périphériques ne sont pas simulés.
"""
import struct

import mcengine as E
from test_arp import Audio, live
from chord_audio_checks import NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from chord_plock_checks import PlockRig, SLOT
from chord_lock_audio_checks import RAW, EXTRACT, SMOOTH
from probe_chord_keys import UPDATE, frequency_ratios
from probe_chord_storage import PROJECT, B1, B2, SERIAL


def run(stock, patched, symbols, extra_code, check):
    rig = PlockRig(stock, patched, symbols)
    view, notes, event = 0x92060000, 0x92061000, 0x92062000
    for offset, pointer in ((148, notes), (152, notes), (156, notes + 0xa00)):
        rig.word(view + offset, pointer)
    held, events = set(), []
    rig.stub(0x4007FAF4, lambda args: int(args[0] in held))
    rig.stub(0x40015AC4, lambda args: 97)
    rig.stub(0x40075F3C, lambda args: 0)
    rig.stub(0x40016E90, lambda args: 0)
    rig.stub(0x4008171E, lambda args: events.append(args[:3]) or 0)
    rig.stub(0x4008145E, lambda args: 0)
    rig.call("ck_ui_config_set", 0, config_word(root=24, extensions=(1,) * 7))

    def key(down):
        (held.add if down else held.discard)(16)
        rig.call(0x4007238C, event, 16, int(down), 123, 127)
        rig.call("ck_ui_key", view, event)

    def record(step):
        assert len(events) == 1, events
        track, note, velocity = events.pop()
        rig.call(0x40012158, PROJECT, track, note, velocity, 0,
                 step, 0, 0, 0xFFFFFFFF)

    rig.live(True, 0)
    key(True)
    record(0)
    rig.pad(1, True)
    # Le recorder peut choisir le pas suivant alors que l'horloge UI indique
    # encore le premier : le pad ne doit pas écrire aux deux endroits.
    record(1)
    check([rig.get(0, s) for s in (0, 1)] == [0, 1],
          "live rec : TRIG puis T1 quantifié au pas suivant conservent HARMONY 0 puis 1")
    rig.pad(1, False)
    key(False)
    rig.live(False)
    header = rig.call("ck_ui_header")
    saved_header = rig.bytes(header, 64)
    captured = {name: rig.bytes(symbols[name], size) for name, size in
                (("held", 256), ("held_pads", 6), ("live_modifiers", 48),
                 ("prepared_modifiers", 48))}
    rig.call(0x4005BA0A, SERIAL, B1, 0)
    rig.call(0x4005B894, B2, SERIAL, 0)
    rig.bind(B2, initialize=False)
    check([rig.get(0, s) for s in (0, 1)] == [0, 1],
          "live rec : save/load conserve séparément l'accord initial et celui de T1")

    audio = Audio(patched)
    e = audio.e
    e.emac.install(E._emac_instrs(bytes(patched), [(a, a + n) for a, n in extra_code]))
    # Audio a déjà mappé la BSS ; réutiliser le constructeur de configuration
    # sans demander un second mapping de la même plage.
    config = NativeAudioConfig.__new__(NativeAudioConfig)
    config.engine = e
    config.write(0x40fe4228, config.ROOT)
    config.write(0x40a7887c, config.ACTIVE)
    config.select(0)
    e.uc.mem_map(0x92000000, 0x02000000)
    e.uc.mem_write(header, saved_header)
    config.write(config.ROOT + 5192 + 60, header)
    for name, data in captured.items():
        e.uc.mem_write(symbols[name], data)
    e.machine_defaults(0, "CHORD")
    e.set(0, note=24, pitch=64, finetune=64, shape=3, color=32)
    e._write_params()

    def sequence(modifier=None, source=1, on=1, lock_only=False, run=True):
        locks = 0
        if modifier is not None:
            locks = e.call(0x40091E66)
            e.uc.mem_write(RAW, b"\xff" * 68)
            e.uc.mem_write(RAW + 2 * SLOT, struct.pack(">H", modifier))
            e.call(EXTRACT, locks, RAW, 0, 0)
        note = e.call(0x40091EB6)
        for offset, value in ((4, on), (8, 0), (12, source), (28, 24),
                              (40, 1 if lock_only else 0x10081), (60, 127), (72, locks)):
            audio.w32(note + offset, value)
        e.call(0x40092116, note)
        return audio.run() if run else None

    def matches(modifier):
        params = e.call(SMOOTH, E.PARAMS) + 14
        e.emac.macsr = 0xa0
        e.call(UPDATE, 24 << 16, E.VOICE0, params)
        actual = tuple(audio.r32(E.VOICE0 + 0x50 + 0x78 * i) for i in range(4))
        expected = frequency_ratios(expected_notes(0, 0, 1, 0, modifier))
        return all(abs(a - b) <= 2 for a, b in zip(actual, expected))

    check(matches(1), "avant relecture : la queue garde T1 après les relâchements")
    # Valeurs connues ici pour isoler la priorité audio de l'écriture quantifiée.
    # La prise et son save/load sont contrôlés séparément ci-dessus.
    check(sequence(0) == 1 and matches(0),
          "file audio : première note EXT rejouée malgré le dernier pad T1 conservé")
    check(sequence(1) == 1 and matches(1),
          "file audio : deuxième note rejouée avec son propre accord T1")
    check(sequence(on=2) == 0 and matches(1),
          "file audio : note-off du séquenceur ne restaure pas un ancien geste live")
    for name, data in captured.items():
        e.uc.mem_write(symbols[name], data)
    check(sequence(0, lock_only=True) == 0 and matches(0),
          "file audio : lock-only EXT reprend aussi la main sans nouvelle attaque")
    for name, data in captured.items():
        e.uc.mem_write(symbols[name], data)
    check(sequence(source=2) == 1 and matches(1),
          "file audio : une attaque live conserve sa transformation T1")
    live(audio, True)
    check(sequence(0) == 0 and matches(1),
          "file audio : un trig séquencé rejeté pendant la prise ne retire pas T1")
    live(audio, False)
    sequence(on=2, source=2)
    check(sequence() == 1 and matches(0),
          "file audio : note sans lock retrouve EXT après le jeu live")
    for name, data in captured.items():
        e.uc.mem_write(symbols[name], data)
    sequence(0, run=False)
    sequence(source=2, run=False)
    check(audio.run() == 1 and matches(1),
          "file audio : séquence puis note live dans le même bloc conservent le nouveau T1")
    sequence(on=2, source=2)
    check(matches(1), "file audio : la fin live garde sa queue T1 après la relecture")
    check(not e.unmapped, "prise→file→DSP : aucun accès mémoire hors du banc")
