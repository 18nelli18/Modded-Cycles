"""Preuve du gain ACID prive : ABI, saturation et rendu natif avant/apres.

Usage : python tools/emu/test_acid_output_gain.py ancien.syx nouveau.syx
Le bootstrap reel est execute ; aucun etat du DSP ACID n'est remplace.
"""
import struct
import subprocess
import sys

from boot_candidate import ROOT, boot
from unicorn import UC_HOOK_CODE, m68k_const as C

_run = subprocess.run
_objdump = str(ROOT.parent / 'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-objdump.exe')
subprocess.run = lambda argv, *a, **kw: _run(
    [_objdump, *argv[1:]] if isinstance(argv, list) and argv[0] == 'm68k-linux-gnu-objdump' else argv, *a, **kw)
import mcengine as E
import test_model_tg as TM

E.PAYLOAD_CODE = (*E.PAYLOAD_CODE, (0x43076000, 0x43078000))


def sat(x):
    return max(-0x80000000, min(0x7fffffff, x * 2))


def main():
    old, new = [boot(p) for p in sys.argv[1:3]]
    engines = [TM.engine(im, payload=mem[0]) for im, mem in (old, new)]
    e = engines[1]
    # Le faux rendu ne sert qu'aux valeurs limites ; le rendu reel suit.
    values = [-0x80000000, -0x7fffffff, -0x40000001, -0x40000000,
              -1, 0, 1, 0x3fffffff, 0x40000000, 0x7fffffff] * 3 + [123, -456]
    out, voice = 0x40710004, 0x40711000
    def stub(u, pc, size, data):
        sp = u.reg_read(C.UC_M68K_REG_A7)
        ret, arg1, arg2 = struct.unpack('>III', u.mem_read(sp, 12))
        assert (arg1, arg2) == (out, voice)
        u.mem_write(out, struct.pack('>32i', *values))
        u.reg_write(C.UC_M68K_REG_D0, 0x12345678)
        u.reg_write(C.UC_M68K_REG_A7, sp + 4)
        u.reg_write(C.UC_M68K_REG_PC, ret)
    hook = e.uc.hook_add(UC_HOOK_CODE, stub, begin=0x46776404, end=0x46776404)
    count = [0]
    def tick(u, pc, size, data):
        count[0] += 1
    counter = e.uc.hook_add(UC_HOOK_CODE, tick, begin=0x467b4100, end=0x467b4160)
    e.uc.mem_write(out - 4, b'ABCD' + bytes(128) + b'EFGH')
    e.uc.reg_write(C.UC_M68K_REG_D2, 0x23456789)
    e.uc.reg_write(C.UC_M68K_REG_A2, 0x34567890)
    assert e.call(0x467b4100, out, voice) == 0x12345678
    assert list(struct.unpack('>32i', e.uc.mem_read(out, 128))) == list(map(sat, values))
    assert bytes(e.uc.mem_read(out - 4, 4)) == b'ABCD'
    assert bytes(e.uc.mem_read(out + 128, 4)) == b'EFGH'
    assert e.uc.reg_read(C.UC_M68K_REG_D2) == 0x23456789
    assert e.uc.reg_read(C.UC_M68K_REG_A2) == 0x34567890
    e.uc.hook_del(hook)
    e.uc.hook_del(counter)
    print('PASS: signed saturation, 32-sample bounds and preserved ABI', flush=True)
    print('Gain wrapper cost:', count[0], 'instructions per 32-sample voice block (DSP excluded)', flush=True)
    captures = [[], []]
    for i, eng in enumerate(engines):
        def capture(u, pc, size, data, i=i):
            ptr = u.reg_read(C.UC_M68K_REG_D3)
            captures[i].append(struct.unpack('>32i', u.mem_read(ptr, 128)))
        # Le dispatch est recopie dans la SRAM au bootstrap natif.
        def locate(u, pc, size, data, eng=eng, capture=capture, sites=set()):
            sp = u.reg_read(C.UC_M68K_REG_A7)
            ret = struct.unpack('>I', u.mem_read(sp, 4))[0]
            if ret not in sites:
                sites.add(ret)
                eng.uc.hook_add(UC_HOOK_CODE, capture, begin=ret, end=ret)
        fn = 0x46776404 if i == 0 else 0x467b4100
        eng.uc.hook_add(UC_HOOK_CODE, locate, begin=fn, end=fn)
        for t in range(6):
            eng.uc.mem_write(E.VOICE0 + t * E.VSTRIDE + 0x38, struct.pack('>I', 1))
            # Identifiant du moteur ACID dans les parametres audio.
            eng.set(t, machine=13, note=36 + t * 7, pitch=64, finetune=64,
                    color=64 + t * 12, shape=t * 25, sweep=t * 25,
                    contour=127 - t * 25, decay=100)
    for b in range(12):
        for eng in engines:
            if b == 5:
                eng.set(0, note=60)
            eng.block(0x3f if b in (0, 8) else 0, 0x3f if b == 0 else 0)
        assert len(captures[0]) == len(captures[1]) == 6 * (b + 1), (b, list(map(len, captures)))
        for a, z in zip(captures[0][-6:], captures[1][-6:]):
            assert tuple(map(sat, a)) == z, (b, a, z)
        for addr, length in [(E.VOICE0, 6 * E.VSTRIDE), (0x46778000, 6 * 128)]:
            assert engines[0].uc.mem_read(addr, length) == engines[1].uc.mem_read(addr, length), (b, hex(addr))
    assert any(x for row in captures[0] for x in row)
    assert not any(eng.unmapped for eng in engines)
    print('PASS: six ACID voices, note change, retrigger; exact saturated 2x and identical DSP states', flush=True)
    for eng in engines:
        for t in range(6):
            eng.set(t, machine=t)
            eng.uc.mem_write(E.VOICE0 + t * E.VSTRIDE + 0x38, struct.pack('>I', 1))
    for b in range(3):
        a, z = [eng.block(0x3f if b == 0 else 0, 0x3f if b == 0 else 0) for eng in engines]
        assert (a == z).all()
    print('PASS: six stock machines unchanged', flush=True)


if __name__ == '__main__':
    main()
