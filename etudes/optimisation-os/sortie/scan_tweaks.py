"""Les écritures de tous les tweaks du dépôt (section 3) qui touchent les détours et les masques des prototypes, et
l'étage de sortie.  python3 scan_tweaks.py"""
import glob
import json

BASE = 0x40000400
ZONES = [(0x40057062, 8, "détour p1"), (0x40057516, 6, "détour p2 delay"), (0x40057ac8, 6, "détour p2 R1"),
         (0x40057dc6, 6, "détour p2 R2"), (0x40056716, 8, "détour p3 (6)"), (0x40056698, 8, "détour p3 (7)"),
         (0x40152d38, 192, "masque p1"), (0x401592bc, 192, "masque p2 lib"), (0x40185f48, 272, "masque p2 delay"),
         (0x4018d918, 328, "masque p2 reverb"), (0x4015943c, 192, "masque p3"),
         (0x40056400, 0x40058480 - 0x40056400, "étage de sortie entier")]
n = 0
hits = {}
for f in sorted(glob.glob("/home/user/Modded-Cycles/tweaks/model-cycles_OS1.13/*.json")):
    d = json.load(open(f))
    if not isinstance(d, dict) or d.get("section") != 3:
        continue
    for w in d.get("writes", []):
        n += 1
        a = BASE + w["off"]
        ln = len(bytes.fromhex(w["new"]))
        for lo, sz, name in ZONES:
            if a < lo + sz and a + ln > lo:
                hits.setdefault(name, set()).add(f"{d['id']}@{a:#x}")
print(len(glob.glob("/home/user/Modded-Cycles/tweaks/model-cycles_OS1.13/*.json")), "fichiers,", n, "écritures")
for lo, sz, name in ZONES:
    print(f"  {name:24s} {lo:#x}+{sz}: {sorted(hits.get(name, []))}")
