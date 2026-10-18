"""Quels tweaks du dépôt écrivent les mêmes octets que les prototypes (même logique que tools/check_overlaps.py :
intervalles [off, off+len) qui se chevauchent ; une écriture identique entière est tolérée)."""
import json, glob, collections, sys
import protos
stock = protos.SEC3.read_bytes()
tws = {n: protos.__dict__[n](stock)[0] for n in ("idle", "mix2", "punch")}
repo = {}
for f in sorted(glob.glob("/home/user/Modded-Cycles/tweaks/model-cycles_OS1.13/*.json")):
    if f.endswith("device.json"): continue
    t = json.load(open(f))
    if "writes" in t:
        repo[t.get("id", f)] = t["writes"]
for n, tw in tws.items():
    print(f"== {n}")
    for w in tw["writes"]:
        a, b = w["off"], w["off"] + len(w["new"]) // 2
        hit = collections.Counter(); same = collections.Counter()
        for rid, ws in repo.items():
            for x in ws:
                c, d = x["off"], x["off"] + len(x["new"]) // 2
                if a < d and c < b:
                    if (c, d, x["new"]) == (a, b, w["new"]): same[rid.split("-")[0]] += 1
                    else: hit[rid] += 1
        ids = sorted(hit)
        fam = collections.Counter(i.split("+")[0].rsplit("-", 0)[0] for i in ids)
        print(f"  0x{a + 0x40000400:08x}..0x{b + 0x40000400:08x} : {len(ids)} tweaks en conflit"
              + (f" ; exemples {ids[:6]}" if ids else "") + (f" ; identiques {sum(same.values())}" if same else ""))
