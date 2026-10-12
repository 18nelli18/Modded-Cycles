#!/usr/bin/env python3
"""Note 57 : PAGE borné par longueur et FUNC+PAGE édition directe, prototype.

Callbacks ColdFire exécutés ; rendu Scale Setup couvert séparément.
"""
import argparse
from test_midi_lane_page import make,key,knob,PAT,raw
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    args=ap.parse_args();r=make(main_os_from_syx(args.cycles))
    assert r.call('mlp_open')==1
    for lane in range(6):
        r.w32(r.s['mlp_track'],lane)
        for length in (1,16,17,32,33,48,49,64):
            assert r.call('ml_config',PAT,lane,4,length)==1
            r.w32(r.s['mlp_step'],0)
            pages=(length+15)//16
            for i in range(pages*2):
                key(r,15)
                assert r.r32(r.s['mlp_step'])==((i+1)%pages)*16, (lane,length,i,r.r32(r.s['mlp_step']),raw(r,3),r.r32(r.s['mlp_func']))
                key(r,15,0);key(r,15,9)
                assert r.r32(r.s['mlp_step'])==((i+1)%pages)*16, (lane,length,i,r.r32(r.s['mlp_step']),raw(r,3),r.r32(r.s['mlp_func']))
        key(r,1);key(r,15,3);key(r,1,0)
        assert r.r32(r.s['mlp_setup'])==2 and r.r32(r.s['mlp_row'])==3
        assert r.r32(r.s['mlp_edit'])==1
        knob(r,-1);assert raw(r,3)==63
        # Réduction depuis la page 4 : sélection bornée, pas masqués conservés.
        r.w32(r.s['mlp_step'],63)
        before=bytes(r.u.mem_read(PAT+264*lane+8,256))
        for _ in range(47):knob(r,-1)
        assert raw(r,3)==16 and r.r32(r.s['mlp_step'])==15
        assert bytes(r.u.mem_read(PAT+264*lane+8,256))==before
        # Les onze réglages déplacés sont accessibles dans cette même vue.
        key(r,32,16)
        assert r.r32(r.s['mlp_edit'])==0
        for _ in range(20):knob(r,-1)
        assert r.r32(r.s['mlp_row'])==0
        for row in range(1,11):
            knob(r,1);assert r.r32(r.s['mlp_row'])==row
        for code in (1,3,8,9,13):
            assert key(r,code)==0 and key(r,code,0)==0
        key(r,12);assert r.r32(r.s['mlp_setup'])==0
        # Slide : même trig, état conservé après relâchement, bascule inverse.
        r.w32(r.s['mlp_step'],0)
        r.w32(0x93082000,1)
        key(r,16);key(r,16,0)
        assert r.u.mem_read(PAT+264*lane+11,1)==b'\x03'
        key(r,16);key(r,16,0)
        assert r.u.mem_read(PAT+264*lane+11,1)==b'\x01'
        r.w32(0x93082000,0)
    print('ok : six voies, huit longueurs, pages/rebouclage, répétitions, FUNC+PAGE puis DATA')
    print('ok : réduction de longueur borne la sélection sans effacer les pas masqués')


if __name__=='__main__':main()
