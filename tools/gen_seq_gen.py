#!/usr/bin/env python3
"""Construit le générateur en gamme et sa variante de menu défilant (notes/53).

--cycles OS officiel --model-tg clone épinglé (build --assemble-only préalable)
--cross m68k-elf- [--check]. Sorties dans tweaks/model-cycles_OS1.13/49-*, aucune image firmware.
Les symboles de Model-TG viennent de son ELF ; chaque masque et sa référence
sont vérifiés sur l'OS officiel. Les deux bases Model-TG sont produites.
"""
import argparse
import hashlib
import json
import os
import pathlib
import struct
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "emu"))
import build
import sprites
from test_sdvintage import main_os_from_syx

SRC = HERE / "machines/seq_gen"
OUT = HERE.parent / "tweaks/model-cycles_OS1.13"
COMMIT = "70b39dd6787770ebefc7a2d78dea1678ec012679"
STOCK = "cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98"
SHARED = 0x4016bfc8
# Registre upstream du 10/10/2026, groupe 34×34 ; tous libres.
SLOTS = [
    (0x4016f8c8, 0x400b0b3c, [".text.sg_generate"]),
    (0x40173848, 0x400b0350, [".text.sg_random", ".rodata.sg_masks", ".text.sg_track_restore"]),
    (0x401780a8, 0x400af946, [".text.sg_key"]),
    (0x401784e8, 0x400af832, [".data.sg_menu", ".data.sg_key"]),
    (0x401835b8, 0x400adedc, [".rodata.sg_menu"]),
    (0x40184df8, 0x400adbc8, [".text.sg_open", ".text.sg_render_tail"]),
    (0x40185308, 0x400adb8c, [".text.sg_open_allocate", ".text.sg_dtor"]),
    (0x40185f48, 0x400ad9c4, [".text.sg_enc", ".text.sg_render_start"]),
    (0x40186238, 0x400ad988, [".text.sg_enc_range", ".text.sg_undo"]),
    (0x40189618, 0x400ad364, [".text.sg_render"]),
    (0x4018af88, 0x400ad18a, [".text.sg_action", ".text.sg_view_start"]),
    (0x4018b1a8, 0x400ad16e, [".text.sg_track_write"]),
    (0x4018ff64, 0x400ac7fc, [".text.sg_menu_key"]),
]
TG_NAMES = ("key_hook", "set_held", "mod_used", "mm_obj", "rtg_on", "sle_on", "scale_state", "key_state")


def symbols(cross, elf):
    result = {}
    for row in subprocess.check_output([cross + "nm", str(elf)], text=True).splitlines():
        parts = row.split()
        if len(parts) == 3:
            result[parts[2]] = int(parts[0], 16)
    return result


BASE_SLOTS = list(SLOTS)

def configure_slots(dynamics=False):
    SLOTS[:] = BASE_SLOTS
    if not dynamics:
        return
    # Masques 47×47 libres, contrôle des références et conflits avant livraison.
    for i,va in ((4,0x4016b6f8),(9,0x4018cd48),(11,0x40171f30),(12,0x40172608)):
        SLOTS[i] = (va,sprites.MASKS[va][1],SLOTS[i][2])
    for va,sections in (
        (0x40179730,[".text.sg_dyn_backup"]),
        (0x40182b38,[".text.sg_dyn_restore"]),
        (0x40182e28,[".text.sg_dyn_step"]),
        (0x4018d1b8,[".text.sg_option",".data.sg_options",".rodata.sg_options"]),
    ):
        SLOTS.append((va,sprites.MASKS[va][1],sections))

def compile_code(cross, tg, scroll=False, dynamics=False):
    """Place chaque section dans un masque et refuse tout dépassement du slot."""
    configure_slots(dynamics)
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        defs = "\n".join(f"TG_{n} = {tg[n]};" for n in TG_NAMES)
        script = defs + "\nSECTIONS {\n"
        for i, (va, _, sections) in enumerate(SLOTS):
            script += f" .slot{i} {va:#x} : {{ " + " ".join(f"*({s})" for s in sections) + " }\n"
            script += f' ASSERT(SIZEOF(.slot{i}) <= {sprites.MASKS[va][0]}, "masque {i} plein")\n'
        script += ' .unused : { *(.text) *(.data) *(.bss) }\n ASSERT(SIZEOF(.unused) == 0, "section non placee")\n}\n'
        (p / "link.ld").write_text(script)
        objects = []
        for name in ("seq_gen", "key", "track", "menu", "dynamics"):
            obj = p / (name + ".o")
            subprocess.run([cross + "as", "-march=cfv4e", *(["--defsym", "SG_SCROLL=1"] if scroll else []), *(["--defsym", "SG_DYNAMICS=1"] if dynamics else []), "-o", str(obj), str(SRC / (name + ".s"))], check=True)
            objects.append(str(obj))
        elf = p / "seq_gen.elf"
        subprocess.run([cross + "ld", "--orphan-handling=error", "-T", str(p / "link.ld"),
                        "-o", str(elf), *objects], check=True)
        blobs = []
        for i in range(len(SLOTS)):
            binary = p / f"slot{i}.bin"
            subprocess.run([cross + "objcopy", "-O", "binary", f"--only-section=.slot{i}", str(elf), str(binary)], check=True)
            blobs.append(binary.read_bytes())
        return blobs, symbols(cross, elf)


def generate(main, base, blobs, syms, tg):
    """Ne copie aucun code Elektron : seuls nos morceaux et redirections sont écrits."""
    def raw(va, size):
        return main[va - build.BASE:va - build.BASE + size]

    def write(va, old, new):
        return {"off": va - build.BASE, "old": old.hex(), "new": new.hex()}

    writes = []
    for (va, ptr, _), blob in zip(SLOTS, blobs):
        size, _, _, kept = sprites.MASKS[va]
        assert raw(va, size) == raw(kept, size), f"masque différent : {va:#x}"
        assert raw(ptr, 4) == struct.pack(">I", va), f"référence différente : {ptr:#x}"
        # Les références alignées doivent se limiter au constructeur documenté.
        refs = [build.BASE + off for off in range(0, len(main) - 3, 2)
                if main[off:off + 4] == struct.pack(">I", va)]
        assert refs == [ptr], f"références supplémentaires : {va:#x} {refs}"
        writes.append(write(ptr, raw(ptr, 4), struct.pack(">I", kept)))
        writes.append(write(va, raw(va, len(blob)), blob))
    hook = next(w for w in base["writes"] if w["off"] == 0x4007240c - build.BASE)
    assert bytes.fromhex(hook["new"]) == b"\x4e\xf9" + struct.pack(">I", tg["key_hook"])
    writes.append(write(0x4007240c, bytes.fromhex(hook["new"]), b"\x4e\xf9" + struct.pack(">I", syms["sg_key"])))
    return {"id": "scale-gen-st" if base["id"] == "model-tg-st" else "scale-gen",
            "order": 49, "name": "Générateur de séquence en gamme (prototype)",
            "description": ["SETTINGS + PAGE : gamme, tonalité, bornes de notes, densité, Generate et Undo.",
                            "Transport arrêté seulement. P-locks conservés ; Undo dans la page uniquement.",
                            "Prototype proposé uniquement dans le flasher de test ; démarrage complet et rendu audio à prouver.",
                            "Page adaptée de Model-TG (TinyGregAudio, MIT). tools/gen_seq_gen.py, notes/53."],
            "device": "Model:Cycles", "os": "1.13", "section": 3,
            "requires": [base["id"]], "conflicts": ["scale-gen" if base["id"] == "model-tg-st" else "scale-gen-st"],
            "writes": writes, "symbols": {n: hex(v) for n, v in syms.items() if n.startswith("sg_")}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--model-tg", type=pathlib.Path, required=True)
    ap.add_argument("--cross", default=os.environ.get("M68K_CROSS", "m68k-elf-"))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--scroll", action="store_true", default=True, help="variante de test à quatre lignes défilantes")
    ap.add_argument("--dynamics", action="store_true", default=True, help="transport et variations validés sur machine")
    args = ap.parse_args()
    assert subprocess.check_output(["git", "-C", str(args.model_tg), "rev-parse", "HEAD"], text=True).strip() == COMMIT
    subprocess.run(["git", "-C", str(args.model_tg), "diff", "--quiet", "HEAD"], check=True)
    stock = main_os_from_syx(args.cycles)
    assert hashlib.sha256(stock).hexdigest() == STOCK, "OS officiel 1.13 requis"
    tg = symbols(args.cross, args.model_tg / "build/_b.elf")
    blobs, syms = compile_code(args.cross, tg, args.scroll, args.dynamics)
    out = OUT
    out.mkdir(parents=True, exist_ok=True)
    for name in ("model-tg", "model-tg-st"):
        base = json.loads((HERE.parent / f"tweaks/model-cycles_OS1.13/30-{name}.json").read_text())
        tweak = generate(stock, base, blobs, syms, tg)
        if args.scroll:
            tweak["name"] = "Générateur en gamme — menu défilant"
            tweak["description"][2] = "Quatre lignes défilantes, police conservée et marges renforcées. Testé sur machine par AveyCole le 10/10/2026."
        if args.dynamics:
            tweak["name"] = "Générateur — transport et variations"
            tweak["description"][0] += " Trois options : velocity, decay et pan."
            tweak["description"][1] = "PLAY/STOP dans la page ; édition arrêtée. Undo restaure notes, velocity et p-locks."
            tweak["description"][2] = "Transport et variations testés sur machine par AveyCole le 10/10/2026."
        build.apply_writes(stock, [base, tweak])
        path = out / ("49-" + tweak["id"] + ".json")
        text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
        if args.check:
            assert path.read_text() == text, f"{path} n'est pas à jour"
        else:
            path.write_text(text)
        print(f"ok : {path.name}, {sum(map(len, blobs))} octets, {len(SLOTS)} masques vérifiés ; " + ("menu défilant" if args.scroll else "menu principal"))


if __name__ == "__main__":
    main()
