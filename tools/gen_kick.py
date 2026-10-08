#!/usr/bin/env python3
"""Génère le tweak « kick » : deux machines de kick ajoutées au Model:Cycles, Kick2 (7e) et Kick3 (8e), ports de
zicBox (apiel/zicBox, audio/engines/PotKick.h et KickWave.h) en virgule fixe (notes/47).

  - Kick2 : VCO à 5 formes (MRPH), waveshaper (SHPR), forme de la chute de hauteur (SW.SH), résonateur (RESO) ;
  - Kick3 : forme d'onde construite par 4 potards (WAVE, FOLD, SKEW, HARM), PITCH = caractère de la chute de hauteur,
    PUNCH = drive. La hauteur suit la note du trig (52 Hz à C4).

Le code est le nôtre (tools/machines/kick/*.cpp), sans le Syntakt ni Braids : le MAIN OS officiel sert à vérifier les
octets d'origine, et la table des descripteurs est recopiée au build depuis TON fichier (recette « cycles »).
Le ColdFire n'a pas d'unité flottante et la libgcc de m68k-linux-gnu est compilée pour le 68020 (elle plante sur
ColdFire) : tout est en entiers, et l'édition de liens ne prend pas libgcc, si bien qu'un float égaré fait échouer le
build au lieu de planter la machine.

La mécanique des machines ajoutées est celle de MACRO (gen_macro.py, notes/43) pour deux machines : mêmes détours
(gs.detours_asm), mêmes tables déplacées, mêmes adresses dans la charge utile (gs.LAYOUT). Le
flasher offre aussi la version avec Model-TG, 34-kick-tg.json (Kick2 et Kick3 en 8e et 9e machines, par-dessus
model-tg-st), comme macro-tg pour MACRO.

    python3 tools/gen_kick.py --cycles model-cycles_OS1.13.syx [--check]

Les JSON versionnés sont compilés par m68k-linux-gnu-g++ 13.3 (Ubuntu 24.04) : un autre GCC donne d'autres octets,
et --check le dit.
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
import gen_syntakt_machines as g8  # noqa: E402
import gen_syntakt_engines as gs   # noqa: E402
import gen_macro as gm             # noqa: E402
import sprites                     # noqa: E402
import usb_steady                  # noqa: E402
import voice_loop                  # noqa: E402

DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "26-kick.json"
OUT_TG = DEV / "34-kick-tg.json"
SRC = HERE / "machines" / "kick"
BASE = gx.BASE

# -O2 comme les autres machines ; pas de RTTI, d'exceptions ni de constructeurs globaux (rien ne les appelle)
CXXFLAGS = ["-mcpu=54418", "-O2", "-ffreestanding", "-fno-rtti", "-fno-exceptions", "-fno-builtin", "-nostdlib",
            "-fno-pic", "-fno-common", "-ffunction-sections", "-fdata-sections", "-fomit-frame-pointer",
            "-Wall", "-Wextra", "-Werror"]

# --- les machines (comme des entrées de gs.CATALOG) ---------------------------------------------------------
# knobs : COLOR, SHAPE, SWEEP, CONTOUR = (nom long, nom court, défaut) ; decay : défaut de l'Amp Decay ;
# image : celle de KICK (l'OS n'en a que 6)
MACHINES = (
    dict(index=6, name="Kick2", src="zic_kick2.cpp", prefix="kick2", image=0, decay=50,
         knobs=(("VCO Morph", "MRPH", 0), ("Shaper", "SHPR", 0), ("Sweep Shape", "SW.SH", 20), ("Body Reso", "RESO", 0))),
    dict(index=7, name="Kick3", src="zic_kick3.cpp", prefix="kick3", image=0, decay=50,
         knobs=(("Wave Shape", "WAVE", 0), ("Wave Fold", "FOLD", 0), ("Wave Skew", "SKEW", 64), ("Harmonic 2", "HARM", 64))),
)
N = len(MACHINES)
FIRSTS = [76 + 5 * i for i in range(N)]           # 1er descripteur de chaque machine

# --- charge utile : gs.LAYOUT. Le code et ses tables vont au début (jusqu'à STUBS) ; aucune variable en BSS (l'état
# est dans la voix de l'OS), la taille de la charge utile est donc celle du début de gs.LAYOUT jusqu'à TABLES_AT.
LINK = """SECTIONS
{{
  .text {code:#x} : {{ *(.text.kick2_update) *(.text.kick2_render) *(.text.kick3_update) *(.text.kick3_render) *(.text*) }}
  .rodata : {{ *(.rodata*) }}
  .data : {{ *(.data*) }}
  /DISCARD/ : {{ *(.comment) *(.note*) *(.eh_frame*) }}
}}
"""


def compile_machines(tmp, pay):
    """Les deux moteurs, liés à pay. Pas de libgcc. Renvoie (octets du code et des tables, symboles)."""
    objs = []
    for m in MACHINES:
        o = tmp / (m["prefix"] + ".o")
        gx.run([gx.CROSS + "g++", *CXXFLAGS, "-c", str(SRC / m["src"]), "-o", str(o)])
        objs.append(o)
    ld, elf, out = tmp / "link.ld", tmp / "kick.elf", tmp / "kick.bin"
    ld.write_text(LINK.format(code=pay))
    gx.run([gx.CROSS + "ld", "-T", str(ld), "--gc-sections", "--no-warn-rwx-segments", "-e", "kick2_update",
            *[f"-u{m['prefix']}_{f}" for m in MACHINES for f in ("update", "render")], "-o", str(elf), *map(str, objs)])
    secs = {}
    for line in gx.run([gx.CROSS + "objdump", "-h", str(elf)]).splitlines():
        f = line.split()
        if len(f) > 4 and f[0].isdigit():
            secs[f[1]] = int(f[2], 16)
    extra = set(secs) - {".text", ".rodata", ".data"}
    if extra:
        raise SystemExit(f"!! sections inattendues (variables globales, constructeurs ?) : {sorted(extra)}")
    gx.run([gx.CROSS + "objcopy", "-O", "binary", str(elf), str(out)])
    blob = out.read_bytes()
    syms = {}
    for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
        p_ = line.split()
        if len(p_) == 3:
            syms[p_[2]] = int(p_[0], 16)
    if pay + len(blob) > gs.STUBS:
        raise SystemExit(f"!! code et tables trop grands : {len(blob)} o")
    return blob, syms


def build_tweak(img, tg=None):
    """Tweak des deux machines (7e et 8e ; 8e et 9e avec Model-TG, dont le Sampler est la 7e). tg : Model-TG
    (gs.tg_context) pour la version combinée."""
    pay = gs.PAY_TG if tg else gs.PAY_ALONE
    gs.set_base(pay)
    first = gs.TG_FIRST if tg else 6
    nm = first + N                              # machines : 6 d'origine, le Sampler avec Model-TG, puis les nôtres
    top = nm - 1
    n = N
    cur = tg["img"] if tg else img              # l'image telle que nos écritures la trouvent
    u32 = lambda va: struct.unpack_from(">I", cur, va - BASE)[0]
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        blob, syms = compile_machines(tmp, pay)
        names_at, upd_at, rnd_at, map_at = gs.DATA, gs.DATA + 4 * nm, gs.DATA + 8 * nm, gs.DATA + 16 * nm
        stubs, ssyms = gm.assemble(tmp, "det", gs.detours_asm(n, [m["image"] for m in MACHINES], FIRSTS, tg)
                                   + (gm.dispatch_tg_asm(syms, rnd_at, tg) if tg else ""), gs.STUBS)
        if gs.STUBS + len(stubs) > gs.DATA:
            raise SystemExit("!! détours trop grands")

        # --- données : noms, tables update/render, machine -> enregistrement, chaînes
        strings = [m["name"] for m in MACHINES] + [k[i] for m in MACHINES for k in m["knobs"] for i in (0, 1)]
        at, addr = map_at + ((nm + 3) & ~3), {}
        for s_ in strings:
            if s_ not in addr:
                addr[s_] = at
                at += len(s_) + 1
        if tg:                                  # noms : ceux de Model-TG (le Sampler montre son échantillon)
            blob_u32 = lambda va: struct.unpack_from(">I", tg["blob"], va - tg["blob_at"])[0]
            names = [blob_u32(tg["sampler_name_table"] + 4 * i) for i in range(7)] + [addr[m["name"]] for m in MACHINES]
        else:
            names = [u32(g7.NAMES + 4 * i) for i in range(6)] + [addr[m["name"]] for m in MACHINES]
        pad = [u32(g7.UPDATE_TAB)] * (first - 6), [u32(g7.RENDER_TAB)] * (first - 6)   # entrée 6 du Sampler : jamais lue
        upd = [u32(g7.UPDATE_TAB + 4 * i) for i in range(6)] + pad[0] + [syms[m["prefix"] + "_update"] for m in MACHINES]
        rnd = [u32(g7.RENDER_TAB + 4 * i) for i in range(6)] + pad[1] + [syms[m["prefix"] + "_render"] for m in MACHINES]
        data = bytearray()
        for t in (names, upd, rnd, range(1, nm + 1)):
            data += b"".join(g7.be32(x) for x in t)
        data += cur[gs.MAP - BASE:gs.MAP - BASE + 6] + bytes(range(6, nm)) + bytes(((nm + 3) & ~3) - nm)
        for s_ in addr:
            data += s_.encode("ascii") + b"\0"
        if gs.DATA + len(data) > gs.DESCN:
            raise SystemExit("!! données")

        # --- 5 descripteurs par machine, sur le modèle de ceux de SNARE (gs.build_tweak)
        new = bytearray()
        for m in MACHINES:
            for k, (long_, short, default) in enumerate(m["knobs"]):
                e = bytearray(img[g7.DESC + (g7.SNARE_DESC + k) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
                e[0x00:0x04] = g7.be32(6)                   # « propre à une machine » ; rattaché à la sienne par les détours
                e[0x10:0x14] = g7.be32(default << 8)
                e[0x2c:0x30] = g7.be32(addr[long_])
                e[0x34:0x38] = g7.be32(addr[short])
                new += e
            e = bytearray(img[g7.DESC + (g7.SNARE_DESC + 4) * g7.DSTRIDE - BASE:][:g7.DSTRIDE])
            e[0x10:0x14] = g7.be32(m["decay"] << 8)
            new += e

        # --- écritures (comme gen_macro.build_tweak, pour n machines)
        writes = []

        def w(va, old, new_):
            if cur[va - BASE:va - BASE + len(old)] != old:
                raise SystemExit(f"!! {va:#x} : {old.hex()} attendu, {cur[va - BASE:va - BASE + len(old)].hex()} trouvé")
            writes.append({"off": va - BASE, "old": old.hex(), "new": new_.hex()})

        def moveq(va, old, new_, reg_byte):
            w(va, bytes([reg_byte, old]), bytes([reg_byte, new_]))

        def jmp(va):
            return bytes.fromhex("4ef9") + g7.be32(va)

        writes.append(None)                     # crochet de démarrage : écrit plus bas (il porte la liste des morceaux)
        red = sprites.redirect_write(gx.CAVE)
        w(BASE + red["off"], bytes.fromhex(red["old"]), bytes.fromhex(red["new"]))
        if tg:                                  # notre crochet, puis le sien (stub.S, CHAIN_TO)
            w(gs.BOOT_CALL + 2, g7.be32(tg["boot_extra_hook"]), g7.be32(gx.CAVE))
        else:
            w(gx.HOOK, bytes.fromhex(gx.HOOK_OLD), jmp(gx.CAVE) + bytes.fromhex("4e71"))
        names_src = tg["sampler_name_table"] if tg else g7.NAMES
        moved = {g7.DESC: gs.DESCN, g7.DESC + 8: gs.DESCN + 8, g7.DESC + 0x20: gs.DESCN + 0x20, g7.ROWS: gs.ROWSN,
                 g7.CCROWS: gs.CCROWSN, names_src: names_at, g7.UPDATE_TAB: upd_at, g7.RENDER_TAB: rnd_at,
                 gs.MAP: map_at}
        # sans Model-TG, la référence à la table render est dans l'appel de la boucle des voix (0x400a7e14), que l'on
        # garde ; avec Model-TG, son dispatch l'a remplacé (et notre détour lit rnd_at)
        want = {g7.DESC: 34, g7.DESC + 8: 1, g7.DESC + 0x20: 2, g7.ROWS: 4 if tg else 5, g7.CCROWS: 2, gs.MAP: 1,
                g7.RENDER_TAB: 0 if tg else 1}
        for old, new_ in moved.items():
            rs = g7.refs32(cur, old)
            if len(rs) != want.get(old, 1):
                raise SystemExit(f"!! références à {old:#x} : {len(rs)}")
            for va in rs:
                w(va, g7.be32(old), g7.be32(new_))
        if tg:
            w(gs.DISPATCH[0], cur[gs.DISPATCH[0] - BASE:gs.DISPATCH[0] - BASE + 6], jmp(ssyms["dispatch"]))
        jumps = g7.JUMPS + g8.JUMPS8
        for va in g7.BOUNDS:
            if va in {j[0] for j in jumps}:
                continue
            b0, b1 = cur[va - BASE], cur[va - BASE + 1]
            if b0 & 0xf1 != 0x70 or b1 not in (75, 76):
                raise SystemExit(f"!! {va:#x}")
            moveq(va, b1, b1 + 5 * n, b0)
        for va, reg in ((0x400a7dba, 0x72), (0x400a7df4, 0x70), (0x4005a6a6, 0x72), (0x400147a4, 0x70),
                        (0x400148aa, 0x72), (0x400148b2, 0x70), (0x400a25e0, 0x70)):
            if tg and va == 0x4005a6a6:
                continue                        # son détour sampler_lfo_gate : chaîné par lfo_gate (plus bas)
            if cur[va - BASE] != reg or cur[va - BASE + 1] not in (5, 6):
                raise SystemExit(f"!! borne {va:#x}")
            moveq(va, cur[va - BASE + 1], top, reg)
        moveq(0x4005a572, 5, 6, 0x72)
        w(0x4005a2b8, bytes.fromhex("487800c0"), bytes.fromhex("4878") + (32 * nm).to_bytes(2, "big"))
        if nm > gs.MARKS_ROW:
            w(0x400a26a2, bytes.fromhex("7850428545f9"), jmp(ssyms["marks"]))
        else:
            moveq(0x400a26e8, cur[0x400a26e8 - BASE + 1], nm, 0x70)
        if not tg:
            for va in (0x4001b69c, 0x400a40a6, 0x400a4fb0):
                moveq(va, 5, 1, 0x70)
        chained = {0x4004df5c: "descr_hook", 0x4004df76: "descr_b_hook"}
        for va, old, sym in jumps:
            old = bytes.fromhex(old)
            if tg and va in chained:            # ses détours, appelés par les nôtres
                old = jmp(tg[chained[va]])
            w(va, old, jmp(ssyms[sym]))
        if tg:
            w(gs.AMP_ROW, bytes.fromhex("20065286eb88"), jmp(ssyms["amp_row"]))
            w(0x4005a6a6, jmp(tg["sampler_lfo_gate"]), jmp(ssyms["lfo_gate"]))
            w(0x4005a6b6, jmp(tg["sampler_amp_gate"]), jmp(ssyms["amp_gate"]))
        for va, old, sym in g7.CALLS:
            w(va, bytes.fromhex(old), bytes.fromhex("4eb9") + g7.be32(ssyms[sym]) + bytes.fromhex("4e71"))

        # --- charge utile
        parts = [
            {"dest": f"{pay:#x}", "hex": blob.hex()},
            {"dest": f"{gs.STUBS:#x}", "hex": stubs.hex()},
            {"dest": f"{gs.DATA:#x}", "hex": bytes(data).hex()},
            {"dest": f"{gs.DESCN:#x}", "cycles": [f"{g7.DESC:#x}", f"{g7.DESC + g7.NDESC * g7.DSTRIDE:#x}"]},
            {"dest": f"{gs.DESCN + g7.NDESC * g7.DSTRIDE:#x}", "hex": bytes(new).hex()},
        ]
        lo_, hi_ = g7.DESC - BASE, g7.DESC - BASE + g7.NDESC * g7.DSTRIDE
        final, orig = bytearray(cur[lo_:hi_]), img[lo_:hi_]
        alg = g7.ALG_DESC * g7.DSTRIDE + 0x0c
        if struct.unpack_from(">I", final, alg)[0] != (first - 1) << 8:
            raise SystemExit("!! max du paramètre Algorithm")
        struct.pack_into(">I", final, alg, top << 8)
        reloc = [[f"{gs.DESCN + k:#x}", orig[k:k + 4].hex(), final[k:k + 4].hex()]
                 for k in range(0, len(final), 4) if final[k:k + 4] != orig[k:k + 4]]
        size = gs.TABLES_AT - pay
        segs = gs.segments(parts, size)
        at = tg["at"] if tg else BASE + gx.IMAGE_LEN
        if at + sum(n_ for _, n_ in segs) > gs.END_LIMIT:
            raise SystemExit(f"!! ajout de {sum(n_ for _, n_ in segs)} o : l'image dépasserait {gs.END_LIMIT:#x}")
        (tmp / "segs.inc").write_text("".join(f"\t.long\t{a:#x}, {n_ // 4}\n" for a, n_ in segs))
        stub, _ = gm.assemble(tmp, "stub", gx.SRC / "stub.S", gx.CAVE, [
            f"-DPAYLOAD_SRC={at:#x}", f"-DPAYLOAD_DST={pay:#x}", f"-DPAYLOAD_LONGS={size // 4}", "-DPACK", f"-I{tmp}",
            *([f"-DCHAIN_TO={tg['boot_extra_hook']:#x}"] if tg else [])])
    if len(stub) > sprites.zone(gx.CAVE)[1]:
        raise SystemExit("!! crochet de démarrage trop grand pour sa place")
    writes[0] = {"off": gx.CAVE - BASE, "old": "ff" * len(stub), "new": stub.hex()}
    if cur[gx.CAVE - BASE:gx.CAVE - BASE + len(stub)] != b"\xff" * len(stub):
        raise SystemExit("!! place du crochet de démarrage déjà prise")
    writes.sort(key=lambda x: x["off"])
    for a_, b_ in zip(writes, writes[1:]):
        if a_["off"] + len(a_["new"]) // 2 > b_["off"]:
            raise SystemExit(f"!! écritures qui se chevauchent en {BASE + b_['off']:#x}")

    tid = "kick-tg" if tg else "kick"
    ids = gm.other_ids() | {"macro", "macro-tg", "kick", "kick-tg", "model-tg"} | (set() if tg else {"model-tg-st"})
    where = ("8e et 9e machines, après le Sampler de Model-TG (7e)" if tg else "7e et 8e machines, après les 6 d'origine")
    out = {
        "id": tid,
        "order": 34 if tg else 26,
        "name": ("Model-TG + " if tg else "") + "Machines Kick2 et Kick3 (ports de zicBox PotKick.h et KickWave.h)",
        "description": ([
            "Version combinée avec Model-TG (notes/31, notes/47) : s'ajoute après model-tg-st, le Sampler reste la 7e",
            "machine, Kick2 est la 8e et Kick3 la 9e. Leur sortie passe par l'étage d'amplitude de Model-TG (Attack, filtre).",
        ] if tg else []) + [
            f"Deux machines de kick en {where} (notes/47).",
            "Kick2 : COLOR = MRPH (forme d'onde : sinus, triangle, scie, carré, scie écrêtée), SHAPE = SHPR (waveshaper),",
            "SWEEP = SW.SH (forme de la chute de hauteur), CONTOUR = RESO (résonateur du corps), PUNCH = drive.",
            "Kick3 : COLOR = WAVE (sinus, triangle, scie, carré), SHAPE = FOLD (repli d'onde), SWEEP = SKEW (asymétrie),",
            "CONTOUR = HARM (harmonique 2), PITCH = caractère de la chute de hauteur, PUNCH = drive. La hauteur suit la note.",
            "Code en virgule fixe (tools/machines/kick/), sans libgcc : le ColdFire n'a pas de flottants. DECAY, GATE et",
            "PUNCH : la chaîne d'ampli d'origine. Généré par tools/gen_kick.py. Aucun octet Elektron dans ce fichier.",
        ] + ([] if tg else [
            "Envoi à l'USB à heure fixe (tools/usb_steady.py, notes/35), boucle des voix : division des pistes par 2",
            "plus courte (tools/voice_loop.py, notes/36), mêmes valeurs.",
        ]),
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
    }
    if tg:
        out["requires"] = [tg["id"]]
    out.update({
        "conflicts": sorted(ids - {tid}),
        "writes": writes,
        "append": {"at": f"{at:#x}", "dest": f"{pay:#x}", "size": size, "parts": parts, "reloc": reloc,
                   "pack": [[f"{a_:#x}", n_] for a_, n_ in segs]},
        # pour la preuve (tools/emu/test_kick.py) : les entrées des deux machines
        "symbols": {f"{m['prefix']}_{f}": f"{syms[m['prefix'] + '_' + f]:#x}" for m in MACHINES for f in ("update", "render")},
    })
    if not tg:                    # comme MACRO seule : envoi à l'USB à heure fixe (notes/35), boucle des voix (notes/36) ;
        out = usb_steady.add_to(out)          # la version combinée les a par model-tg-st
        out = voice_loop.add_to(out)
    return out, dict(code=len(blob), image=sum(n_ for _, n_ in segs), syms=syms)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--check", action="store_true", help="vérifie que les JSON versionnés correspondent")
    args = ap.parse_args()
    img = g7.cycles_main(args.cycles)
    if len(img) != gx.IMAGE_LEN:
        raise SystemExit("!! ce n'est pas le MAIN OS 1.13 officiel")
    bad = 0
    for path, tg in ((OUT, None), (OUT_TG, gs.tg_context(img))):
        tweak, info = build_tweak(img, tg)
        text = json.dumps(tweak, indent=1) + "\n"
        print(f"  {tweak['id']} : {len(tweak['writes'])} écritures, code et tables {info['code']} o, ajout à l'image "
              f"{info['image']} o")
        bad += gm.emit(path, text, args.check)
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
