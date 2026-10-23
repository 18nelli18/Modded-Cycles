#!/usr/bin/env python3
"""Preuve du compresseur de la charge utile (tools/aplib_grow.py pack, notes/50 §10) sur le Modded Cycles OS : l'OS
de os.json est construit comme par build.py --os, puis le crochet de démarrage s'exécute pour de vrai (Unicorn) :
le jsr de 0x40000530 -> notre crochet (décompresseur aPLib de stub.S, 2e étage) -> boot_extra_hook de Model-TG.

  1. le flux relu par mtlib.aplib.depack redonne la charge utile, octet pour octet ;
  2. dans l'émulation, la charge utile décompressée à 0x46700000 est celle que build.py a calculée, la SRAM
     reçoit ses deux zones (code et voix du Syntakt), pile et registres d2..d7/a2..a6 intacts, et le crochet finit
     sur boot_extra_hook ;
  3. l'image décompressée finit sous 0x40200000 (la marge est affichée) ;
  4. docs/flasher/builder.js compresse les mêmes octets (node, s'il est là).

    python3 tools/emu/test_payload_pack.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
"""
import argparse
import json
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_UNMAPPED
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import aplib_grow                   # noqa: E402
import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
from mtlib import aplib, container  # noqa: E402

BASE = 0x40000400
FAILS = []


def check(ok, msg):
    print(("  OK   " if ok else "  FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


def build_os(cycles, syntakt):
    """(MAIN OS d'origine, MAIN OS patché, [(tweak, adresse d'exécution, charge utile au démarrage, octets
    rangés)])."""
    raw = pathlib.Path(cycles).read_bytes()
    stream, _ = build.unwrap(raw)
    c = container.parse(stream)
    s3 = next(s for s in c["sections"] if s["id"] == 3)
    main_os, _ = aplib.depack(c["blob"][s3["off"]:s3["off"] + s3["size"]])
    cat = build.load_catalog()
    _, dev, tweaks = build.pick_target(cat, build.sha(raw))
    os_def = json.loads((ROOT / "os.json").read_text(encoding="utf-8"))
    chosen = sorted((tweaks[t] for t in os_def["tweaks"]), key=lambda t: t["order"])
    patched, _ = build.apply_writes(main_os, chosen)
    seen = []
    orig = build.payload_image

    def spy(t, rt):
        img = orig(t, rt)
        seen.append((t, int(t["append"]["dest"], 16), rt, img))
        return img

    build.payload_image = spy
    try:
        payload, _ = build.build_payload(chosen, main_os, syntakt)
    finally:
        build.payload_image = orig
    return main_os, patched + payload, seen


def boot(img, dst, rt, hook, syms=None):
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)
    uc.mem_write(BASE, img)
    uc.mem_map(dst, 0x00100000)
    uc.mem_write(dst, b"\xa5" * 0x00100000)              # ce que la SDRAM contient avant : n'importe quoi
    uc.mem_map(0x80000000, 0x00010000)
    sram = bytearray(0x10000)                             # SRAM après son initialisation par l'OS (0x4000045c)
    for lo, hi, d in gs.CY_SRAM_INIT:
        sram[d - 0x80000000:d - 0x80000000 + hi - lo] = img[lo - BASE:hi - BASE]
    uc.mem_write(0x80000000, bytes(sram))
    uc.mem_map(0x90000000, 0x00020000)
    bad = []
    uc.hook_add(UC_HOOK_MEM_UNMAPPED, lambda u, a, addr, s, v, d: bad.append(addr) or False)
    keep = {r: 0x11110000 + i for i, r in enumerate((mk.UC_M68K_REG_D2, mk.UC_M68K_REG_D3, mk.UC_M68K_REG_D4,
                                                     mk.UC_M68K_REG_D5, mk.UC_M68K_REG_D6, mk.UC_M68K_REG_D7,
                                                     mk.UC_M68K_REG_A2, mk.UC_M68K_REG_A3, mk.UC_M68K_REG_A4,
                                                     mk.UC_M68K_REG_A5, mk.UC_M68K_REG_A6))}
    for r, v in keep.items():
        uc.reg_write(r, v)
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2700)
    sp0 = 0x90010000
    uc.reg_write(mk.UC_M68K_REG_A7, sp0)
    uc.emu_start(gs.BOOT_CALL, hook, count=100_000_000)
    pc, sp = uc.reg_read(mk.UC_M68K_REG_PC), uc.reg_read(mk.UC_M68K_REG_A7)
    ret = struct.unpack(">I", uc.mem_read(sp, 4))[0]
    regs = all(uc.reg_read(r) == v for r, v in keep.items())
    check(pc == hook and sp == sp0 - 4 and ret == gs.BOOT_CALL + 6 and regs and not bad,
          f"jsr {gs.BOOT_CALL:#x} -> notre crochet -> boot_extra_hook {hook:#x} ; pile et d2..d7/a2..a6 intactes")
    got = bytes(uc.mem_read(dst, len(rt)))
    if syms and "hot_boot" in syms:                       # code chaud en SRAM (notes/76) : ce que hot_boot a écrit
        import hotboot                                    # noqa: E402
        ok, msg, got, rt = hotboot.effects(uc, img, dst, got, rt, syms)
        check(ok, msg)
    if got != rt:
        diff = [k for k in range(len(rt)) if got[k] != rt[k]]
        print(f"    {len(diff)} octets differents, de +{diff[0]:#x} a +{diff[-1]:#x}")
    check(got == rt, f"charge utile décompressée à {dst:#x} : {len(rt)} o, celle de build.py (tables d'ondes de "
                     "CHORD reprises de la SRAM par le 2e étage)")
    import mcengine as E                                  # noqa: E402
    want = bytearray(sram)
    for stage, run, n in E.SRAM_BANKS:
        o = stage - E.PAYLOAD_DST
        want[run - 0x80000000:run - 0x80000000 + n] = rt[o:o + n]
    check(bytes(uc.mem_read(0x80000000, 0x10000)) == bytes(want),
          "SRAM : les deux zones (code et voix du Syntakt) remplies, le reste intact")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    args = ap.parse_args()
    stock, img, seen = build_os(args.cycles, args.syntakt)
    sys.path.insert(0, str(HERE))
    import syntakt                                        # noqa: E402
    import test_macro_syntakt as tmx                      # noqa: E402
    st_img = syntakt.dsp_image(args.syntakt)
    tg = json.loads((ROOT / "tweaks" / "model-cycles_OS1.13" / "30-model-tg-st.json").read_text(encoding="utf-8"))
    hook = int(tg["symbols"]["boot_extra_hook"], 16)
    for t, dst, rt, packed in seen:
        if not t["append"].get("compress"):
            continue
        print(f"{t['id']} : {len(rt)} o -> {len(packed)} o rangés")
        check(aplib.depack(bytes(aplib.SECT_HDR) + packed)[0] == rt, "mtlib.aplib.depack relit la charge utile")
        # le 2e étage du crochet recopie les tables d'ondes de CHORD (mises en SRAM par l'OS) dans la charge utile
        want = bytearray(rt)
        c0 = tmx.chord_at(t, {"st_img": st_img}) - dst
        chord = tmx.chord_tables(stock)
        want[c0:c0 + len(chord)] = chord
        gs.set_base(dst)
        boot(img, dst, bytes(want), hook, {k: int(v, 16) for k, v in t.get("symbols", {}).items()})
        if shutil.which("node"):
            with tempfile.TemporaryDirectory() as tmp:
                p = pathlib.Path(tmp)
                (p / "rt.bin").write_bytes(rt)
                js = ("const fs=require('fs');const api=require(process.argv[1]);"
                      "fs.writeFileSync(process.argv[3],api.aplibPack(new Uint8Array(fs.readFileSync(process.argv[2]))));")
                subprocess.run(["node", "-e", js, str(ROOT / "docs" / "flasher" / "builder.js"), str(p / "rt.bin"),
                                str(p / "js.bin")], check=True)
                check((p / "js.bin").read_bytes() == packed, "builder.js (aplibPack) : les mêmes octets")
        else:
            print("  (node absent : builder.js non vérifié)")
    end = BASE + len(img)
    check(end <= gs.END_LIMIT, f"image décompressée jusqu'à {end:#x} : marge {gs.END_LIMIT - end} o sous "
                               f"{gs.END_LIMIT:#x}")
    print("TOUT OK" if not FAILS else f"{len(FAILS)} ÉCHEC(S)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
