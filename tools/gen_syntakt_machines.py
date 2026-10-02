#!/usr/bin/env python3
"""Génère le tweak « syntakt-vintage » : les vrais moteurs SD VINTAGE et CP VINTAGE du Syntakt en 7e et
8e machines « SDVtg » et « CPVtg », à côté des 6 machines d'origine (notes/19).

Même méthode que gen_sdvintage_7th.py (notes/18, testé sur la machine), étendue à deux machines :
  - moteur : la fermeture du Syntakt comprend update/render des moteurs 6 et 7 (30 fonctions), plus les
    tables de CP VINTAGE ; passerelle bridge_multi.c (un moteur du Syntakt par machine ajoutée) ;
  - OS Cycles : bornes des machines 5 -> 7, tables à 8 entrées, 86 descripteurs (76 d'origine + 5 + 5),
    enregistrements par machine 7 et 8, écran MACHINES à 8 noms et 8 repères.
Il lit TON Syntakt_OS1.42.syx et TON model-cycles_OS1.13.syx pour analyser et vérifier ; le tweak ne
contient aucun firmware Elektron (écritures avec octets d'origine vérifiés, notre code, recette de copie).

    python3 tools/gen_syntakt_machines.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx [--check]
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
import gen_sdvintage_7th as g7     # noqa: E402
import sprites                     # noqa: E402
import syntakt                     # noqa: E402

DST = HERE.parent / "tweaks" / "model-cycles_OS1.13" / "23-syntakt-vintage.json"
BASE = gx.BASE

# --- les machines ajoutées : (index Cycles, nom, moteur du Syntakt, potards, DECAY, image) -----------------
# Potards : (nom long, nom court, défaut) pour COLOR, SHAPE, SWEEP, CONTOUR = p1..p4 du Syntakt.
# Noms et défauts : descripteurs de l'interface du Syntakt (section 3, 0x4022ff74.., 0x40230114..), noms
# longs coupés en mots de 8 lettres au plus (la fenêtre des potards affiche un mot par ligne, notes/18 §10).
MACHINES = (
    dict(index=6, name="SDVtg", engine=6, update=0x40008074, render=0x4000847a, image=1, decay=33,
         knobs=(("Inharm", "INHM", 0), ("Freq Complex", "FCMP", 110), ("Pitch Sweep", "SWEP", 74),
                ("Mod Envelope", "MENV", 80))),
    dict(index=7, name="CPVtg", engine=7, update=0x40008580, render=0x40008988, image=3, decay=32,
         knobs=(("Body Char", "BODY", 24), ("Balance", "BAL", 25), ("Spacing Crunch", "SPCR", 46),
                ("Body Envelope", "BENV", 37))),
)
NMACH = 6 + len(MACHINES)                       # 8
NDESC = g7.NDESC + 5 * len(MACHINES)            # 86

# --- moteur du Syntakt : fermeture et plages copiées ---------------------------------------------------
ROOTS = gx.ROOTS + (0x40008580, 0x40008988)     # + update/render de CP VINTAGE
SEGMENTS = (                                     # (source Syntakt, fin, destination)
    (0x40002544, 0x40008ae8, 0x43000000),       # les 30 fonctions (plage contiguë)
    (0x4000e488, 0x40010490, 0x43006600),       # table centrée sur 0x4000f48c (8 Ko), CP VINTAGE
    (0x40014980, 0x40016b90, 0x43008800),       # constantes + 2 tables de 4 Ko (0x40014b80, 0x40015b80)
    (0x40028438, 0x4003be38, 0x4300ac00),       # DEC x MENV, tables de 512 o (SD et CP VINTAGE)
    (0x80000000, 0x80010000, 0x43020000),       # réplique de sa SRAM
    (0x4404f000, 0x44050000, 0x43030000),       # fenêtre de son BSS
)
IMM_ADDR = {0x40014b80, 0x40015b80, 0x4000f48c, 0x4000e488, 0x80004a50, 0x80004a70, 0x80004af0}  # movea #adr

# --- charge utile ------------------------------------------------------------------------------------------
DST_BRIDGE = 0x43031000
STUBS = 0x43033000                              # machine8.S
DATA = 0x43033800                               # 8 noms, update/render à 8 entrées, VEC8, chaînes
NAMES8, UPD8, RND8, VEC8 = DATA, DATA + 32, DATA + 64, DATA + 96
DESC8 = 0x43034000                              # 86 descripteurs (0x12d0 o)
ROWS8 = 0x43035300                              # 8 x 32 o
CCROWS8 = 0x43035400                            # 8 x 32 o
REC8, REC9 = 0x43035500, 0x43035560             # enregistrements par machine de SDVtg et CPVtg (76 o + drapeau)
END = 0x430355c0

MOVEQ = {76: NDESC, 75: NDESC - 1}
# Le champ « machine » d'un descripteur vaut 7 pour « toutes les machines » : ceux de CPVtg portent 6 et sont
# rattachés à la machine 7 par deux détours (constructeur des tables, machine du descripteur).
DESC_FIELD = {6: 6, 7: 6}
JUMPS8 = (
    (0x4005a50a, "724c202f0004", "desc_machine"),    # remplace aussi sa borne (retirée de BOUNDS ici)
    (0x4005a340, "7005b085643e", "builder_row"),
)
SMALL = (
    (0x400a7dba, "7205", "7207"),              # boucle des voix : machine au déclenchement <= 7
    (0x400a7df4, "7005", "7007"),              # garde du dispatch update/render
    (g7.ENGINE_MAP + 6, "0000", "0607"),       # machines 6, 7 -> entrées 6, 7 des tables
    (0x4005a2b8, "487800c0", "48780100"),      # constructeur : efface 8 rangées
    (0x4005a572, "7205", "7206"),              # « descripteur propre à une machine » : champ <= 6 (7 = toutes)
    (0x4005a6a6, "7205", "7207"),              # recherche (slot, machine) -> descripteur : machine <= 7
    (0x400147a4, "7005", "7007"),              # réglage de la machine d'une piste (0x4001477e) : <= 7
    (0x400148aa, "7205", "7207"),              # molette (0x4001488a) : machine + pas bornée à 7
    (0x400148b2, "7005", "7007"),
    (0x400a25e0, "7005", "7007"),              # écran MACHINES : nom et images jusqu'à 7
    (0x400a26a2, "7850", "7849"),              # écran MACHINES : repères à partir de x = 73 (8 repères tiennent)
    (0x400a26e8, "7006", "7008"),              # écran MACHINES : 8 repères
    (0x4001b69c, "7005", "7001"),              # icônes bornées : SNARE au-delà de 5
    (0x400a40a6, "7005", "7001"),
    (0x400a4fb0, "7005", "7001"),
)


def compile_code(tmp, payload_longs):
    """Passerelle (bridge_multi.c + stub.S, link.ld de la passerelle) et détours (machine8.S)."""
    obj, stub, elf = tmp / "bridge.o", tmp / "stub.o", tmp / "bridge.elf"
    gx.run([gx.CROSS + "gcc", *gx.CFLAGS, "-c", str(gx.SRC / "bridge_multi.c"), "-o", str(obj)])
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(gx.SRC / "stub.S"), "-o", str(stub),
            f"-DPAYLOAD_SRC={BASE + gx.IMAGE_LEN:#x}", f"-DPAYLOAD_DST={gx.DST_CODE:#x}", f"-DPAYLOAD_LONGS={payload_longs}"])
    gx.run([gx.CROSS + "ld", "-T", str(gx.SRC / "link.ld"), "-o", str(elf), str(stub), str(obj)])
    blobs = {}
    for sec in (".stub", ".bridge"):
        out = tmp / (sec.strip(".") + ".bin")
        gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", sec, str(elf), str(out)])
        blobs[sec] = out.read_bytes()
    syms, data_end = {}, DST_BRIDGE + 0x1000
    for line in gx.run([gx.CROSS + "nm", "-S", str(elf)]).splitlines():
        parts = line.split()
        syms[parts[-1]] = int(parts[0], 16)
        if len(parts) == 4 and int(parts[0], 16) >= DST_BRIDGE + 0x1000:
            data_end = max(data_end, int(parts[0], 16) + int(parts[1], 16))
    if len(blobs[".bridge"]) > 0x1000 or data_end > gx.DST_END:
        raise SystemExit("!! passerelle trop grande")
    m8o, m8elf, m8bin = tmp / "m8.o", tmp / "m8.elf", tmp / "m8.bin"
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", "-c", str(gx.SRC / "machine8.S"), "-o", str(m8o),
            f"-DREC8={REC8:#x}", f"-DREC9={REC9:#x}", f"-DVEC8={VEC8:#x}", f"-DDESC8={DESC8:#x}"])
    gx.run([gx.CROSS + "ld", "-Ttext", f"{STUBS:#x}", "-o", str(m8elf), str(m8o)])
    gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", ".text", str(m8elf), str(m8bin)])
    ssyms = {p[-1]: int(p[0], 16) for p in (l.split() for l in gx.run([gx.CROSS + "nm", str(m8elf)]).splitlines())
             if len(p) == 3}
    stubs = m8bin.read_bytes()
    if STUBS + len(stubs) > DATA:
        raise SystemExit("!! détours trop grands")
    return blobs, syms, stubs, ssyms


def build_tweak(img, st_img):
    u32 = lambda va: struct.unpack_from(">I", img, va - BASE)[0]
    # analyse du Syntakt avec la fermeture et les plages des deux moteurs
    gx.ROOTS, gx.SEGMENTS = ROOTS, SEGMENTS
    gx.IMM_ADDR = gx.IMM_ADDR | IMM_ADDR
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        ins = gx.disasm(st_img, tmp)
        funcs, insns = gx.closure(ins)
        relocs = gx.relocations(st_img, ins, insns)
        size = END - gx.DST_CODE
        blobs, syms, stubs, ssyms = compile_code(tmp, size // 4)

    # --- données : noms, update/render à 8 entrées, VEC8, chaînes
    strings = [m["name"] for m in MACHINES] + [k[i] for m in MACHINES for k in m["knobs"] for i in (0, 1)]
    at, addr = DATA + 128, {}
    for s in strings:
        if s not in addr:
            addr[s] = at
            at += len(s) + 1
    names = [u32(g7.NAMES + 4 * i) for i in range(6)] + [addr[m["name"]] for m in MACHINES]
    upd = [u32(g7.UPDATE_TAB + 4 * i) for i in range(6)] + [syms["bridge_update_sd"], syms["bridge_update_cp"]]
    rnd = [u32(g7.RENDER_TAB + 4 * i) for i in range(6)] + [syms["bridge_render_sd"], syms["bridge_render_cp"]]
    data = bytearray()
    for t in (names, upd, rnd, range(1, 9)):
        data += b"".join(g7.be32(x) for x in t)
    for s in addr:
        data += s.encode("ascii") + b"\0"
    if DATA + len(data) > DESC8 or len(data) < 128:
        raise SystemExit("!! données")

    # --- 10 descripteurs : 5 par machine, sur le modèle de ceux de SNARE (51..55)
    new = bytearray()
    for m in MACHINES:
        for k, (long_, short, default) in enumerate(m["knobs"]):
            e = bytearray(img[g7.DESC + (g7.SNARE_DESC + k) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
            e[0x00:0x04] = g7.be32(DESC_FIELD[m["index"]])
            e[0x10:0x14] = g7.be32(default << 8)
            e[0x2c:0x30] = g7.be32(addr[long_])
            e[0x34:0x38] = g7.be32(addr[short])
            new += e
        e = bytearray(img[g7.DESC + (g7.SNARE_DESC + 4) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
        e[0x10:0x14] = g7.be32(m["decay"] << 8)
        new += e

    # --- écritures dans l'OS Cycles
    writes = []

    def w(va, old, new_):
        if img[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! {va:#x} : {old.hex()} attendu, {img[va - BASE:va - BASE + len(old)].hex()} trouvé")
        writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

    stub = blobs[".stub"]
    w(gx.CAVE, b"\xff" * len(stub), stub)
    writes.append(sprites.redirect_write(gx.CAVE))
    w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), bytes.fromhex("4ef9") + g7.be32(gx.CAVE) + bytes.fromhex("4e71"))
    moved = {g7.DESC: DESC8, g7.DESC + 8: DESC8 + 8, g7.DESC + 0x20: DESC8 + 0x20, g7.ROWS: ROWS8,
             g7.CCROWS: CCROWS8, g7.NAMES: NAMES8, g7.UPDATE_TAB: UPD8, g7.RENDER_TAB: RND8}
    count = {}
    for old, new_ in moved.items():
        rs = g7.refs32(img, old)
        count[old] = len(rs)
        for va in rs:
            w(va, g7.be32(old), g7.be32(new_))
    expect = {g7.DESC: 34, g7.DESC + 8: 1, g7.DESC + 0x20: 2, g7.ROWS: 5, g7.CCROWS: 2, g7.NAMES: 1,
              g7.UPDATE_TAB: 1, g7.RENDER_TAB: 1}
    if count != expect:
        raise SystemExit(f"!! références : {count}")
    for va in g7.BOUNDS:
        if va in {j[0] for j in JUMPS8}:
            continue
        n = img[va - BASE + 1]
        if img[va - BASE] & 0xf1 != 0x70 or n not in MOVEQ:
            raise SystemExit(f"!! {va:#x} n'est pas moveq #75/#76")
        w(va, img[va - BASE:va - BASE + 2], bytes([img[va - BASE], MOVEQ[n]]))
    for va, old, new_ in SMALL:
        w(va, bytes.fromhex(old), bytes.fromhex(new_))
    for va, old, sym in g7.JUMPS + JUMPS8:
        w(va, bytes.fromhex(old), bytes.fromhex("4ef9") + g7.be32(ssyms[sym]))
    for va, old, sym in g7.CALLS:
        w(va, bytes.fromhex(old), bytes.fromhex("4eb9") + g7.be32(ssyms[sym]) + bytes.fromhex("4e71"))
    writes.sort(key=lambda x: x["off"])
    for a, b in zip(writes, writes[1:]):
        if a["off"] + len(a["new"]) // 2 > b["off"]:
            raise SystemExit(f"!! écritures qui se chevauchent en {BASE + b['off']:#x}")

    # --- recette de la charge utile
    parts = [{"dest": f"{dst:#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]} for lo, hi, dst in SEGMENTS[:4]]
    for lo, hi, dst in gx.ST_SRAM_INIT:
        parts.append({"dest": f"{gx.move(dst):#x}", "syntakt": [f"{lo:#x}", f"{hi:#x}"]})
    parts += [
        {"dest": f"{DST_BRIDGE:#x}", "hex": blobs[".bridge"].hex()},
        {"dest": f"{STUBS:#x}", "hex": stubs.hex()},
        {"dest": f"{DATA:#x}", "hex": bytes(data).hex()},
        {"dest": f"{DESC8:#x}", "cycles": [f"{g7.DESC:#x}", f"{g7.DESC + g7.NDESC * g7.DSTRIDE:#x}"]},
        {"dest": f"{DESC8 + g7.NDESC * g7.DSTRIDE:#x}", "hex": bytes(new).hex()},
    ]
    reloc = [[f"{gx.move(va):#x}", gx.be32(old), gx.be32(new_)] for va, old, new_ in relocs]
    alg_max = g7.DESC + g7.ALG_DESC * g7.DSTRIDE + 0x0c
    if u32(alg_max) != 5 << 8:
        raise SystemExit("!! max du paramètre Algorithm")
    reloc.append([f"{alg_max - g7.DESC + DESC8:#x}", gx.be32(5 << 8), gx.be32((NMACH - 1) << 8)])
    code_bytes = sum(ins[a][0] for a in insns)
    return {
        "id": "syntakt-vintage",
        "order": 23,
        "name": "Vrais moteurs SD VINTAGE et CP VINTAGE du Syntakt en 7e et 8e machines (SDVtg, CPVtg)",
        "description": [
            "Les moteurs SD VINTAGE et CP VINTAGE du Syntakt (OS 1.42 ou 1.41), extraits AU BUILD de TON Syntakt_OS1.42.syx",
            f"({len(funcs)} fonctions, {code_bytes} o de code, avec leurs tables), en 7e et 8e machines",
            "« SDVtg » et « CPVtg » : les 6 machines d'origine ne changent pas. Potards propres, noms et",
            "défauts du Syntakt. SDVtg : Inharm, Freq Complex, Pitch Sweep, Mod Envelope (0/110/74/80, DEC 33).",
            "CPVtg : Body Char, Balance, Spacing Crunch, Body Envelope (24/25/46/37, DEC 32). Notes/19.",
            "Demande build.py --syntakt Syntakt_OS1.42.syx. Aucun octet Elektron dans ce fichier.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "conflicts": ["sdvintage-snare", "sdvintage-exact", "sdvintage-7th"],
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
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    tweak, funcs, code_bytes, ssyms = build_tweak(img, syntakt.dsp_image(args.syntakt))
    text = json.dumps(tweak, indent=1) + "\n"
    ap_ = tweak["append"]
    print(f"  {len(funcs)} fonctions, {code_bytes} o ; {len(tweak['writes'])} écritures ; {len(ap_['reloc'])} relocalisations ;"
          f" charge utile {ap_['size']} o -> {ap_['dest']}")
    if args.check:
        if not DST.exists() or DST.read_text(encoding="utf-8") != text:
            raise SystemExit(f"!! {DST.name} ne correspond pas (autre GCC ?)")
        print(f"  {DST.name} est à jour")
        return
    DST.write_text(text, encoding="utf-8")
    print(f"  écrit : {DST.relative_to(HERE.parent)}")


if __name__ == "__main__":
    main()
