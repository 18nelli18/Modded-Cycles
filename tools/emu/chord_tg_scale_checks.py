"""Coexistence Chord Keys / Scale Lock sur le code final Model-TG (notes/40).

Les entrées note-on/off, les deux détours TG et leur snap_note sont exécutés.
Les files audio et recorder sont observées APRÈS leur construction native ;
l'horloge/quantification, les objets de machine et les observateurs sont ceux
du banc PlockRig. La note observée est remise au vrai recorder puis au save/load.
Les adresses de Scale/Key sont décodées dans le payload final, sans dépendre
d'un clone Model-TG ni de symboles externes. Aucun transport MIDI ni périphérique
physique n'est simulé. Durée habituelle : quelques secondes.
"""
from chord_audio_checks import config_word
from chord_plock_checks import PlockRig
from probe_chord_storage import BASE, B1, B2, SERIAL, PROJECT

ON, OFF = 0x4008171e, 0x4008145e
SITES = ((0x40081734, 8), (0x4008146c, 8))
FOLDS = ((0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 8, 10),
         (0, 2, 3, 5, 7, 9, 10), (0, 2, 4, 7, 9))


def _tg_state(image):
    """Résout les trois lectures PC-relative du vrai snap_note Model-TG."""
    hook = 0x4008173c - BASE
    assert image[hook:hook + 2] == b"\x4e\xf9", "Scale Lock TG absent"
    entry = int.from_bytes(image[hook + 2:hook + 6], "big")
    code = image[entry - BASE:entry - BASE + 74]
    calls = [i for i in range(0, len(code) - 3, 2) if code[i:i + 2] == b"\x4e\xba"]
    assert len(calls) == 1, "Appel snap_note TG ambigu"
    call = calls[0]
    snap = entry + call + 2 + int.from_bytes(code[call + 2:call + 4], "big", signed=True)
    code = image[snap - BASE:snap - BASE + 106]
    assert code[:4] == b"\x2f\x0d\x4a\x3a", "Prologue snap_note TG inattendu"
    scale = snap + 4 + int.from_bytes(code[4:6], "big", signed=True)
    reads = [i for i in range(0, len(code) - 7, 2)
             if code[i:i + 2] == b"\x1c\x3a" and code[i + 4:i + 8] == b"\xd2\x86\x26\x01"]
    assert len(reads) == 1, "Lecture de Key TG ambiguë"
    key = snap + reads[0] + 2 + int.from_bytes(code[reads[0] + 2:reads[0] + 4], "big", signed=True)
    assert key == scale + 1, "Disposition Scale/Key TG inattendue"
    return scale, key


def _rig(reference, patched, symbols, bypass=True):
    rig = PlockRig(reference, patched, symbols)
    if not bypass:
        # Le témoin conserve le stockage de la fixture ; seules les deux
        # entrées de décision CK sont remises aux instructions TG/stock.
        for address, size in SITES:
            rig.uc.mem_write(address, reference[address - BASE:address - BASE + size])
        rig.uc.ctl_flush_tb()
    rig.audio_events, rig.recorder_events = [], []

    def capture(args, target, size):
        target.append(rig.bytes(args[0], size))
        return 0

    def clock(args):
        rig.uc.mem_write(args[2], b"\0\0")
        return 0

    rig.stub(0x40054828, lambda a: 0)
    rig.stub(0x400813e2, lambda a: 0)
    rig.stub(0x40056178, clock)
    rig.stub(0x4005894a, lambda a: capture(a, rig.audio_events, 56))
    rig.stub(0x40080bf6, lambda a: capture(a, rig.recorder_events, 32))
    rig.word(0x8000184c, 2000)
    # Valeurs natives : aucune note tenue, aucun début mémorisé.
    rig.uc.mem_write(0x40fb680c, b"\xff" * (6 * 128 * 4))
    return rig


def _notes(rig):
    return [(int.from_bytes(event[:4], "big"),
             int.from_bytes(event[4:8], "big"),
             int.from_bytes(event[12:16], "big")) for event in rig.audio_events]


def _pair(rig, track, note):
    rig.audio_events.clear()
    rig.recorder_events.clear()
    rig.call(ON, track, note, 97, 64, 0, 0xffffffff, 0xffffffff)
    rig.call(OFF, track, note, 64)
    return _notes(rig)


def _fold(note, scale, key):
    if not scale or note == 127:
        return note
    tones = FOLDS[scale - 1]
    octave, degree = divmod(note - 52, len(tones))
    return 48 + 12 * octave + tones[degree] + key


def run_stock(reference, patched, symbols, check):
    """Sans Model-TG, les deux nouvelles accroches gardent les événements stock."""
    original = _rig(reference, patched, symbols, bypass=False)
    changed = _rig(reference, patched, symbols)
    same, count = True, 0
    for machine in (5, 4):
        for enabled in (False, True):
            for rig in (original, changed):
                rig.machine = machine
                for track in range(6):
                    rig.call("ck_ui_config_set", track, config_word(enabled=enabled))
            for track in range(6):
                for note in (0, 24, 48, 59, 74, 127, 128, 0xffffffff):
                    before = _pair(original, track, note)
                    after = _pair(changed, track, note)
                    same &= (before == after and original.audio_events == changed.audio_events
                             and original.recorder_events == changed.recorder_events)
                    count += 1
    check(same, f"sans Model-TG : {count} paires ON/OFF, Keys ON/OFF et CHORD/TONE, événements stock inchangés")


def run(reference, patched, symbols, check):
    scale_address, key_address = _tg_state(reference)
    original = _rig(reference, patched, symbols, bypass=False)
    changed = _rig(reference, patched, symbols)
    tested, exact, transformed = 0, True, False
    first = None
    for scale in range(5):
        for key in (0, 5, 11):
            for rig in (original, changed):
                rig.uc.mem_write(scale_address, bytes([scale]))
                rig.uc.mem_write(key_address, bytes([key]))
            for track in range(6):
                for note in (24, 48, 50, 59, 74, 127):
                    before = _pair(original, track, note)
                    after = _pair(changed, track, note)
                    folded = _fold(note, scale, key)
                    expected_before = ([(track, folded, 1), (track, folded, 2)]
                                       if 0 <= folded <= 127 else [])
                    expected_after = [(track, note, 1), (track, note, 2)]
                    good = before == expected_before and after == expected_after
                    exact &= good
                    transformed |= before != after
                    if not good and first is None:
                        first = (scale, key, track, note, before, after)
                    tested += 1
    check(exact and transformed,
          f"Scale Lock TG : {tested} paires ON/OFF, quatre gammes + OFF, six pistes CHORD Keys, notes exactes ({first})")

    for enabled, machine, label in ((False, 5, "Keys OFF"), (True, 4, "TONE"),
                                    (True, 6, "Sampler"), (True, 10, "moteur Syntakt")):
        same, folded = True, False
        for rig in (original, changed):
            rig.machine = machine
            rig.uc.mem_write(scale_address, b"\x01")
            rig.uc.mem_write(key_address, b"\x05")
            for track in range(6):
                rig.call("ck_ui_config_set", track, config_word(enabled=enabled))
        for track in range(6):
            for note in (48, 52, 59, 74, 127, 128):
                before = _pair(original, track, note)
                after = _pair(changed, track, note)
                same &= before == after and original.recorder_events == changed.recorder_events
                folded |= bool(after and after[0][1] != note)
        check(same and folded, f"Scale Lock TG : {label} garde les notes et les événements recorder natifs")

    changed.machine = 5
    for track in range(6):
        changed.call("ck_ui_config_set", track, config_word())
    rejected = all(not _pair(changed, track, note)
                   for track in range(6) for note in (128, 255, 0xffffffff))
    check(rejected, "Scale Lock TG : CHORD Keys conserve le rejet stock des notes hors 0..127")
    _record_and_release(reference, patched, symbols, scale_address, key_address, check)


def _record_and_release(reference, patched, symbols, scale_address, key_address, check):
    rig = _rig(reference, patched, symbols)
    rig.uc.mem_write(scale_address, b"\x04")
    rig.uc.mem_write(key_address, b"\x0b")
    view, notes, event = 0x92060000, 0x92061000, 0x92062000
    for offset, pointer in ((148, notes), (152, notes), (156, notes + 0xa00)):
        rig.word(view + offset, pointer)
    held = set()
    rig.stub(0x4007faf4, lambda a: int(a[0] in held))
    rig.stub(0x40015ac4, lambda a: 97)
    rig.stub(0x40075f3c, lambda a: 0)
    rig.stub(0x40016e90, lambda a: 0)

    def key(number, down):
        (held.add if down else held.discard)(15 + number)
        rig.call(0x4007238c, event, 15 + number, int(down), 123, 127)
        rig.call("ck_ui_key", view, event)

    rig.live(True, 0)
    key(3, True)
    # L'événement recorder réellement construit par note_on porte note +16,
    # vélocité +17, piste +8 ; le banc ne choisit que son pas quantifié.
    recorded = rig.recorder_events[-1]
    track, note, velocity = recorded[8], recorded[16], recorded[17]
    rig.call(0x40012158, PROJECT, track, note, velocity, 0, 0, 0, 0, 0xffffffff)
    initial = _notes(rig) == [(0, 52, 1)] and (track, note, velocity) == (0, 52, 97)
    rig.call(0x4005ba0a, SERIAL, B1, 0)
    rig.call(0x4005b894, B2, SERIAL, 0)
    # Une désactivation avant le release ne doit pas transformer la fin de
    # cette note en un autre degré TG et laisser un compteur de note bloqué.
    rig.call("ck_ui_config_set", 0, config_word(enabled=False))
    key(3, False)
    check(initial and _notes(rig) == [(0, 52, 1), (0, 52, 2)] and
          rig.word(0x40fb5c0c + 52 * 4) == 0 and rig.word(0x40fb57ec) == 0,
          "Scale Lock TG : vraie touche CHORD, événement audio/recorder chromatique et note-off fidèle après Keys OFF")
    rig.bind(B2, initialize=False)
    # NOTE est l'octet par pas lu par l'accesseur natif, hors des lanes P-lock.
    check((rig.call(0x40015eaa, rig.track(0), 0) & 255) == 52 and
          bool(rig.call(0x40015c20, rig.track(0), 0) & 255),
          "Scale Lock TG : le vrai recorder puis save/load gardent la hauteur CHORD 52 au pas enregistré")

    for source in ("API", "relais KeyboardView stock"):
        for chord_first in (False, True):
            rig.audio_events.clear()
            rig.recorder_events.clear()
            rig.machine = 5
            key(3, True)
            rig.machine = 4
            if source == "API":
                rig.call(ON, 0, 52, 97, 64, 0, 0xffffffff, 0xffffffff)
            else:
                rig.call(0x40019e7a, view, 0, 52, 97, 0xffffffff)
            if chord_first:
                key(3, False)
            if source == "API":
                rig.call(OFF, 0, 52, 64)
            else:
                # Même retour direct 0x40019cba que le release CHORD, mais
                # appel du helper depuis le banc, hors de notre wrapper.
                rig.call(0x40019c84, view, 0, 52)
            if not chord_first:
                key(3, False)
            releases = [(0, n, 2) for n in ((52, 59) if chord_first else (59, 52))]
            check(_notes(rig) == [(0, 52, 1), (0, 59, 1)] + releases and
                  rig.word(0x40fb5c0c + 52 * 4) == rig.word(0x40fb5c0c + 59 * 4) ==
                  rig.word(0x40fb57ec) == 0,
                  f"Scale Lock TG : CHORD vers TONE, note égale {source}, "
                  f"release {'CHORD' if chord_first else source} d'abord, aucune note bloquée")
