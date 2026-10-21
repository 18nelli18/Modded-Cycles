"""Retrait physique du filtre global du profil fixe, filtre Wizard conserve.

Le loader copie Wizard de 46794700 vers 401aa140. On retire donc les octets
dans la source du loader, avant compression. Les adresses des fonctions
voisines restent stables ; les trous FF ne contiennent plus de code filtre.
Les tables filt_* restent partagees avec le filtre propre au sampler.
"""
import hashlib
import struct

RT = 0x46700000
WIZARD = 0x401aa140
SOURCE = 0x46794700
RANGES = (
    (0x401bad48, 0x401bb080, "global filter coefficient setup and DSP"),
    (0x401bbd60, 0x401bbe24, "global filter coefficients and delay state"),
    (0x401b25ae, 0x401b25c7, "global filter labels"),
)


def prune(prefix, runtime, base=0x40000400):
    # Ce helper ne s'applique qu'apres le retrait de l'adaptateur universel.
    assert prefix[0x400a7da8-base:0x400a7da8-base+6] == bytes.fromhex("4ef94016790c")
    call = 0x401ac180 + SOURCE - WIZARD - RT
    assert runtime[call:call+6] == bytes.fromhex("4eb9401bad48")
    runtime[call:call+6] = bytes.fromhex("4e714e714e71")
    # Le dernier appel DSP etait deja desactive ; supprimer aussi ses pushes.
    dead = 0x401b3f52 + SOURCE - WIZARD - RT
    assert runtime[dead:dead+12] == bytes.fromhex("2f032f2f00204e714e71508f")
    runtime[dead:dead+12] = bytes.fromhex("6000000a") + b"\xff"*8
    removed = []
    for start, end, label in RANGES:
        i = start + SOURCE - WIZARD - RT
        old = bytes(runtime[i:i+end-start])
        assert len(old) == end-start
        if start == 0x401bad48:
            assert old[:8] == bytes.fromhex("4feffff448d7001a")
        if start == 0x401b25ae:
            assert old == b"Filter\0FLT\0Resonance\0RES\0"
        runtime[i:i+len(old)] = b"\xff"*len(old)
        removed.append(dict(start=hex(start), end=hex(end), bytes=len(old),
                            label=label, old_sha256=hashlib.sha256(old).hexdigest()))
    # Plus aucune adresse absolue vers les routines ou etats retires.
    for data in (prefix, runtime):
        for i in range(0, len(data)-3, 2):
            value = struct.unpack_from(">I", data, i)[0]
            assert not any(a <= value < b for a, b, _ in RANGES), (hex(i), hex(value))
    return removed
