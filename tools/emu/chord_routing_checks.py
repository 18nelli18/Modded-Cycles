"""Régressions du routage Chord Keys (notes/40, review PR #46).

Les constructeurs PadEvent/KeyEvent, les deux dispatchers de l'OS, PadsView,
KeyboardView et PatternAndBankSelectView sont exécutés. Le scanner stock et son
masque de relâchement produisent les événements remis aux vrais dispatchers.
Le remplissage de pile
est volontairement non nul : PadEvent ne construit qu'un octet à +28 et laisse
son alignement intact. Les sorties de notes/sélection sont observées à leur
entrée ; l'allocation, les verrous et les accesseurs de projet sont ceux du
banc UI commun. Le registre d'horloge du scanner est préparé en RAM émulée ;
aucun démarrage complet ni circuit physique n'est simulé.
"""
import struct

import chord_ui_checks as ui
import probe_chord_pads as pads


KEYBOARD, KEY_NODE, PAD_NODE = 0x93012000, 0x93010100, 0x93010200
PATTERN_VIEW, PATTERN_NODE = 0x93014000, 0x93010300


def _rig(image, symbols=None):
    rig, config, selected, machine, _ = ui._ui_rig(image, symbols)
    rig.w32(pads.VIEW, 0x40100218)
    rig.w32(pads.VIEW + 16, 0x401002a8)
    rig.w32(KEYBOARD, 0x400ff9c4)
    rig.w32(KEYBOARD + 16, 0x400ffa4c)
    rig.w32(KEYBOARD + 44, pads.CONTROLLER)
    rig.w32(KEYBOARD + 148, ui.KEY_NOTES)
    rig.w32(KEYBOARD + 152, ui.KEY_NOTES)
    rig.w32(KEYBOARD + 156, ui.KEY_NOTES + 0xa00)
    rig.w32(KEY_NODE, pads.CONTROLLER + 20)
    rig.w32(KEY_NODE + 8, KEYBOARD)
    rig.w32(KEY_NODE + 4, PAD_NODE)
    rig.w32(PAD_NODE, KEY_NODE)
    rig.w32(PAD_NODE + 8, pads.VIEW)
    rig.w32(PAD_NODE + 4, pads.CONTROLLER + 20)
    rig.w32(pads.CONTROLLER + 20, PAD_NODE)
    rig.w32(pads.CONTROLLER + 24, KEY_NODE)
    heap = [0x93200000]

    def allocate(args):
        pointer = heap[0]
        heap[0] += (args[0] + 15) & ~15
        rig.uc.mem_write(pointer, bytes(args[0]))
        return pointer

    class SelectingCalls(list):
        def append(self, call):
            if call[0] == "select":
                selected[0] = call[1][0]
            super().append(call)

    rig.calls = SelectingCalls()
    for address, handler in (
            (0x400802e0, allocate), (0x400802ec, lambda a: 0),
            (0x400e8684, lambda a: 0), (0x400d08ce, lambda a: 0)):
        ui._install(rig, address, handler)
    return rig, config, selected, machine


def _key(rig, down, flags=0, key=1):
    (rig.pressed.add if down else rig.pressed.discard)(15 + key)
    rig.calls.clear()
    rig.call(ui.KEY_CTOR, pads.EVENT, 15 + key, int(down) | flags, 123, 127)
    return rig.call(0x40077720, pads.CONTROLLER, pads.EVENT) & 255


def _pad(rig, number, down, padding, function=0):
    rig.calls.clear()
    rig.uc.mem_write(pads.EVENT + 28, b"\xff" + padding)
    rig.call(pads.PAD_CTOR, pads.EVENT, number, int(down), 100, 123, function)
    assert bytes(rig.uc.mem_read(pads.EVENT + 28, 4)) == bytes([function]) + padding
    return rig.call(0x4007746c, pads.CONTROLLER, pads.EVENT) & 255


def _padding(stock, image, symbols, check):
    for padding in (b"\x01\0\0", b"\0\x80\0", b"\0\0\xff", b"\xa5\x5a\xe3"):
        reference, _, stock_selected, _ = _rig(stock)
        rig, _, selected, _ = _rig(image, symbols)
        _key(rig, True)
        valid = rig.calls == [ui._on(2, 48)]
        for number in range(1, 7):
            # Stock sélectionne toujours le pad, même si FUNC est faux.
            _pad(reference, number, True, padding)
            valid &= ("select", (number - 1,)) in reference.calls
            valid &= stock_selected[0] == number - 1
            _pad(reference, number, False, padding)
            valid &= _pad(rig, number, True, padding) == 1
            valid &= rig.calls == [("off", (2, 48, 64)), ui._on(2, 48)] and selected[0] == 2
            valid &= rig.call(symbols["ck_ui_modifier_get"], 2, ui.HEADER) == number
            valid &= rig.call(symbols["ck_ui_active_note"], 2) == 48
            _pad(rig, number, False, padding)
            valid &= not rig.calls and rig.call(symbols["ck_ui_modifier_get"], 2, ui.HEADER) == number
        _key(rig, False)
        valid &= rig.calls == [("off", (2, 48, 64))]
        check(valid and not rig.bad and not reference.bad,
              f"routage pads : TRIG tenu puis T1–T6, vrai FUNC=0, padding {padding.hex()}, piste conservée")

    # Le booléen réellement actif conserve le repli, quel que soit son padding.
    for function, held in ((1, set()), (0, {1}), (0, {2}), (0, {3}), (0, {4})):
        before, _, _, _ = _rig(stock)
        after, _, _, _ = _rig(image, symbols)
        outputs = []
        for rig in (before, after):
            rig.pressed = held
            results = []
            for down in (True, False):
                consumed = _pad(rig, 6, down, b"\xa5\x5a\xe3", function)
                results.append((consumed, rig.calls[:], rig.held(6)))
            outputs.append(results)
        check(outputs[0] == outputs[1],
              f"routage pads : FUNC réel={function}, touche réservée={sorted(held)}, repli stock inchangé")


def _pattern_release(rig):
    """Le chemin stock PATTERN garde une autre touche de sélection enfoncée."""
    rig.w32(PATTERN_VIEW, 0x40100860)
    rig.w32(PATTERN_VIEW + 140, 3)
    rig.w32(PATTERN_NODE + 4, KEY_NODE)
    rig.w32(PATTERN_NODE + 8, PATTERN_VIEW)
    rig.w32(pads.CONTROLLER + 24, PATTERN_NODE)
    rig.uc.mem_write(ui.UIST + 389, b"\1")
    consumed = _key(rig, False)
    rig.w32(pads.CONTROLLER + 24, KEY_NODE)
    rig.uc.mem_write(ui.UIST + 389, b"\0")
    return consumed


def _lost_release(image, symbols, check):
    for fallback in ("Keys OFF", "autre machine", "FUNC", "TRACK", "annulation puis OFF", "autre piste OFF", "Keys ON"):
        rig, _, selected, machine = _rig(image, symbols)
        _key(rig, True)
        # PATTERN devient prioritaire pendant la note ; deux touches de sa
        # propre sélection sont tenues. Sa routine absorbe la fin du TRIG 1.
        consumed = _pattern_release(rig)
        check(consumed == 1 and not rig.calls and rig.r32(PATTERN_VIEW + 140) == 2 and
              rig.call(symbols["ck_ui_active_note"], 2) == 48,
              f"relâchement perdu ({fallback}) : vraie vue PATTERN consomme le TRIG avant KeyboardView")
        _pad(rig, 1, True, b"\xa5\x5a\xe3")
        check(not rig.calls, "attaque T : capture TRIG périmée après PATTERN, aucune note fantôme")
        _pad(rig, 1, False, b"\xa5\x5a\xe3")
        if fallback in ("Keys OFF", "annulation puis OFF"):
            if fallback == "annulation puis OFF":
                rig.call(symbols["ck_ui_cancel_track"], 2)
            rig.call(symbols["ck_ui_config_set"], 2, 48 << 21)
        elif fallback == "autre piste OFF":
            selected[0] = 5
            rig.call(symbols["ck_ui_config_set"], 5, 48 << 21)
        elif fallback == "autre machine":
            machine[0] = 0
        elif fallback in ("FUNC", "TRACK"):
            rig.pressed = {1 if fallback == "FUNC" else 2}
        flags = 2 if fallback == "FUNC" else 0
        _key(rig, True, flags)
        events = rig.calls[:]
        _key(rig, False, flags)
        track = selected[0]
        note = 48 if fallback == "Keys ON" else 52
        old_off = [] if fallback == "annulation puis OFF" else [("off", (2, 48, 64))]
        check(events == old_off + [ui._on(track, note)] and
              rig.calls == [("off", (track, note, 64))] and
              rig.call(symbols["ck_ui_active_note"], 2) == 128 and not rig.bad,
              f"relâchement perdu ({fallback}) : frappe neuve annule l'ancienne capture, puis note-off stock transmis")

    rig, _, selected, machine = _rig(image, symbols)
    selected[0] = 1
    _key(rig, True, key=2)
    selected[0] = 2
    _key(rig, True)
    _key(rig, True, flags=8)
    check(not rig.calls and rig.call(symbols["ck_ui_active_note"], 1) == 50 and
          rig.call(symbols["ck_ui_active_note"], 2) == 48,
          "capture TRIG : une répétition de maintien ne termine aucune des deux pistes tenues")
    _pattern_release(rig)
    machine[0] = 0
    _key(rig, True)
    _key(rig, False)
    _key(rig, False, key=2)
    check(rig.calls == [("off", (1, 50, 64))] and not rig.bad,
          "capture TRIG : récupérer une touche perdue conserve la capture indépendante d'une autre touche/piste")

    rig, _, _, _ = _rig(image, symbols)
    _key(rig, True)
    _pattern_release(rig)
    trigs = {}

    def set_trig(args, value):
        trigs[args[1]] = value
        return 0

    for address, handler in {
            0x4000ee90: lambda a: 0x93101000,
            0x400124b8: lambda a: 0,
            0x40015c20: lambda a: int(trigs.get(a[1]) == "note"),
            0x40015c7c: lambda a: int(trigs.get(a[1]) == "lock"),
            0x40017b48: lambda a: set_trig(a, "note"),
            0x40017bb0: lambda a: set_trig(a, "lock"),
            0x40017c4e: lambda a: set_trig(a, None),
            0x400760ba: lambda a: 0,
            0x40069b84: lambda a: 0,
    }.items():
        ui._install(rig, address, handler)
    grid, node = 0x93300000, 0x93010400
    rig.w32(grid, 0x40100ae8)
    rig.w32(grid + 16, 0x40100b78)
    rig.w32(PAD_NODE + 4, node)
    rig.w32(node, PAD_NODE)
    rig.w32(node + 8, grid)
    rig.w32(node + 4, pads.CONTROLLER + 20)
    rig.w32(pads.CONTROLLER + 20, node)
    rig.uc.mem_write(ui.UIST + 357, b"\1\1")
    _key(rig, True)
    check(rig.calls == [("off", (2, 48, 64))] and trigs == {0: "note"} and
          rig.call(symbols["ck_ui_active_note"], 2) == 128 and not rig.bad,
          "capture TRIG : après release perdue, l'édition réelle pose le pas et termine l'ancienne note")


def _suppressed_release(image, symbols, check):
    """Vrai scanner de touches et vrai setter de son masque de relâchement."""
    rig, _, _, machine = _rig(image, symbols)
    rig.uc.mem_map(0xfc070000, 0x1000)
    queued = []

    def enqueue(args):
        queued.append(struct.unpack(">4I", rig.uc.mem_read(args[1], 16)))
        return 0

    ui._install(rig, 0x40001fba, enqueue)
    physical = rig.r32(0x4010ae5c + 16 * 4)
    group, mask = physical // 8, 1 << (physical % 8)
    rig.uc.mem_write(0x40f95744 + group, bytes([mask]))
    rig.w32(0x40148cd8, physical)
    rig.w32(0x40148cd4, physical)
    _key(rig, True)
    rig.call(0x4007fb32, 16)
    check(bytes(rig.uc.mem_read(0x40f95724 + group, 1)) == bytes([mask]),
          "masque natif : le helper stock marque le relâchement du TRIG tenu")
    rig.call(0x4007fbde, group, 0)
    check(not queued and bytes(rig.uc.mem_read(0x40f95724 + group, 1)) == b"\0" and
          rig.call(symbols["ck_ui_active_note"], 2) == 48,
          "masque natif : le scanner stock supprime réellement le release avant construction de KeyEvent")
    machine[0] = 0
    rig.call(0x4007fbde, group, mask)
    message = queued.pop()
    rig.calls.clear()
    rig.call(ui.KEY_CTOR, pads.EVENT, message[1], message[2], message[3], 127)
    rig.call(0x40077720, pads.CONTROLLER, pads.EVENT)
    press = rig.calls[:]
    rig.call(0x4007fbde, group, 0)
    message = queued.pop()
    rig.calls.clear()
    rig.call(ui.KEY_CTOR, pads.EVENT, message[1], message[2], message[3], 127)
    rig.call(0x40077720, pads.CONTROLLER, pads.EVENT)
    check(press == [("off", (2, 48, 64)), ui._on(2, 52)] and
          rig.calls == [("off", (2, 52, 64))] and not queued and not rig.bad,
          "masque natif : les événements suivants du scanner retrouvent leur note-on/off stock après nettoyage")


def run(stock, image, symbols, check):
    _padding(stock, image, symbols, check)
    _lost_release(image, symbols, check)
    _suppressed_release(image, symbols, check)
