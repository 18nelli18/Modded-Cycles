"""Boucles par échantillon : pour chaque fonction, instructions par échantillon et par appel (adresses exécutées
>= 31 fois par appel), surcoût par appel. Données : seq_joue.pkl (6 pistes KICK..CHORD qui jouent, seqprof.py)."""
import pickle, bisect, collections, json
from prof import NAMES
d = pickle.load(open("seq_joue.pkl", "rb"))
addr = d["addr"]
sp = json.load(open("seqprof.json"))["joue"]["fns"]
byname = {v: k for k, v in NAMES.items()}
calls = {}
for n, (inc, exc, c) in sp.items():
    a = byname.get(n)
    if a is None:
        try: a = int(n, 16)
        except ValueError: continue
    calls[a] = c
starts = sorted(set(list(calls) + [a for a in NAMES if a >= 0x40056000]))
per = collections.defaultdict(list)
for a, c in addr.items():
    i = bisect.bisect_right(starts, a) - 1
    if i >= 0 and a >= 0x40056000:
        per[starts[i]].append((a, c))
rows = []
for f, l in per.items():
    c = max(calls.get(f, 1), 1)
    tot = sum(x[1] for x in l)
    loop = sum(x[1] for x in l if x[1] >= 31 * c)
    rows.append((tot, f, c, loop / 32 / c, (tot - loop) / c))
print(f"{'fonction':28s} {'instr/bloc':>10s} {'appels':>6s} {'instr/éch./appel':>16s} {'hors boucle/appel':>17s}")
for tot, f, c, ps, ov in sorted(rows, reverse=True):
    if tot < 60: continue
    print(f"{NAMES.get(f, hex(f)):28s} {tot:10d} {c:6d} {ps:16.1f} {ov:17.1f}")
