"""Ce que hot_boot (le chargeur du code chaud, notes/76) écrit au démarrage, pour les preuves qui exécutent le vrai
crochet de démarrage (test_payload_pack.py, test_macro_syntakt.py, donc test_modal.py) : chaque entrée détournée
porte « jmp talon », rien d'autre ne change dans l'image de l'OS, ses variables sont à part."""
import struct

BASE = 0x40000400
MAGIC = 0x484f5421


def effects(uc, img, dst, got, rt, syms):
    """(ok, message, charge utile obtenue, attendue) : les deux sans les octets que hot_boot a le droit d'écrire
    (entrées détournées de la charge utile, variables du chargeur), après avoir vérifié ces octets."""
    import gen_sram_hot as gh                             # noqa: E402  (tools/)
    nu, nd, nr = struct.unpack_from(">3H", rt, syms["hot_n"] - dst)
    dets = [struct.unpack_from(">IHHHBB", rt, syms["hot_dets"] - dst + 12 * i) for i in range(nd)]
    now = bytes(uc.mem_read(BASE, len(img)))
    got, rt = bytearray(got), bytearray(rt)
    ok, sites, live = True, [], 0
    for i, (at, _, _, sm, k, _) in enumerate(dets):
        src = img[at - BASE:at - BASE + k] if at < BASE + len(img) else bytes(rt[at - dst:at - dst + k])
        if sum(src) & 0xffff != sm:
            continue
        live += 1
        jmp = b"\x4e\xf9" + (syms["hot_stubs"] + 8 * i).to_bytes(4, "big")
        if at < BASE + len(img):
            ok &= now[at - BASE:at - BASE + 6] == jmp
            sites.append((at - BASE, at - BASE + 6))
        else:
            ok &= bytes(got[at - dst:at - dst + 6]) == jmp
            got[at - dst:at - dst + 6] = rt[at - dst:at - dst + 6]
    rest = bytearray(now)
    for lo, hi in sites:
        rest[lo:hi] = img[lo:hi]
    a, b = gh.HOT_RAM - dst, gh.HOT_END - dst
    got[a:b], rt[a:b] = bytes(b - a), bytes(b - a)
    booted = struct.unpack(">I", uc.mem_read(syms["hot_booted"], 4))[0] == MAGIC
    msg = (f"code chaud : hot_boot a posé ses {live}/{nd} détours ({len(sites)} dans l'OS, {live - len(sites)} dans la "
           "charge utile), rien d'autre dans l'OS")
    return ok and live == nd and bytes(rest) == img and booted, msg, bytes(got), bytes(rt)
