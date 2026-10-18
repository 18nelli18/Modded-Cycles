#!/usr/bin/env python3
"""mkimg.py ids out.bin : MAIN OS stock + tweaks (écritures + charges utiles), image plate à VA 0x40000400."""
import sys, pathlib
sys.path.insert(0, '/home/user/Modded-Cycles/tools')
import build
SEC3 = '/tmp/claude-0/-home-user-Modded-Cycles/4cafd55d-d242-5df3-ad6a-3e64ee54ea56/scratchpad/os/sec3.bin'
def make(ids, syntakt='/home/user/Modded-Cycles/firmware/Syntakt_OS1.42.syx'):
    main = open(SEC3, 'rb').read()
    cat = build.load_catalog()
    byid = cat['model-cycles_OS1.13'][1]
    chosen = sorted((byid[i] for i in ids), key=lambda t: t['order'])
    img, _ = build.apply_writes(main, chosen)
    pay, _ = build.build_payload(chosen, main, syntakt)
    return img + pay
if __name__ == '__main__':
    ids = [x for x in sys.argv[1].split(',') if x]
    open(sys.argv[2], 'wb').write(make(ids))
