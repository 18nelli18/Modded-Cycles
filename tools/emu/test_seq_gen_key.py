#!/usr/bin/env python3
"""Preuve du raccourci sur le vrai key_hook de Model-TG épinglé (70b39dd).

L'ouverture de la nouvelle page est simulée ; le lecteur de touches de Model-TG
et le détour du générateur sont exécutés. Aucun tweak flashable n'est produit.
python3 tools/emu/test_seq_gen_key.py --cycles firmware/model-cycles_OS1.13.syx
  --model-tg ../model-tg [--cross m68k-elf-]
"""
import argparse
import pathlib
import struct
import subprocess
import sys
import tempfile

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as mk

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_sdvintage import main_os_from_syx

SRC = pathlib.Path(__file__).resolve().parents[1] / "machines/seq_gen/key.s"
CODE, OPEN, STOP, STACK, EVENT = 0x41002000, 0x4100e000, 0x4100f000, 0x42008000, 0x42001000


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--model-tg", type=pathlib.Path, required=True)
    ap.add_argument("--cross", default="m68k-elf-")
    args = ap.parse_args()
    repo, cross = args.model_tg.resolve(), args.cross
    assert subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip() == \
        "70b39dd6787770ebefc7a2d78dea1678ec012679"
    syms = {}
    for row in subprocess.check_output([cross + "nm", str(repo / "build/_b.elf")], text=True).splitlines():
        p = row.split()
        if len(p) == 3:
            syms[p[2]] = int(p[0], 16)
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        defs = "\n".join(f"TG_{name} = {syms[name]};" for name in (
            "key_hook", "set_held", "mod_used", "mm_obj", "rtg_on", "sle_on"))
        (p / "link.ld").write_text(defs + f"\nsg_open = {OPEN};\nSECTIONS {{ . = {CODE}; .text : {{ *(.text*) *(.data*) }} }}")
        for cmd in ([cross + "as", "-march=cfv4e", "-o", str(p / "key.o"), str(SRC)],
                    [cross + "ld", "-T", str(p / "link.ld"), "-o", str(p / "key.elf"), str(p / "key.o")],
                    [cross + "objcopy", "-O", "binary", str(p / "key.elf"), str(p / "key.bin")]):
            subprocess.run(cmd, check=True)
        key_blob = (p / "key.bin").read_bytes()
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)
    uc.mem_write(0x40000400, main_os_from_syx(args.cycles))
    uc.mem_write(0x401ab750, (repo / "build/_b.bin").read_bytes())
    uc.mem_write(CODE, key_blob)
    uc.mem_write(0x4007240c, b"\x4e\xf9" + struct.pack(">I", CODE))
    uc.reg_write(mk.UC_M68K_REG_SR, 0x2000)
    opens = []

    def open_page(u, address, size, data):
        opens.append(1)
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        u.reg_write(mk.UC_M68K_REG_PC, struct.unpack(">I", u.mem_read(sp, 4))[0])
        u.reg_write(mk.UC_M68K_REG_A7, sp + 4)

    uc.hook_add(UC_HOOK_CODE, open_page, begin=OPEN, end=OPEN)

    def call(code, flags, time, fresh=True, patched=True):
        if fresh:
            uc.mem_write(EVENT, struct.pack(">6I", 0, 0, time, code, flags, 127))
        uc.mem_write(STACK, struct.pack(">2I", STOP, EVENT))
        uc.reg_write(mk.UC_M68K_REG_A7, STACK)
        uc.emu_start(0x4007240c if patched else syms["key_hook"], STOP, count=10000)
        assert uc.reg_read(mk.UC_M68K_REG_PC) == STOP
        assert uc.reg_read(mk.UC_M68K_REG_A7) == STACK + 4
        return uc.reg_read(mk.UC_M68K_REG_D0)

    assert call(13, 1, 1) == 13
    assert call(15, 1, 2) == 0
    for _ in range(10):
        assert call(15, 1, 2, False) == 0
    assert len(opens) == 1
    assert struct.unpack(">I", uc.mem_read(syms["mod_used"], 4))[0] == 1
    assert call(13, 16, 3) == 0
    assert call(15, 16, 4) == 0
    assert call(15, 16, 4, False) == 0
    assert call(15, 1, 5) == 15
    assert call(15, 16, 6) == 15
    print("ok : ouverture unique malgré lectures répétées ; relâchements dans les deux ordres ; tampon événement réutilisé")
    for turn in range(3):
        call(13, 1, 10 + turn * 3)
        assert call(15, 1, 11 + turn * 3) == 0
        assert call(15, 16, 12 + turn * 3) == 0
        assert call(13, 16, 13 + turn * 3) == 0
    assert len(opens) == 4
    print("ok : réouvertures après relâchement normal")
    call(13, 1, 30)
    assert call(15, 3, 31) == 15
    for name in ("mm_obj", "rtg_on", "sle_on"):
        uc.mem_write(syms[name], struct.pack(">I", 1))
        assert call(15, 1, 32) == 15
        uc.mem_write(syms[name], bytes(4))
    assert len(opens) == 4
    call(13, 16, 33)
    print("ok : FUNC + PAGE, menu Model-TG, retrig et éditeur de slices gardent priorité")
    for code in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 32):
        for flags in (1, 9, 16):
            assert call(code, flags, 40) == call(code, flags, 40, patched=False)
    print("ok : autres touches sans SETTINGS identiques au vrai lecteur Model-TG")
    print(f"ok : {len(key_blob)} octets de prototype ; ouverture de page simulée, pas encore validée")


if __name__ == "__main__":
    main()
