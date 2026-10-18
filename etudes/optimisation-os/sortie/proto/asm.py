"""Assemble un .S de prototype à une adresse : rend les octets (ColdFire, as -mcpu=54418 ; pas de gcc m68k ici)."""
import os
import subprocess
import tempfile

CROSS = "m68k-linux-gnu-"


def assemble(src, va, defs=()):
    with tempfile.TemporaryDirectory() as d:
        o, elf, bin_ = (os.path.join(d, n) for n in ("a.o", "a.elf", "a.bin"))
        subprocess.run([CROSS + "as", "-mcpu=54418", "-o", o, src] + [f"--defsym={k}={v}" for k, v in defs],
                       check=True)
        subprocess.run([CROSS + "ld", "-Ttext", hex(va), "-o", elf, o], check=True)
        subprocess.run([CROSS + "objcopy", "-O", "binary", "-j", ".text", elf, bin_], check=True)
        syms = subprocess.run([CROSS + "nm", elf], check=True, capture_output=True, text=True).stdout
        return open(bin_, "rb").read(), {l.split()[2]: int(l.split()[0], 16) for l in syms.splitlines()
                                         if len(l.split()) == 3}


def jmp(src_va, dst, pad):
    """jmp dst (6 o) puis nop (4e71) jusqu'à pad octets."""
    b = bytes.fromhex("4ef9") + dst.to_bytes(4, "big")
    assert pad >= 6 and (pad - 6) % 2 == 0
    return b + bytes.fromhex("4e71") * ((pad - 6) // 2)
