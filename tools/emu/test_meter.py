#!/usr/bin/env python3
"""Preuve du compteur de charge (tweak de diagnostic syntakt-meter, notes/23).

Le minuteur DMA 0 du Cycles (0x fc07000c, 135,168 MHz) est simulé : chaque lecture renvoie la valeur choisie par
le test. On vérifie, sur le vrai code du tweak :
  - la sonde de la boucle des voix (0x4005981e -> voice_probe) : même sortie et même pile qu'un appel direct,
    durée ajoutée au compteur de la boucle des voix ;
  - les moteurs du Syntakt : sortie identique au tweak sans compteur, temps compté dans S ;
  - meter_end : après 750 blocs, les noms des machines 7 à 10 donnent M (pic), A (moyenne), V, S en % du bloc.

    python3 tools/emu/test_meter.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.41.syx
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_MEM_READ

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402

DEV = HERE.parent.parent / "tweaks" / "model-cycles_OS1.13"
TIMER = 0xfc07000c
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def firmware(stock, name, syntakt):
    tw = json.loads((DEV / name).read_text(encoding="utf-8"))
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, syntakt)
    return bytes(p) + pl, tw


class Clock:
    """Minuteur simulé : chaque lecture avance de `step` ticks."""
    def __init__(self, e, step=100):
        self.t, self.step, self.reads = 0, step, 0
        e.uc.mem_map(0xfc070000, 0x1000)
        e.uc.hook_add(UC_HOOK_MEM_READ, self._read, begin=TIMER, end=TIMER + 3)

    def _read(self, uc, access, addr, size, value, ud):
        self.t = (self.t + self.step) & 0xffffffff
        self.reads += 1
        uc.mem_write(TIMER, struct.pack(">I", self.t))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    img_m, tw_m = firmware(stock, "90-syntakt-meter.json", args.syntakt)
    img_r, _ = firmware(stock, "24-syntakt-sd-cp-toy-bits-swarm.json", args.syntakt)
    w = {x["off"] + 0x40000400: x for x in tw_m["writes"]}
    voice_probe = int(w[0x4005981e]["new"][4:], 16)
    audio_probe = int(w[0x40059382]["new"][4:], 16)
    print(f"sondes : fonction audio -> {audio_probe:#x}, boucle des voix -> {voice_probe:#x}")

    # 1. son : moteurs du Syntakt identiques avec et sans compteur (le minuteur est lu autour de chaque appel)
    print("son")
    outs = {}
    for name, img in (("compteur", img_m), ("normal", img_r)):
        e = E.Engine(img)
        clk = Clock(e)
        for t, eng in enumerate(gs.CATALOG.values()):
            if t >= 5:
                break
            e.set(t, machine=6 + t, note=60, pitch=64, color=eng["knobs"][0][2], shape=eng["knobs"][1][2],
                  sweep=eng["knobs"][2][2], contour=eng["knobs"][3][2], punch=0, gate=0, finetune=64, decay=eng["decay"])
        outs[name] = np.concatenate([e.block(0x1f if b == 1 else 0) for b in range(60)], axis=1)
        outs[name + " lectures"] = clk.reads
    check(np.array_equal(outs["compteur"], outs["normal"]) and np.abs(outs["normal"]).max() > 1e6,
          f"5 moteurs du Syntakt : sortie identique avec et sans compteur ({outs['compteur lectures']} lectures du minuteur)")

    # 2. sonde de la boucle des voix : même sortie et même pile qu'un appel direct, durée comptée
    print("sonde de la boucle des voix")
    res = {}
    for how in ("direct", "sonde"):
        e = E.Engine(img_m)
        clk = Clock(e, step=1000)
        e.set(0, machine=1, note=60, pitch=64, color=10, shape=127, sweep=8, contour=0, punch=0, gate=0, finetune=64, decay=40)
        e.set(1, machine=10, note=48, pitch=64, color=20, shape=15, sweep=70, contour=127, punch=0, gate=0, finetune=64, decay=75)
        blocks = []
        for b in range(8):
            e._write_params()
            sp = E.STACK - 0x100
            frame = struct.pack(">IIIII", E.STOP, E.TRACK_BASE, E.PARAMS, 3 if b == 1 else 0, 0)
            e.uc.mem_write(sp, frame)
            e.uc.reg_write(E.mk.UC_M68K_REG_A7, sp)
            e.uc.emu_start(voice_probe if how == "sonde" else E.VOICE_LOOP, E.STOP, count=5_000_000)
            same_stack = bytes(e.uc.mem_read(sp + 4, 16)) == frame[4:] and e.uc.reg_read(E.mk.UC_M68K_REG_A7) == sp + 4
            blocks.append(np.frombuffer(bytes(e.uc.mem_read(E.TRACK_BASE, 6 * 0x80)), dtype=">i4").copy())
        res[how] = (np.concatenate(blocks), same_stack, e)
    check(np.array_equal(res["direct"][0], res["sonde"][0]) and res["sonde"][1],
          "voice_probe : même sortie que la boucle des voix appelée directement, pile rendue intacte")

    # 3. meter_end, sur un scénario connu : bloc de 90 112 ticks, fonction audio 45 056 (50 %), un bloc à 81 101 (90 %)
    print("calcul de la charge (meter_end)")
    e = E.Engine(img_m)
    e.uc.mem_map(0xfc070000, 0x1000)
    names = [a for a in (0x43033800 + 4 * i for i in range(6, 10))]
    ptrs = [struct.unpack(">I", e.uc.mem_read(a, 4))[0] for a in names]
    sy = {k: int(v, 16) for k, v in tw_m["meter"].items()}          # adresses des variables, notées dans le tweak
    t0_audio, voice_ticks, st_ticks, meter_end = (sy["meter_t0_audio"], sy["meter_voice_ticks"], sy["meter_st_ticks"],
                                                  sy["meter_end"])
    t = 10_000_000                                    # 1er appel : écart > 20 blocs -> remise à zéro
    for b in range(752):
        dur = 81101 if b == 400 else 45056
        e.uc.mem_write(t0_audio, struct.pack(">I", t & 0xffffffff))
        e.uc.mem_write(voice_ticks, struct.pack(">I", 27034))       # 30 %
        e.uc.mem_write(st_ticks, struct.pack(">I", 9012))           # 10 %
        e.uc.mem_write(TIMER, struct.pack(">I", (t + dur) & 0xffffffff))
        e.call(meter_end)
        t += 90112
    got = [bytes(e.uc.mem_read(p, 6)).split(b"\0")[0].decode() for p in ptrs]
    check(got == ["M90%", "A50%", "V30%", "S10%"], f"noms des machines 7 à 10 après 750 blocs : {got}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
