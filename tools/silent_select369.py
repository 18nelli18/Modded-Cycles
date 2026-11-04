"""Commit SIL commun aux selecteurs stock, ajouts et Machinedrum.

Le selecteur MD contourne mb_step : pendant le commit seulement, reprendre
directement le candidat affiche avant la suite native de setMachine.
"""
import hashlib
import struct

BASE = 0x46700000
CODE = 0x4679f500
LIMIT = 0x4679f800
SITE = 0x400148aa


def apply(meta, native, runtime, out=None):
    assert meta.get('without_stage_profile') or meta.get('song_cursor367')
    assert not meta.get('silent_select369')
    assert not any(runtime[CODE-BASE:LIMIT-BASE])
    sy = meta['activity_masks']['symbols']
    committing = meta['silent_commit_guard']['committing']
    candidate = sy['mb_candidate']
    old = bytes(native[SITE-0x40000400:SITE-0x40000400+6])
    assert old[:2] == bytes.fromhex('4ef9'), old.hex()
    target = struct.unpack('>I', old[2:])[0]
    assert BASE <= target < BASE+len(runtime)
    # Aucun registre temporaire ni nouvel etat. Stk reprend son selecteur exact.
    blob = (bytes.fromhex('4ab9')+struct.pack('>I', committing)
            +bytes.fromhex('670e2039')+struct.pack('>I', candidate)
            +bytes.fromhex('72ff4ef9400148bc')+old)
    assert len(blob) == 28
    new = bytes.fromhex('4ef9')+struct.pack('>I', CODE)
    native[SITE-0x40000400:SITE-0x40000400+6] = new
    runtime[CODE-BASE:CODE-BASE+len(blob)] = blob
    return dict(code=CODE, code_bytes=len(blob), committing=committing,
                candidate=candidate, prior_selector=target,
                sha256=hashlib.sha256(blob).hexdigest(),
                patches=[dict(at=SITE, region='native', old=old.hex(), new=new.hex()),
                         dict(at=CODE, region='runtime', old=bytes(len(blob)).hex(), new=blob.hex())],
                new_state_bytes=0, added_audio_hooks=0, hardware_tested=False)
