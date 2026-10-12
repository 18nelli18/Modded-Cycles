#!/usr/bin/env python3
"""Note 57 : vérifier l'identité de projet dans les conversions natives.

Exécute le getter Project, le save limité au champ identité, et le préfixe
load jusqu'à la restauration de l'en-tête. Pas de disque ni sauvegarde
complète : cette preuve ne raccorde aucun fichier annexe au firmware.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_seq_gen_menu import Rig, OBJ, RAW, STACK, STOP, SIGNAL
from test_sdvintage import main_os_from_syx


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    r = Rig(main_os_from_syx(args.cycles), {'writes': []},
            {'writes': [], 'symbols': {}})
    saved, restored, callback = 0x41400000, 0x93010000, 0x93020000
    r.u.mem_write(callback, bytes(16))
    for identity in (1, 0x12345678, 0xffffffff, 0):
        r.w32(RAW+8, identity)
        assert r.call(0x4000eae2, OBJ) == identity
        r.u.mem_write(saved, bytes(32))
        assert r.call(0x4005d18a, saved, RAW, 0, 0x20, callback)&255 == 1
        assert r.r32(saved+24) == identity
        # Les contrôles de version et les copies de l'en-tête sont natifs.
        r.w32(saved, 0xbeefbace)
        r.w32(saved+4, 6)
        r.w32(saved+0x210400, 0xbacef00c)
        r.u.mem_write(restored, bytes([165])*28)
        r.u.reg_write(mk.UC_M68K_REG_A7, STACK)
        r.u.mem_write(STACK, struct.pack('>4I', STOP, restored, saved, callback))
        r.u.emu_start(0x4005d3dc, 0x4005d468, count=10000)
        assert r.u.reg_read(mk.UC_M68K_REG_PC) == 0x4005d468
        assert r.r32(restored+8) == identity
    # Tester le renouvellement et le garde zéro avec notifications observées.
    identities = iter((0x10203040, 0x50607080))
    generated, notifications = [], []
    def identity(a):
        value = next(identities)
        generated.append(value)
        return value
    def notify(a):
        notifications.append(r.r32(a[1]+4))
        return 0
    r.stubs[0x4009575a] = identity
    r.u.hook_add(UC_HOOK_CODE, r.stub, begin=0x4009575a, end=0x4009575a)
    r.stubs[SIGNAL] = notify
    r.w32(RAW+8, 0)
    r.call(0x4000eb72, OBJ)
    assert r.r32(RAW+8) == 0x10203040
    r.call(0x4000eb72, OBJ)
    assert len(generated) == 1 and notifications == [0x20]
    r.call(0x4000eb12, OBJ)
    assert r.r32(RAW+8) == 0x50607080
    assert notifications == [0x20, 0x20]
    print('ok : getter natif Project +8 -> save v6 +24 -> préfixe load +8, quatre identités')
    print('ok : identité nulle générée une fois ; renouvellement explicite et notification 0x20')
    print('Limite : en-tête seulement ; stabilité Save As/copie, fichiers et disque non prouvés')


if __name__ == '__main__':
    main()
