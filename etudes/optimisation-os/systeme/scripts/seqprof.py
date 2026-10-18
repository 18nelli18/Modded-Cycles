#!/usr/bin/env python3
"""Profil par fonction du corps de l'interruption de rendu, bloc de 6 trigs avec 10 p-locks (seqcost.py)."""
import sys, collections, bisect
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu"); sys.path.insert(0, "/home/user/Modded-Cycles/tools")
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
import mcengine as E, seqrig as S
img = open(sys.argv[1], "rb").read()
locks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
ntr = int(sys.argv[3]) if len(sys.argv) > 3 else 6
e = E.Engine(img); rig = S.Rig(e, bpm=120)
at = rig.now + 2 * rig.blk + rig.blk // 3
for t in range(ntr):
    rig.set_step(t, 0, vel=110, length=S.LEN_1_16, note=50 + t)
    for k in range(locks):
        rig.set_lock(t, 0, 0x0a + k, (40 + 3 * k) << 8)
    rig.schedule_step(t, 0, at)
# pile d'appels : on attribue chaque instruction à la fonction appelée la plus récente
stack = ["isr"]; hist = collections.Counter(); on = [False]
def hk(uc, a, s, u):
    if not on[0]: return
    op = bytes(uc.mem_read(a, 2))
    hist[stack[-1]] += 1
    if op[0] == 0x4e and op[1] in (0xb9, 0xba, 0x90, 0x91, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97):   # jsr
        hk.pending = True
    elif op == b"\x4e\x75":
        if len(stack) > 1: stack.pop()
        hk.pending = False
        return
    elif hasattr(hk, "pending") and hk.pending:
        pass
hk.pending = False
def hk2(uc, a, s, u):
    if not on[0]: return
    if hk.pending:
        stack.append(hex(a)); hk.pending = False
e.uc.hook_add(UC_HOOK_CODE, hk2)
e.uc.hook_add(UC_HOOK_CODE, hk)
for b in range(6):
    rig.w32(S.NOW, rig.now)
    fp0 = S.ISTACK - 4
    e.uc.reg_write(mk.UC_M68K_REG_A6, fp0); e.uc.reg_write(mk.UC_M68K_REG_A7, fp0 - 168); e.uc.reg_write(mk.UC_M68K_REG_D7, 0)
    hist.clear(); stack[:] = ["isr"]; on[0] = True
    e.uc.emu_start(0x40058ca0, 0x40059382, count=5_000_000)
    on[0] = False
    tot = sum(hist.values())
    if tot > 1000:
        print("bloc", b, "total", tot)
        for k, v in hist.most_common(25): print(f"  {k:12s} {v:6d}")
    fp = e.uc.reg_read(mk.UC_M68K_REG_A6); e.call(0x4005979e, fp - 44); rig.now += rig.blk
