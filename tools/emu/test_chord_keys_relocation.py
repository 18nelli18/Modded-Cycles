#!/usr/bin/env python3
"""Relocation MIT ChordKeys : calculs ColdFire amont vs relogés, sans OS.

Les vrais noyaux compilés sont exécutés dans Unicorn aux anciennes/nouvelles
adresses. Accord/gamme, HARMONY, voicing/gain et noms utilisent leurs tables
relogées ; aucun résultat firmware/hardware n'est revendiqué. Les hooks UI,
MIDI et DSP doivent aussi passer la suite d'intégration PR87 du générateur.
"""
import argparse
import copy
import json
from pathlib import Path
import random
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
from unicorn import m68k_const as mk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chord_keys_relocate import BASE, relocate

MEM, OUT, STACK, STOP = 0x93000000, 0x93000100, 0x93010000, 0x93020000


class Rig:
    def __init__(self, compiled, symbols):
        self.syms = symbols
        self.u = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
        self.u.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
        self.u.mem_map(0x40000000, 0x02000000)
        self.u.mem_map(0x93000000, 0x40000)
        for at, data in compiled:
            self.u.mem_write(at, data)
        self.u.mem_write(STOP, b"\x4e\x71")

    def call(self, name, *args):
        self.u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        for i in range(2, 8):
            self.u.reg_write(getattr(mk, f"UC_M68K_REG_D{i}"), 0xa5a50000+i)
        for i in range(2, 7):
            self.u.reg_write(getattr(mk, f"UC_M68K_REG_A{i}"), 0xa5a51000+i)
        self.u.mem_write(STACK, struct.pack(">"+"I"*(len(args)+1), STOP, *[a & 0xffffffff for a in args]))
        self.u.reg_write(mk.UC_M68K_REG_A7, STACK)
        self.u.emu_start(self.syms[name], STOP, count=100000)
        if self.u.reg_read(mk.UC_M68K_REG_PC) != STOP or self.u.reg_read(mk.UC_M68K_REG_A7) != STACK+4:
            raise AssertionError((name, "retour/pile"))
        for i in range(2, 8):
            assert self.u.reg_read(getattr(mk, f"UC_M68K_REG_D{i}")) == 0xa5a50000+i, (name, "D", i)
        for i in range(2, 7):
            assert self.u.reg_read(getattr(mk, f"UC_M68K_REG_A{i}")) == 0xa5a51000+i, (name, "A", i)
        return self.u.reg_read(mk.UC_M68K_REG_D0)

    def write(self, at, data):
        self.u.mem_write(at, data)

    def read(self, at, size):
        return bytes(self.u.mem_read(at, size))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--recipe", default="work/chord-pr87/tweaks/model-cycles_OS1.13/45-chord-keys.json")
    ap.add_argument("--layout", default="work/chord-supermodel-layout.json")
    args = ap.parse_args()
    recipe, layout = json.loads(Path(args.recipe).read_text()), json.loads(Path(args.layout).read_text())
    compiled, symbols, audit = relocate(recipe, layout)
    old = [(BASE+w["off"], bytes.fromhex(w["new"])) for w in recipe["writes"]
           if any(BASE+w["off"] <= int(v, 0) < BASE+w["off"]+len(w["new"])/2 for v in recipe["symbols"].values())]
    before = Rig(old, {name: int(v, 0) for name, v in recipe["symbols"].items()})
    after = Rig(compiled, symbols)
    count = 0
    def same(name, values, data=None, out_size=0):
        nonlocal count
        for rig in (before, after):
            rig.write(MEM, (data or b"").ljust(128, b"\xa5"))
            rig.write(OUT, b"\xa5"*128)
        original = before.call(name, *values)
        actual = after.call(name, *values)
        assert actual == original, (name, values, original, actual)
        if out_size:
            assert after.read(OUT, out_size) == before.read(OUT, out_size), (name, values)
        count += 1
        return original

    for value in (-32768, -1, 0, 1, 3*256, 42*256, 43*256, 64*256, 85*256, 86*256, 127*256, 32767):
        same("ck_palette_index", (value,))
        same("ck_voicing_index", (value,))
    for root in (0, 36, 60, 96, 127):
        for mode in range(7):
            for extension in range(5):
                data = struct.pack(">9I", root, mode, *([extension]*7))
                for key in range(16):
                    same("chord_keys_build", (MEM, key, OUT), data, 48)
    print("ok : 2800 accords/limites et tables de gammes, registres/pile identiques")
    packets = []
    for mode in range(7):
        for degree in range(7):
            for extension in range(5):
                for palette in range(3):
                    for transform in range(7):
                        n = same("ck_harmony_intervals", (mode, degree, extension, palette, transform, OUT), out_size=16)
                        if n and len(packets) < 300:
                            intervals = before.read(OUT, 16)
                            packet = same("ck_chord_packet", (60, MEM, n, 60), intervals)
                            packets.append(packet)
    print("ok : 5145 HARMONY/palettes/extensions, branches et tables identiques")
    randomizer = random.Random(0x87)
    for count_notes in (3, 4):
        for index in range(9):
            for _ in range(20):
                notes = sorted(randomizer.sample(range(48, 88), count_notes)) + [0]*(4-count_notes)
                data = struct.pack(">4I", *notes)
                for rig in (before, after):
                    rig.write(MEM, data)
                    rig.call("ck_voicing_apply", MEM, count_notes, index)
                assert before.read(MEM, 16) == after.read(MEM, 16)
                for voice in range(4):
                    same("ck_voicing_gain", (index, voice, count_notes))
    for packet in (0, *packets, *(p | 0x400 for p in packets)):
        # Deux buffers distincts, la routine parcourt les tables de pointeurs
        # et les chaînes anonymes présentes entre les symboles des clusters.
        for rig in (before, after):
            rig.write(MEM, b"\xa5"*128)
            rig.call("ck_chord_name", packet, MEM, MEM+32)
        assert before.read(MEM, 64) == after.read(MEM, 64), hex(packet)
    print("ok : 360 voicings, gains et 601 noms/omissions, pointeurs/chaînes identiques")

    # Le module refuse les révisions non épinglées et réserves ambiguës.
    broken = copy.deepcopy(recipe)
    write = next(w for w in broken["writes"] if len(w["new"]) > 32)
    write["new"] = (bytes.fromhex(write["new"])[:-1]+b"\xff").hex()
    for bad_recipe, bad_layout in ((broken, layout), (recipe, [layout[0], layout[0]]),
                                   (recipe, [{"at": "0x40150000", "capacity": 8}])):
        try:
            relocate(bad_recipe, bad_layout)
        except ValueError:
            pass
        else:
            raise AssertionError("entrée dangereuse acceptée")
    print(f"ok : {count} comparaisons ColdFire, {audit['units']} unités ; ambiguïtés/refus et aucun OS nécessaire")


if __name__ == "__main__":
    main()
