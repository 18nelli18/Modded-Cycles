#!/usr/bin/env python3
"""Preuves ciblées Chord Keys / OS 2.0 : lanes LFO 2, état Sampler, step record (notes/42 §28).

Routines OS de sérialisation complète/partielle et d'enregistrement réelles.
Le banc step record construit le projet natif ; seule la transformation tenue
est préparée directement, les gestes UI ayant leurs preuves séparées.
Durée : environ vingt secondes.
    python3 tools/emu/chord_os2_checks.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx
"""
import argparse
import struct

import test_step_rec as sr
from chord_plock_checks import PlockRig, SLOT, B1, B2, SERIAL
from gen_chord_keys import load_stock


def run_locks(reference, image, symbols):
    r = PlockRig(reference, image, symbols)
    values = {23: 1200, 24: 28000, 25: 256, SLOT: 6,
              28: 0x3500, 29: 0x0400, 30: 0x0200, 31: 0x0b00, 32: 0x4000}
    for track in range(6):
        for slot, value in values.items():
            r.set(track, 7, slot, value)
    r.call(0x4005BA0A, SERIAL, B1, 0)
    r.call(0x4005B894, B2, SERIAL, 0)
    r.bind(B2, initialize=False)
    assert all(r.get(t, 7, k) == v for t in range(6) for k, v in values.items())
    print('ok OS 2.0 : save/load des 54 lanes Attack/Filter/Resonance/HARMONY/LFO 2 indépendantes', flush=True)
    r.set(0, 7, SLOT, 2)
    r.call(0x4005BA90, SERIAL + 4336, B2 + 4332, 0, SLOT, 0)
    r.call(0x4005B894, B1, SERIAL, 0)
    r.bind(B1, initialize=False)
    assert r.get(0, 7) == 2
    assert all(r.get(t, 7, k) == v for t in range(6) for k, v in values.items() if (t, k) != (0, SLOT))
    print('ok OS 2.0 : mise à jour partielle HARMONY conserve toutes les lanes voisines', flush=True)


def run_step(image, runtimes, symbols):
    r = sr.Rig(image, runtimes)
    bank = r.call(0x4000EB9C, r.proj)
    def sound(track):
        obj = r.call(0x40009C1A, bank, track)
        return r.call(r.u32(r.u32(obj) + 40), obj)
    chord, sampler = sound(0), sound(1)
    r.uc.mem_write(chord + 38, struct.pack('>H', 5 << 8))
    r.uc.mem_write(sampler + 38, struct.pack('>H', 6 << 8))
    # Les modes du Sampler vivent dans le SON, pas dans sa lane de lock.
    sentinel = 0x700089d0
    r.w32(sampler + 72, sentinel)
    r.call(symbols['ck_ui_config_set'], 0, 0x80000000 | (48 << 21))
    header = r.call(symbols['ck_ui_header'])
    r.key(sr.REC)
    r.key(sr.REC, sr.PRESS | sr.DOUBLE)
    for step, modifier in enumerate((1, 6, 0)):
        r.w32(symbols['live_modifiers'], header)
        r.w32(symbols['live_modifiers'] + 4, modifier)
        r.note(0, 48 + step, 100)
        r.release(0, 48 + step)
        assert r.lock(0, step, SLOT) == modifier, (step, r.lock(0, step, SLOT), modifier)
    r.key(sr.REC)
    assert r.u32(sampler + 72) == sentinel
    assert all(r.lock(1, step, SLOT) == 0xffff for step in range(3))
    assert not r.bad and not sr.FAIL, (r.bad, sr.FAIL)
    print('ok OS 2.0 : REC deux fois, trois notes avec HARMONY 1/6/0, arrêt et état Sampler intact', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--syntakt', required=True)
    args = p.parse_args()
    stock = load_stock(args.cycles)
    by_id, tweaks = sr.os_tweaks(['chord-keys'])
    _, image, runtimes = sr.build_img(stock, tweaks, args.syntakt)
    _, reference, _ = sr.build_img(stock, [t for t in tweaks if t['id'] != 'chord-keys'], args.syntakt)
    symbols = {k: int(v, 16) for k, v in by_id['chord-keys']['symbols'].items()}
    run_locks(reference, image, symbols)
    run_step(image, runtimes, symbols)
    print('TOUT OK')


if __name__ == '__main__':
    main()
