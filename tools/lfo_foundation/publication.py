# SPDX-License-Identifier: MIT
# Périmètre explicite : LICENSE dans ce répertoire.
"""Vérifie le chaînage des tampons LFO, sans calculer de résultat DSP.

Adapté du contrat original de lachlanfysh ; origine détaillée dans notes/41.
Les sorties sont fournies par l'appelant. Les tests de cette contribution
utilisent seulement des sorties synthétiques : python3 tools/test_lfo_foundation.py
"""

WORK_BYTES = 476
TRACKS = 6
CONTROL_BYTES = 16
TRACK_STRIDE = 66
NEUTRAL_DEPTH = 0x4000


def _workspace(value):
    if type(value) is not bytes or len(value) != WORK_BYTES:
        raise ValueError("complete workspace required")


def expected_private_input(live, controls):
    _workspace(live)
    if (not isinstance(controls, (tuple, list)) or len(controls) != TRACKS
            or any(type(row) is not bytes or len(row) != CONTROL_BYTES
                   for row in controls)):
        raise ValueError("six independent control rows required")
    result = bytearray(live)
    for track, control in enumerate(controls):
        offset = 16 + TRACK_STRIDE * track
        result[offset:offset + CONTROL_BYTES] = control
    return bytes(result)


def advance_expected_publication(live, private_input, supplied_output):
    for workspace in (live, private_input, supplied_output):
        _workspace(workspace)
    result = bytearray(live)
    for track in range(TRACKS):
        destination = private_input[22 + TRACK_STRIDE * track]
        if destination == 0:
            continue
        if not 10 <= destination <= 22:
            raise ValueError("destination outside the publication contract")
        depth = int.from_bytes(
            private_input[30 + TRACK_STRIDE * track:32 + TRACK_STRIDE * track],
            "big")
        if depth == NEUTRAL_DEPTH:
            continue
        offset = 14 + TRACK_STRIDE * track + 2 * destination
        result[offset:offset + 2] = supplied_output[offset:offset + 2]
    return bytes(result)


def compare_snapshot(live, controls, captured):
    _workspace(captured)
    expected = expected_private_input(live, controls)
    if captured != expected:
        first = next(i for i, (a, b) in enumerate(zip(expected, captured))
                     if a != b)
        raise AssertionError(("private snapshot lost preceding publication", first))
    return expected
