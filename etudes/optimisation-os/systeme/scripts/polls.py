#!/usr/bin/env python3
"""Repère les attentes actives sur un registre de périphérique : une lecture de 0xfc...... / 0xec...... / 0x8c......
suivie, à 4 instructions au plus, d'un branchement conditionnel vers elle-même ou juste avant. Liste brute, à trier."""
import re
import sys

lines = open(sys.argv[1], errors="replace").read().splitlines()
ins = []
for l in lines:
    m = re.match(r"([0-9a-f]{8}):\t[0-9a-f ]+\t(.*)", l)
    if m:
        ins.append((int(m.group(1), 16), m.group(2)))
for i, (a, t) in enumerate(ins):
    if re.search(r"\b0x(fc|ec|8c)[0-9a-f]{6}\b", t) and re.match(r"(move|btst|tst|and|cmp)", t) and ",%" in t or \
       re.match(r"(tst|btst)\S* .*0x(fc|ec|8c)[0-9a-f]{6}", t):
        for j in range(i + 1, min(i + 5, len(ins))):
            b, u = ins[j]
            m = re.match(r"b(eq|ne|cc|cs|pl|mi|ge|lt|gt|le|hi|ls)[sw]? 0x([0-9a-f]+)", u)
            if m:
                tgt = int(m.group(2), 16)
                if a - 12 <= tgt <= a:
                    print(f"{a:08x}: {t}   ->   {b:08x}: {u}")
                break
