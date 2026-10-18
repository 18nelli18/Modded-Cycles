#!/usr/bin/env python3
"""Trace d'un bloc audio complet (interruption de rendu 0x40058ca0.. + fonction audio 0x4005979e avec mixeur, effets
et sortie codec), sur le vrai code de l'OS 1.13 d'origine, par le banc de l'étage de sortie de l'agent sortie
(optim/sortie/banc.py, lu tel quel). 6 pistes : KICK, SNARE, METAL, PERC, TONE, CHORD, sons par défaut de l'OS,
déclenchées au bloc 2 ; on enregistre les blocs 8..11 (régime établi) : lignes de code dans l'ordre d'exécution,
accès aux données (adresse, écriture ?).

    python3 trace.py out.npz [--stopped]
"""
import sys

import numpy as np

sys.path.insert(0, "/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/optim/sortie")
sys.path.insert(0, "/home/user/Modded-Cycles/tools/emu")
import banc                                         # noqa: E402
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE   # noqa: E402

MACH = (0, 1, 2, 3, 4, 5)


def main():
    out = sys.argv[1]
    stopped = "--stopped" in sys.argv
    b = banc.Banc()
    rig = b.rig
    for t, m in enumerate(MACH):
        rig.param(t, 0x09, m << 8)
    code, data = [], []
    on = [False]

    def hc(uc, a, s, u):
        if on[0]:
            code.append(a)

    def hm(uc, acc, a, s, v, u):
        if on[0]:
            data.append((a, 1 if acc == UC_MEM_WRITE else 0))
    b.uc.hook_add(UC_HOOK_CODE, hc)
    b.uc.hook_add(UC_HOOK_MEM_READ | UC_HOOK_MEM_WRITE, hm)
    marks = []
    for k in range(12):
        if k == 2 and not stopped:
            for t in range(6):
                rig.set_step(t, 0, vel=110, length=127, note=48 + t)
                rig.schedule_step(t, 0, rig.now + rig.blk // 3)
        on[0] = k >= 8
        if on[0]:
            marks.append((len(code), len(data)))
        info = b.block()
        print(k, [int(np.abs(info["out"][t]).max()) for t in range(6)], int(np.abs(info["ring"]).max()))
    marks.append((len(code), len(data)))
    np.savez_compressed(out, code=np.array(code, dtype=np.uint32),
                        daddr=np.array([d[0] for d in data], dtype=np.uint32),
                        dw=np.array([d[1] for d in data], dtype=np.uint8), marks=np.array(marks))
    print("instructions", len(code), "accès", len(data))


if __name__ == "__main__":
    main()
