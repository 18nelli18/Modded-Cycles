"""Simulation de cache (8 Ko I + 8 Ko D, 4 voies, lignes de 16 o, LRU, copyback avec allocation en écriture) sur la
suite des accès de 0x4005979e (sans mixeur ni effets), relevée par seqprof.py. Froid : caches vides (l'interface les a
vidés entre deux blocs) ; chaud : même bloc rejoué derrière lui-même (rien d'autre entre deux blocs)."""
import pickle, sys, collections
from prof import Cache, simulate

VOICES = (0x42308828 >> 4, (0x42308828 + 6 * 0x31c + 15) >> 4)
CPI, LINE = 1.54, 15
BLOCK = 166667
for state in ("joue", "muette", "arret"):
    d = pickle.load(open(f"seq_{state}.pkl", "rb"))
    seq = d["seq"]
    n_ins = sum(1 for x in seq if x[0] == "I")
    (cold,), ic, dc = simulate([seq])
    res, ic, dc = simulate([seq, seq])
    warm = res[1]
    # part des états de voix dans les défauts de données à froid
    vs = [x for x in seq if x[0] != "I" and VOICES[0] <= x[1] < VOICES[1]]
    vlines = len({x[1] for x in vs})
    dlines_sd = len({x[1] for x in seq if x[0] != "I" and x[2] == "SDRAM-cache"})
    ilines = len({x[1] for x in seq if x[0] == "I"})
    def cost(r):
        mi, md, wb, unc = r
        return (mi + md + wb) * LINE
    print(f"{state:6s} instructions {n_ins} ({100 * n_ins * CPI / BLOCK:.1f} % d'un bloc) ; lignes de code {ilines}, "
          f"de données SDRAM {dlines_sd} (dont états des voix {vlines})")
    for name, r in (("froid", cold), ("chaud", warm)):
        mi, md, wb, unc = r
        print(f"   {name} : défauts I {mi}, D {md}, réécritures {wb} -> {cost(r)} cycles = {100 * cost(r) / BLOCK:.1f} % ; "
              f"total modèle {100 * (n_ins * CPI + cost(r)) / BLOCK:.1f} %")
