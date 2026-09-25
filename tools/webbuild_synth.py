#!/usr/bin/env python3
"""Fabrique une image ELE3 synthetique + les .syx modifies attendus (via le
pipeline Python de reference), pour tester le port JS docs/flasher/builder.js."""
import hashlib, json, pathlib, sys, hmac
sys.path.insert(0, "tools")
import build                                   # tools/build.py (rend mtlib importable)
from mtlib import aplib, container
from mtlib.syx import wrap, unwrap, BYTES_PER_MSG

OUT = pathlib.Path(sys.argv[1])
BASE = 0x40000400
SECT_LEN = 1744192
DEV = json.loads(pathlib.Path("tweaks/model-cycles_OS1.13/device.json").read_text())
TWEAKS = {}
for f in ("10-6ch-multiout", "11-6ch-usbup"):
    TWEAKS[f] = json.loads(pathlib.Path(f"tweaks/model-cycles_OS1.13/{f}.json").read_text())

# --- 1. MAIN OS synthetique -------------------------------------------------
main = bytearray((i * 37 + 11) & 0xFF for i in range(SECT_LEN))   # remplissage deterministe

# cave 0xFF (comme dans l'image reelle : 0x40154ae4, 1040 o), bordee de non-0xFF
cave_off = 0x40154ae4 - BASE
main[cave_off - 1] = 0x4E
main[cave_off:cave_off + 1040] = b"\xff" * 1040
main[cave_off + 1040] = 0x4E

# octets 'old' de chaque tweak, a leur offset
for t in TWEAKS.values():
    for w in t["writes"]:
        old = bytes.fromhex(w["old"])
        main[w["off"]:w["off"] + len(old)] = old

# materiel de cle HMAC : ancre + chaine + \0 + constante 32 o, dans une zone libre
key_off = 0x800
s = b"REVERB SEND"
const = bytes((i * 7 + 3) & 0xFF for i in range(32))
material = container.KEY_ANCHOR + s + b"\0" + const
main[key_off:key_off + len(material)] = material
h = hashlib.sha256(s).digest(); hr = hashlib.sha256(s[::-1]).digest()
key = bytes(a ^ b ^ c for a, b, c in zip(h, hr, const))

main = bytes(main)

# --- 2. section 3 compressee (tout en litteraux) ----------------------------
ops_lit = [(aplib.LITERAL, i, 0, 1) for i in range(len(main))]
s3 = aplib.repack(main, ops_lit, bytearray(len(main)))
assert aplib.depack(s3)[0] == main, "aller-retour aplib synthetique"

# --- 3. blob ELE3 (1 section, id 3), mise en page comme container.rebuild ----
TABLE_OFF, ENTRY_SZ, ALIGN, DIGEST = 0x20, 16, 16, 32
first = TABLE_OFF + ENTRY_SZ                    # 0x30
off3 = (first + ALIGN - 1) & ~(ALIGN - 1)
blob = bytearray(off3 + len(s3))
blob[0:4] = b"ELE3"
blob[8:16] = b"1.13\0\0\0\0"
blob[0x1c:0x20] = (1).to_bytes(4, "big")        # count
blob[0x20:0x24] = (3).to_bytes(4, "big")        # id
blob[0x24:0x28] = off3.to_bytes(4, "big")       # off
blob[0x28:0x2c] = len(s3).to_bytes(4, "big")    # size
blob[0x2c:0x30] = (0).to_bytes(4, "big")        # attr
blob[off3:off3 + len(s3)] = s3
end = off3 + len(s3)
hmac_off = (end + 4 + ALIGN - 1) & ~(ALIGN - 1)
blob += b"\0" * (hmac_off + DIGEST - len(blob))
digest = hmac.new(key, bytes(blob[:hmac_off]), hashlib.sha256).digest()
blob[hmac_off:hmac_off + DIGEST] = digest
blob = bytes(blob)

stream = container.build_stream(blob, BYTES_PER_MSG)
raw = wrap(stream, 0x11, start_seq=114)
OUT.joinpath("synth.syx").write_bytes(raw)

meta = {"section_sha256": hashlib.sha256(main).hexdigest(), "device": DEV["device"], "os": DEV["os"]}

# --- 4. sorties attendues via le pipeline Python de reference ---------------
def ref_build(raw, tweak):
    stream, info = unwrap(raw)
    c = container.parse(stream)
    sec3 = next(s for s in c["sections"] if s["id"] == 3)
    m, ops = aplib.depack(c["blob"][sec3["off"]:sec3["off"] + sec3["size"]])
    patched, dirty = build.apply_writes(m, [tweak])
    new_s3 = aplib.repack(patched, ops, dirty)
    msg = c["blob"][:len(c["blob"]) - container.DIGEST_LEN]
    expect = c["blob"][len(c["blob"]) - container.DIGEST_LEN:]
    plain = []
    for sx in c["sections"]:
        try: plain.append(aplib.depack(c["blob"][sx["off"]:sx["off"] + sx["size"]])[0])
        except Exception: pass
    k = container.find_key(plain, msg, expect)
    assert k == key, "find_key doit retrouver la meme cle"
    nb = container.rebuild(c, {3: new_s3}, k)
    out = wrap(container.build_stream(nb, BYTES_PER_MSG), info["product"], info["start_seq"])
    return out, hashlib.sha256(patched).hexdigest()

meta["expect"] = {}
for name, t in TWEAKS.items():
    out, sha = ref_build(raw, t)
    OUT.joinpath(f"expect_{t['id']}.syx").write_bytes(out)
    meta["expect"][t["id"]] = {"sha_mainos": sha, "bytes": len(out)}

OUT.joinpath("meta.json").write_text(json.dumps(meta))
print("synth.syx", len(raw), "o ; section3 sha", meta["section_sha256"][:16],
      "; tweaks", list(meta["expect"]))
