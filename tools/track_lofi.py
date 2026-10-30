"""Lo-fi de piste sur toutes les machines (notes/86) : écritures ajoutées à Model-TG.

Deux vrais paramètres de toutes les machines, Lo-Fi Rate (k 27) et Lo-Fi Bits (k 30) : descripteurs 1 et 2 (des
emplacements « Error » libres), groupe 7 (communs), drapeaux 0x600 (destinations des LFO et de la vélocité), posés par
le build.py de Model-TG comme ses Attack, Filtre et Résonance (MC_PATCHES de gen_model_tg.py) ; rangés avec le son dans
la case 18 de l'enregistrement (+64/+65, un octet chacun) par la fin de snd_save_post / snd_load_post, qui saute ici ;
réglés par MACHINES + COLOR / SHAPE sur toutes les machines (dh_pass et le descripteur du Sampler sous MACHINES, qui
sautent ici), affichés « OFF », « 46K » .. « 4K », « 12B » .. « 2B » comme le lo-fi de MACRO. Chaque saut remplace des
instructions de Model-TG à taille égale : aucun symbole ne bouge. Le code et les noms vont dans huit masques de sprite
48x22 libérés (tools/sprites.py), écrits avec Model-TG comme sampler_mode_filter.
"""
import pathlib
import subprocess
import tempfile

import gen_sdvintage_exact as gx
import sprites

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "machines" / "track_lofi"
BASE = 0x40000400
CAVES = {".cave": 0x4015943c, ".cave2": 0x4015f38c, ".cave3": 0x40165fec,    # masques 48x22 libérés (192 o)
         ".cave4": 0x40168da4, ".cave5": 0x4016dab8, ".cave6": 0x4016fae8, ".cave7": 0x40170c48,
         ".cave8": 0x40171a48}
# sx_side de Model-TG (le côté d'une piste Sampler stéréo, 6 x 128 o comme 0x80001858) et sx_on (stéréo dans ce
# bloc, par piste) : écrits en dur, comparé à sa
# table de symboles par check_syms (appelé par gen_model_tg.py) dans les deux variantes
SX_SIDE = 0x401b9f30
SX_ON = 0x401b9b24
# le son : après Volume + Dist (0x40056f58), comme le filtre par piste (notes/47 §2)
HOOK, HOOK_OLD = 0x40059852, "4eb940056f58"

NOTE = ("Lo-fi de piste (tools/track_lofi.py, notes/86) : Lo-Fi Rate (k 27) et Lo-Fi Bits (k 30), descripteurs 1 "
        "et 2, MACHINES + COLOR / SHAPE sur toutes les machines, rangés dans la case 18 de l'enregistrement du son.")


def lofi_khz(r):
    """Fréquence d'échantillonnage du pas r (1..64) de RATE, en kHz arrondis : celle du lo-fi de MACRO
    (gen_syntakt_engines.lofi_khz, macro.cc : RATE_STEP)."""
    return round(48 * 2 ** (-86 * r / 1536))


def lofi_inc(r):
    """Avance de la phase (Q16) par trame au pas r (1..64) de Rate : 65536 x 2^(-86 r / 1536), la même loi."""
    return round(65536 * 2 ** (-86 * r / 1536))


def compile_lofi():
    """{section: (adresse, octets)}, symboles."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "tl_tables.inc").write_text(
            ".macro TL_KHZ\n\t.byte\t" + ", ".join(str(lofi_khz(r)) for r in range(1, 65)) + "\n.endm\n"
            ".macro TL_INC\n\t.word\t" + ", ".join(str(lofi_inc(r)) for r in range(1, 65)) + "\n.endm\n",
            encoding="ascii")
        obj, elf = d / "tl.o", d / "tl.elf"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", f"-DSX_SIDE={SX_SIDE:#x}", f"-DSX_ON={SX_ON:#x}", "-Wa,-I" + str(d), "-c", str(SRC / "track_lofi.S"), "-o", str(obj)])
        gx.run([gx.CROSS + "ld", "-T", str(SRC / "track_lofi.ld"), "--no-warn-rwx-segments", "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        heads = subprocess.run([gx.CROSS + "objdump", "-h", str(elf)], capture_output=True, text=True,
                               check=True).stdout
        out = {}
        for line in heads.splitlines():
            p = line.split()
            if len(p) >= 4 and p[1] in CAVES:
                b = d / (p[1].strip(".") + ".bin")
                gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", p[1], str(elf), str(b)])
                out[p[1]] = (int(p[3], 16), b.read_bytes())
        return out, syms


SECS, SYMS = compile_lofi()
SAVE, LOAD, DH, ATK = SYMS["tl_save"], SYMS["tl_load"], SYMS["tl_dh"], SYMS["tl_atk"]
# (id, k, clé de tri, nom long, nom court) : après Attack (35), Filtre (36), Résonance (37) de Model-TG
DESCRIPTORS = ((0x01, 27, 38, SYMS["tl_s_rate"], SYMS["tl_s_rte"]),
               (0x02, 30, 39, SYMS["tl_s_bits"], SYMS["tl_s_bts"]))


def writes(stock):
    """Le code dans les masques et la redirection de leurs sprites."""
    out = []
    for name, mask in CAVES.items():
        addr, code = SECS[name]
        room = sprites.zone(mask)[1]
        if addr != mask or len(code) > room:
            raise SystemExit(f"!! track_lofi {name} : {len(code)} o à {addr:#x}, place {room} o à {mask:#x}")
        out += [{"off": addr - BASE, "old": stock[addr - BASE:addr - BASE + len(code)].hex(), "new": code.hex()},
                sprites.redirect_write(mask)]
    if stock[HOOK - BASE:HOOK - BASE + 6].hex() != HOOK_OLD:
        raise SystemExit(f"!! track_lofi : octets d'origine inattendus en {HOOK:#x}")
    out.append({"off": HOOK - BASE, "old": HOOK_OLD, "new": "4eb9" + f"{SYMS['tl_post']:08x}"})
    return out


def check_syms(syms):
    """sx_side de Model-TG, écrit en dur ci-dessus, contre la table de symboles de sa construction."""
    for name, want in (("sx_side", SX_SIDE), ("sx_on", SX_ON)):
        if syms.get(name) != want:
            raise SystemExit(f"!! track_lofi : {name} de Model-TG en {syms.get(name, 0):#x}, pas {want:#x}")


def build_rows():
    """Les lignes ajoutées au build.py de Model-TG, après ses Filtre et Résonance : nos deux descripteurs, posés comme
    les siens (groupe 7, k, 0..32512, défaut 0 = éteint, ni page ni potard, drapeaux 0x600, tri, noms, catégorie Amp)."""
    rows = ", ".join(f"(0x{i:02x},{k},{s},0x{ln:08x},0x{sn:08x})" for i, k, s, ln, sn in DESCRIPTORS)
    return (
        "# Modded-Cycles: track lo-fi (tools/track_lofi.py, notes/86), Lo-Fi Rate / Bits on k=27 / 30, two more\n"
        "# Error placeholders, laid out like Attack; names in our own cave.\n"
        f"for _id,_k,_sort,_ln,_sn in ({rows}):\n"
        "    _E=0x4010dce0+_id*56\n"
        "    assert bytes(d[_E-BASE:_E-BASE+8])==bytes.fromhex(\"ffffffffffffffff\"), \\\n"
        "        f\"param id 0x{_id:02x} is not the Error placeholder any more\"\n"
        "    d[_E-BASE:_E-BASE+56]=struct.pack('>14I', 7, _k, 0, 32512, 0, 0,\n"
        "        0xffffffff, 0xffffffff, 0, 0x600, _sort, _ln, 0x40129882, _sn)\n"
        "    print(f\"  param id 0x{_id:02x} -> k={_k} (track lo-fi)\")\n")
