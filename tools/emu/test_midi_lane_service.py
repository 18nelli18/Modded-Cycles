#!/usr/bin/env python3
"""Note 57 : file MIDI secondaire vers routeur OS, appelé hors interruption.

Exécute le pont assembleur et le routeur natif ; seules les sorties physiques
et leurs verrous sont simulés. Vérifie budget, refus IPL, notes off et ABI.
"""
import argparse
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_midi_both import Rig, STACK, STOP, DEV
from test_midi_lane_runtime import load, BANK, SIZE
from test_sdvintage import main_os_from_syx
import build


def prove(image, combined, thru):
    r = Rig(image, thru)
    u = r.uc
    symbols = load(r)
    output = []
    locks = []

    def hook(u, addr, size, data):
        sp = u.reg_read(mk.UC_M68K_REG_A7)
        if addr in (0x40001100, 0x40003396):
            n, p = struct.unpack('>II', u.mem_read(sp+4, 8))
            assert n == 3
            assert not (u.reg_read(mk.UC_M68K_REG_SR) & 0x700)
            output.append(('DIN' if addr == 0x40001100 else 'USB', bytes(u.mem_read(p, n))))
        elif addr in (0x400032ca, 0x400032da):
            locks.append(addr)
        else:
            raise AssertionError('appel inattendu du moteur sonore')
        u.reg_write(mk.UC_M68K_REG_D0, 0)
        u.reg_write(mk.UC_M68K_REG_A7, sp+4)
        u.reg_write(mk.UC_M68K_REG_PC, struct.unpack('>I', u.mem_read(sp, 4))[0])

    for addr in (0x40001100, 0x40003396, 0x400032ca, 0x400032da,
                 0x4005894a, 0x400548ce, 0x40058e28):
        u.hook_add(UC_HOOK_CODE, hook, begin=addr, end=addr)

    def call(name, *args, sr=0x2005):
        regs = [getattr(mk, 'UC_M68K_REG_D'+str(i)) for i in range(2, 8)]
        regs += [getattr(mk, 'UC_M68K_REG_A'+str(i)) for i in range(2, 7)]
        saved = {reg: 0x93600000+reg*4 for reg in regs}
        for reg, value in saved.items():
            u.reg_write(reg, value)
        u.reg_write(mk.UC_M68K_REG_SR, sr)
        u.reg_write(mk.UC_M68K_REG_A7, STACK)
        u.mem_write(STACK, struct.pack('>'+'I'*(len(args)+1), STOP, *args))
        u.emu_start(symbols[name], STOP, count=20000)
        assert u.reg_read(mk.UC_M68K_REG_PC) == STOP
        assert u.reg_read(mk.UC_M68K_REG_A7) == STACK+4
        assert u.reg_read(mk.UC_M68K_REG_SR) == sr
        assert all(u.reg_read(reg) == value for reg, value in saved.items())
        return u.reg_read(mk.UC_M68K_REG_D0)

    def seed():
        u.mem_write(BANK, bytes(SIZE))
        u.mem_write(0x40fe4228, struct.pack('>I', 1))
        output.clear()
        locks.clear()
        packets = []
        for lane in range(6):
            p = ((0x96+lane)<<24) | ((60+lane)<<16) | (100<<8) | (2+lane%3)
            assert call('ml_step', BANK, lane, p, 1) == 1
            packets.append(p)
        for lane in range(6):
            call('ml_stop', BANK, lane)
        return packets + [p & 0xefff00ff for p in packets]

    for sr in (0x2105, 0x2300, 0x2505, 0x2700):
        seed()
        before = bytes(u.mem_read(BANK, SIZE))
        assert call('ml_service', BANK, 8, sr=sr) == 0
        assert bytes(u.mem_read(BANK, SIZE)) == before and not output and not locks
    seed()
    u.mem_write(0x40fe4228, bytes(4))
    before = bytes(u.mem_read(BANK, SIZE))
    assert call('ml_service', BANK, 8) == 0
    assert bytes(u.mem_read(BANK, SIZE)) == before and not output

    for budget in (0, 1, 7, 8, 9, 0xffffffff):
        packets = seed()
        n = min(budget, 8)
        assert call('ml_service', BANK, budget) == n
        assert struct.unpack('>I', u.mem_read(BANK, 4))[0] == 12-n
        expected = []
        for p in packets[:n]:
            ports = {2: ['USB'], 3: ['DIN'], 4: ['DIN', 'USB']}[p & 255]
            if thru and not combined:
                ports = [port for port in ports if port != 'DIN']
            expected += [(port, struct.pack('>I', p)[:3]) for port in ports]
        assert output == expected, (budget, output, expected)
        assert locks == [addr for port, _ in expected if port == 'USB'
                         for addr in (0x400032ca, 0x400032da)]
        while call('ml_service', BANK, 8):
            pass
        expected_all = []
        for p in packets:
            ports = {2: ['USB'], 3: ['DIN'], 4: ['DIN', 'USB']}[p & 255]
            if thru and not combined:
                ports = [port for port in ports if port != 'DIN']
            expected_all += [(port, struct.pack('>I', p)[:3]) for port in ports]
        assert output == expected_all
        assert struct.unpack('>I', u.mem_read(BANK, 4))[0] == 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    stock = main_os_from_syx(args.cycles)
    patched, _ = build.apply_writes(stock, [json.loads((DEV/'50-midi-both.json').read_text())])
    for image, combined in ((stock, False), (patched, True)):
        for thru in (0, 1):
            prove(image, combined, thru)
    print('ok : pont file→routeur natif, six canaux 7..12, USB/DIN/both, OUT/THRU stock et modifié')
    print('ok : budget 0/1/7/8/plafond, refus IPL/singleton absent sans retrait, note-offs, pile/SR/registres')
    print('NOTE : sorties physiques simulées ; horloge, pages, sauvegarde et hook UI restent à intégrer')


if __name__ == '__main__':
    main()
