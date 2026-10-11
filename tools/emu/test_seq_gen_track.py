#!/usr/bin/env python3
"""Prototype d'édition + Undo avec le VRAI setter OS de notes (0x40016642).

Objet piste et observateur simulés ; getters de longueur et setter OS exécutés.
Ne prouve pas encore la propagation des notifications vers le séquenceur audio.
"""
import argparse
import pathlib
import random
import struct
import subprocess
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_sdvintage import main_os_from_syx

SRC = pathlib.Path(__file__).resolve().parents[1] / "machines/seq_gen/track.s"
CODE, STOP, OBJ, VT, RAW, NOTES, BACKUP, STACK = (
    0x41000000, 0x4100f000, 0x42000000, 0x42000100, 0x42001000,
    0x42002000, 0x42003000, 0x42008000)
GET, NOTIFY = 0x4100d000, 0x4100d100


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--cross", default="m68k-elf-")
    args = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        (p / "link.ld").write_text(f"SECTIONS {{ . = {CODE}; .text : {{ *(.text*) }} }}")
        for cmd in ([args.cross + "as", "-march=cfv4e", "-o", str(p / "track.o"), str(SRC)],
                    [args.cross + "ld", "-T", str(p / "link.ld"), "-o", str(p / "track.elf"), str(p / "track.o")],
                    [args.cross + "objcopy", "-O", "binary", str(p / "track.elf"), str(p / "track.bin")]):
            subprocess.run(cmd, check=True)
        blob = (p / "track.bin").read_bytes()
        syms = {r.split()[2]: int(r.split()[0], 16) for r in subprocess.check_output(
            [args.cross + "nm", str(p / "track.elf")], text=True).splitlines() if len(r.split()) == 3}
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)
    uc.mem_write(0x40000400, main_os_from_syx(args.cycles))
    uc.mem_write(CODE, blob)
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    uc.mem_write(OBJ, struct.pack(">I", VT) + bytes(60))
    uc.mem_write(VT + 40, struct.pack(">I", GET))
    uc.mem_write(VT + 16, struct.pack(">I", NOTIFY))
    uc.mem_write(GET, b"\x20\x3c" + struct.pack(">I", RAW) + b"\x4e\x75")
    uc.mem_write(NOTIFY, b"\x4e\x75")
    signals = []

    def notify(u, addr, size, data):
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        obj, event = struct.unpack(">2I", u.mem_read(sp + 4, 8))
        typ, step = struct.unpack(">2I", u.mem_read(event, 8))
        assert obj == OBJ and typ == 0x400ff59c
        signals.append(step)

    uc.hook_add(UC_HOOK_CODE, notify, begin=NOTIFY, end=NOTIFY)
    rng = random.Random(48)
    regs = [getattr(mk, f"UC_M68K_REG_D{i}") for i in range(2, 8)] + [
        getattr(mk, f"UC_M68K_REG_A{i}") for i in range(3, 7)]

    def call(name, length):
        uc.mem_write(STACK, struct.pack(">I", STOP))
        uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        uc.reg_write(mk.UC_M68K_REG_A0, OBJ)
        uc.reg_write(mk.UC_M68K_REG_A1, NOTES)
        uc.reg_write(mk.UC_M68K_REG_A2, BACKUP)
        uc.reg_write(mk.UC_M68K_REG_D0, length)
        saved = {r: rng.getrandbits(32) for r in regs}
        for r, v in saved.items():
            uc.reg_write(r, v)
        signals.clear()
        uc.emu_start(syms[name], STOP, count=200000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == STOP
        assert uc.reg_read(mk.UC_M68K_REG_A7) == STACK + 4
        assert all(uc.reg_read(r) == v for r, v in saved.items())
        assert uc.reg_read(mk.UC_M68K_REG_A2) == BACKUP
        return uc.reg_read(mk.UC_M68K_REG_D0)

    for length in (1, 16, 64):
        for trial in range(20):
            raw = bytearray(rng.getrandbits(8) for _ in range(722))
            for step in range(64):
                raw[580 + step] = rng.choice([255, rng.randrange(128)])
            raw[713:715] = struct.pack(">H", length)
            notes = bytes(rng.choice([255, rng.randrange(128)]) for _ in range(length))
            uc.mem_write(RAW, bytes(raw))
            uc.mem_write(NOTES, notes)
            uc.mem_write(BACKUP - 8, b"\xa5" * 738)
            assert call("sg_track_write", length) == 1
            assert bytes(uc.mem_read(BACKUP, 722)) == raw
            expected = bytearray(raw)
            for step, note in enumerate(notes):
                flags = struct.unpack_from(">H", expected, step * 2)[0]
                flags = flags & 65534 if note == 255 else flags & 65533 | 513
                struct.pack_into(">H", expected, step * 2, flags)
                if note != 255:
                    expected[580 + step] = note
            assert bytes(uc.mem_read(RAW, 722)) == expected
            assert signals == list(range(length))
            assert call("sg_track_restore", length) == 1
            assert bytes(uc.mem_read(RAW, 722)) == raw
            assert signals == list(range(length))
            assert bytes(uc.mem_read(BACKUP - 8, 8)) == b"\xa5" * 8
            assert bytes(uc.mem_read(BACKUP + 722, 8)) == b"\xa5" * 8
    print("ok : 60 pistes avec flags et réglages variés ; Generate puis Undo restitue les 722 octets")
    print("ok : vrai setter OS et vraies notifications de pas ; registres, pile et bornes de sauvegarde")
    raw = bytes(uc.mem_read(RAW, 722))
    for flag in (0x40a78874, 0x40a7883c):
        uc.mem_write(flag, struct.pack(">I", 1))
        assert call("sg_track_write", 64) == 0
        assert call("sg_track_restore", 64) == 0
        assert bytes(uc.mem_read(RAW, 722)) == raw and not signals
        uc.mem_write(flag, bytes(4))
    uc.mem_write(NOTES, b"\x80" + bytes(63))
    assert call("sg_track_write", 64) == 0
    assert bytes(uc.mem_read(RAW, 722)) == raw and not signals
    print("ok : lecture/transport actif et note invalide refusés sans modification")
    print(f"ok : {len(blob)} octets de prototype ; propagation audio reste à prouver")


if __name__ == "__main__":
    main()
