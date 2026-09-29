"""Lecture de l'OS du Syntakt (Syntakt_OS1.41.syx officiel, jamais fourni ici) : conteneur ELE3 et
programme du processeur DSP (section 7), pour le banc d'émulation stengine.py (notes/16).

Particularités par rapport aux Models (tools/mtlib) :
- produit SysEx 0x16, constantes de checksum V = 0x35 et C0 = 0x2C ;
- DEUX flux de paquets (octet 7 = 0x00 puis 0x01), le second avec C0 - 1 ; mis bout à bout, ils forment
  un seul conteneur ELE3 de 8 sections ;
- la section 7 (383 760 o, brute) est le programme du 2e ColdFire, chargé à 0x40000400.

    python3 tools/emu/syntakt.py Syntakt_OS1.41.syx      # vérifie et affiche les sections
"""
import collections
import hashlib
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from mtlib import aplib, container, syx   # noqa: E402

SYX_SHA256 = "8e2488f462c4a5656396a895f113bcd415e9900fa8709340dccf45d4cb9ed19e"   # Syntakt_OS1.41.syx (zip 1.41)
DSP_SHA256 = "daf6451cf9587c0b628e901b7bb6b25f4e2633d448c534c0c181dd35ec783bc2"   # sa section 7
PRODUCT, V, C0 = 0x16, 0x35, 0x2C


def load(path):
    """Syntakt_OS1.41.syx officiel -> {id de section: octets décompressés}. Vérifie tout."""
    raw = pathlib.Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SYX_SHA256:
        raise SystemExit(f"!! {path} n'est pas le Syntakt_OS1.41.syx officiel")
    msgs = syx._split(raw)
    head, data = msgs[0], msgs[1:-1]
    if head[1:4] != syx.ELEKTRON or head[4] != PRODUCT:
        raise SystemExit("!! pas un fichier Syntakt")
    streams = collections.defaultdict(list)
    for n, m in enumerate(data):
        if len(m) != syx.MSG_LEN or m[syx.CS_OFF] != syx.checksum(m, V, C0 - m[7]):
            raise SystemExit(f"!! paquet {n} : checksum invalide")
        streams[m[7]].append(m)
    body = b"".join(syx.unpack7(m[syx.PAYLOAD_OFF:syx.PAYLOAD_END]) for k in sorted(streams) for m in streams[k])
    c = container.parse(body)
    out = {}
    for s in c["sections"]:
        st = c["blob"][s["off"]:s["off"] + s["size"]]
        try:
            out[s["id"]] = aplib.depack(st)[0]
        except Exception:
            out[s["id"]] = st
    return out


def dsp_image(path):
    """Programme du processeur DSP (section 7), vérifié."""
    img = load(path)[7]
    if hashlib.sha256(img).hexdigest() != DSP_SHA256:
        raise SystemExit("!! section 7 inattendue")
    return img


if __name__ == "__main__":
    for sid, d in load(sys.argv[1]).items():
        print(f"section {sid}: {len(d)} o, SHA-256 {hashlib.sha256(d).hexdigest()[:16]}...")
