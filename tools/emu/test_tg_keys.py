#!/usr/bin/env python3
"""Proof of the Model-TG retouch "SETTINGS + FUNC gives back the stock Save pattern prompt" (notes/81).

The REAL `key_hook` of Model-TG, assembled from its own source with the retouch of tools/gen_model_tg.py
(MC_PATCHES), run under Unicorn on the patched MAIN OS: each key event is a fake event (code at +12, flags at +16)
and the value returned in d0 tells whether the stock OS sees the key (the code) or not (0).

Flags measured by Model-TG (KeyProbe): bit 0 down, bit 1 FUNC, bit 3 repeat, bit 5 long press.

What is checked:
  - SETTINGS long press with FUNC held: PASSED to the OS (the stock Save pattern prompt is back);
  - SETTINGS long press alone: eaten (SETTINGS stays the chords' modifier);
  - short press, repeat and release: unchanged (the Config Menu still opens);
  - release after a chord: still eaten (no Config Menu behind it);
  - the "SETTINGS held" state follows the press and the release.

    python3 tools/emu/test_tg_keys.py --cycles model-cycles_OS1.13.syx --model-tg ../Model-TG
"""
import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import build                        # noqa: E402
import mcengine as E                # noqa: E402
import gen_model_tg as G            # noqa: E402

KEY_SETTINGS = 13                   # measured by Model-TG's KeyProbe
BLOB = 0x401ab750                   # Model-TG's own code block, run in place
EVENT = 0x40801000                  # fake key event, in the emulated BSS
DOWN, FUNC, REPEAT, LONG = 1, 2, 8, 32
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg, flush=True)
    if not ok:
        FAIL.append(msg)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", required=True)
    ap.add_argument("--model-tg", required=True, help="clone of Model-TG at the pinned commit")
    args = ap.parse_args()

    tw, stock, log, syms = G.export(pathlib.Path(args.cycles).resolve(),
                                    pathlib.Path(args.model_tg).resolve(), G.MC_PATCHES)
    p, _ = build.apply_writes(stock, [tw])
    pl, _ = build.build_payload([tw], stock, None)
    img = bytes(p) + pl
    e = E.Engine(img, extra_code=[(BLOB, E.BASE + len(img) - BLOB)])
    e.uc.mem_map(0x40800000, 0x01800000)
    uc = e.uc
    held, used, hook = syms["set_held"], syms["mod_used"], syms["key_hook"]
    print("Model-TG keys (key_hook of the retouched source)")

    def press(flags, code=KEY_SETTINGS):
        """One key event: what key_hook returns, and the state it leaves behind."""
        uc.mem_write(EVENT + 12, struct.pack(">I", code))
        uc.mem_write(EVENT + 16, struct.pack(">I", flags))
        d0 = e.call(hook, EVENT)
        return (d0, struct.unpack(">I", uc.mem_read(held, 4))[0],
                struct.unpack(">I", uc.mem_read(used, 4))[0])

    uc.mem_write(held, bytes(4))
    uc.mem_write(used, bytes(4))

    d0, h, _ = press(LONG | FUNC)
    check(d0 == KEY_SETTINGS and h == 0,
          f"long press with FUNC: passed to the OS (d0 = {d0:#x}), SETTINGS not held ({h})")

    d0, _, _ = press(LONG)
    check(d0 == 0, f"long press alone: eaten (d0 = {d0:#x}), still the chords' modifier")

    d0, h, u = press(DOWN)
    check(d0 == KEY_SETTINGS and h == 1 and u == 0,
          f"short press: passed (d0 = {d0:#x}), SETTINGS held ({h}), no chord yet ({u})")

    d0, h, _ = press(DOWN | REPEAT)
    check(d0 == KEY_SETTINGS and h == 1, f"repeat: passed (d0 = {d0:#x}), SETTINGS held ({h})")

    # a chord fired: the trig-key path itself (the slide trig) needs the sequencer state, which this
    # rig does not mount; what the release does depends only on the mod_used flag it sets.
    uc.mem_write(used, struct.pack(">I", 1))
    uc.mem_write(held, bytes(4))
    d0, _, _ = press(0)
    check(d0 == 0, f"release after a chord: eaten (d0 = {d0:#x}), no Config Menu behind it")

    uc.mem_write(used, bytes(4))
    d0, h, _ = press(0)
    check(d0 == KEY_SETTINGS and h == 0, f"release of a plain press: passed (d0 = {d0:#x}), not held ({h})")

    d0, _, _ = press(LONG | FUNC, code=1)
    check(d0 == 1, f"another key (FUNC) with FUNC held: passed as it is (d0 = {d0:#x})")

    print()
    print("FAIL" if FAIL else "TOUT OK")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
