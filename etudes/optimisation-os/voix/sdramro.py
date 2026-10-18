"""Lignes de SDRAM cachée lues par la fonction audio (relevé corrigé : lectures comprises), par plage et par fonction,
en séparant les états des voix (0x42308828 + 6 x 0x31c) du reste (tables, paramètres)."""
import pickle, collections, sys
VO = (0x42308828, 0x42308828 + 6 * 0x31c)
for state in sys.argv[1:] or ["joue", "arret"]:
    d = pickle.load(open(f"seq_{state}.pkl", "rb"))
    seq = d["seq"]
    wl = {x[1] for x in seq if x[0] == "W" and x[2] == "SDRAM-cache"}
    rl = {x[1] for x in seq if x[0] == "R" and x[2] == "SDRAM-cache"}
    allv = wl | rl
    inv = lambda l: VO[0] >> 4 <= l < (VO[1] + 15) >> 4
    print(f"== {state} : lignes SDRAM cachée {len(allv)} (écrites {len(wl)}, lues seulement {len(rl - wl)}) ; "
          f"états des voix {sum(1 for l in allv if inv(l))}, autres {sum(1 for l in allv if not inv(l))}")
    # plages contiguës hors voix
    ro = sorted(l for l in allv if not inv(l))
    runs = []
    for l in ro:
        if runs and l - runs[-1][1] <= 2:
            runs[-1][1] = l
        else:
            runs.append([l, l])
    for a, b in runs:
        fns = sorted({f for f, regs in d["fnlines"].items() for x in regs.get("SDRAM-cache", []) if a <= x <= b})
        n = sum(1 for l in ro if a <= l <= b)
        print(f"   {a << 4:#010x}..{(b + 1) << 4:#010x} {n:3d} lignes ({'écrites' if any(a <= l <= b for l in wl) else 'lues'}) : {', '.join(fns)[:150]}")
