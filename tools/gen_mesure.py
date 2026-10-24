#!/usr/bin/env python3
"""Firmware de mesure du Modded Cycles OS (notes/75) : l'OS de os.json, plus des sondes dans l'interruption audio,
un compteur du temps libre de l'interface et des essais d'étalonnage, affichés dans trois écrans de plus de la page
System de Model-TG. Ce n'est PAS une carte du flasher : ce script construit le .syx de diagnostic sur TON .syx
officiel, comme tools/build.py --os, et rien d'autre.

Ce qui change par rapport à l'OS (tout le reste est à l'octet près celui de os.json) :
  - le code (tools/machines/mesure/ : mesure.c, mesure_hooks.S) dans des masques de sprites libres de l'OS
    (tools/sprites.py), ses variables dans la fenêtre RAM, au-dessus du BSS de l'OS (notes/56 §3.5.2) ;
  - les appels sondés de l'interruption audio (SITES : jsr cible -> jsr m_w_k), le vecteur de l'interruption audio
    posé au démarrage (0x4005966a : isr_prof de Model-TG -> m_isr, qui passe à isr_prof), la boucle d'attente de la
    tâche de priorité 0 (0x4000543a -> m_idle) ;
  - dans le bloc de Model-TG : sa page System a 5 écrans au lieu de 2 (le cran de DATA, mm_e_sys) et le choix de
    l'écran passe par m_sys (sys_render).

    python3 tools/gen_mesure.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx -o mesure.syx
"""
import argparse
import copy
import json
import pathlib
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import gen_sram_hot as gh          # noqa: E402
import sprites                     # noqa: E402

SRC = HERE / "machines" / "mesure"
DEV = ROOT / "tweaks" / "model-cycles_OS1.13"
BASE = gx.BASE
RAM = (0x4233a000, 0x4233b000)     # variables (.ram) ; puis le code droit et le tampon des essais (mesure.c, jusqu'à
                                   # 0x4233c100), sous le step record (0x4233e800)
# appels sondés : (site, cible attendue dans l'OS de os.json, rôle) ; dans l'ordre de m_w_0..m_w_11 (mesure_hooks.S)
SITES = (
    (0x40059338, 0x40002ae0, "audio venu de l'USB"),
    (0x40059382, gh.ENTRY["hot_probe"], "code chaud en SRAM (notes/76), puis fonction audio (sonde des moteurs)"),
    (0x400597a8, 0x40058474, "lissage des paramètres"),
    (0x400597b4, 0x40056e24, "modulation de vélocité"),
    (0x400597c6, 0x40183646, "LFO (LFO 2, 3, 4)"),
    (0x4005981e, 0x401b715c, "boucle des voix (fx_early de Model-TG)"),
    (0x4005982a, 0x401b7d0e, "après les voix (Model-TG)"),
    (0x40059840, 0x4008f1f0, "recopie des gains de vélocité"),
    (0x40059852, 0x40056f58, "Volume + Dist"),
    (0x4005985c, 0x40056ea8, "0x40056ea8"),
    (0x40059872, 0x401b7b54, "étage de sortie (Model-TG, puis mixeur, envois, effets, master)"),
    (0x40059392, 0x4015c2d6, "envoi à l'USB, puis la fin du bloc (m_block_end)"),
)
VECTOR = 0x4005966a                # move.l #isr_prof,d0 (puis move.l d0,0x400002fc) : le vecteur de l'audio
IDLE = (0x4000543a, "4fef001860fe")  # lea 24(sp),sp ; bra.s . : la boucle d'attente de la tâche de priorité 0
# Model-TG (bloc de 30-model-tg-st.json) : adresse, octets attendus, rôle
TG = {
    "ISR_PROF": (0x401b803e, "2f002039fc07800c", "isr_prof : note l'entrée de l'interruption audio"),
    "PAGE0": (0x401b6fc0, "203a1142", "sys_render : l'écran 0 (CPU, PEAK, RAM, FREE)"),
    "SYS_R2": (0x401b708a, "76007800", "sys_r2 : l'écran 1 (les pistes)"),
    "SYS_R_OUT": (0x401b7080, "4cd704184fef000c4e75", "sys_r_out : la fin de sys_render"),
}
SYS_PG = 0x401b7540                # sys_pg, lu par sys_render en 0x401b6fb6 (move.l (d16,pc),d0)
TG_DISPATCH = (0x401b6fb6, "203a058853806700" "00cc")  # move.l sys_pg,d0 ; subq.l #1,d0 ; beq.w sys_r2
TG_PAGES = (0x401b1ca4, "0c81000000016c0a")              # mm_e_sys : cmpi.l #1,d1 ; bge.s (dernier écran : 1)
NPAGES = 5                         # 0, 1 : Model-TG ; 2 AUDIO, 3 BENCH, 4 COLD


def os_tweaks():
    tweaks = {}
    for f in DEV.glob("[0-9]*.json"):
        t = json.loads(f.read_text(encoding="utf-8"))
        tweaks[t["id"]] = t
    ids = json.loads((ROOT / "os.json").read_text(encoding="utf-8"))["tweaks"]
    return sorted((tweaks[i] for i in ids), key=lambda t: t["order"])


def free_masks(stock, patched):
    """Masques de sprites libres dans l'OS : octets d'origine, et la constante du constructeur vise encore le
    masque (aucun tweak de l'OS ne l'a redirigé pour s'en servir)."""
    out = []
    for va, info in sorted(sprites.MASKS.items()):
        size, const = info[0], info[1]
        if len(info) < 4:                               # les trois masques 0xFF : pas de copie gardée
            continue
        o, c = va - BASE, const - BASE
        if patched[o:o + size] == stock[o:o + size] and patched[c:c + 4] == va.to_bytes(4, "big"):
            out.append((va, size))
    return out


def objects(tmp, defs):
    c, s = tmp / "mesure.o", tmp / "hooks.o"
    gx.run([gx.CROSS + "gcc", *gx.CFLAGS, "-c", str(SRC / "mesure.c"), "-o", str(c)])
    gx.run([gx.CROSS + "gcc", "-mcpu=54418", *[f"-Wa,--defsym,{k}={v:#x}" for k, v in defs.items()], "-c",
            str(SRC / "mesure_hooks.S"), "-o", str(s)])
    return [c, s]


def sections(objs):
    """[(nom, taille, alignement)] des sections à placer dans l'image (code, constantes, données initialisées)."""
    out = []
    for o in objs:
        for line in gx.run([gx.CROSS + "objdump", "-h", str(o)]).splitlines():
            p = line.split()
            if len(p) >= 7 and p[0].isdigit():
                name, size, align = p[1], int(p[2], 16), 2 ** int(p[6].split("**")[1])
                if size and not name.startswith((".bss", ".comment", ".note")):
                    out.append((name, size, align))
    return out


def pack(secs, masks):
    """Range les sections dans les masques (la plus grande d'abord, dans le premier masque où elle tient) : {masque :
    [sections]}."""
    room = {va: [va, va + size] for va, size in masks}
    where = {va: [] for va, _ in masks}
    for name, size, align in sorted(secs, key=lambda s: (-s[1], s[0])):
        a = max(align, 2)
        for va, _ in sorted(masks, key=lambda m: (m[1], m[0])):
            at = (room[va][0] + a - 1) & ~(a - 1)
            if at + size <= room[va][1]:
                room[va][0] = at + size
                where[va].append(name)
                break
        else:
            raise SystemExit(f"!! {name} ({size} o) : plus de masque libre assez grand")
    return {va: names for va, names in where.items() if names}


def compile_mesure(stock, patched):
    """Le code lié : ({masque : octets}, symboles)."""
    masks = free_masks(stock, patched)
    defs = {f"T_{k}": tgt for k, (_, tgt, _) in enumerate(SITES)}
    defs.update({k: v[0] for k, v in TG.items()})
    defs["SYS_PG"] = SYS_PG
    with tempfile.TemporaryDirectory() as d:
        tmp = pathlib.Path(d)
        objs = objects(tmp, defs)
        where = pack(sections(objs), masks)
        ld = ["SECTIONS", "{"]
        for va, names in sorted(where.items()):
            ld.append(f"  .m{va:08x} {va:#x} : {{ " + " ".join(f"*({n})" for n in names) + " }")
        ld += [f"  .ram {RAM[0]:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }}",
               "  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }", "}"]
        (tmp / "m.ld").write_text("\n".join(ld) + "\n")
        elf = tmp / "m.elf"
        gx.run([gx.CROSS + "ld", "-T", str(tmp / "m.ld"), "--no-warn-rwx-segments", "-o", str(elf), *map(str, objs)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        heads = gx.run([gx.CROSS + "objdump", "-h", str(elf)])
        out, sizes = {}, dict(masks)
        for line in heads.splitlines():
            p = line.split()
            if len(p) >= 7 and p[0].isdigit():
                name, size, vma = p[1], int(p[2], 16), int(p[3], 16)
                if name == ".ram":
                    if vma != RAM[0] or vma + size > RAM[1]:
                        raise SystemExit(f"!! variables : {size} o en {vma:#x}, au-delà de {RAM[1]:#x}")
                    continue
                if not name.startswith(".m") or vma not in sizes or size > sizes[vma]:
                    raise SystemExit(f"!! section {name} ({size} o en {vma:#x}) hors des masques")
                b = tmp / "s.bin"
                gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", name, str(elf), str(b)])
                out[vma] = b.read_bytes()
    return out, syms


def tg_patched(tg, writes):
    """Une copie du tweak de Model-TG, son bloc (en place) retouché : writes = [(adresse, ancien, nouveau)]."""
    t = copy.deepcopy(tg)
    part = t["append"]["parts"][0]
    at, blob = int(part["dest"], 16), bytearray(bytes.fromhex(part["hex"]))
    for va, old, new in writes:
        o = va - at
        if not 0 <= o <= len(blob) - len(old) or blob[o:o + len(old)] != old:
            raise SystemExit(f"!! Model-TG {va:#x} : {old.hex()} attendu, {blob[o:o + len(old)].hex()} trouvé")
        blob[o:o + len(new)] = new
    part["hex"] = blob.hex()
    t["id"] = "model-tg-st"
    return t


def build_tweaks(stock):
    """Les tweaks du firmware de mesure : ceux de os.json (Model-TG retouché) et « mesure » ; et ses symboles."""
    chosen = os_tweaks()
    patched, _ = build.apply_writes(stock, chosen)
    tg = next(t for t in chosen if t["id"] == "model-tg-st")
    blob = bytes.fromhex(tg["append"]["parts"][0]["hex"])
    at = int(tg["append"]["parts"][0]["dest"], 16)
    for k, (va, want, _) in TG.items():
        if blob[va - at:va - at + len(want) // 2].hex() != want:
            raise SystemExit(f"!! Model-TG {k} ({va:#x}) : autres octets que {want} (autre version ?)")
    code, syms = compile_mesure(stock, patched)
    writes = []

    def w(va, old, new):
        o = va - BASE
        if patched[o:o + len(old)] != old:
            raise SystemExit(f"!! {va:#x} : {old.hex()} attendu dans l'OS, {patched[o:o + len(old)].hex()} trouvé")
        writes.append({"off": o, "old": old.hex(), "new": new.hex()})
    for va, b in sorted(code.items()):
        w(va, patched[va - BASE:va - BASE + len(b)], b)
        writes.append(sprites.redirect_write(va))
    for k, (va, tgt, _) in enumerate(SITES):
        w(va, struct.pack(">HI", 0x4eb9, tgt), struct.pack(">HI", 0x4eb9, syms[f"m_w_{k}"]))
    w(VECTOR, struct.pack(">HI", 0x203c, TG["ISR_PROF"][0]), struct.pack(">HI", 0x203c, syms["m_isr"]))
    w(IDLE[0], bytes.fromhex(IDLE[1]), struct.pack(">HI", 0x4ef9, syms["m_idle"]))
    tgw = [(TG_DISPATCH[0], bytes.fromhex(TG_DISPATCH[1]), struct.pack(">HI", 0x4ef9, syms["m_sys"]) + bytes.fromhex("4e714e71")),
           (TG_PAGES[0], bytes.fromhex(TG_PAGES[1]), struct.pack(">HI", 0x0c81, NPAGES - 1) + bytes.fromhex("6c0a"))]
    chosen = [tg_patched(t, tgw) if t["id"] == "model-tg-st" else t for t in chosen]
    mesure = {"id": "mesure", "order": 999, "name": "Firmware de mesure (notes/75)", "device": "Model:Cycles",
              "os": "1.13", "section": 3, "writes": writes}
    return chosen + [mesure], syms, code


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="model-cycles_OS1.13.syx officiel")
    ap.add_argument("--syntakt", required=True, help="Syntakt_OS1.42.syx (ou 1.41) officiel")
    ap.add_argument("-o", "--output", required=True, help="le .syx de mesure à écrire")
    args = ap.parse_args()
    raw = pathlib.Path(args.cycles).read_bytes()
    stream, _ = build.unwrap(raw)
    c = build.container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    stock = build.aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])[0]
    dev = json.loads((DEV / "device.json").read_text(encoding="utf-8"))
    if build.sha(raw) != dev["stock_syx_sha256"] or build.sha(stock) != dev["section_sha256"]:
        raise SystemExit("!! ce n'est pas le .syx officiel de l'OS 1.13 (empreintes de device.json)")
    chosen, syms, code = build_tweaks(stock)
    used = sum(len(b) for b in code.values())
    print(f"  code de mesure : {used} o dans {len(code)} masques ; variables en {RAM[0]:#x}")
    out, _ = build.build_syx(raw, chosen, args.syntakt, False, dev.get("cave_refs_ok"))
    pathlib.Path(args.output).write_bytes(out)
    print(f"  écrit : {args.output} ({len(out)} o)")


if __name__ == "__main__":
    main()
