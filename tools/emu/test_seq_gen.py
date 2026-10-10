#!/usr/bin/env python3
"""Preuve du cœur ColdFire du générateur (pas encore un tweak à flasher).

Exécute le vrai code assemblé : gammes/tonalités, bornes, repos, graines,
registre/pile et refus sans écriture. Ne prouve pas encore l'interface OS.
Commande : M68K_CROSS=m68k-elf- python3 tools/emu/test_seq_gen.py
"""
import os
import pathlib
import random
import struct
import subprocess
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

SRC = pathlib.Path(__file__).resolve().parents[1] / "machines/seq_gen/seq_gen.s"
CROSS = os.environ.get("M68K_CROSS", "m68k-elf-")
CODE, CONFIG, OUTPUT, STACK, STOP = 0x41000000, 0x42000000, 0x42001000, 0x42008000, 0x4100f000
SCALES = [tuple(range(12)), (0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 8, 10),
          (0, 2, 3, 5, 7, 9, 10), (0, 2, 4, 7, 9)]
REGS = [getattr(mk, f"UC_M68K_REG_D{i}") for i in range(2, 8)] + [
    getattr(mk, f"UC_M68K_REG_A{i}") for i in range(2, 7)]


def main():
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        (p / "link.ld").write_text(f"SECTIONS {{ . = {CODE}; .text : {{ *(.text*) *(.rodata*) }} }}")
        for cmd in ([CROSS + "as", "-march=cfv4e", "-o", str(p / "code.o"), str(SRC)],
                    [CROSS + "ld", "-T", str(p / "link.ld"), "-o", str(p / "code.elf"), str(p / "code.o")],
                    [CROSS + "objcopy", "-O", "binary", str(p / "code.elf"), str(p / "code.bin")]):
            subprocess.run(cmd, check=True)
        blob = (p / "code.bin").read_bytes()
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(CODE, 0x10000)
    uc.mem_map(CONFIG, 0x10000)
    uc.mem_write(CODE, blob)
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    writes = []
    uc.hook_add(UC_HOOK_MEM_WRITE, lambda u, a, addr, n, v, d: writes.append((addr, n)))
    rng = random.Random(841)

    def run(cfg, valid=True):
        packed = struct.pack(">7I", *[x & 0xffffffff for x in cfg])
        uc.mem_write(CONFIG, packed)
        uc.mem_write(OUTPUT - 16, b"\xa5" * 96)
        uc.mem_write(STACK, struct.pack(">I", STOP))
        uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        uc.reg_write(mk.UC_M68K_REG_A0, CONFIG)
        uc.reg_write(mk.UC_M68K_REG_A1, OUTPUT)
        saved = {r: rng.getrandbits(32) for r in REGS}
        for reg, value in saved.items():
            uc.reg_write(reg, value)
        writes.clear()
        uc.emu_start(CODE, STOP, count=100000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == STOP, "ne termine pas"
        assert uc.reg_read(mk.UC_M68K_REG_A7) == STACK + 4, "pile"
        assert all(uc.reg_read(r) == v for r, v in saved.items()), "registres"
        allowed = [(STACK - 180, STACK), (CONFIG + 24, CONFIG + 28), (OUTPUT, OUTPUT + cfg[0])]
        assert all(any(lo <= addr and addr + n <= hi for lo, hi in allowed) for addr, n in writes), "écriture hors limites"
        result = uc.reg_read(mk.UC_M68K_REG_D0)
        out = bytes(uc.mem_read(OUTPUT, 64))
        assert bytes(uc.mem_read(OUTPUT - 16, 16)) == b"\xa5" * 16
        assert bytes(uc.mem_read(CONFIG, 24)) == packed[:24]
        if not valid:
            assert result == 0xffffffff
            assert out == b"\xa5" * 64
            assert bytes(uc.mem_read(CONFIG, 28)) == packed
        else:
            length, density, low, high, scale, key, seed = cfg
            assert result == sum(n != 255 for n in out[:length])
            assert out[length:] == b"\xa5" * (64 - length)
            for note in out[:length]:
                assert note == 255 or low <= note <= high and (note - key) % 12 in SCALES[scale]
            if density == 0:
                assert result == 0
            if density == 100:
                assert result == length
        return out, bytes(uc.mem_read(CONFIG + 24, 4))

    for scale in range(5):
        for key in range(12):
            for length in (1, 16, 64):
                for density in (0, 35, 100):
                    cfg = [length, density, 36, 84, scale, key, rng.getrandbits(32)]
                    assert run(cfg) == run(cfg), "reproductibilité"
    print("ok : 1 080 exécutions, toutes gammes/tonalités, densités et longueurs, reproductibilité")
    for note in range(128):
        for scale in range(5):
            for key in range(12):
                run([1, 100, note, note, scale, key, 0], (note - key) % 12 in SCALES[scale])
    print("ok : 7 680 plages à une note, y compris plages sans note autorisée et graine nulle")
    for index, value in ((0, 0), (0, 65), (0, -1), (1, 101), (1, -1), (2, 128),
                         (3, 128), (4, 5), (4, -1), (5, 12), (5, -1)):
        cfg = [16, 50, 36, 84, 1, 0, 123]
        cfg[index] = value
        run(cfg, False)
    run([16, 50, 84, 36, 1, 0, 123], False)
    print("ok : configurations invalides refusées sans modifier sortie ni graine")
    print(f"ok : {len(blob)} octets de code et tables ; registres, pile et écritures vérifiés à chaque appel")


if __name__ == "__main__":
    main()
