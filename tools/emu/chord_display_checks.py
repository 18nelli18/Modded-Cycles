"""Preuve du bandeau d'accord : touches, Bitmap, polices, flush et DSPI réels.

Le panneau LCD est celui de test_boot_anim : le flux DSPI restitue l'orientation
physique. La sélection de piste et le projet sont les objets du banc UI ; le
calcul audio/publié est vérifié séparément par chord_pad_audio_checks. Ici les
instantanés passent par le vrai éditeur atomique ColdFire. Aucun rendu hôte ne
remplace les glyphes, le clipping, l'échange des tampons ou l'envoi à l'écran.
"""
import struct

from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_CODE

from chord_ui_checks import _ui_rig, _key, _install
from test_boot_anim import Panel, PUSHR, BUF_PTRS, BITMAP, DRAW_TEXT, FLUSH
import test_sdvintage_7th as t7


BUFFER_A, BUFFER_B = 0x93300010, 0x93301010
CANVAS, TEXT_A, TEXT_B, INTERVALS = 0x93302000, 0x93303000, 0x93303100, 0x93303200
BACKGROUND = bytes((i * 47 + i // 13) & 255 for i in range(1024))
APPLICATION = 0x93304000


def _prepare(image, symbols=None):
    rig, config, selected, machine, _ = _ui_rig(image, symbols)
    payload = image[t7.E.IMAGE_LEN:]
    if payload:
        rig.uc.mem_map(t7.E.PAYLOAD_DST, (len(payload) + 0xFFFFF) & ~0xFFFFF)
        rig.uc.mem_write(t7.E.PAYLOAD_DST, bytes(payload))
    rig.uc.mem_map(0xFC000000, 0x100000)
    panel = Panel()
    rig.chord_panel = panel

    def write(uc, access, address, size, value, user):
        if address == PUSHR:
            panel.push(value)

    rig.uc.hook_add(UC_HOOK_MEM_WRITE, write)
    return rig, config, selected, machine, panel


def _background(rig):
    rig.w32(BUF_PTRS, BUFFER_A)
    rig.w32(BUF_PTRS + 4, BUFFER_B)
    for pointer, data in ((BUFFER_A, BACKGROUND), (BUFFER_B, bytes(1024))):
        rig.uc.mem_write(pointer - 16, b"\xa5" * 16 + data + b"\xa5" * 16)
    # L'ancien tampon représente réellement le contenu déjà transmis au LCD.
    rig.chord_panel.ram = [[0] * 128 for _ in range(8)]


def _sentinels(rig):
    return all(bytes(rig.uc.mem_read(pointer + offset, 16)) == b"\xa5" * 16
               for pointer in (BUFFER_A, BUFFER_B) for offset in (-16, 1024))


def _expected(rig, name, omissions):
    data = bytearray(BACKGROUND)
    for x in range(128):
        word = struct.unpack_from(">I", data, 8 * x + 4)[0] & 0xFFF00000
        struct.pack_into(">I", data, 8 * x + 4, word)
    rig.uc.mem_write(BUFFER_A, bytes(data))
    rig.call(BITMAP, CANVAS, 128, 64, BUFFER_A, 0)
    for text, pointer, font, width, y in (
            (name, TEXT_A, 0x4014120C, 8, 54),
            (omissions, TEXT_B, 0x40140AB0, 6, 44)):
        rig.uc.mem_write(pointer, text.encode("ascii") + b"\0")
        rig.call(DRAW_TEXT, CANVAS, font, (128 - (len(text) * width - 1)) // 2,
                 y, 0, len(text), pointer)


def _application(rig):
    """Application::draw et contrôleur réels, liste de vues vide et statut omis."""
    controller = APPLICATION + 64
    rig.w32(controller + 20, controller + 20)
    rig.w32(controller + 28, controller + 20)
    rig.uc.mem_write(controller + 32, b"\0")
    rig.uc.mem_write(0x404A90F8, b"\1")
    rig.w32(0x404A90F0, BUFFER_A)
    _install(rig, 0x400062E0, lambda args: 0)
    renders = []
    rig.uc.hook_add(UC_HOOK_CODE, lambda *args: renders.append(1),
                    begin=0x40076C1A, end=0x40076C1A)
    return controller, renders


def _redraw(stock, image, symbols, check):
    reference, _, _, _, reference_panel = _prepare(stock)
    altered, _, _, _, panel = _prepare(image, symbols)
    for rig in (reference, altered):
        _background(rig)
    ref_controller, ref_renders = _application(reference)
    controller, renders = _application(altered)
    for rig in (reference, altered):
        rig.call(0x400075DA, APPLICATION)
    check(not ref_renders and not renders and reference.r32(BUF_PTRS) == altered.r32(BUF_PTRS),
          "rafraîchissement : vraie Application::draw inactive tant qu'aucun accord n'est tenu")
    _key(altered, 1, True)
    altered.uc.mem_write(INTERVALS, struct.pack(">4I", 0, 4, 7, 11))
    altered.call(symbols["ck_chord_live_publish"], 2, 48, INTERVALS, 4, 0)
    altered.call(0x400075DA, APPLICATION)
    first = panel.image()
    before = altered.r32(BUF_PTRS)
    altered.call(0x400075DA, APPLICATION)
    check(len(renders) == 1 and altered.r32(BUF_PTRS) == before
          and altered.uc.mem_read(controller + 32, 1) == b"\0",
          "rafraîchissement : première frappe reconstruit et envoie l'écran ; accord stable sans redraw forcé")
    # Aucune nouvelle touche : le moteur seul publie une autre palette/pad.
    altered.uc.mem_write(INTERVALS, struct.pack(">4I", 0, 4, 11, 18))
    altered.call(symbols["ck_chord_live_publish"], 2, 48, INTERVALS, 4, 4)
    altered.call(0x400075DA, APPLICATION)
    check(len(renders) == 2 and altered.r32(BUF_PTRS) != before and panel.image() != first,
          "rafraîchissement : variation sonore publiée sans touche redessine nom et basse")
    _key(altered, 1, False)
    altered.call(0x400075DA, APPLICATION)
    reference.uc.mem_write(ref_controller + 32, b"\1")
    reference.call(0x400075DA, APPLICATION)
    check(len(renders) == 3 and panel.image() == reference_panel.image()
          and _sentinels(altered) and _sentinels(reference),
          "rafraîchissement : relâchement force le vrai effacement/re-dessin et retire intégralement le bandeau")
    altered.uc.mem_write(controller + 32, b"\1")
    altered.call(0x400075DA, APPLICATION)
    check(len(renders) == 4 and panel.image() == reference_panel.image(),
          "rafraîchissement : demande native préexistante conservée hors Chord Keys")


def run(stock, image, symbols, check):
    reference, _, _, _, original_panel = _prepare(stock)
    altered, config, selected, machine, panel = _prepare(image, symbols)
    _background(reference)
    reference.call(FLUSH)
    stock_screen = original_panel.image()
    _background(altered)
    altered.call(FLUSH)
    check(panel.image() == stock_screen and _sentinels(altered),
          "écran : aucun accord tenu, flush/panneau exactement stock et aucun accès au projet avant l'UI")

    cases = (
        (1, [0, 4, 7, 11], 0, "Cmaj7", ""),
        (3, [0, 3, 10, 14], 0, "Em9", "no5"),
        (3, [0, 3, 10, 13], 0, "Em7(b9)", "no5"),
        (1, [0, 4, 11, 18], 4, "Cmaj7(#11)/E", "no5"),
        (7, [0, 6, 10, 21], 6, "Bm13b5/F", "no3,9,11"),
        (1, [0, 5, 7, 10], 0, "C7sus4", ""),
        (1, [7, 11, 14, 17], 7, "G7", ""),
        (1, [7, 11, 14, 17], 2, "G7/D", ""),
        (15, [0, 4, 7, 11], 11, "Cmaj7/B", "HIGH LIMIT", 0x400),
        (16, [0, 3, 7, 10], 10, "Dm7/C", "HIGH LIMIT", 0x400),
    )
    for key, intervals, bass, name, omissions, *flags in cases:
        _key(altered, key, True)
        note = altered.call(symbols["ck_ui_active_note"], 2)
        altered.uc.mem_write(INTERVALS, struct.pack(">4I", *intervals))
        altered.call(symbols["ck_chord_live_publish"], 2, note, INTERVALS, 4, bass)
        if flags:
            pointer = symbols["ck_chord_live"] + 8
            altered.w32(pointer, altered.r32(pointer) | flags[0])
        _background(altered)
        _background(reference)
        _expected(reference, name, omissions)
        reference.call(FLUSH)
        altered.call(FLUSH)
        actual = panel.image()
        check(actual == original_panel.image() and actual[20:] == stock_screen[20:]
              and _sentinels(altered)
              and altered.r32(BUF_PTRS) == BUFFER_B and altered.r32(BUF_PTRS + 4) == BUFFER_A,
              f"écran : {name} / {omissions or 'accord complet'}, vrais glyphes et DSPI à l'endroit, reste inchangé")
        _key(altered, key, False)

    for reason in ("relâchement", "autre piste", "autre machine", "Keys OFF", "instantané précédent"):
        selected[0], machine[0] = 2, 5
        config[2] |= 0x80000000
        if reason != "relâchement":
            _key(altered, 1, True)
        if reason == "autre piste":
            selected[0] = 1
        elif reason == "autre machine":
            machine[0] = 0
        elif reason == "Keys OFF":
            config[2] &= 0x7FFFFFFF
        elif reason == "instantané précédent":
            altered.w32(symbols["ck_chord_live"] + 8,
                        (altered.r32(symbols["ck_chord_live"] + 8) & ~127) | 50)
        _background(altered)
        altered.call(FLUSH)
        check(panel.image() == stock_screen and _sentinels(altered),
              f"écran : {reason}, aucun nom périmé et écran stock conservé")
        _key(altered, 1, False)
    check(not reference.bad and not altered.bad, "écran : aucun accès mémoire hors du banc")
    _redraw(stock, image, symbols, check)
