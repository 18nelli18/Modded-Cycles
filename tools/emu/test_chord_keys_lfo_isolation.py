#!/usr/bin/env python3
"""HARMONY RAM26 et LFO2 natif : isolation réelle avec Model-TG plain/ST.

Extraction/application/lissage de locks, dispatcher LFO2, bitmap HARMONY,
codec du son et save/load de rangées natifs. Les pointeurs de projet et
l'observateur UI sont fournis par les fixtures existantes ; aucune E/S disque.
--cycles --chord --bank --lfo --tg [--tg ...] (recettes générées finales).
Le SLOT32 PR87 est aussi exécuté pour garder la preuve de sa collision.
"""
import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import build
import mcengine as E
import test_model_tg as tg_audio
from chord_keys_slot26 import adapt, PATCHES
from test_sdvintage import main_os_from_syx
from chord_audio_checks import NativeAudioConfig, config_word
from chord_keys_compat.chord_plock_checks import PlockRig, UI
from probe_chord_storage import B1, B2, SERIAL

RAW, EVENT, SOUND, CONTEXT = 0x420C0000, 0x420C2000, 0x420C3000, 0x420D0000
EXTRACT, APPLY, RESET, SET_PARAM, SMOOTH = 0x4005487C, 0x400583DA, 0x40058308, 0x400583BA, 0x40058474
DEPTH, SAMPLE_STATE = 0x6000, 0x700089D0


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def clusters(chord, bank):
    symbols = {k: int(v, 16) for k, v in chord['symbols'].items()}
    result = []
    for write in chord['writes']:
        at = build.BASE + write['off']
        code = bytes.fromhex(write['new'])
        if any(at <= v < at + len(code) for v in symbols.values()):
            result.append((at, code))
    part = bank['append']['parts'][0]
    raw, dest = bytes.fromhex(part['hex']), int(part['dest'], 16)
    for reservation in chord['bank_reservations']:
        at, size = int(reservation['at'], 16), reservation['size']
        result.append((at, raw[at - dest:at - dest + size]))
    return result, symbols


def versions(chord, bank):
    compiled, symbols = clusters(chord, bank)
    if chord.get('harmony_slot') == 26 or chord.get('slot26_audit'):
        fixed = compiled
        broken = [(at, bytearray(code)) for at, code in compiled]
        for name, offset, old, new, _ in PATCHES:
            address = symbols[name] + offset
            at, code = next((a, d) for a, d in broken if a <= address < a + len(d))
            assert code[address - at:address - at + len(bytes.fromhex(new))] == bytes.fromhex(new)
            code[address - at:address - at + len(bytes.fromhex(old))] = bytes.fromhex(old)
        broken = [(at, bytes(code)) for at, code in broken]
        restored, _ = adapt(broken, symbols)
        assert restored == fixed
    else:
        broken = compiled
        fixed, _ = adapt(compiled, symbols)
    return broken, fixed, symbols


def ram_image(stock, tg, lfo, chord, bank, compiled):
    raw = bytearray(build.apply_writes(stock, [tg, lfo, chord])[0])
    for t in (tg, bank):
        for part in t['append']['parts']:
            at, body = int(part['dest'], 16) - build.BASE, bytes.fromhex(part['hex'])
            if at + len(body) > len(raw):
                raw.extend(bytes(at + len(body) - len(raw)))
            raw[at:at + len(body)] = body
    for at, code in compiled:
        raw[at - build.BASE:at - build.BASE + len(code)] = code
    return bytes(raw)


def setup_engine(image, lf, ck):
    e = tg_audio.engine(image)
    config = NativeAudioConfig.__new__(NativeAudioConfig)
    config.engine = e
    config.write(0x40FE4228, config.ROOT)
    config.write(0x40A7887C, config.ACTIVE)
    config.select(0)
    config.configure([config_word(root=24, extensions=(1,) * 7)] * 6)
    e.uc.mem_write(CONTEXT, bytes(1240))
    e.uc.mem_write(lf['lf2_context'], struct.pack('>I', CONTEXT))
    for track in range(6):
        e.machine_defaults(track, 'CHORD')
        e.set(track, note=24, pitch=64, finetune=64, color=32, shape=3)
    e._write_params()
    for track in range(6):
        row = E.PARAMS + 14 + track * 66
        e.uc.mem_write(row + 16, struct.pack('>H', 0x4000))
        # Sampler metadata deliberately survives in the CHORD base sound.
        e.uc.mem_write(row + 52, struct.pack('>I', SAMPLE_STATE))
        e.uc.mem_write(row + 56, struct.pack('>5H', 22000, 9 << 8, 0, 18 << 8, DEPTH))
    e.uc.mem_write(SOUND, bytes(100))
    e.uc.mem_write(SOUND + 20, bytes(e.uc.mem_read(E.PARAMS + 14, 66)))
    e.uc.mem_write(SOUND + 94, struct.pack('>H', 127))
    for index in range(238):
        value = int.from_bytes(e.uc.mem_read(E.PARAMS + 2 * index, 2), 'big', signed=True)
        e.call(SET_PARAM, index, value, E.PARAMS)
    return e


def apply(e, track, slot, value):
    e.uc.mem_write(RAW, b'\xFF' * 68)
    e.uc.mem_write(RAW + 2 * slot, struct.pack('>H', value))
    e.call(EXTRACT, EVENT, RAW, 0, 0)
    e.call(APPLY, track, EVENT, E.PARAMS)
    e.emac.macsr = 0xA0
    return e.call(SMOOTH, E.PARAMS)


def word(e, address, size=2):
    return int.from_bytes(e.uc.mem_read(address, size), 'big')


def dispatch(e, lf, frame):
    e.emac.macsr = 0x20
    e.call(lf['lf2_dispatch'], frame, 14400, 0)


def collision_and_isolation(old, fixed, lf, ck):
    broken = setup_engine(old, lf, ck)
    frame = apply(broken, 0, 32, 6)
    dispatch(broken, lf, frame)
    assert word(broken, CONTEXT + 192 + 14) == 6
    assert word(broken, SOUND + 84) == DEPTH
    assert broken.call(ck['ck_audio_locked_controls'], 0, 6) == 0x601
    print('ok : régression PR87 conservée ; HARMONY32 remplaçait DEP par6 malgré son+84=0x6000', flush=True)

    e = setup_engine(fixed, lf, ck)
    base_sound = bytes(e.uc.mem_read(SOUND, 100))
    phases, deltas, checked = set(), set(), 0
    for track in range(6):
        for modifier in range(7):
            frame = apply(e, track, 26, modifier)
            assert word(e, frame + 14 + track * 66 + 52) == modifier
            dispatch(e, lf, frame)
            for lane in range(6):
                assert word(e, CONTEXT + 192 + lane * 16 + 14) == DEPTH
                assert word(e, frame + 14 + lane * 66 + 64) == DEPTH
            assert e.call(ck['ck_audio_locked_controls'], track, modifier) == (modifier << 8) | 1
            assert bytes(e.uc.mem_read(SOUND, 100)) == base_sound
            phases.add(bytes(e.uc.mem_read(CONTEXT, 192)))
            deltas.add(word(e, CONTEXT + track * 32 + 20, 4))
            checked += 1
        e.call(RESET, track, E.PARAMS, SOUND)
        e.emac.macsr = 0xA0
        frame = e.call(SMOOTH, E.PARAMS)
        dispatch(e, lf, frame)
        assert word(e, frame + 14 + track * 66 + 52, 4) == SAMPLE_STATE
        assert e.call(ck['ck_audio_locked_controls'], track, SAMPLE_STATE >> 16) == 1
        assert word(e, CONTEXT + 192 + track * 16 + 14) == DEPTH
    assert len(phases) > 10 and deltas - {0} and not e.unmapped and not broken.unmapped
    print(f'ok : {checked} locks HARMONY26, six LFO2 actifs, sept gestes, reset natif ; DEP et état Sampler du son intacts', flush=True)


def codec(stock, image, lf, ck):
    # Les codecs natifs gardent les deux mots de métadonnées TG dans +84..87
    # et les cinq réglages LFO2 dans +88..91 de l'enregistrement du son.
    e = setup_engine(image, lf, ck)
    saved, loaded = 0x420C5000, 0x420C6000
    source = bytes(e.uc.mem_read(SOUND, 100))
    e.call(0x4005AFA0, saved, SOUND)
    assert word(e, saved + 84, 4) == SAMPLE_STATE
    e.call(0x4005AECC, loaded, saved)
    assert word(e, loaded + 72, 4) == SAMPLE_STATE
    assert word(e, loaded + 84) == DEPTH
    expected = list(struct.unpack('>5H', source[76:86]))
    expected[0] &= 0xFF80
    expected[4] &= 0xFF80
    assert struct.unpack('>5H', e.uc.mem_read(loaded + 76, 10)) == tuple(expected)
    print('ok : vrais codecs du son TG+LFO2 ; Sampler26/27 et cinq réglages LFO2 sauvés/relus indépendamment', flush=True)

    r = PlockRig(stock, image, ck)
    for track in range(6):
        r.call('write_lock', r.track(track), track, track + 1)
        assert r.get(track, track, 26) == track + 1
        r.call('ck_ui_config_set', track, config_word(root=24, extensions=(1,) * 7))
        r.uc.mem_write(UI + 357, b'\x01')
        r.word(UI + 352, 1 << track)
        assert r.call('ck_plock_grid', track, track + 1) == 1
        assert r.get(track, track, 26) == 0
        assert r.call('ck_plock_grid', track, track + 1) == 1
        assert r.get(track, track, 26) == track + 1
    r.call(0x4005BA0A, SERIAL, B1, 0)
    for track in range(6):
        assert r.bytes(SERIAL + 4336 + 130 * track, 2) == bytes([33, track])
    r.call(0x4005B894, B2, SERIAL, 0)
    r.bind(B2, initialize=False)
    for track in range(6):
        assert r.get(track, track, 26) == track + 1
        assert r.get(track, track, 32) == -1
        assert r.call('ck_plock_decode_hook', track, 33) == 26
    r.set(2, 9, 26, 4)
    r.call(0x4005BA90, SERIAL + 4336, B2 + 4332, 0, 26, 2)
    r.call(0x4005B894, B1, SERIAL, 0)
    r.bind(B1, initialize=False)
    assert r.get(2, 9, 26) == 4
    print('ok : save/load natifs des six rangées ; identifiant disque33 relu en RAM26, aucun lock32 créé', flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles', required=True)
    p.add_argument('--chord', required=True)
    p.add_argument('--bank', required=True)
    p.add_argument('--lfo', required=True)
    p.add_argument('--tg', action='append', required=True)
    a = p.parse_args()
    stock, chord, bank, lfo = main_os_from_syx(a.cycles), read(a.chord), read(a.bank), read(a.lfo)
    broken, fixed, ck = versions(chord, bank)
    lf = {k: int(v, 16) for k, v in lfo['symbols'].items()}
    for path in a.tg:
        tg = read(path)
        old = ram_image(stock, tg, lfo, chord, bank, broken)
        image = ram_image(stock, tg, lfo, chord, bank, fixed)
        print('Variante ' + tg['id'], flush=True)
        collision_and_isolation(old, image, lf, ck)
        codec(stock, image, lf, ck)
    print('ok : HARMONY26 + LFO2 isolés ; routines réelles, aucun résultat matériel revendiqué', flush=True)


if __name__ == '__main__':
    main()
