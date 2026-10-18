"""Le reste du delay quand la queue ne s'éteint pas : valeurs exactes (sortie, écriture dans la ligne, état du filtre)
sur quelques blocs, après une salve de bruit (comme queue2.py).

    python3 residu.py blocs envoi_delay envoi_reverb delay_time fdbk size
"""
import sys
sys.dont_write_bytecode = True
import numpy as np                  # noqa: E402
import banc                         # noqa: E402
import queue2                       # noqa: E402  (lit sys.argv[1:7])


def main():
    b = banc.Banc()
    for t in range(6):
        b.param(t, 20, queue2.DS)
        b.param(t, 21, queue2.RS)
    for slot, v in ((9, queue2.DT), (10, queue2.FB), (11, queue2.SZ), (12, queue2.TONE)):
        b.param(6, slot, v)
    for t in range(6):
        b.rig.set_step(t, 0, vel=120, length=14)
    pr = queue2.Probe(b)
    for k in range(queue2.N):
        pr.k = k
        if k == 2:
            for t in range(6):
                b.rig.schedule_step(t, 0, b.rig.now + b.rig.blk)
        b.block()
        if k >= queue2.N - 3:
            sn = pr.snap
            print(f"bloc {k}")
            print("  sortie delay  L:", sn["dout"][0::2][:8], "... R:", sn["dout"][1::2][:8],
                  "uniques", np.unique(sn["dout"]))
            print("  écrit ligne   :", np.unique(sn["dline"]), " filtre b8dc :", b.r32s(0x8000b8dc, 4),
                  " gains a100 :", b.r32s(0x8000a100, 4))
            print("  prises A      :", np.unique(b.r32s(0x8000b590, 68)), " B :", np.unique(b.r32s(0x8000b6a0, 68)))
            print("  sortie reverb :", int(np.abs(sn["rout"]).max()), " anneau :", np.unique(b.r32s(banc.RING, 128)))


if __name__ == "__main__":
    main()
