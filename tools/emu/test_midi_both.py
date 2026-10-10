#!/usr/bin/env python3
"""Vérifie que THRU relaie l'entrée et transmet aussi la sortie (notes/50).

Le test exécute les trois portes d'émission et le test de relais de l'OS 1.13,
sur l'image stock et après application du tweak. Le getter est intercepté pour simuler
OUT et THRU ; le menu reste celui de l'OS.

    python3 tools/emu/test_midi_both.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import json
import pathlib
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import build  # noqa: E402
import gen_midi_both as G  # noqa: E402
import test_sdvintage_exact as startup  # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TWEAK = DEV / "44-midi-both.json"
STACK = 0x90010000
STOP = 0x9F000000
OUT_GATES = (0x4000154A, 0x4000156A, 0x40001590)
GET_BOOL = 0x40044DF8
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


class Rig:
    def __init__(self, image, mode):
        self.uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        self.uc.mem_map(0x40000000, 0x01000000)
        self.uc.mem_write(build.BASE, image)
        self.uc.mem_map(0x90000000, 0x10000000)
        self.uc.mem_write(STOP, b"\x4e\x71\x4e\x71")
        self.mode = mode
        self.stop_at = None
        self.result = None
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _hook(self, uc, addr, size, _):
        if addr == GET_BOOL:
            sp = uc.reg_read(mk.UC_M68K_REG_A7)
            ret = struct.unpack(">I", uc.mem_read(sp, 4))[0]
            # The OUT/THRU setting is ID 0x50. Its original getter returns the
            # stored value (0, 1, or 2), even though stock only used it as a bool.
            uc.reg_write(mk.UC_M68K_REG_D0, self.mode)
            uc.reg_write(mk.UC_M68K_REG_A7, sp + 4)
            uc.reg_write(mk.UC_M68K_REG_PC, ret)
            return
        if self.stop_at is not None and addr in (self.stop_at if isinstance(self.stop_at, tuple) else (self.stop_at,)):
            self.result = [uc.reg_read(getattr(mk, f"UC_M68K_REG_{r}")) for r in ("D0", "D3", "PC")]
            uc.emu_stop()

    def run(self, start, stop_at):
        self.stop_at = stop_at
        self.result = None
        self.uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        self.uc.reg_write(mk.UC_M68K_REG_PC, start)
        self.uc.emu_start(start, 0, count=300)
        return self.result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    args = ap.parse_args()
    stock = G.stock_mainos(args.cycles)
    tweak = json.loads(TWEAK.read_text(encoding="utf-8"))
    patched, _ = build.apply_writes(stock, [tweak])
    payload, _ = build.build_payload([tweak], stock, None)
    os_image = patched + payload

    # Run the actual bootstrap decompressor and OS startup copy/BSS hook. The
    # MIDI tweak adds no appended payload, but these checks guard the complete
    # image path that the web flasher will produce.
    check(startup.bootstrap_depack_ok(args.cycles, tweak, None), "real bootstrap decompresses the MIDI build")
    check(startup.boot_hook_ok(os_image, payload), "startup hook returns normally and preserves SRAM")

    for site in OUT_GATES:
        skip = site + (26 if site == OUT_GATES[2] else 22)
        for mode, expected_pc in ((0, site + 10), (1, skip)):
            rig = Rig(stock, mode)
            got = rig.run(site, (site + 10, skip))
            check(got is not None and got[2] == expected_pc,
                  f"porte stock {site:#x}, mode {mode}: {'sortie' if mode == 0 else 'bloquée'}")

        rig = Rig(patched, 1)
        got = rig.run(site, site + 10)
        check(got is not None and got[0] == 0 and got[2] == site + 10,
              f"porte modifiée {site:#x}: sortie autorisée en THRU")

    # Le chemin de relais stock est conservé : OUT ne relaie pas, THRU relaie.
    for mode, next_pc in ((0, 0x400012E6), (1, 0x400012E0)):
        rig = Rig(patched, mode)
        got = rig.run(0x400012D2, next_pc)
        check(got is not None and got[2] == next_pc, f"relais entrant, mode {mode}")

    print("\nTHRU émet et relaie." if not FAIL else f"\n{len(FAIL)} échec(s).")
    raise SystemExit(bool(FAIL))


if __name__ == "__main__":
    main()
