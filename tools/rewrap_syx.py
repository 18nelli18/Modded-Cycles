#!/usr/bin/env python3
"""Répare le transport SysEx d'un .syx dont le numéro de séquence a débordé.

Les firmwares de plus de ~16 140 paquets (Supermodel Full 2.62+, Lite et Optional depuis 2.56, et leurs versions pour Model:Samples)
ont été emballés avec un numéro de séquence `00 (seq >> 7) (seq & 0x7F)` non masqué : à partir de la
séquence 16 384, un octet 0x80 se retrouve dans le SysEx. Web MIDI refuse ces messages (« Invalid MIDI
message ») et le menu de démarrage reste bloqué sur RECEIVING... Le numéro est un entier de 21 bits sur
3 octets de 7 bits (bootstrap 0x8000355c, OS 0x40081c5c) : ce script relit le flux et le réemballe ainsi
(mtlib.syx.rewrap). Même conteneur, même MAIN OS, même signature ; seul l'emballage change.
Un fichier sain est laissé tel quel.

    python3 tools/rewrap_syx.py Supermodel_Full_2.64_8d9d7df60e21.syx            # -> ..._rewrapped.syx
    python3 tools/rewrap_syx.py in.syx -o out.syx
"""
import argparse
import hashlib
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from mtlib import syx  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('syx', help='le .syx à réparer')
    ap.add_argument('-o', '--out', help='fichier de sortie (défaut : <nom>_rewrapped.syx)')
    a = ap.parse_args()
    src = pathlib.Path(a.syx)
    raw = src.read_bytes()
    bad = syx.invalid_messages(raw)
    if not bad:
        print(f'{src.name} : SysEx valide, rien à faire.')
        return
    out = syx.rewrap(raw)
    dst = pathlib.Path(a.out) if a.out else src.with_name(src.stem + '_rewrapped.syx')
    dst.write_bytes(out)
    body = syx.unwrap(raw)[0]
    print(f'{src.name} : {len(bad)} message(s) invalide(s) à partir du n° {bad[0]}')
    print(f'  flux identique   : SHA-256 {hashlib.sha256(body).hexdigest()}')
    print(f'  écrit            : {dst} (SHA-256 {hashlib.sha256(out).hexdigest()})')


if __name__ == '__main__':
    main()
