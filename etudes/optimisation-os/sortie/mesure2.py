"""Coût de l'étage de sortie au modèle de cache (trace.py), OS d'origine contre prototypes p1+p2+p3.

    python3 mesure2.py
Scénarios de mesure.py : six (6 pistes, réglages par défaut : envois 0, VOL+DIST 60) et six_fx (envois 40/40).
"""
import sys
sys.dont_write_bytecode = True
sys.argv = [sys.argv[0], "1", "p1,p2,p3"]
import trace                # noqa: E402
import mesure               # noqa: E402
import test_combo           # noqa: E402

for a, n in ((0x40152d38, "détours (prototypes)"), (0x40152df8, "autre-os"), (0x401592bc, "détours (prototypes)"),
             (0x4015937c, "autre-os"), (0x4015943c, "détours (prototypes)"), (0x401594fc, "autre-os"),
             (0x40185f48, "détours (prototypes)"), (0x40186058, "autre-os"), (0x4018d918, "détours (prototypes)"),
             (0x4018da60, "autre-os")):
    trace.FUNCS.append((a, n))
trace.FUNCS.sort()
trace.STARTS[:] = [a for a, _ in trace.FUNCS]
trace.POSTE["détours (prototypes)"] = "8 détours des prototypes"

patch, extra, _ = test_combo.build(["p1", "p2", "p3"])
for scen in ("six", "six_fx"):
    for label, kw in (("OS d'origine", None), ("p1+p2+p3", dict(patch=patch, extra_code=extra))):
        for flush in (False, True):
            res, tr = mesure.run(scen, flush=flush, banc_kw=kw)
            print(f"\n##### {scen} — {label}")
            mesure.table(res)
