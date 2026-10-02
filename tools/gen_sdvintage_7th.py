#!/usr/bin/env python3
"""Génère le tweak « sdvintage-7th » : le vrai SD VINTAGE du Syntakt en 7e machine « SDVtg », à côté de
SNARE, avec ses propres potards (notes/18).

Outil de développeur, comme gen_sdvintage_exact.py dont il reprend l'analyse du Syntakt (même moteur, même
passerelle). Il lit TON Syntakt_OS1.42.syx et TON model-cycles_OS1.13.syx pour ANALYSER et VÉRIFIER, mais
le tweak ne contient aucun firmware Elektron : nos écritures (chacune avec ses octets d'origine vérifiés),
notre code, et une recette de charge utile (plages de tes fichiers à copier, relocalisations).

Ce qui change dans l'OS Cycles (adresses : notes/18) :
  - moteur : bornes 5 -> 6, octet de correspondance, tables update/render à 7 entrées (entrée 6 = passerelle) ;
  - paramètre « Algorithm » : max 5 -> 6 (menu MACHINES, machine locks, CC 70) ;
  - descripteurs : la table de 76 entrées est recopiée en SDRAM avec 5 entrées de plus pour SDVtg
    (INHM, FCMP, SWEP, MENV et Amp Decay, défauts du Syntakt) ; ses 37 références et 43 bornes suivent.
    L'ancienne table reste en place, intacte ;
  - état par descripteur (76 objets de 100 o) : SDVtg partage ceux de SNARE ;
  - tables par machine construites au démarrage : une 7e rangée (déplacées en SDRAM) ;
  - écran MACHINES : 7e nom « SDVtg », 7e repère, icônes de SNARE ; autres icônes : SNARE pour SDVtg.

    python3 tools/gen_sdvintage_7th.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
    python3 tools/gen_sdvintage_7th.py --cycles ... --syntakt ... --check
"""
import argparse
import json
import pathlib
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import syntakt                     # noqa: E402
from build import unwrap, container, aplib   # noqa: E402

DST = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "22-sdvintage-7th.json"
BASE = gx.BASE
MACHINE = 6                                    # index de SDVtg dans les tables des machines

# --- OS Cycles 1.13 --------------------------------------------------------------------------------
DESC, NDESC, DSTRIDE = 0x4010dce0, 76, 0x38    # descripteurs de paramètres
SNARE_DESC = 51                                # COLOR, SHAPE, SWEEP, CONTOUR de SNARE, puis son Amp Decay (55)
ALG_DESC = 41                                  # « Algorithm » : le choix de la machine
ROWS, CCROWS = 0x40a79418, 0x40a7ada4          # tables par machine du BSS (6 x 32 o), construites par 0x4005a274
NAMES = 0x401177e4                             # 6 noms de machines (écran MACHINES)
RENDER_TAB, UPDATE_TAB, ENGINE_MAP = 0x40118610, 0x40118628, 0x40118640
MOVEQ = {76: 81, 75: 80}                       # nombre de descripteurs : bornes d'index
# Bornes « nombre de descripteurs » (moveq #76 / #75) des accesseurs de la table, relevées dans le
# désassemblage : toutes dans des fonctions qui lisent la table, schéma « cmp ; shi ; and » ou « cmp ; bcs ».
# Exclues : 0x4004df68 / 0x4004df82 (taille d'une structure de son de 76 o, PAS le nombre de descripteurs)
# et 0x4004df40 / 0x4004dfa2 (état par descripteur : détours state_at / state_connect).
BOUNDS = (
    0x4000a93e, 0x4000a95e, 0x4000a984, 0x4000aa52, 0x4000b208, 0x4000b22a, 0x4000b3e4, 0x4000b476,
    0x4000b51a, 0x4000b65a, 0x4000b6ec, 0x4000b788, 0x4000b946, 0x4001d5e2, 0x4001d8ee, 0x4001d90e,
    0x4001e026, 0x4001f326, 0x40022a7c, 0x40022afe, 0x40029e78, 0x40029e98, 0x4002b430, 0x40046d5c,
    0x4004e31e, 0x4004e3ba, 0x4005a368, 0x4005a4e8, 0x4005a50a, 0x4005a52c, 0x4005a556, 0x4005a582,
    0x4005a5cc, 0x4005a5fe, 0x4005a628, 0x4005a65c, 0x4005a76a, 0x4005a7aa, 0x4005a7d0, 0x4005a7f8,
    0x4005a81a, 0x4005a83c, 0x4005a85e,
)
# (adresse, octets d'origine, nouveaux octets) : bornes « machine <= 5 » et autres constantes
SMALL = (
    (0x400a7dba, "7205", "7206"),              # boucle des voix : machine au déclenchement <= 6
    (0x400a7df4, "7005", "7006"),              # garde du dispatch update/render
    (ENGINE_MAP + 6, "00", "06"),              # machine 6 -> moteur 6
    (0x4005a2b8, "487800c0", "487800e0"),      # constructeur : efface 7 rangées au lieu de 6
    (0x4005a340, "7005", "7006"),              # constructeur : descripteur propre à une machine si machine <= 6
    (0x4005a572, "7205", "7206"),              # « descripteur propre à une machine » : machine <= 6
    (0x4005a6a6, "7205", "7206"),              # recherche (slot, machine) -> descripteur : machine <= 6
    (0x400147a4, "7005", "7006"),              # réglage de la machine d'une piste (0x4001477e) : accepte 6
    (0x400148aa, "7205", "7206"),              # molette de l'écran MACHINES (0x4001488a) : machine + pas,
    (0x400148b2, "7005", "7006"),              # bornée à 6 au lieu de 5 (comparaison, puis valeur)
    (0x400a25e0, "7005", "7006"),              # écran MACHINES : nom et images jusqu'à 6
    (0x400a26e8, "7006", "7007"),              # écran MACHINES : 7 repères de position
    (0x4001b69c, "7005", "7001"),              # icônes bornées : SNARE (1) au lieu de CHORD (5) au-delà de 5
    (0x400a40a6, "7005", "7001"),
    (0x400a4fb0, "7005", "7001"),
)
# (adresse, octets d'origine, symbole du détour) : « jmp détour » à la place d'instructions entières
JUMPS = (
    (0x4004df40, "704c222f0004", "state_at"),
    (0x4004dfa2, "704c222f0004", "state_connect"),
    (0x4005a8f0, "7405b4816532", "cc_bounds"),
    (0x400a2638, "eb8c48780001", "drum_icons"),
    (0x400a4dc4, "700541e8000a", "small_icon"),
    (0x4004df5c, "7206202f0004", "record_at"),    # enregistrement par machine (index machine + 1)
    (0x4004df76, "7205202f0004", "record_of"),    # enregistrement par machine (index machine)
)
# (adresse, octets d'origine, symbole) : « jsr détour ; nop » à la place de deux instructions (8 o)
CALLS = (
    (0x4001e8da, "202f0020226a0068", "knob_vec"),  # potard -> descripteur : machine -> enregistrement
)

# --- SDVtg : noms et défauts du Syntakt (manuel Syntakt, section SD VINTAGE) ---------------------------
NAME = "SDVtg"
# Noms longs : ceux du Syntakt, raccourcis pour tenir à l'écran. La fenêtre des potards coupe le nom aux
# espaces (0x40096320) et centre chaque mot sur ~32 pixels : un mot ne doit pas dépasser la largeur de ceux de
# l'OS (« Velocity », « Envelope », 8 lettres). « Inharmonicity » puis « Inharmonic » dépassaient (essais du 30/09).
KNOBS = (  # (nom long, nom court, défaut) pour COLOR, SHAPE, SWEEP, CONTOUR
    ("Inharm", "INHM", 0), ("Freq Complex", "FCMP", 110), ("Pitch Sweep", "SWEP", 74),
    ("Mod Envelope", "MENV", 80),
)
DECAY_DEFAULT = 33

# --- charge utile, après celle du moteur exact (0x43000000..0x43033000) --------------------------------
STUBS = 0x43033000                             # machine7.S
DATA = 0x43033800                              # noms, tables update/render, VEC7, chaînes
VEC7 = DATA + 84                               # machine -> enregistrement, 7 entrées [1..7] (écran principal)
DESC7 = 0x43034000                             # 81 descripteurs
NDESC7 = NDESC + 5
ROWS7 = 0x43035200                             # 7 x 32 o
CCROWS7 = 0x43035300                           # 7 x 32 o
REC8 = 0x43035400                              # 8e enregistrement par machine (SDVtg), 76 o, construit au 1er usage
REC8_BUILT = REC8 + 76
END = 0x43035460


def be32(x):
    return struct.pack(">I", x & 0xffffffff)


def cycles_main(path):
    stream, _ = unwrap(pathlib.Path(path).read_bytes())
    c = container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    return aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]


def refs32(img, v):
    b, out, i = be32(v), [], img.find(be32(v))
    while i >= 0:
        if i % 2 == 0:
            out.append(BASE + i)
        i = img.find(b, i + 1)
    return out


def compile_stubs(tmp):
    obj, elf, out = tmp / "m7.o", tmp / "m7.elf", tmp / "m7.bin"
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(gx.SRC / "machine7.S"), "-o", str(obj),
            f"-DREC8={REC8:#x}", f"-DREC8_BUILT={REC8_BUILT:#x}", f"-DVEC7={VEC7:#x}"])
    gx.run([gx.CROSS + "ld", "-Ttext", f"{STUBS:#x}", "-o", str(elf), str(obj)])
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".text", str(elf), str(out)])
    syms = {p[-1]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(elf)]).splitlines())
            if len(p) == 3}
    blob = out.read_bytes()
    if STUBS + len(blob) > DATA:
        raise SystemExit("!! détours trop grands")
    return blob, syms


def build_tweak(img, st_img):
    u32 = lambda va: struct.unpack_from(">I", img, va - BASE)[0]
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        ins = gx.disasm(st_img, tmp)
        funcs, insns = gx.closure(ins)
        relocs = gx.relocations(st_img, ins, insns)
        size = END - gx.DST_CODE
        blobs, syms, data_end = gx.compile_bridge(tmp, size // 4)
        if data_end > gx.DST_END:
            raise SystemExit("!! données de la passerelle trop grandes")
        stubs, ssyms = compile_stubs(tmp)

    # --- données : noms, tables update/render à 7 entrées, chaînes
    data = bytearray()
    strings = {}

    def string(s):
        if s not in strings:
            strings[s] = s
        return s
    for s in [NAME] + [k[0] for k in KNOBS] + [k[1] for k in KNOBS]:
        string(s)
    tables = 4 * 7 * 4
    at, addr = DATA + tables, {}
    for s in strings:
        addr[s] = at
        at += len(s) + 1
    names7 = [u32(NAMES + 4 * i) for i in range(6)] + [addr[NAME]]
    upd7 = [u32(UPDATE_TAB + 4 * i) for i in range(6)] + [syms["bridge_update"]]
    rnd7 = [u32(RENDER_TAB + 4 * i) for i in range(6)] + [syms["bridge_render"]]
    for t in (names7, upd7, rnd7, range(1, 8)):
        data += b"".join(be32(x) for x in t)
    if DATA + 84 != VEC7:
        raise SystemExit("!! VEC7")
    for s in strings:
        data += s.encode("ascii") + b"\0"
    if DATA + len(data) > DESC7:
        raise SystemExit("!! données trop grandes")
    NAMES7, UPD7, RND7 = DATA, DATA + 28, DATA + 56

    # --- 5 descripteurs de SDVtg, sur le modèle de ceux de SNARE (mêmes slots, plages, CC, drapeaux)
    new = bytearray()
    for k, (long_, short, default) in enumerate(KNOBS):
        e = bytearray(img[DESC + (SNARE_DESC + k) * DSTRIDE - BASE:][:DSTRIDE])
        e[0x00:0x04] = be32(MACHINE)
        e[0x10:0x14] = be32(default << 8)
        e[0x2c:0x30] = be32(addr[long_])
        e[0x34:0x38] = be32(addr[short])
        new += e
    e = bytearray(img[DESC + (SNARE_DESC + 4) * DSTRIDE - BASE:][:DSTRIDE])   # Amp Decay propre à la machine
    e[0x10:0x14] = be32(DECAY_DEFAULT << 8)
    new += e
    if struct.unpack_from(">I", new, 0x30)[0] != u32(DESC + SNARE_DESC * DSTRIDE + 0x30):
        raise SystemExit("!! descripteurs")

    # --- écritures dans l'OS Cycles
    writes = []

    def w(va, old, new_):
        if img[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! {va:#x} : {old.hex()} attendu, {img[va - BASE:va - BASE + len(old)].hex()} trouvé")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

    stub = blobs[".stub"]
    w(gx.CAVE, b"\xff" * len(stub), stub)
    writes.append(sprites.redirect_write(gx.CAVE))
    w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), bytes.fromhex("4ef9") + be32(gx.CAVE) + bytes.fromhex("4e71"))
    moved = {DESC: DESC7, DESC + 8: DESC7 + 8, DESC + 0x20: DESC7 + 0x20,
             ROWS: ROWS7, CCROWS: CCROWS7, NAMES: NAMES7, UPDATE_TAB: UPD7, RENDER_TAB: RND7}
    count = {}
    for old, new_ in moved.items():
        rs = refs32(img, old)
        count[old] = len(rs)
        for va in rs:
            w(va, be32(old), be32(new_))
    expect = {DESC: 34, DESC + 8: 1, DESC + 0x20: 2, ROWS: 5, CCROWS: 2, NAMES: 1, UPDATE_TAB: 1, RENDER_TAB: 1}
    if count != expect:
        raise SystemExit(f"!! références : {count}")
    for va in BOUNDS:
        n = img[va - BASE + 1]
        if img[va - BASE] & 0xf1 != 0x70 or n not in MOVEQ:
            raise SystemExit(f"!! {va:#x} n'est pas moveq #75/#76")
        w(va, img[va - BASE:va - BASE + 2], bytes([img[va - BASE], MOVEQ[n]]))
    for va, old, new_ in SMALL:
        w(va, bytes.fromhex(old), bytes.fromhex(new_))
    for va, old, sym in JUMPS:
        w(va, bytes.fromhex(old), bytes.fromhex("4ef9") + be32(ssyms[sym]))
    for va, old, sym in CALLS:
        w(va, bytes.fromhex(old), bytes.fromhex("4eb9") + be32(ssyms[sym]) + bytes.fromhex("4e71"))
    writes.sort(key=lambda x: x["off"])
    for a, b in zip(writes, writes[1:]):
        if a["off"] + len(a["new"]) // 2 > b["off"]:
            raise SystemExit(f"!! écritures qui se chevauchent en {BASE + b['off']:#x}")

    # --- recette de la charge utile
    parts = [{"dest": f"{dst:#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]} for lo, hi, dst in gx.SEGMENTS[:3]]
    for lo, hi, dst in gx.ST_SRAM_INIT:
        parts.append({"dest": f"{gx.move(dst):#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]})
    parts += [
        {"dest": f"{gx.DST_BRIDGE:#x}", "hex": blobs[".bridge"].hex()},
        {"dest": f"{STUBS:#x}", "hex": stubs.hex()},
        {"dest": f"{DATA:#x}", "hex": bytes(data).hex()},
        {"dest": f"{DESC7:#x}", "cycles": [f"{DESC:#x}", f"{DESC + NDESC * DSTRIDE:#x}"]},
        {"dest": f"{DESC7 + NDESC * DSTRIDE:#x}", "hex": bytes(new).hex()},
    ]
    reloc = [[f"{gx.move(va):#x}", gx.be32(old), gx.be32(new_)] for va, old, new_ in relocs]
    alg_max = DESC + ALG_DESC * DSTRIDE + 0x0c
    if u32(alg_max) != 5 << 8:
        raise SystemExit("!! max du paramètre Algorithm")
    reloc.append([f"{alg_max - DESC + DESC7:#x}", gx.be32(5 << 8), gx.be32(6 << 8)])
    code_bytes = sum(ins[a][0] for a in insns)
    return {
        "id": "sdvintage-7th",
        "order": 22,
        "name": "Vrai moteur SD VINTAGE du Syntakt en 7e machine (SDVtg), a cote de SNARE",
        "description": [
            "Le moteur SD VINTAGE du Syntakt (OS 1.42 ou 1.41), extrait AU BUILD de TON Syntakt_OS1.42.syx",
            f"({len(funcs)} fonctions, {code_bytes} o de code, avec ses tables), en 7e machine « {NAME} » :",
            "SNARE reste la SNARE d'origine. Potards propres, noms et defauts du Syntakt :",
            "COLOR=INHM (Inharm), SHAPE=FCMP, SWEEP=SWEP (Pitch Sweep), CONTOUR=MENV (Mod Envelope),",
            "DECAY=DEC ; defauts 0 / 110 / 74 / 80 / 33. Menu MACHINES, machine locks et CC 70 (valeur 6).",
            "Table des descripteurs recopiee en SDRAM avec 5 entrees de plus (notes/18).",
            "Demande build.py --syntakt Syntakt_OS1.42.syx. Aucun octet Elektron dans ce fichier.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": ["sdvintage-snare", "sdvintage-exact"],
        "writes": writes,
        "append": {
            "at": f"{BASE + gx.IMAGE_LEN:#x}",
            "dest": f"{gx.DST_CODE:#x}",
            "size": size,
            "syntakt": {"os": dict(syntakt.OFFICIAL), "section": 7, "section_sha256": syntakt.DSP_SHA256},
            "parts": parts,
            "reloc": reloc,
        },
    }, funcs, code_bytes, ssyms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que le JSON versionné correspond")
    args = ap.parse_args()
    img = cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak, funcs, code_bytes, ssyms = build_tweak(img, syntakt.dsp_image(args.syntakt))
    text = json.dumps(tweak, indent=1) + "\n"
    ap_ = tweak["append"]
    print(f"  {len(tweak['writes'])} écritures ; charge utile {ap_['size']} o -> {ap_['dest']} ;"
          f" détours {', '.join(f'{s} {ssyms[s]:#x}' for _, _, s in JUMPS)}")
    if args.check:
        if not DST.exists() or DST.read_text(encoding="utf-8") != text:
            raise SystemExit(f"!! {DST.name} ne correspond pas (autre GCC ?)")
        print(f"  {DST.name} est à jour")
        return
    DST.write_text(text, encoding="utf-8")
    print(f"  écrit : {DST.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
