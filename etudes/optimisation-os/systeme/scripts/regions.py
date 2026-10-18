import sys, numpy as np, collections
sys.path.insert(0, ".")
import cachesim as C
bl = C.blocks(sys.argv[1])
b = bl[-1]
z = np.load(sys.argv[1]); marks = z["marks"]
code = z["code"][marks[-2][0]:marks[-1][0]]
R = [("rendu ISR 0x40058c5e-0x400593e0", 0x40058c5e, 0x40059500), ("fonction audio 0x4005979e-0x40059900", 0x40059500, 0x40059a00),
     ("étage de sortie 0x40056000-0x40058c5e", 0x40056000, 0x40058c5e), ("voix 0x400a7000-0x400ac000", 0x400a7000, 0x400ac000),
     ("LFO/lissage 0x40091000-0x40093000", 0x40091000, 0x40093000), ("USB 0x40002000-0x40005600", 0x40002000, 0x40005600),
     ("autre", 0, 1 << 32)]
seen = set(); 
for name, lo, hi in R:
    m = (code >= lo) & (code < hi)
    lines = set((code[m] >> 4).tolist()) - seen
    seen |= lines
    n = int(m.sum())
    print(f"{name:42s} instr {n:6d}  lignes distinctes {len(lines):4d} ({len(lines)*16/1024:.1f} Ko)")
# fonctions les plus lourdes en lignes : regrouper par plage de 0x100
cnt = collections.Counter((x >> 8) for x in set((code >> 4).tolist()))
print("plages de 4 Ko les plus présentes (lignes):")
c4 = collections.Counter((x >> 8) for x in set((code >> 4).tolist()))
for k, v in sorted(c4.items(), key=lambda t: -t[1])[:15]:
    print(f"  {k<<12:#x} : {v}")
dl = b["dl"]
cd = collections.Counter((int(x) << 4) >> 16 for x in set(dl.tolist()))
print("données cachées par 64 Ko :", [(hex(k << 16), v) for k, v in sorted(cd.items(), key=lambda t: -t[1])[:12]])
