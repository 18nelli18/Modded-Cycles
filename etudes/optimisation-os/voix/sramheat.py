import pickle, collections
ALL = collections.defaultdict(set)   # ligne -> fonctions
for state in ("joue", "muette", "arret"):
    d = pickle.load(open(f"seq_{state}.pkl", "rb"))
    for fn, regs in d["fnlines"].items():
        for l in regs.get("SRAM", []):
            ALL[l].add(fn)
# regroupe en plages contiguës de lignes ayant le même ensemble de fonctions
lines = sorted(ALL)
runs = []
for l in lines:
    key = frozenset(ALL[l])
    if runs and runs[-1][1] == l - 1 and runs[-1][2] == key:
        runs[-1][1] = l
    else:
        runs.append([l, l, key])
tot = 0
for a, b, k in runs:
    n = (b - a + 1) * 16; tot += n
    print(f"{a << 4:#010x}..{(b + 1) << 4:#010x} {n:6d} o  {', '.join(sorted(k))}")
print("total", tot, "o touchés par 0x4005979e (sans mixeur ni effets), sur 65 536")
