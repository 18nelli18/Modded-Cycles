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
            assert ('M%d', lane+1) in r.texts, r.texts
            assert ('CH %d',lane+7) in r.texts,r.texts
            assert not any(fmt=='Vel %d' for fmt,value in r.texts),r.texts
            assert ('%s', r.s['mlp_stock_b']) in r.texts
            assert r.r32(r.s['mlp_stock_drawing']) == 0
            assert before == bytes(r.u.mem_read(pattern, 1584))
    print('ok : dessin natif repos/trig tenu, M1..M6, badge B, données MIDI intactes')
    # Vérifier le sélecteur reçu par le vrai dessinateur natif.
    from unicorn.m68k_const import UC_M68K_REG_A2
    selectors = []
    def capture_field(uc, address, size, data):
        selectors.append(r.r32(uc.reg_read(UC_M68K_REG_A2)+104))
    hook = r.u.hook_add(UC_HOOK_CODE, capture_field, begin=0x40029a04, end=0x40029a04)
    r.w32(r.s['mlp_held'],1)
    for row, expected in ((7,0),(8,1),(9,2),(0,0)):
        r.w32(r.s['mlp_row'],row)
        r.call('mlp_render',0,bitmap)
        assert selectors[-1] == expected, (row,selectors)
    r.u.hook_del(hook)
    print('ok : sélection Note/Vel/Len transmise au dessin stock, repli sûr')

    for lane in range(6):
        r.w32(r.s['mlp_track'],lane)
        for channel in range(16):
            assert r.call('ml_config',pattern,lane,2,channel)==1
            before=bytes(r.u.mem_read(pattern,1584))
            r.texts.clear();r.call('mlp_render',0,bitmap)
            assert ('CH %d',channel+1) in r.texts,r.texts
            assert before==bytes(r.u.mem_read(pattern,1584))
        assert r.call('ml_config',pattern,lane,2,lane+6)==1
    print('ok : canal affiché1..16 sur six voies, suit le réglage sans modifier les notes')
    for velocity in (1,64,127):
        r.u.mem_write(pattern+264*5+9,bytes([velocity]))
        r.texts.clear();before=bytes(r.u.mem_read(pattern,1584))
        r.call('mlp_render',0,bitmap)
        assert not any(fmt=='Vel %d' for fmt,value in r.texts)
        assert before==bytes(r.u.mem_read(pattern,1584))
    print('ok : vélocité1/64/127, aucun curseur dupliqué, données intactes')
    r.w32(r.s['mlp_held'],0)
    r.w32(r.s['mlp_setup'],2)
    for row in range(11):
        for edit in (0,1):
            r.w32(r.s['mlp_row'],row);r.w32(r.s['mlp_edit'],edit)
            r.texts.clear()
            before=bytes(r.u.mem_read(pattern,1584))
            r.call('mlp_render',0,bitmap)
            assert any(fmt=='Scale' for fmt,value in r.texts),r.texts
            assert any(fmt=='Setup' for fmt,value in r.texts),r.texts
            if row in (0,1):
                assert ('M%d',6) in r.texts,r.texts
                assert ('%d',12) in r.texts,r.texts
            if row in (2,3,4):
                assert any(fmt=='%d' and value==16 for fmt,value in r.texts),r.texts
            assert before==bytes(r.u.mem_read(pattern,1584))
    print('ok : Scale Setup stock, onze réglages, défilement, sélection/édition, aucune écriture musicale')


if __name__ == '__main__':
    main()
