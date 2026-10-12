#!/usr/bin/env python3
"""Note 57 : dessin natif des six voies B, labels MIDI et isolation des données.

MainScreenView, NoteVelocityView, polices et sprites exécutés dans Unicorn.
Seuls les getters d'environnement sont synthétiques ; aucun résultat matériel.
"""
import argparse
from render_midi_bank import DrawingRig, stock_fixture
from test_midi_lane_page import load
from test_sdvintage import main_os_from_syx


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
    r = DrawingRig(main_os_from_syx(args.cycles), {'writes': []},
                   {'writes': [], 'symbols': {}})
    from unicorn import UC_HOOK_CODE
    r.stubs[0x400802ec] = lambda a: 0
    r.u.hook_add(UC_HOOK_CODE, r.stub, begin=0x400802ec, end=0x400802ec)
    load(r, stock_display=True)
    stock_fixture(r)
    pattern, bitmap, framebuffer = 0x93070000, 0x93006000, 0x93090000
    assert r.call('ml_init', pattern) == 1
    r.w32(r.s['ml_pattern'], pattern)
    r.call(0x400e7dbc)
    r.call(0x40070172, bitmap, 128, 64, framebuffer, 0)
    for lane in range(6):
        r.w32(r.s['mlp_track'], lane)
        r.u.mem_write(pattern+264*lane+8, bytes([60+lane, 90+lane, 1, 1]))
        before = bytes(r.u.mem_read(pattern, 1584))
        for held in (0, 1):
            r.w32(r.s['mlp_held'], held)
            r.texts.clear()
            r.call('mlp_render', 0, bitmap)
            assert ('TR%d', lane+7) in r.texts, r.texts
            assert ('%s', r.s['mlp_stock_b']) in r.texts
            assert r.r32(r.s['mlp_stock_drawing']) == 0
            assert before == bytes(r.u.mem_read(pattern, 1584))
    print('ok : dessin natif repos/trig tenu, TR7..TR12, badge B, données MIDI intactes')


if __name__ == '__main__':
    main()
