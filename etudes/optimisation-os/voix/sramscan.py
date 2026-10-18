import struct, collections
img = open("../../os/sec3.bin","rb").read()
BASE=0x40000400
CODE_END = 0x40118000
refs = collections.defaultdict(list)
for off in range(0, CODE_END-BASE-4, 2):
    v = struct.unpack_from(">I", img, off)[0]
    if 0x80000000 <= v < 0x80010000:
        refs[v].append(off+BASE)
print(len(refs), "cibles distinctes,", sum(len(x) for x in refs.values()), "références")
# regroupe par cible
for v in sorted(refs):
    r = refs[v]
    print(f"{v:#010x} {len(r):3d} refs  {' '.join(hex(a) for a in r[:6])}{' ...' if len(r)>6 else ''}")
