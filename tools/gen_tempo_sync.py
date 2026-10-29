#!/usr/bin/env python3
"""Generates tweaks/model-cycles_OS1.13/61-tempo-sync.json: DELAY TIME and LFO SPEED in note values of the tempo
(notes/82).

SETTINGS held + a turn of DELAY TIME or LFO SPEED: right switches the parameter to SYNC (the nearest note value),
left back to FREE (the nearest stock value). In SYNC a plain turn steps through the note values (the retrig's
1/64 .. 1 BAR, triplets and dotted ones, plus 1/128, 1/96, 4/3, 3/2, 2 BAR, and 4, 8, 16 BAR for the LFOs); the
sign of an LFO value is its direction. The value is kept in the parameter's own word (kit, sound, LFO 2 record,
LFO 3/4 tables), so a pattern keeps its note value across tempo changes and saves.

Code: tools/machines/tempo_sync/tempo_sync.S, assembled (m68k gcc -mcpu=54418), its sections placed in freed 48x22
sprite masks (first that fits, largest first), each redirected to the kept mask (tools/sprites.py). It reads and
writes two variables of Model-TG (SETTINGS held, "a chord was used"), at the addresses of 30-model-tg-st.json's
symbols: the tweak requires model-tg-st.

    python3 tools/gen_tempo_sync.py --cycles model-cycles_OS1.13.syx [--check]
"""
import argparse
import json
import pathlib
import re
import struct
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "emu"))

import build                       # noqa: E402
import gen_sdvintage_exact as gx   # noqa: E402
import sprites                     # noqa: E402
import test_sdvintage as T         # noqa: E402

SRC = HERE / "machines" / "tempo_sync" / "tempo_sync.S"
DEV = HERE.parent / "tweaks" / "model-cycles_OS1.13"
OUT = DEV / "61-tempo-sync.json"
TG = DEV / "30-model-tg-st.json"
BASE = gx.BASE
# Free 48x22 masks (192 B) taken by this mod, from the top of the list (the open branches use the bottom ones);
# those left empty are not touched.
MASKS = (0x40192a24, 0x4019089c, 0x40190334, 0x4018d038, 0x4018cbc8, 0x4018bb48, 0x4018b9c8, 0x40184c78,
         0x40184af8, 0x40184808, 0x40183408, 0x401829b8)
ROOM = 192
# (address, stock bytes, symbol, opcode, role)
HOOKS = (
    (0x400581ae, "716801ac41f940149310", "ts_audio", 0x4eb9,
     "delay line length (0x4005802e): mvs.w 428(a0),d0 ; lea 0x40149310,a0 -> jsr ts_audio ; nop ; nop"),
    (0x400584f6, "203c8000100c", "ts_smooth", 0x4eb9,
     "end of the parameter smoothing (0x40058474): move.l #0x8000100c,d0 -> jsr ts_smooth"),
    (0x40091b38, "362c0006e4a7", "ts_lfo", 0x4eb9,
     "LFO phase step (0x40091ab2): move.w 6(a4),d3 ; asr.l d2,d7 -> jsr ts_lfo"),
    (0x4000a986, "48d70cfc246f0030", "ts_hook", 0x4eb9,
     "knob step of a parameter (0x4000a980): movem.l d2-d7/a2-a3,(sp) ; movea.l 48(sp),a2 -> jsr ts_hook ; nop"),
    (0x4004dfda, "203c00000100", "ts_dfmt", 0x4ef9,
     "DELAY TIME text: move.l #256,d0 -> jmp ts_dfmt"),
    (0x4004e00e, "203cffffc000", "ts_lfmt", 0x4ef9,
     "LFO SPEED text: move.l #-16384,d0 -> jmp ts_lfmt"),
    (0x4001d8ae, "280f06840000003c", "ts_face", 0x4eb9,
     "value window font (0x4001d818): move.l sp,d4 ; add.l #60,d4 -> jsr ts_face ; nop (police 6x10 grasse en SYNC)"),
    (0x4001d8d6, "4eb940071a04", "ts_draw", 0x4eb9,
     "value window text (0x4001d818): jsr 0x40071a04 (DRAW_TEXT) -> jsr ts_draw (centre la ligne de 10 px)"),
)
SYMBOLS = ("ts_audio", "ts_smooth", "ts_lfo", "ts_hook", "ts_dfmt", "ts_lfmt", "lu", "names", "tsf",
           "ts_face", "ts_draw", "small")
TG_SYMBOLS = ("set_held", "mod_used")


def sections(path):
    """[(name, size, address, alignment)] of the non-empty sections."""
    found = []
    for line in gx.run([gx.CROSS + "objdump", "-h", str(path)]).splitlines():
        m = re.match(r"\s*\d+\s+(\.\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+\S+\s+\S+\s+2\*\*(\d+)", line)
        if m and int(m.group(2), 16):
            found.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16), 1 << int(m.group(4))))
    return found


def tg_symbols():
    syms = {n: int(v, 16) for n, v in json.loads(TG.read_text(encoding="utf-8"))["symbols"].items()}
    missing = [n for n in TG_SYMBOLS if n not in syms]
    if missing:
        raise SystemExit(f"!! {TG.name} does not carry the symbols {missing} (tools/gen_model_tg.py)")
    return {n: syms[n] for n in TG_SYMBOLS}


def compile_ts(tg):
    """Assembles, places the sections in the masks, links. Returns ([(mask, bytes)], symbols)."""
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        obj, elf, ld = d / "ts.o", d / "ts.elf", d / "ts.ld"
        gx.run([gx.CROSS + "gcc", "-mcpu=54418", f"-Wa,--defsym,SET_HELD={tg['set_held']:#x}",
                f"-Wa,--defsym,MOD_USED={tg['mod_used']:#x}", "-c", str(SRC), "-o", str(obj)])
        parts = [(n, s, max(a, 2)) for n, s, _, a in sections(obj) if n.startswith((".text.", ".data."))]
        if [n for n, *_ in sections(obj) if not n.startswith((".text.", ".data."))]:
            raise SystemExit("!! unexpected section in tempo_sync.o")
        bins = [{"at": va, "size": 0, "parts": []} for va in MASKS]
        for name, size, align in sorted(parts, key=lambda p: (-p[1], p[0])):
            for b in bins:
                at = (b["size"] + align - 1) & -align
                if at + size <= ROOM:
                    b["parts"].append((name, align))
                    b["size"] = at + size
                    break
            else:
                raise SystemExit(f"!! {name} ({size} B): no room left in the masks")
        bins = [b for b in bins if b["parts"]]
        script = ["SECTIONS {"]
        for i, b in enumerate(bins):
            script.append(f"  .m{i} {b['at']:#x} : {{")
            script.extend(f"    . = ALIGN({a}); *({n})" for n, a in b["parts"])
            script.append("  }")
        script += ["  /DISCARD/ : { *(.text) *(.data) *(.bss) *(.comment) *(.note*) *(.eh_frame*) }", "}"]
        ld.write_text("\n".join(script) + "\n")
        gx.run([gx.CROSS + "ld", "--no-warn-rwx-segments", "--orphan-handling=error", "-T", str(ld), "-o", str(elf),
                str(obj)])
        syms = {}
        for line in gx.run([gx.CROSS + "nm", str(elf)]).splitlines():
            p = line.split()
            if len(p) == 3:
                syms[p[2]] = int(p[0], 16)
        out = []
        for name, size, addr, _ in sections(elf):
            if addr not in MASKS or size > ROOM:
                raise SystemExit(f"!! section {name} outside a mask: {size} B at {addr:#x}")
            binf = d / (name.strip(".") + ".bin")
            gx.run([gx.CROSS + "objcopy", "-O", "binary", "-j", name, str(elf), str(binf)])
            out.append((addr, binf.read_bytes().ljust(size, b"\0")))
    return sorted(out), syms


def build_tweak(stock):
    tg = tg_symbols()
    placed, syms = compile_ts(tg)
    writes = []
    for addr, code in placed:
        size, const, _, kept = sprites.MASKS[addr]
        if size != ROOM or stock[addr - BASE:addr - BASE + size] != stock[kept - BASE:kept - BASE + size]:
            raise SystemExit(f"!! mask {addr:#x} is not identical to the kept mask {kept:#x}")
        if [m.start() for m in re.finditer(re.escape(struct.pack(">I", addr)), stock)] != [const - BASE]:
            raise SystemExit(f"!! unexpected references to the mask {addr:#x}")
        writes.append({"off": addr - BASE, "old": stock[addr - BASE:addr - BASE + len(code)].hex(), "new": code.hex()})
        writes.append(sprites.redirect_write(addr))
    for va, old_hex, sym, op, _ in HOOKS:
        old = bytes.fromhex(old_hex)
        if stock[va - BASE:va - BASE + len(old)] != old:
            raise SystemExit(f"!! unexpected stock bytes at {va:#x}")
        new = struct.pack(">HI", op, syms[sym])
        new += b"\x4e\x71" * ((len(old) - len(new)) // 2)
        writes.append({"off": va - BASE, "old": old_hex, "new": new.hex()})
    writes.sort(key=lambda w: w["off"])
    used = sum(len(c) for _, c in placed)
    masks = ", ".join(f"{a:#x}" for a, _ in placed)
    tweak = {
        "id": "tempo-sync",
        "order": 61,
        "name": "DELAY TIME et LFO SPEED en valeurs de notes du tempo (SETTINGS + potard)",
        "description": [
            "SETTINGS tenu + DELAY TIME ou LFO SPEED : vers la droite, SYNC (la valeur de note la plus proche) ; vers "
            "la gauche, FREE (la valeur d'origine la plus proche). En SYNC, le potard seul passe d'une valeur de note "
            "à l'autre : celles du retrig de Model-TG (1/64 .. 1 BAR, triolets et pointées), plus 1/128, 1/96, 4/3, "
            "3/2, 2 BAR, et 4, 8, 16 BAR pour les LFO. Le signe d'une valeur de LFO est son sens.",
            "Gardé dans le mot du paramètre (kit, son, LFO 2, LFO 3/4) : bit 7 = SYNC. Le délai suit le tempo et "
            "reste borné à 8 s par l'OS ; « > » à côté de la valeur quand il l'est. Le LFO fait un cycle par valeur "
            "de note, quel que soit MULT.",
            "La fenêtre de valeur affiche les valeurs de note dans la police 6x10 grasse de l'OS, centrée : elles ne "
            "tiennent pas dans la grande (« 3/16 » 48 px, « 1 BAR » 65 px, « -16 BAR » 82 px mesurés pour une plaque "
            "de 60 px) ; en FREE, la fenêtre reste celle de l'OS, pixel pour pixel.",
            "Lit et écrit SETTINGS tenu et « accord utilisé » de Model-TG (set_held, mod_used, symboles de "
            "30-model-tg-st.json) : demande model-tg-st.",
            f"Code et données : {used} o dans {len(placed)} masques de sprites 48x22 libérés ({masks}). "
            "Généré par tools/gen_tempo_sync.py, notes/82.",
        ],
        "device": "Model:Cycles",
        "os": "1.13",
        "section": 3,
        "requires": ["model-tg-st"],
        "symbols": {n: f"{syms[n]:#x}" for n in SYMBOLS},
        "writes": writes,
    }
    return tweak, syms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True, help="official model-cycles_OS1.13.syx")
    ap.add_argument("--check", action="store_true", help="checks that the committed JSON matches")
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    if build.sha(stock) != json.loads((DEV / "device.json").read_text(encoding="utf-8"))["section_sha256"]:
        raise SystemExit("!! not the official MAIN OS 1.13")
    tweak, _ = build_tweak(stock)
    build.apply_writes(stock, [tweak])
    text = json.dumps(tweak, indent=1, ensure_ascii=False) + "\n"
    print("  " + tweak["description"][-1])
    if args.check:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print(f"  {OUT.name} {'is up to date' if ok else 'DOES NOT MATCH (other binutils?)'}")
        raise SystemExit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8")
    print(f"  written: {OUT.relative_to(HERE.parent)} ({len(tweak['writes'])} writes)")


if __name__ == "__main__":
    main()
