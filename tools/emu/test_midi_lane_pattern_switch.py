#!/usr/bin/env python3
"""Note 57 : raccordement expérimental des banques au hook audio natif.

Code stock 40053330 (branche inactive), getter natif d'identité, callbacks
d'édition et runtime réels. Changements de pattern fournis par fixture ;
allocation et writer physiques simulés. Aucune preuve de stockage disque.
"""
import argparse
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig, EVENT
from test_sdvintage import main_os_from_syx
from test_midi_lane_page import load, key, knob


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    r = Rig(main_os_from_syx(args.cycles), {'writes': []},
            {'writes': [], 'symbols': {}})
    load(r, pattern_banks=True)
    u = r.u
    u.mem_map(0x80000000, 0x20000)
    assert r.call('ml_prepare') == 1
    ctx = r.r32(r.s['ml_context'])
    table = r.r32(r.s['ml_bank_table'])
    empty = r.r32(r.s['ml_bank_empty'])
    active, obj = 0x93010000, 0x93080000
    r.w32(0x40a7887c, active)
    r.w32(r.s['mlp_obj'], obj)
    r.w32(r.s['mlp_track'], 0)
    runtime = ctx+1584
    def select(index):
        r.w32(active+30706, index)
        assert r.call(0x40054828) == index
    def ui():
        u.reg_write(mk.UC_M68K_REG_SR, 0x2000)
        return r.call('ml_bank_ui_sync')
    def tick(now):
        u.reg_write(mk.UC_M68K_REG_SR, 0x2700)
        r.w32(0x8000184c, now)
        r.call('ml_audio_hook')
    def drain():
        packets = []
        while r.r32(runtime):
            packets.append(r.call('ml_take', runtime))
        return packets
    # Préparer deux patterns avec les vrais callbacks trig + DATA.
    select(0)
    assert ui() == 1
    key(r, 16)
    key(r, 16, 0)
    saved_a = bytes(u.mem_read(ctx, 1584))
    select(1)
    assert ui() == 1
    bank_b = r.r32(table+4)
    assert bank_b and bank_b != ctx
    key(r, 16)
    knob(r, 1)
    key(r, 16, 0)
    saved_b = bytes(u.mem_read(bank_b, 1584))
    assert saved_a != saved_b
    assert bytes(u.mem_read(ctx, 1584)) == saved_a
    # Vrai site d'appel audio stock + hook privé, première échéance armée.
    r.w32(0x40a74544, 0)
    r.w32(0x40a7883c, 1)
    for name, value in (('ml_start_due', 100), ('ml_start_context', ctx),
                        ('ml_start_serial', 1)):
        r.w32(r.s[name], value)
    select(0)
    assert ui() == 1
    allocations = r.new_count
    tick(100)
    ons_a = [p for p in drain() if p >> 28 == 9]
    assert len(ons_a) == 1
    # Un prochain pattern demandé ne change pas la banque avant l'identité active.
    r.w32(0x40a788f4, 1)
    tick(101)
    assert r.r32(r.s['ml_play_pattern']) == ctx
    select(1)
    tick(102)
    assert r.r32(r.s['ml_play_pattern']) == bank_b
    packets = drain()
    assert packets[0] >> 28 == 8 and packets[-1] >> 28 == 9
    assert (packets[-1] >> 16)&127 == ((ons_a[0] >> 16)&127)+1
    assert r.new_count == allocations, 'allocation dans le hook audio'
    # L'éditeur ne bascule qu'à son propre service, sans corruption de maintien.
    assert r.r32(r.s['ml_pattern']) == ctx
    r.w32(r.s['mlp_held'], 1)
    assert ui() == 1
    assert r.r32(r.s['ml_pattern']) == bank_b
    assert r.r32(r.s['mlp_held']) == 0
    select(0)
    tick(103)
    assert ui() == 1
    assert bytes(u.mem_read(ctx, 1584)) == saved_a
    assert bytes(u.mem_read(bank_b, 1584)) == saved_b
    print('ok : édition A/B réelle, hook audio stock, note-off avant nouvelle note, retour intact')
    print('ok : demande future sans basculement prématuré, édition/lecture séparées, aucune allocation IRQ')
    # Un pattern jamais visité reste silencieux, sans hériter des notes précédentes.
    select(95)
    tick(104)
    assert r.r32(r.s['ml_play_pattern']) == empty
    assert all(p >> 28 == 8 for p in drain())
    r.fail_new = r.new_count+1
    assert ui() == 0
    assert r.r32(table+95*4) == 0
    before = bytes(u.mem_read(bank_b, 1584))
    r.fail_new = r.new_count+1
    key(r, 17)
    assert bytes(u.mem_read(bank_b, 1584)) == before
    r.fail_new = 0
    assert ui() == 1
    bank_95 = r.r32(table+95*4)
    assert bank_95 and bank_95 not in (ctx, bank_b, empty)
    tick(105)
    assert r.r32(r.s['ml_play_pattern']) == bank_95
    assert not drain()
    print('ok : pattern vide sans notes héritées, allocation refusée sans modification, reprise après échec')


if __name__ == '__main__':
    main()
