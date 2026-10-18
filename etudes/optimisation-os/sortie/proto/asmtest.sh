set -e
cd "$(dirname "$0")"
python3 - <<'PY' 2>&1 | grep -v "cannot find entry"
import asm
L, D, R = 0x401592bc, 0x40185f48, 0x4018d918
c0, s0 = asm.assemble("fx_lib.S", L)
defs = [("ZSCAN", hex(s0["zscan"])), ("ZFILL", hex(s0["zfill"]))]
c1, s1 = asm.assemble("fx_dly.S", D, defs)
c2, s2 = asm.assemble("fx_rev.S", R, defs)
print("fx_lib", len(c0), "/ 192 ; fx_dly", len(c1), "/ 272 ; fx_rev", len(c2), "/ 328")
PY
