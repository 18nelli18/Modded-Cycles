"""Accords MIDI depuis la vraie boucle audio et ses P-locks OS 1.13.

La file d'événements audio, l'arbitrage, la sélection du son et l'application
des locks sont natifs. Seul l'envoi à la tâche MIDI est observé ; son worker,
ses durées et ses pilotes ont leur preuve dans chord_midi_checks.py.
"""
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import mcengine as E
from test_arp import Audio, KIT, live
from chord_audio_checks import NativeAudioConfig, config_word
from chord_harmony_checks import expected_notes
from chord_lock_audio_checks import RAW, EXTRACT
from chord_plock_checks import SLOT

MIDI_QUEUE = 0x40fcb2ec
PARAMS = 0x800015ae


class EventRig(Audio):
    """Observe le message complet après les locks, sans remplacer le producteur."""

    def __init__(self, image, symbols):
        super().__init__(image)
        self.symbols, self.messages, self.param_snapshots = symbols, [], []
        self.config = NativeAudioConfig.__new__(NativeAudioConfig)
        self.config.engine = self.e
        self.config.write(0x40fe4228, self.config.ROOT)
        self.config.write(0x40a7887c, self.config.ACTIVE)
        self.config.select(0)
        for pattern in (0, 1):
            self.config.configure([config_word(root=24, extensions=(1,) * 7)] * 6,
                                  pattern)
        self.midi(0x3f)
        for track in range(6):
            self.e.machine_defaults(track, "CHORD")
            self.e.set(track, note=24, pitch=64, finetune=64, shape=0, color=32)
        self.e._write_params()
        for track in range(6):
            params = bytes(self.uc.mem_read(E.PARAMS + 14 + 66 * track, 66))
            self.uc.mem_write(PARAMS + 66 * track, params)
            self.uc.mem_write(KIT + 0x1c + 100 * track + 20, params)
        self.uc.hook_add(UC_HOOK_CODE, self._post,
                         begin=0x40001fba, end=0x40001fba)
        self.counting, self.instructions = False, 0
        self.uc.hook_add(UC_HOOK_CODE, self._count)

    def _count(self, uc, address, size, user):
        if self.counting:
            self.instructions += 1

    def run(self, limit=None):
        self.counting, self.instructions = True, 0
        try:
            return super().run(limit)
        finally:
            self.counting = False

    def midi(self, mask, pattern=0):
        self.config.write(self.config.HEADERS + 256 * pattern + 32,
                          0x434b0300 | mask)

    def _post(self, uc, address, size, user):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        queue, pointer = struct.unpack(">II", uc.mem_read(sp + 4, 8))
        if queue == MIDI_QUEUE:
            packet = bytes(uc.mem_read(pointer, 16))
            self.messages.append(packet)
            self.param_snapshots.append(struct.unpack(">33H", uc.mem_read(
                PARAMS + 66 * packet[8], 66)))
        uc.reg_write(mk.UC_M68K_REG_D0, 0)
        uc.reg_write(mk.UC_M68K_REG_PC, self.r32(sp))
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def sequence(self, track=0, modifier=None, color=None, source=1,
                 on=1, midi=True, lock_only=False, run=True):
        locks = 0
        if modifier is not None or color is not None:
            locks = self.e.call(0x40091e66)
            self.uc.mem_write(RAW, b"\xff" * 68)
            for slot, value in ((SLOT, modifier), (11, color)):
                if value is not None:
                    self.uc.mem_write(RAW + 2 * slot, struct.pack(">H", value))
            self.e.call(EXTRACT, locks, RAW, 0, 0)
        note = self.e.call(0x40091eb6)
        for offset, value in ((4, on), (8, track), (12, source), (28, 24),
                              (40, 1 if lock_only else 0x10081), (52, 91),
                              (60, 127), (72, locks)):
            self.w32(note + offset, value)
        self.uc.mem_write(note + 20, bytes([int(midi)]))
        self.uc.mem_write(note + 22, b"\x61\x00")
        self.e.call(0x40092116, note)
        return self.run() if run else None

    def clear(self):
        self.messages.clear()
        self.param_snapshots.clear()


def notes(rig):
    return [packet[9] for packet in rig.messages]


def run(stock, patched, symbols, extra_code, check):
    """Preuve ciblée du déplacement du producteur après les P-locks."""
    original, changed = (EventRig(image, symbols) for image in (stock, patched))
    changed.midi(0)
    same, costs = True, {}
    for track in range(6):
        for rig in (original, changed):
            rig.clear()
            mask = rig.sequence(track=track)
            same &= mask == 1 << track
            if track == 0:
                costs["stock" if rig is original else "ROOT"] = rig.instructions
        same &= changed.messages == original.messages and notes(changed) == [24]
    check(same, "MIDI ROOT : vraie file audio, six pistes, mêmes messages complets que le producteur stock")

    cost_rig = EventRig(patched, symbols)
    cost_rig.sequence()
    costs["CHORD"] = cost_rig.instructions
    check(notes(cost_rig) == [24, 28, 31, 35],
          "MIDI coût d'une attaque native de quatre notes, instructions émulées "
          f"(pas un pourcentage CPU matériel) : stock={costs['stock']}, "
          f"ROOT={costs['ROOT']}, CHORD={costs['CHORD']}")

    changed.midi(0x3f)
    exact = True
    for track in range(6):
        for modifier, color, palette in ((1, 32, 0), (6, 64, 1), (2, 110, 2), (0, 32, 0)):
            changed.clear()
            mask = changed.sequence(track=track, modifier=modifier, color=color << 8)
            expected = [24 + note for note in expected_notes(0, 0, 1, palette, modifier)]
            exact &= mask == 1 << track and notes(changed) == expected
            exact &= all(p[SLOT] == modifier and p[11] == color << 8
                         for p in changed.param_snapshots)
            exact &= all(p[0] == 1 and p[8] == track and p[10] == 97
                         and struct.unpack_from(">I", p, 12)[0] == 91
                         for p in changed.messages)
    check(exact, "MIDI CHORD : 24 trigs natifs, six pistes, COLOR/HARMONY appliqués avant les notes, vélocité et LEN conservés")

    changed.clear()
    off = changed.sequence(on=2) == 0 and not changed.messages
    lock_only = changed.sequence(modifier=5, lock_only=True) == 0 and not changed.messages
    changed.sequence(modifier=4, midi=False)
    check(off and lock_only and not changed.messages,
          "MIDI file audio : note-off, lock-only et MOut OFF n'ajoutent aucune attaque")

    # Le producteur live natif marque sa note pour l'audio seulement : le
    # clavier a déjà envoyé son MIDI, le hook de file ne doit pas le doubler.
    changed.clear()
    changed.send(1, 0, 24)
    live_mask = changed.run()
    live_once = live_mask == 1 and not changed.messages
    changed.send(2, 0, 24)
    changed.run()
    check(live_once and not changed.messages,
          "MIDI live : vrai producteur audio natif, aucun doublon à l'attaque ou au relâchement")

    # Une attaque du séquenceur rejetée pendant le live rec reste rejetée
    # avant d'atteindre la nouvelle accroche MIDI.
    changed.send(1, 0, 24)
    changed.run()
    live(changed, True)
    changed.clear()
    rejected = changed.sequence(modifier=6) == 0 and not changed.messages
    live(changed, False)
    check(rejected, "MIDI live rec : trig du séquenceur rejeté, aucun accord MIDI parasite")
    changed.send(2, 0, 24)
    changed.run()

    changed.clear()
    changed.uc.mem_write(0x40a78e24, b"\x00\x01")
    muted = changed.sequence(modifier=6) == 0 and not changed.messages
    changed.uc.mem_write(0x40a78e24, b"\x00\x00")
    check(muted, "MIDI mute : trig du séquenceur muet, aucune voix MIDI ajoutée")

    changed.clear()
    changed.config.select(1)
    changed.midi(0, pattern=1)
    changed.sequence(modifier=1)
    root_only = notes(changed) == [24]
    changed.clear()
    changed.config.select(0)
    changed.sequence(modifier=1)
    check(root_only and notes(changed) == [24, 28, 35, 38],
          "MIDI file audio : mode du pattern joué, ROOT puis CHORD, sans cache du précédent")
    check(not original.e.unmapped and not changed.e.unmapped,
          "MIDI file audio : reprise native atteinte, aucun accès mémoire hors du banc")
