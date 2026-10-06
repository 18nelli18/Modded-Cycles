"""Contrôles du code ColdFire du clavier d'accords (notes/42).

Appelé par la preuve principale avec le MAIN OS modifié et les symboles du
générateur. Le stockage lit et écrit un vrai en-tête de pattern en RAM émulée ;
ses propres preuves vérifient les formats de projet. PadsView, PadEvent, les
relais de notes, le contrôleur de vues, QuickMute et le constructeur du menu sont
réellement exécutés. La sélection du pattern et la notification sont simulées.
Les sélections, envois audio/MIDI et opérations de mute sont observés à leur
entrée ; la synthèse et le séquenceur sont vérifiés par les autres contrôles.
"""
import struct

from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk

import probe_chord_pads as pads
import test_arp as arp
import test_sdvintage_7th as t7

PROJECT, PATTERN, HEADER = 0x93100000, 0x93102000, 0x93108000


class _HeaderWords:
    """Observation/instrumentation des mots persistants ; les menus utilisent le vrai setter."""

    def __init__(self, emulator):
        self.emulator = emulator

    def __getitem__(self, track):
        return self.emulator.r32(HEADER + 40 + 4 * track)

    def __setitem__(self, track, value):
        self.emulator.w32(HEADER + 40 + 4 * track, value)


def _header(emulator):
    emulator.chord_header_ready = True
    emulator.w32(0x40FE4228, PROJECT)
    emulator.w32(PATTERN + 44, 0x400FD8C0)
    emulator.w32(PATTERN + 60, HEADER)
    return _HeaderWords(emulator)


def _install(rig, address, handler):
    rig.uc.hook_add(UC_HOOK_CODE, rig._stub(handler), begin=address, end=address)


def _pad_rig(image, symbols):
    rig = pads.Rig(image)
    config = _header(rig)
    selected, machine = [2], [5]
    _install(rig, 0x40012412, lambda a: selected[0])
    _install(rig, 0x4001E318, lambda a: machine[0])
    _install(rig, 0x400D0F6C, lambda a: 0)
    for track in range(6):
        rig.call(symbols["ck_ui_config_set"], track, (48 << 21) | 0x80000000)
    rate_reader = rig.r32(0x4001D260)
    if rate_reader != 0x40016086:
        # L'arpège remplace le lecteur Rte. Ce réglage périphérique reste simulé,
        # comme la lecture stock dans pads.Rig ; ses autres preuves testent l'arp.
        _install(rig, rate_reader, lambda a: rig.rate)
    return rig, config, selected, machine


def _event(rig, symbols, pad, down, velocity=100, func=0):
    rig.calls.clear()
    rig.call(pads.PAD_CTOR, pads.EVENT, pad, int(down), velocity, 123, func)
    return rig.call(symbols["ck_ui_pad"], pads.VIEW, pads.EVENT)


def _pads(image, symbols, check):
    rig, config, selected, machine = _pad_rig(image, symbols)
    check(all(rig.call(symbols["ck_ui_config_get"], track) == config[track] for track in range(6)),
          "pads : six configurations lues par la vraie API persistante")
    check(rig.r32(0x4010025C) == symbols["ck_ui_pad"] and
          rig.r32(0x401002B0) == symbols["ck_ui_pad_thunk"],
          "pads : pointeurs principal et secondaire redirigés")
    for bank in range(2):
        for pad in range(1, 7):
            rig.pressed = {4} if bank else set()
            slot = 6 * bank + pad - 1
            note = 48 + 12 * (slot // 7) + (0, 2, 4, 5, 7, 9, 11)[slot % 7]
            _event(rig, symbols, pad, True, 80 + pad)
            check(rig.calls == [("on", (2, note, 80 + pad, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
                  f"pads : T{pad}, banque {bank + 1}, note {note} sur la piste sélectionnée, sans retrig")
            rig.pressed.clear()
            selected[0] = 5
            _event(rig, symbols, pad, False)
            check(rig.calls == [("off", (2, note, 64))],
                  f"pads : T{pad}, relâchement fidèle malgré banque et sélection changées")
            selected[0] = 2

    rig.fixed_velocity = 111
    _event(rig, symbols, 1, True, velocity=30)
    check(rig.calls == [("on", (2, 48, 111, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "pads : vélocité fixe active, valeur globale prioritaire sur la frappe")
    _event(rig, symbols, 1, False)
    rig.fixed_velocity = None
    _event(rig, symbols, 1, True, velocity=37)
    check(rig.calls == [("on", (2, 48, 37, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "pads : vélocité fixe désactivée, vélocité de la frappe conservée")
    _event(rig, symbols, 1, False)

    _event(rig, symbols, 1, True)
    _event(rig, symbols, 2, True)
    check(rig.calls == [("off", (2, 48, 64)), ("on", (2, 50, 100, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "pads : la dernière frappe remplace l'accord précédent")
    _event(rig, symbols, 1, False)
    check(not rig.calls, "pads : relâcher l'ancien pad ne coupe pas le nouveau")
    _event(rig, symbols, 2, False)
    check(rig.calls == [("off", (2, 50, 64))], "pads : relâcher le dernier pad termine son accord")
    _event(rig, symbols, 2, False)
    check(not rig.calls, "pads : double relâchement ignoré")

    config[2] &= 0x7FFFFFFF
    _event(rig, symbols, 4, True)
    check(rig.calls == [("select", (3,)), ("on", (3, 63, 100, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "pads : mode OFF, consommateur stock et piste physique")
    _event(rig, symbols, 4, False)
    config[2] |= 0x80000000
    machine[0] = 0
    _event(rig, symbols, 5, True)
    check(rig.calls == [("select", (4,)), ("on", (4, 64, 100, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "pads : autre machine, consommateur stock")
    _event(rig, symbols, 5, False)
    machine[0] = 5

    rig.pressed = {2}
    _event(rig, symbols, 3, True)
    check(rig.calls == [("select", (2,))], "pads : TRACK garde la sélection sans note")
    _event(rig, symbols, 3, False)
    rig.pressed.clear()
    for key, name in ((1, "FUNC"), (3, "PATTERN")):
        # Comparaison au consommateur stock seul : le dispatch des vues modales
        # est contrôlé séparément ; ne pas confondre ce repli avec leur action.
        rig.pressed = {key}
        _event(rig, symbols, 4, True, func=int(key == 1))
        got = rig.calls[:]
        _event(rig, symbols, 4, False, func=int(key == 1))
        rig.calls.clear()
        rig.call(pads.PAD_CTOR, pads.EVENT, 4, 1, 100, 123, int(key == 1))
        rig.call(pads.PAD_CONSUMER, pads.VIEW, pads.EVENT)
        check(rig.calls == got, f"pads : {name}, repli identique au consommateur stock")
        _event(rig, symbols, 4, False, func=int(key == 1))
    rig.pressed.clear()

    _event(rig, symbols, 1, True)
    config[2] &= 0x7FFFFFFF
    machine[0] = 0
    _event(rig, symbols, 1, False)
    check(rig.calls == [("off", (2, 48, 64))],
          "pads : désactivation et changement de machine ne perdent pas la fin de note")
    config[2] |= 0x80000000
    machine[0] = 5
    selected[0] = 0
    _event(rig, symbols, 1, True)
    selected[0] = 1
    _event(rig, symbols, 2, True)
    rig.calls.clear()
    rig.call(symbols["ck_ui_cancel_track"], 1)
    check(rig.calls == [("off", (1, 50, 64))], "pads : annulation ciblée, autre piste conservée")
    _event(rig, symbols, 2, False)
    check(not rig.calls, "pads : le pad annulé garde son identité jusqu'au relâchement")
    _event(rig, symbols, 1, False)
    check(rig.calls == [("off", (0, 48, 64))], "pads : l'autre piste se relâche normalement")
    check(not rig.bad, "pads : aucun accès mémoire hors du banc")


def _dispatch(image, symbols, check):
    rig, _, _, _ = _pad_rig(image, symbols)
    # Les deux sous-objets dont le dispatch réel se sert. Liste de vues avec
    # QuickMute avant PadsView, comme une vue prioritaire affichée au premier plan.
    rig.w32(pads.VIEW, 0x40100218)
    rig.w32(pads.VIEW + 16, 0x401002A8)
    heap = [0x93200000]

    def allocate(args):
        pointer = heap[0]
        heap[0] += (args[0] + 15) & ~15
        rig.uc.mem_write(pointer, bytes(args[0]))
        return pointer

    for address, handler in (
            (0x400802E0, allocate), (0x400802EC, lambda a: 0),
            (0x400E8684, lambda a: 0), (0x400D08CE, lambda a: 0),
            (0x40013904, rig._capture("mute", 3))):
        _install(rig, address, handler)
    mute_node, pads_node, mute_view = 0x93010000, 0x93010100, 0x93011000
    rig.w32(pads_node + 8, pads.VIEW)
    rig.w32(pads_node + 4, pads.CONTROLLER + 20)
    rig.w32(pads.CONTROLLER + 20, pads_node)
    rig.w32(pads.CONTROLLER + 24, pads_node)

    def dispatch(pad, down):
        rig.calls.clear()
        rig.call(pads.PAD_CTOR, pads.EVENT, pad, int(down), 100, 123, 0)
        rig.call(0x4007746C, pads.CONTROLLER, pads.EVENT)

    dispatch(1, True)
    check(rig.calls == [("on", (2, 48, 100, 64, 0, 0xFFFFFFFF, 0xFFFFFFFF))],
          "dispatch réel : l'interface secondaire rejoint le clavier d'accords")
    dispatch(1, False)
    check(rig.calls == [("off", (2, 48, 64))], "dispatch réel : fin de l'accord")
    rig.w32(mute_node + 8, mute_view)
    rig.w32(mute_node + 4, pads_node)
    rig.w32(pads.CONTROLLER + 24, mute_node)
    rig.w32(mute_view, 0x40100C40)
    rig.w32(mute_view + 16, 0x40100CCC)
    dispatch(2, True)
    check(rig.calls == [("mute", (0x93101000, 1, 1))],
          "dispatch réel : QuickMute consomme l'appui avant PadsView, sans accord")
    dispatch(2, False)
    check(not rig.calls, "dispatch réel : QuickMute consomme son relâchement")
    check(not rig.bad, "dispatch réel : aucun accès mémoire hors du banc")


def _menu_rig(image, symbols):
    emulator = arp.Emu(image)
    items, drawn = [], []
    # Le constructeur stock initialise son propre projet ; on installe notre
    # en-tête isolé après sa construction, pour les callbacks du nouveau menu.
    emulator.chord_header_ready = False
    config, selected, machine = _HeaderWords(emulator), [2], [5]

    def hook(uc, address, size, user):
        sp = uc.reg_read(mk.UC_M68K_REG_A7)
        args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
        if address == 0x400734B0:
            funcs = []
            for pointer in args[1:5]:
                storage, _, manager, invoke = struct.unpack(">4I", uc.mem_read(pointer, 16))
                funcs.append((manager, invoke, emulator.r32(storage)))
            items.append(funcs)
        elif address == 0x4000F23E:
            emulator._pop(uc, emulator.track.obj)
        elif address == 0x4000F208 and emulator.chord_header_ready:
            emulator._pop(uc, PATTERN)
        elif address == 0x40012412:
            emulator._pop(uc, selected[0])
        elif address == 0x4001E318:
            emulator._pop(uc, machine[0])
        elif address == 0x40071A04:
            drawn.append(args)
            emulator._pop(uc, 0)
        elif address in (0x40072260, 0x40072080, 0x400D0F6C):
            emulator._pop(uc, 0)

    addresses = (0x400734B0, 0x4000F23E, 0x4000F208, 0x40012412, 0x4001E318,
                 0x40071A04, 0x40072260, 0x40072080, 0x400D0F6C)
    for address in addresses:
        emulator.uc.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)
    return emulator, items, drawn, config, selected, machine


def _menu(image, symbols, check):
    emulator, items, drawn, config, selected, machine = _menu_rig(image, symbols)
    view = 0x93000000
    emulator.uc.mem_write(view, bytes(0x400))
    emulator.call(0x4002D138, view)
    original_count = len(items)
    items.clear()
    emulator.uc.mem_write(view, bytes(0x400))
    emulator.call(symbols["ck_ui_menu_ctor"], view)
    check(len(items) == original_count + 10,
          f"menu réel : {original_count} lignes préexistantes conservées, dix ajoutées")
    if len(items) != original_count + 10:
        return
    _header(emulator)
    emulator.call(symbols["ck_storage_reset"], HEADER)
    expected = ("Keys", "Root", "Scale", "I Ext", "II Ext", "III Ext", "IV Ext", "V Ext", "VI Ext", "VII Ext")
    for field, name in enumerate(expected):
        label, press, draw, change = items[original_count + field]
        valid = all(func[0] == 0x4002CF00 for func in items[original_count + field])
        valid &= arp.cstr(emulator, label[2]) == name and press[1:] == (0x4002CCD0, view)
        valid &= draw[2] == field and change[2] == field
        # Exécuter également le vrai libellé std::string, avec son ABI a0.
        functor = arp.make_fn(emulator, label)
        string = 0x93600100
        emulator.uc.reg_write(mk.UC_M68K_REG_A0, string)
        sp = t7.STACK - 0x400
        emulator.uc.mem_write(sp, struct.pack(">II", t7.STOP, functor))
        emulator.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        emulator.uc.emu_start(label[1], t7.STOP, count=200_000)
        check(valid and arp.std_string(emulator, string) == name, f"menu : libellé {name}, vraie std::string")

        changer = arp.make_fn(emulator, change)
        shift = 31 if field == 0 else 21 if field == 1 else 28 if field == 2 else 3 * (field - 3)
        mask = 1 if field == 0 else 127 if field == 1 else 7
        for delta, target in ((99, (1, 48, 6, 4, 4, 4, 4, 4, 4, 4)[field]),
                              (-99, 24 if field == 1 else 0)):
            before = config[2]
            emulator.call(change[1], changer, 0, delta & 0xFFFFFFFF)
            check(((config[2] >> shift) & mask) == target and
                  (config[2] & ~(mask << shift)) == (before & ~(mask << shift)),
                  f"menu : {name}, borne {target}, autres champs conservés")

        config[2] = (48 << 21) | 0x80000000 | (5 << 28) | sum(4 << (3 * degree) for degree in range(7))
        drawer = arp.make_fn(emulator, draw)
        drawn.clear()
        emulator.call(draw[1], drawer, 0, 0x93700000, 0x93710000, 7)
        args = drawn[-1]
        value = arp.cstr(emulator, args[6])
        if field == 1:
            good = arp.cstr(emulator, args[5]) == "%s%d" and value == "C" and args[7] == 3
        else:
            good = arp.cstr(emulator, args[5]) == "%s" and value == ("ON" if field == 0 else "MINOR" if field == 2 else "13")
        check(good and args[2:5] == (0x93710000 + 24, 7, 4), f"menu : affichage {name} et placement stock")

    config[2] = 48 << 21
    machine[0] = 0
    change = items[original_count][3]
    emulator.call(change[1], arp.make_fn(emulator, change), 0, 1)
    check(config[2] == 48 << 21, "menu : activation refusée sur une machine autre que CHORD")
    check(not emulator.bad, "menu : aucun accès mémoire hors du banc")


def _live(image, symbols, check):
    """Pad -> relais stock -> vraie file audio, et messages stock de live rec.

    Le projet, les touches, les verrous et la position temporelle sont simulés.
    Ui observe la file de l'interface : cette preuve s'arrête avant l'écriture
    du trig dans le pattern ; le rendu harmonique est vérifié séparément.
    """
    audio = arp.Audio(image)
    audio.uc.mem_map(0x93000000, 0x01000000)
    ui = arp.Ui(audio)
    track, pressed = 2, set()
    _header(audio)

    def stub(handler):
        def hook(uc, address, size, user):
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            args = struct.unpack(">8I", uc.mem_read(sp + 4, 32))
            uc.reg_write(mk.UC_M68K_REG_D0, handler(args) & 0xFFFFFFFF)
            uc.reg_write(mk.UC_M68K_REG_PC, audio.r32(sp))
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
        return hook

    for address, handler in {
            0x400CF866: lambda a: PROJECT,
            0x4000EB90: lambda a: 0x93101000,
            0x4000F208: lambda a: PATTERN,
            0x40012412: lambda a: track,
            0x4001E318: lambda a: 5,
            0x40013464: lambda a: 0,
            0x4007FAF4: lambda a: int(a[0] in pressed),
            0x40001D2C: lambda a: 0,
            0x40001E4E: lambda a: 0,
            0x400CF23C: lambda a: 0,
            0x40016E90: lambda a: 0,
            0x400D0F6C: lambda a: 0,
    }.items():
        audio.uc.hook_add(UC_HOOK_CODE, stub(handler), begin=address, end=address)
    audio.w32(pads.VIEW + 44, pads.CONTROLLER)
    audio.w32(pads.CONTROLLER + 20, pads.CONTROLLER + 20)
    audio.w32(0x40A7887C, arp.BANK)
    audio.uc.mem_write(arp.BANK + 722 * track + 710, struct.pack(">H", 0x680))
    audio.uc.mem_write(0x40FB680C, b"\xff" * 4 * 128 * 6)
    audio.e.call(symbols["ck_ui_config_set"], track, 0x80000000 | (48 << 21) | (4 << 18))
    arp.live(audio, True)

    def event(down):
        audio.w32(0x8000184C, audio.now)
        audio.e.call(pads.PAD_CTOR, pads.EVENT, 1, int(down), 100, 123, 0)
        audio.e.call(symbols["ck_ui_pad"], pads.VIEW, pads.EVENT)
        return audio.run()

    pressed.add(4)
    mask = event(True)
    check(mask is not None and mask & (1 << track) and audio.state(track)[:2] == (59, 59),
          "live rec : RETRIG + T1 atteint la vraie file audio, degré VII = note 59")
    check([arp.msg(m)[:5] for m in ui.os] == [("ON", track, 59, 100, -1)] and not ui.posted,
          "live rec : le message stock garde la fondamentale, la vélocité et aucun retrig")
    pressed.clear()
    audio.now += 40000
    event(False)
    check([arp.msg(m)[:5] for m in ui.os] == [("ON", track, 59, 100, -1),
                                           ("OFF", track, 59, 0, 20000)],
          "live rec : le relâchement stock garde la note et sa durée après changement de banque")
    check(not audio.e.unmapped, "live rec : aucun accès mémoire hors du banc")


def run(stock, patched, symbols, check):
    """Exécute les contrôles ; check(bool, texte) appartient à la preuve principale."""
    del stock  # Les chemins stock appelés en repli sont dans l'image modifiée.
    symbols = {name: int(value, 16) if isinstance(value, str) else value for name, value in symbols.items()}
    _pads(patched, symbols, check)
    _dispatch(patched, symbols, check)
    _menu(patched, symbols, check)
    _live(patched, symbols, check)
