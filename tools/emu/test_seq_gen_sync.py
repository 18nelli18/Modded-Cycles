#!/usr/bin/env python3
"""Génération → vraie notification OS → vraie copie au format séquenceur.

Exécute 0x4001908a, 0x400d72be, 0x400180d6, le RTTI, les masques
64 bits et 0x4005b642. Seuls allocation/libération et ordonnanceur sont
simulés : les fermetures sont capturées, puis exécutées hors notification,
comme des tâches différées. L'initialisation complète et le rendu audio
ne sont pas couverts. Les données hors pas actifs doivent rester identiques.
"""
import argparse
import json
import pathlib
import struct

from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig, RAW, OBJ
from test_sdvintage import main_os_from_syx

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEST, PENDING = 0x93003000, 0x93004000


class SyncRig(Rig):
    def __init__(self, stock, base, tweak):
        super().__init__(stock, base, tweak)
        # Vtable réelle de la piste éditable, getter et notification d'origine.
        self.w32(OBJ, 0x400ff894)
        self.w32(OBJ + 16, RAW)
        self.w32(OBJ + 32, DEST)
        # Inhibe les observateurs UI ; la synchronisation précède ce test.
        self.u.mem_write(OBJ + 12, b"\x01")
        self.pending = []
        for addr, fn in {0x400802ec: lambda a: 0,
                         0x400cfb90: lambda a: 0x93005000,
                         0x40068d0a: self.queue}.items():
            self.stubs[addr] = fn
            self.u.hook_add(UC_HOOK_CODE, self.stub, begin=addr, end=addr)
        # Une vraie conversion complète fournit l'état initial, pas une
        # réimplémentation Python du format interne de l'OS.
        self.call(0x4005b642, DEST, RAW, 0, 0xffffffff, 0xffffffff)
        self.initial_dest = bytes(self.u.mem_read(DEST, 722))

    def queue(self, args):
        closure = args[2]
        self.pending.append((self.r32(closure + 12),
                             bytes(self.u.mem_read(self.r32(closure), 16))))
        self.u.mem_write(args[3], bytes(16))
        return 0

    def drain(self):
        for fn, data in self.pending:
            assert fn == 0x400156e6
            self.u.mem_write(PENDING, struct.pack(">I", PENDING + 32))
            self.u.mem_write(PENDING + 32, data)
            self.call(fn, PENDING)
        self.pending.clear()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycles", required=True)
    args = ap.parse_args()
    stock = main_os_from_syx(args.cycles)
    for variant, dep in (("scale-gen", "model-tg"), ("scale-gen-st", "model-tg-st")):
        base = json.loads((ROOT / f"tweaks/model-cycles_OS1.13/30-{dep}.json").read_text())
        tweak = json.loads((ROOT / f"tweaks/model-cycles_OS1.13/49-{variant}.json").read_text())
        for length in (1, 16, 64):
            for density in (0, 35, 100):
                r = SyncRig(stock, base, tweak)
                r.u.mem_write(RAW + 713, struct.pack(">H", length))
                r.call(0x4005b642, DEST, RAW, 0, 0xffffffff, 0xffffffff)
                r.initial_dest = bytes(r.u.mem_read(DEST, 722))
                original = bytes(r.u.mem_read(RAW, 722))
                r.call("sg_open")
                r.w32(r.s["sg_config"] + 4, density)
                r.call("sg_action_generate")
                assert len(r.pending) == length
                assert bytes(r.u.mem_read(DEST, 722)) == r.initial_dest
                generated = bytes(r.u.mem_read(RAW, 722))
                r.drain()
                actual = bytes(r.u.mem_read(DEST, 722))
                # Comparaison avec la conversion complète du véritable OS.
                r.call(0x4005b642, DEST, RAW, 0, 0xffffffff, 0xffffffff)
                assert bytes(r.u.mem_read(DEST, 722)) == actual
                for step in range(length):
                    assert actual[step * 2:step * 2 + 2] == generated[step * 2:step * 2 + 2]
                    assert actual[128 + step] == generated[580 + step]
                r.call("sg_action_undo")
                assert bytes(r.u.mem_read(RAW, 722)) == original
                assert len(r.pending) == length
                r.drain()
                assert bytes(r.u.mem_read(DEST, 722)) == r.initial_dest
        print(f"ok : {variant}, 9 cas, notification/RTTI/masque 64 bits réels ; copie différée des flags et notes, Undo exact côté séquenceur")
    print("Limite : ordonnanceur et observateurs UI simulés ; démarrage complet et rendu audio non couverts.")


if __name__ == "__main__":
    main()
