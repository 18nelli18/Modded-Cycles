#!/usr/bin/env python3
"""Preuve en émulation du compteur de temps libre (idle.S) sur l'image de l'OS 1.13 d'origine.

1. vérifie les octets d'origine en 0x4000543a (lea 24(sp),sp ; bra.s .) et les remplace par jmp idle ;
2. lance la tâche d'attente depuis 0x4000543a avec un minuteur DMA 0 modélisé (1 cycle de bus par instruction,
   6 par lecture du minuteur) et des « vols » de temps qui imitent la machine en lecture : bloc audio (1 500/s,
   charge L), panneau (12 000/s, 60 cycles), USB (8 000/s, 2 x 150 cycles), interface (30 images/s) ;
3. compare le temps libre compté au temps libre vrai, et vérifie que la boucle n'écrit que son compteur et ne
   sort pas d'elle-même.

    python3 idle_proto.py sec3.bin idle.bin
"""
import random
import struct
import sys

from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn import m68k_const as mk

BASE, STUB, ACC = 0x40000400, 0x40152d38, 0x40152d60
HOOK, OLD = 0x4000543a, bytes.fromhex("4fef001860fe")
DTIM0 = 0xfc07000c
BUS = 135_168_000


def run(img, stub, audio_load, ui_load, ms=20, seed=1):
    rng = random.Random(seed)
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    uc.mem_map(0x40000000, 0x02400000)
    uc.mem_map(0xfc000000, 0x100000)
    uc.mem_write(BASE, img)
    assert bytes(uc.mem_read(HOOK, 6)) == OLD, "octets d'origine différents"
    uc.mem_write(HOOK, b"\x4e\xf9" + struct.pack(">I", STUB))
    uc.mem_write(STUB, stub)
    # vols de temps : (début, durée) en cycles de bus
    span = BUS * ms // 1000
    ev = []
    blk = BUS // 1500
    for k in range(span // blk + 1):
        ev.append((k * blk + rng.randrange(50), int(blk * audio_load)))
    for k in range(span // (BUS // 12000) + 1):
        ev.append((k * (BUS // 12000) + rng.randrange(100), 60))
    for k in range(span // (BUS // 8000) + 1):
        ev.append((k * (BUS // 8000) + rng.randrange(100), 300))
    for k in range(span // (BUS // 30) + 1):                       # interface : une image, puis attente
        ev.append((k * (BUS // 30) + rng.randrange(1000), int(BUS // 30 * ui_load)))
    ev.sort()
    st = dict(clock=0, stolen=0, short=0, i=0, bad_w=[], bad_pc=set(), t0=None)

    def steal_upto():
        while st["i"] < len(ev) and ev[st["i"]][0] <= st["clock"]:
            d = ev[st["i"]][1]
            st["clock"] += d
            st["stolen"] += d
            if d <= 128:
                st["short"] += d
            st["i"] += 1

    def hc(uc_, a, s, u):
        st["clock"] += 1
        if not (a == HOOK or STUB <= a < ACC):
            st["bad_pc"].add(hex(a))
        steal_upto()
        if st["clock"] >= span:
            uc_.emu_stop()

    def hr(uc_, acc, a, s, v, u):
        if a == DTIM0:
            st["clock"] += 6
            steal_upto()
            if st["t0"] is None:
                st["t0"] = (st["clock"], st["stolen"])
            st["t1"] = (st["clock"], st["stolen"])
            uc_.mem_write(DTIM0, struct.pack(">I", st["clock"] & 0xffffffff))

    def hw(uc_, acc, a, s, v, u):
        if a != ACC and not 0x41ff0000 <= a < 0x42000000:            # pile (lea 24(sp) n'écrit rien)
            st["bad_w"].append(hex(a))
    uc.hook_add(UC_HOOK_CODE, hc)
    uc.hook_add(UC_HOOK_MEM_READ, hr)
    uc.hook_add(UC_HOOK_MEM_WRITE, hw)
    uc.reg_write(mk.UC_M68K_REG_A7, 0x41ffff00 - 24)
    uc.emu_start(HOOK, 0, count=50_000_000)
    acc = struct.unpack(">I", uc.mem_read(ACC, 4))[0]
    (c0, s0), (c1, s1) = st["t0"], st["t1"]
    true_idle = (c1 - c0) - (s1 - s0)
    return dict(elapsed=c1 - c0, true=true_idle, counted=acc, short=st["short"], bad_w=st["bad_w"][:5],
                bad_pc=sorted(st["bad_pc"])[:5])


def main():
    img = open(sys.argv[1], "rb").read()
    stub = open(sys.argv[2], "rb").read()
    print("charge audio, interface -> temps libre vrai / compté (écart), vols courts comptés à tort ; contrôles")
    for audio, ui in ((0.77, 0.05), (0.50, 0.10), (0.90, 0.02), (0.0, 0.0)):
        r = run(img, stub, audio, ui)
        e = r["elapsed"]
        print(f"audio {audio:4.0%} interface {ui:4.0%} : libre vrai {100 * r['true'] / e:6.2f} %, compté "
              f"{100 * r['counted'] / e:6.2f} % (écart {100 * (r['counted'] - r['true']) / e:+5.2f} pt), "
              f"vols courts {100 * r['short'] / e:4.2f} % ; écritures hors compteur {r['bad_w'] or 'aucune'}, "
              f"PC hors boucle {r['bad_pc'] or 'aucun'}")


if __name__ == "__main__":
    main()
