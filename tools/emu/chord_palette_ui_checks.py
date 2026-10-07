"""Preuves COLOR/PALETTE sur le vrai formatter et le dessin OS (notes/40).

Appelé par test_chord_keys.py. Les objets de piste et allocations sont simulés,
mais sprintf, std::string, les métriques et les pixels de police sont exécutés.
Les replis sont comparés aux mêmes routines de l'image stock.
"""
import struct

from chord_ui_checks import HEADER, _install, _ui_rig
import test_sdvintage_7th as t7


BANK, OUTPUT, SPRITE = 0x93130000, 0x93131000, 0x93132000
CANVAS, PIXELS, STRING, LABEL = 0x93133000, 0x93134010, 0x93135000, 0x93135100


def _prepare(firmware, exported=None):
    rig, config, selected, machine, _ = _ui_rig(firmware, exported)
    payload = firmware[t7.E.IMAGE_LEN:]
    if payload:
        rig.uc.mem_map(t7.E.PAYLOAD_DST, (len(payload) + 0xFFFFF) & ~0xFFFFF)
        rig.uc.mem_write(t7.E.PAYLOAD_DST, bytes(payload))
    drawn = []
    _install(rig, 0x4000EB9C, lambda a: BANK)
    _install(rig, 0x4000C0A6, lambda a: 1)
    _install(rig, 0x40072058, lambda a: SPRITE)
    _install(rig, 0x40071DA4, lambda a: drawn.append(a[:6]) or 0)
    heap = [0x93200000]

    def allocate(args):
        pointer = heap[0]
        heap[0] += (args[0] + 15) & ~15
        rig.uc.mem_write(pointer, bytes(args[0]))
        return pointer

    _install(rig, 0x400802E0, allocate)
    _install(rig, 0x400802EC, lambda a: 0)
    rig.uc.mem_write(CANVAS, struct.pack(">5I", 0, 128, 64, 2, PIXELS))
    for track in range(6):
        rig.w32(BANK + 504 + 8 * track, 0x400FD134)
    rig.w32(0x40A70710, 1)
    rig.w32(0x40A70714, 0x400456C8)
    for descriptor in (51, 71, 72):
        record = 0x40A71754 + 100 * descriptor
        rig.w32(record + 28, 1)
        rig.w32(record + 32, 0x4004DFDA if descriptor == 72 else 0x400456C8)
        rig.w32(record + 44, 1)
        rig.w32(record + 48, 0x4004611E)
    return rig, config, selected, machine, drawn


def _text(rig, function, obj, descriptor, value):
    rig.uc.mem_write(OUTPUT, b"\xa5" * 64)
    rig.call(function, obj, descriptor, value & 0xFFFFFFFF, OUTPUT)
    return bytes(rig.uc.mem_read(OUTPUT, 64)).split(b"\0", 1)[0].decode("ascii")


def _cstr(rig, pointer):
    return bytes(rig.uc.mem_read(pointer, 32)).split(b"\0", 1)[0].decode("ascii")


def run(stock, image, symbols, check):
    """check(bool, libellé) est fourni par la preuve principale."""
    symbols = {name: int(value, 16) if isinstance(value, str) else value
               for name, value in symbols.items()}
    reference, _, _, ref_machine, stock_drawn = _prepare(stock)
    altered, config, selected, machine, drawn = _prepare(image, symbols)
    format_fn, draw_fn = altered.r32(0x400FD170), altered.r32(0x400FD174)
    name_fn = altered.r32(0x4001E4CC)
    labels = ("DIATONIC", "JAZZ", "TENSION")
    values = sorted({-32768, -1, 32767, *range(0, 128 << 8, 256),
                     *((boundary << 8) + delta for boundary in (43, 86) for delta in (-1, 0, 1))})
    before = bytes(altered.uc.mem_read(HEADER, 64))
    valid = True
    for track in range(6):
        obj = BANK + 504 + 8 * track
        selected[0] = (track + 1) % 6
        for value in values:
            expected = labels[0 if value < 43 * 256 else 1 if value < 86 * 256 else 2]
            actual = _text(altered, format_fn, obj, 71, value)
            valid &= actual == expected
        valid &= _cstr(altered, altered.call(name_fn, obj, 71)) == "Chord Palette"
    check(valid and bytes(altered.uc.mem_read(HEADER, 64)) == before,
          "COLOR UI : Chord Palette, trois noms, toutes bornes 8.8 signées, six pistes indépendantes")

    # Les huit caractères de DIATONIC doivent entrer réellement dans 64 pixels,
    # pas seulement être tronqués par le canevas à la droite de l'écran.
    valid, pictures = True, set()
    for value, label in zip((0, 43 << 8, 86 << 8), labels):
        altered.uc.mem_write(LABEL, label.encode("ascii") + b"\0")
        altered.call(0x400F980C, STRING, LABEL, OUTPUT)
        width = altered.call(0x40072102, 0x4014120C, 0xFFFFFFFF, STRING)
        valid &= width == len(label) * 8 - 1 and width <= 64
        altered.call(0x400F7D5C, STRING)
        altered.uc.mem_write(PIXELS - 16, b"\xa5" * 16 + bytes(1024) + b"\xa5" * 16)
        drawn.clear()
        valid &= altered.call(draw_fn, BANK + 504, 71, value, 1, CANVAS, 96, 34) == 1
        valid &= not drawn
        picture = bytes(altered.uc.mem_read(PIXELS, 1024))
        pictures.add(picture)
        lit = [(x, y) for x in range(128) for y in range(64)
               if struct.unpack_from(">I", picture, 8 * x + 4 * (y // 32))[0] & (1 << (31 - y % 32))]
        valid &= bool(lit) and all(64 <= x <= 127 and 40 <= y <= 48 for x, y in lit)
        valid &= bytes(altered.uc.mem_read(PIXELS - 16, 16)) == b"\xa5" * 16
        valid &= bytes(altered.uc.mem_read(PIXELS + 1024, 16)) == b"\xa5" * 16
    check(valid and len(pictures) == 3,
          "COLOR UI : vrais glyphes DIATONIC/JAZZ/TENSION, police 4014120c, largeur maximale63 px")

    valid = True
    for why, track, descriptor, chord, enabled, revision, offset in (
            ("Keys OFF", 2, 71, True, False, 1, 0),
            ("autre piste OFF", 4, 71, True, False, 1, 0),
            ("autre machine", 2, 71, False, True, 1, 0),
            ("autre paramètre", 2, 51, True, True, 1, 0),
            ("objet extérieur", 2, 71, True, True, 1, 2)):
        selected[0] = 0
        config[track] = (48 << 21) | (0x80000000 if enabled else 0)
        machine[0] = ref_machine[0] = 5 if chord else 0
        obj = BANK + 504 + 8 * track + offset
        if offset:
            altered.w32(obj, 0x400FD134)
            reference.w32(obj, 0x400FD134)
        case_ok = True
        for value in (0, 32 << 8, 43 << 8, 86 << 8, 127 << 8):
            case_ok &= _text(altered, format_fn, obj, descriptor, value) == \
                _text(reference, 0x4000A70E, obj, descriptor, value)
            drawn.clear()
            stock_drawn.clear()
            args = (obj, descriptor, value, 1, OUTPUT, 96, 34)
            case_ok &= altered.call(draw_fn, *args) == reference.call(0x4000A66A, *args)
            case_ok &= drawn == stock_drawn
        case_ok &= _cstr(altered, altered.call(name_fn, obj, descriptor)) == \
            _cstr(reference, reference.call(0x4000B22A, obj, descriptor))
        check(case_ok, f"COLOR UI : {why}, noms, formatter et dessin natifs inchangés")
        config[track] = (48 << 21) | 0x80000000
        valid &= case_ok
    check(valid and not altered.bad and not reference.bad,
          "COLOR UI : tous replis vérifiés et aucun accès mémoire hors du banc")
