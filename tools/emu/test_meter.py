#!/usr/bin/env python3
"""Preuve du compteur de charge (tweak de diagnostic syntakt-meter, notes/23).

Le minuteur DMA 0 du Cycles (0xfc07000c, 135,168 MHz) est simulé. On vérifie, sur le vrai code du tweak :
  - le son : les 5 moteurs du Syntakt donnent la même sortie qu'avec le tweak normal ;
  - la sonde de la fonction audio (0x40059382 -> audio_probe) : la fonction appelée (remplacée ici par une
    fonction factice) voit la même pile, d0 revient intact, et audio_end mesure le bloc ;
  - audio_end : après 750 blocs, le nom de chaque machine est « pic/moyenne » de la charge, ou, avec METER_VOICE,
    « moyenne/voix » : charge moyenne et coût de la voix qui la joue (la plus chère si plusieurs pistes), en % de la
    durée d'un bloc ; « -- » si aucune piste ne la joue ;
  - l'écran MACHINES : les 11 machines portent leur propre nom (« --/-- » avant la 1re mesure).

    python3 tools/emu/test_meter.py --cycles model-cycles_OS1.13.syx --syntakt Syntakt_OS1.42.syx
"""
import argparse
import json
import pathlib
import struct
import sys

import numpy as np
from unicorn import UC_HOOK_MEM_READ
from unicorn import m68k_const as mk

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import gen_syntakt_engines as gs    # noqa: E402
import mcengine as E                # noqa: E402
import test_sdvintage as T          # noqa: E402
import test_sdvintage_7th as t7     # noqa: E402

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
    return bytes(p) + pl, pl, tw


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--syntakt", required=True)
    args = ap.parse_args()
    stock = T.main_os_from_syx(args.cycles)
    img_m, pl_m, tw_m = firmware(stock, "90-syntakt-meter.json", args.syntakt)
    img_r, _, _ = firmware(stock, "24-syntakt-sd-cp-toy-bits-swarm.json", args.syntakt)
    w = {x["off"] + 0x40000400: x for x in tw_m["writes"]}
    audio_probe = int(w[0x40059382]["new"][4:], 16)
    sy = {k: int(v, 16) for k, v in tw_m["gov"].items()}
    print(f"sonde de la fonction audio : {audio_probe:#x}")

    print("son")
    outs = {}
    for name, img in (("compteur", img_m), ("normal", img_r)):
        e = E.Engine(img)
        for t, eng in enumerate(list(gs.CATALOG.values())[:5]):
            e.set(t, machine=6 + t, note=60, pitch=64, color=eng["knobs"][0][2], shape=eng["knobs"][1][2],
                  sweep=eng["knobs"][2][2], contour=eng["knobs"][3][2], punch=0, gate=0, finetune=64, decay=eng["decay"])
        outs[name] = np.concatenate([e.block(0x1f if b == 1 else 0) for b in range(60)], axis=1)
    check(np.array_equal(outs["compteur"], outs["normal"]) and np.abs(outs["normal"]).max() > 1e6,
          "5 moteurs du Syntakt : sortie identique avec et sans compteur")

    print("sonde de la fonction audio")
    e = E.Engine(img_m)
    clock = [5_000_000]

    def tick(uc, access, addr, size, value, ud):
        clock[0] += 45056                            # chaque lecture avance d'un demi-bloc
        uc.mem_write(TIMER, struct.pack(">I", clock[0] & 0xffffffff))
    e.uc.hook_add(UC_HOOK_MEM_READ, tick, begin=TIMER, end=TIMER + 3)
    # fonction audio factice : recopie ses 4 arguments et son pointeur de pile à 0x93000000, rend d0 = 0x1234
    fake = bytes.fromhex("41f99300000020ef000420ef000820ef000c20ef001020cf203c000012344e75")
    saved = bytes(e.uc.mem_read(0x4005979e, len(fake)))
    e.uc.mem_map(0x93000000, 0x1000)
    e.uc.mem_write(0x4005979e, fake)
    ok = True
    for b in range(3):
        sp = E.STACK - 0x100
        frame = struct.pack(">IIIII", E.STOP, 0x11111111 + b, 0x22222222, 0x33333333, 0x44444444)
        e.uc.mem_write(sp, frame)
        e.uc.reg_write(mk.UC_M68K_REG_A7, sp)
        e.uc.emu_start(audio_probe, E.STOP, count=100_000)
        seen = struct.unpack(">5I", e.uc.mem_read(0x93000000, 20))
        ok &= seen[:4] == struct.unpack(">4I", frame[4:]) and seen[4] == sp        # même pile qu'un jsr direct
        ok &= e.uc.reg_read(mk.UC_M68K_REG_D0) == 0x1234 and e.uc.reg_read(mk.UC_M68K_REG_A7) == sp + 4
        ok &= bytes(e.uc.mem_read(sp + 4, 16)) == frame[4:]
    last_t0 = struct.unpack(">I", e.uc.mem_read(sy["gov_t0_audio"], 4))[0]
    e.uc.mem_write(0x4005979e, saved)
    check(ok and last_t0 == (clock[0] - 45056) & 0xffffffff,
          "audio_probe : la fonction appelée voit les mêmes arguments et la même pile, d0 revient, le bloc est mesuré")

    print("calcul de la charge (audio_end) et écran MACHINES")
    e = E.Engine(img_m)
    names = [struct.unpack(">I", e.uc.mem_read(0x43033800 + 4 * i, 4))[0] for i in range(11)]
    text = lambda a: bytes(e.uc.mem_read(a, 8)).split(b"\0")[0].decode()
    before = [text(a) for a in names]
    # moteur et coût mesuré (en % d'un bloc) de chaque piste, comme les laisse voice_gate / voice_after
    eng, pct = [0, 1, 6, 8, 10, 10], [7, 8, 11, 9, 13, 15]
    e.uc.mem_write(sy["gov_eng"], bytes(eng))
    e.uc.mem_write(sy["gov_cost"], struct.pack(">6I", *[p_ * 90112 // 100 + 1 for p_ in pct]))
    t = 10_000_000                                    # 1er appel : écart > 20 blocs -> remise à zéro
    for b in range(752):
        dur = 81101 if b == 400 else 45056            # 50 % ; un bloc à 90 %
        e.uc.mem_write(sy["gov_t0_audio"], struct.pack(">I", t & 0xffffffff))
        e.uc.mem_write(TIMER, struct.pack(">I", (t + dur) & 0xffffffff))
        e.call(sy["audio_end"])
        t += 90112
    after = [text(a) for a in names]
    if gs.METER_VOICE:
        want, what = ["50/7", "50/8", "50/--", "50/--", "50/--", "50/--", "50/11", "50/--", "50/9", "50/--", "50/15"], \
            "« moyenne/voix »"
    else:
        want, what = ["90/50"] * 11, "« pic/moyenne »"
    check(len(set(names)) == 11 and before == ["--/--"] * 11 and after == want,
          f"nom de chaque machine : « --/-- » avant la 1re mesure, puis {what} après 750 blocs à 50 % (un à 90 %) : {after}")
    txt = [t7.drum_select(img_m, pl_m, m)[0] for m in (0, 5, 6, 10)]
    check(all(x == ["--/--"] for x in txt), f"écran MACHINES avant la 1re mesure (machines 1, 6, 7, 11) : {txt}")
    print("\nTOUT OK" if not FAIL else f"\n{len(FAIL)} ÉCHEC(S)")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
