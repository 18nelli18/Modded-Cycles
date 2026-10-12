#!/usr/bin/env python3
"""Reproduit la corruption DIN quand le relais octet coupe une note-off.

Preuve du protocole, sans émulation du UART : le chemin physique devra encore
être testé après intégration d'un relais par messages complets.
"""


def decode(stream):
    status = None
    data = []
    messages = []
    for byte in stream:
        if byte >= 0xf8:
            continue
        if byte & 0x80:
            status = byte if byte < 0xf0 else None
            data = []
            continue
        if status is None:
            continue
        data.append(byte)
        length = 1 if status >> 4 in (0xc, 0xd) else 2
        if len(data) == length:
            messages.append((status, *data))
            data = []
    return messages


def main():
    # Canal 7, note 60 : le statut CC reçu coupe la note-off produite.
    off = [0x86, 60, 0]
    cc = [0xb6, 74, 100]
    wire = [off[0], cc[0], *off[1:], *cc[1:]]
    assert tuple(off) not in decode(wire)
    print('ok: un CC entrant intercalé fait disparaître la note-off DIN')

    # Même sans coupure, le running status entrant hérite du dernier statut local.
    wire = [*cc, *off, 74, 80]
    assert (0xb6, 74, 80) not in decode(wire)
    print('ok: le running status entrant est aussi corrompu par une sortie locale')

    # Contrat exigé du futur relais : paquet entier et statut toujours explicite.
    for wire in ([*off, *cc], [*cc, *off], [*off, 0xf8, *cc]):
        assert tuple(off) in decode(wire) and tuple(cc) in decode(wire)
    print('ok: messages entiers avec statut explicite préservent CC et note-off')


if __name__ == '__main__':
    main()
