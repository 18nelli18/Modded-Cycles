"""Un réglage tourné puis ramené revient-il exactement à sa valeur ? (lissage 0x40058474, gains des envois)

    python3 lissage.py
Piste 2 : envoi delay 0 -> 40 -> 0 ; piste 0 : VOL+DIST 60 -> 90 -> 60, par les cibles (comme un potard).
"""
import struct
import sys
sys.dont_write_bytecode = True
import banc        # noqa: E402
import seqrig      # noqa: E402

b = banc.Banc()


def smooth(t, slot):
    j = (0xe + 0x42 * t + 2 * slot) // 2
    return struct.unpack(">i", bytes(b.uc.mem_read(seqrig.SMOOTH + 4 * j, 4)))[0], \
        struct.unpack(">h", bytes(b.uc.mem_read(seqrig.PARAMS + 2 * j, 2)))[0]


for k in range(700):
    if k == 10:
        b.target(2, 20, 40)
        b.target(0, 19, 90)
    if k == 60:
        b.target(2, 20, 0)
        b.target(0, 19, 60)
    b.block()
    if k in (9, 59, 61, 70, 100, 150, 200, 259, 300, 350, 400, 450, 500, 600, 699):
        g = [int(x) for x in b.r32s(0x40a78bd0, 6)]
        print(f"bloc {k}: envoi delay piste 2 (lissage, lu) {smooth(2, 20)} ; VOL+DIST piste 0 {smooth(0, 19)} ; "
              f"gains envoi delay G {g} ; wet paire 0 {[int(x) for x in b.r32s(0x40a78c2c, 2)]}")
