"""Preuve : mix2 (0x400a9884) sans sa 1re boucle morte. Son ET états des voix identiques à l'octet près, coût."""
import sys, random, struct, subprocess
import numpy as np
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu"); sys.path.insert(0, "/home/user/Modded-Cycles/tools")
import mcengine as E
import build
from unicorn import UC_HOOK_CODE

SEC3 = "/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin"
STOCK = open(SEC3, "rb").read()
BASE = 0x40000400
AT, N = 0x400a98c4, 0x40
subprocess.run(["m68k-linux-gnu-as", "-mcpu=54418", "-o", "mix2.o", "mix2.S"], check=True)
subprocess.run(["m68k-linux-gnu-objcopy", "-O", "binary", "-j", ".text", "mix2.o", "mix2.bin"], check=True)
code = open("mix2.bin", "rb").read()[:0x1c]
code = code + bytes.fromhex("4e71") * ((N - len(code)) // 2)
assert len(code) == N
TW = {"id": "mix2-proto", "writes": [{"off": AT - BASE, "old": STOCK[AT - BASE:AT - BASE + N].hex(), "new": code.hex()}]}
IMG = bytes(build.apply_writes(STOCK, [TW])[0])
FAIL = []


def check(ok, msg):
    print(("  ok    " if ok else "  ECHEC ") + msg, flush=True)
    FAIL.extend([] if ok else [msg])


def run(img, setup, blocks, trigs, changes, count=False):
    e = E.Engine(img)
    for t, kw in setup.items():
        e.set(t, **kw)
    n = [0]
    if count:
        e.uc.hook_add(UC_HOOK_CODE, lambda uc, a, s, u: n.__setitem__(0, n[0] + 1))
    outs, states, cost = [], [], []
    for b in range(blocks):
        for t, kw in changes.get(b, {}).items():
            e.set(t, **kw)
        n[0] = 0
        outs.append(e.block(trigs.get(b, 0)))
        states.append(bytes(e.uc.mem_read(E.VOICE0, 6 * E.VSTRIDE)))
        cost.append(n[0])
    return np.stack(outs), states, cost


r = random.Random(7)
tot_r = tot_m = 0
for trial in range(8):
    setup = {t: dict(machine=r.choice([0, 1, 2, 3, r.randrange(6)]), note=r.randint(30, 90), pitch=r.randint(40, 88),
                     color=r.randint(0, 127), shape=r.randint(0, 127), sweep=r.randint(0, 127),
                     contour=r.randint(0, 127), punch=r.randint(0, 1), gate=r.randint(0, 1),
                     finetune=r.randint(0, 127), decay=r.randint(1, 127)) for t in range(6)}
    trigs = {}
    for b in r.sample(range(1, 300), 25):
        trigs[b] = r.randrange(1, 64)
    changes = {}
    for b in r.sample(range(1, 300), 60):
        changes[b] = {r.randrange(6): {r.choice(["color", "shape", "sweep", "contour", "decay", "pitch"]): r.randint(0, 127)}}
    ro, rs, rc = run(STOCK, setup, 300, trigs, changes, count=True)
    mo, ms, mc = run(IMG, setup, 300, trigs, changes, count=True)
    same = np.array_equal(ro, mo) and rs == ms
    tot_r += sum(rc); tot_m += sum(mc)
    check(same and np.abs(ro).max() > 0, f"essai {trial} : machines {[setup[t]['machine'] for t in range(6)]}, 25 trigs, "
          f"60 changements de réglages : sorties et états des 6 voix identiques sur 300 blocs ; instructions "
          f"{sum(rc) // 300} -> {sum(mc) // 300} par bloc")
print(f"moyenne : {tot_r // 2400} -> {tot_m // 2400} instructions par bloc ({100 * (tot_m - tot_r) / tot_r:+.1f} %)")
print("TOUT OK" if not FAIL else f"{len(FAIL)} ÉCHEC(S)")
