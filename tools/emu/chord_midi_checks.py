"""Sortie MIDI : helpers clavier/pads et ordonnanceur MIDI natifs OS 1.13.

Les accès au projet/son, files RTOS et pilotes physiques sont instrumentés ;
les hooks finaux, octets MIDI, routage USB/DIN, listes de durée et STOP sont
réellement exécutés. Aucun transport ou temporisation matériel n'est simulé.
"""
import struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from chord_plock_checks import PlockRig
from chord_audio_checks import config_word
from chord_harmony_checks import expected_notes
from probe_chord_storage import BASE, B1, PROJECT, STACK, STOP

SOUND, SOUND_OBJECT, SOUND_VTABLE = 0x92060000, 0x92060100, 0x92060200
EVENT, CLOCK = 0x92061000, 0x92061100
PARAMS = 0x800015ae
LIVE_SITES = ((0x40019ee2, 10), (0x40019cba, 8), (0x4001d094, 6), (0x4001d120, 6))


class MidiRig(PlockRig):
    def __init__(self, stock, patched, symbols, original=False):
        super().__init__(stock, patched, symbols)
        if original:
            for address, size in LIVE_SITES:
                self.uc.mem_write(address, stock[address - BASE:address - BASE + size])
            self.uc.ctl_flush_tb()
        self.output, self.queue, self.events = [], [], []
        self.channels = list(range(6))
        self.mout, self.destination = True, 3  # réglage utilisateur BOTH
        self.stub(0x40016e90, lambda a: int(self.mout))
        self.stub(0x40012e82, lambda a: self.channels[a[1]])
        self.stub(0x40044e6c, lambda a: self.destination)
        self.stub(0x4006bdfe, lambda a: 0)
        self.stub(0x4008171e, lambda a: 0)
        self.stub(0x4008145e, lambda a: 0)
        self.stub(0x4000eb9c, lambda a: SOUND_OBJECT)
        self.stub(0x40009c1a, lambda a: SOUND_OBJECT)
        self.word(SOUND_OBJECT, SOUND_VTABLE)
        self.word(SOUND_VTABLE + 40, 0x92060300)
        self.stub(0x92060300, lambda a: SOUND)
        self.stub(0x40001584, lambda a: self.emit('DIN', a))
        self.stub(0x40003396, lambda a: self.emit('USB', a))
        for addr in (0x400032ca, 0x400032da, 0x40001f58, 0x400019ec, 0x40001a38):
            self.stub(addr, lambda a: 0)
        self.stub(0x40001fba, self.enqueue)
        self.call(0x4008a55a)
        self.queue.clear()
        self.uc.mem_map(0, 0x1000)  # fenêtre basse native, sentinelle vide des listes
        self.uc.hook_add(UC_HOOK_CODE, self.dequeue, begin=0x4000204c, end=0x4000204c)
        for track in range(6):
            self.call('ck_ui_config_set', track, config_word(root=24))
            self.params(track)
        self.params_live()

    def emit(self, destination, args):
        self.output.append((destination, self.bytes(args[1], args[0])))
        return 0

    def enqueue(self, args):
        assert args[0] == 0x40fcb2ec
        packet = self.bytes(args[1], 16)
        self.events.append(packet)
        # La file retient un pointeur comme le RTOS réel, pas une copie.
        self.queue.append(args[1])
        return 0

    def dequeue(self, uc, pc, size, user):
        if not self.queue:
            uc.reg_write(mk.UC_M68K_REG_PC, STOP)
            return
        pointer = self.queue.pop(0)
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        uc.reg_write(mk.UC_M68K_REG_D0, pointer)
        uc.reg_write(mk.UC_M68K_REG_PC, self.word(sp))
        uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    def worker(self):
        for track, channel in enumerate(self.channels):
            self.uc.mem_write(0x40fdd580 + track, bytes([channel & 255]))
        self.call(0x4008a0ba)

    def params(self, track, palette=0, shape=0, modifier=0, machine=5):
        data = [0] * 33
        data[9], data[11], data[12], data[28] = machine << 8, (32, 64, 110)[palette] << 8, shape << 8, modifier
        self.uc.mem_write(PARAMS + 66 * track, struct.pack('>33H', *data))
        self.word(0x423087f8 + 8 * track, (1 << 28) if modifier else 0)

    def params_live(self, palette=0, shape=0, machine=5):
        self.params(0, palette, shape, machine=machine)
        self.uc.mem_write(SOUND + 20, self.bytes(PARAMS, 66))

    def live_on(self, track=0, note=24, velocity=97, pad=False):
        self.call(0x4001d05e if pad else 0x40019e7a, 0, track, note, velocity, 0xffffffff)

    def live_off(self, track=0, note=24, pad=False):
        self.call(0x4001d0fc if pad else 0x40019c84, 0, track, note)

    def key(self, number, down):
        (self.pressed.add if down else self.pressed.discard)(15 + number)
        self.call(0x4007238c, EVENT, 15 + number, int(down), 0, 97)
        self.call('ck_ui_key', 0, EVENT)

    def pad(self, number, down):
        self.call(0x40074072, EVENT, number, int(down), 100, 0, 0)
        self.call('ck_ui_pad', 0, EVENT)

    def sequence(self, track=0, note=24, velocity=97, length=100, time=1000, midi=True):
        event = bytearray(80)
        struct.pack_into('>I', event, 4, 1)
        struct.pack_into('>I', event, 12, 1)
        event[20], event[22] = int(midi), velocity
        struct.pack_into('>I', event, 28, note)
        struct.pack_into('>I', event, 52, length)
        self.uc.mem_write(EVENT, bytes(event))
        self.call('ck_audio_event', track, EVENT)
        self.call('ck_midi_sequence', track, EVENT, time)

    def worker_message(self, kind, time=0):
        pointer = self.call(0x4008a5d0)
        self.uc.mem_write(pointer, bytes(16))
        self.uc.mem_write(pointer, bytes([kind]))
        self.word(pointer + 12, time)
        self.queue.append(pointer)
        self.worker()


def messages(rig, destination='DIN'):
    return [tuple(data) for port, data in rig.output if port == destination]


def run(stock, patched, symbols, check):
    original, changed = (MidiRig(stock, patched, symbols, original=x) for x in (True, False))
    same = True
    for track in range(6):
        for pad in (False, True):
            for mout in (False, True):
                for route in range(4):
                    for rig in (original, changed):
                        rig.output.clear()
                        rig.mout, rig.destination = mout, route
                        rig.live_on(track, 48 + track, 71, pad)
                        rig.live_off(track, 48 + track, pad)
                    same &= original.output == changed.output
    check(same, 'MIDI ROOT : 96 paires clavier/pads × six pistes × MOut × destinations, octets stock identiques')
    changed.mout, changed.destination = True, 3
    for track in range(6):
        changed.call('ck_ui_midi_set', track, 1)
    changed.output.clear()
    changed.live_on()
    check(messages(changed) == [(0x90, 24, 97), (0x90, 28, 97), (0x90, 31, 97)]
          and messages(changed, 'USB') == messages(changed),
          'MIDI CHORD : vraie attaque clavier, triade et vélocité identiques USB + DIN')
    changed.channels[0], changed.destination, changed.mout = 9, 0, False
    changed.call('ck_ui_midi_set', 0, 0)
    changed.live_off()
    check(messages(changed)[-3:] == [(0x80, 24, 0), (0x80, 28, 0), (0x80, 31, 0)]
          and messages(changed, 'USB') == messages(changed),
          'MIDI OFF capturé : ancien canal/destinations conservés malgré MOut OFF, changement de canal et retour ROOT')
    changed.channels[0], changed.destination, changed.mout = 0, 3, True
    changed.call('ck_ui_midi_set', 0, 1)
    changed.destination = 0
    changed.output.clear()
    changed.live_on()
    changed.destination = 3
    changed.live_off()
    check(not changed.output,
          'MIDI destination OFF capturée : activer USB + DIN avant le relâchement n’envoie aucun note-off parasite')
    changed.output.clear()
    changed.live_on(note=24)
    changed.live_on(note=28)
    before = list(changed.output)
    changed.live_off(note=24)
    check(changed.output == before and messages(changed)[3:6] == [(0x80, 24, 0), (0x80, 28, 0), (0x80, 31, 0)],
          'MIDI remplacement : ancien accord terminé avant le suivant, ancien relâchement absorbé même avec note partagée')
    changed.live_off(note=28)

    gesture = MidiRig(stock, patched, symbols)
    gesture.call('ck_ui_midi_set', 0, 1)
    gesture.pressed = set()
    gesture.stub(0x4007faf4, lambda a: int(a[0] in gesture.pressed))
    gesture.stub(0x40015ac4, lambda a: 97)
    gesture.pad(1, True)
    gesture.key(1, True)
    first = messages(gesture)
    gesture.key(1, False)
    gesture.output.clear()
    gesture.key(2, True)
    second = messages(gesture)
    gesture.output.clear()
    gesture.pad(2, True)
    replay = messages(gesture)
    gesture.pad(2, False)
    gesture.pad(1, False)
    gesture.key(2, False)
    check(first == [(0x90, n, 97) for n in (24, 28, 35, 38)]
          and second == [(0x90, n, 97) for n in (26, 29, 36, 40)]
          and replay == [(0x80, n, 0) for n in (26, 29, 36, 40)] +
                        [(0x90, n, 97) for n in (26, 29, 36, 43)],
          'MIDI gestes réels : T1 tenu sur deux TRIG puis T2 réattaque quatre voix, mêmes vélocités et offs complets')

    fallback = True
    for keys, machine, note in ((False, 5, 24), (True, 4, 24), (True, 5, 25)):
        changed.call('ck_ui_config_set', 0, config_word(root=24, enabled=keys))
        changed.params_live(machine=machine)
        changed.output.clear()
        changed.live_on(note=note)
        changed.live_off(note=note)
        fallback &= messages(changed) == [(0x90, note, 97), (0x80, note, 0)]
    changed.call('ck_ui_config_set', 0, config_word(root=24))
    changed.params_live()
    check(fallback, 'MIDI CHORD gardes : Keys OFF, autre machine ou fondamentale hors gamme conservent la note ROOT')
    changed.call('ck_ui_midi_set', 0, 0)
    changed.live_on(note=25)
    changed.call('ck_ui_midi_set', 0, 1)
    changed.live_on(note=24)
    changed.output.clear()
    changed.live_off(note=25)
    check(messages(changed) == [(0x80, 25, 0)],
          'MIDI ROOT→CHORD : le relâchement ROOT antérieur reste transmis pendant un nouvel accord')
    changed.live_off(note=24)

    # Chaque accord passe par le producteur ColdFire et le vrai worker natif.
    voiced = True
    for palette in range(3):
        for index, shape in enumerate(range(0, 33, 4)):
            for modifier in range(7):
                changed.params(0, palette, shape, modifier)
                changed.output.clear()
                changed.sequence(length=0)
                changed.worker()
                # L'oracle musical autonome est commun aux preuves DSP ;
                # le placement des voix est vérifié ici par le code émulé.
                base = expected_notes(0, 0, 0, palette, modifier)
                notes = list(base)
                # Référence explicite des inversions fermées/ouvertes.
                if index:
                    notes = sorted(n % 12 for n in notes)
                    for _ in range((index - 1) % 4):
                        notes[0] += 12
                        notes.sort()
                    if index >= 5:
                        for i in range(1, len(notes), 2):
                            notes[i] += 12
                        notes.sort()
                expected = sorted(24 + n for n in notes if 24 + n < 128)
                actual = sorted(n for status, n, v in messages(changed) if status == 0x90 and v)
                voiced &= actual == expected
                changed.worker_message(6)
    check(voiced, 'MIDI séquence : 189 accords, trois palettes × sept gestes × neuf dispositions puis arrêt natif')

    changed.params(0)
    changed.output.clear()
    changed.sequence(length=100, time=1000)
    changed.worker()
    changed.worker_message(3, 1199)
    before = messages(changed)
    changed.worker_message(3, 1201)
    check(len(before) == 3 and len(messages(changed)) == 6
          and all(v == 0 for _, _, v in messages(changed)[3:]),
          'MIDI LEN : trois voix tenues jusqu’à l’échéance puis trois note-off du vrai ordonnanceur')
    changed.output.clear()
    changed.sequence(midi=False)
    changed.worker()
    check(not changed.output, 'MIDI séquence MOut OFF : aucun message ajouté')

    # 24 notes simultanées puis répétitions : 128 tampons et 2048 fiches natives.
    dense = True
    for repetition in range(10):
        changed.output.clear()
        for track in range(6):
            changed.call('ck_ui_config_set', track, config_word(root=24, extensions=(1,) * 7))
            changed.params(track)
            changed.sequence(track, 24, 80 + track, 100, time=1000 + repetition * 10)
        changed.worker()
        on = [packet for packet in messages(changed) if packet[2]]
        dense &= len(on) == 24
    changed.output.clear()
    changed.worker_message(6)
    check(dense and len(messages(changed)) == 24 and all(v == 0 for _, _, v in messages(changed))
          and not any(changed.bytes(0x40fcf570, 16 * 128 * 4)),
          'MIDI charge ciblée : 10 attaques × six pistes × quatre voix, recyclage natif puis STOP sans note restante')
