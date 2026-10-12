#!/usr/bin/env python3
"""Régression FUNC B : consommer la touche avant le menu mute audio.

Callback ColdFire réel ; propagation de vue modélisée par sa valeur de retour.
Le dispatch global complet et le comportement physique restent à tester.
"""
import argparse
from test_midi_lane_page import make,key,PAT,RUNTIME
from test_seq_gen_menu import EVENT,RAW
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    a=ap.parse_args();r=make(main_os_from_syx(a.cycles));assert r.call('mlp_open')==1
    obj=r.r32(r.s['mlp_obj']);audio=bytes(r.u.mem_read(RAW,722))
    # Le release du FUNC tenu avant l'ouverture atteint une fois le handler A.
    assert key(r,1,0)==0
    assert key(r,1,0)==1
    live=r.s['ml_live_runtime']
    for lane in range(6):
        packet=((0x96+lane)<<24)|(60<<16)|(100<<8)|4
        assert r.call('ml_step',RUNTIME,lane,packet,8)==1
        assert r.call('ml_step',live,lane,packet,64)==1
        assert r.call('ml_take',RUNTIME)==packet and r.call('ml_take',live)==packet
        assert key(r,1,1)==1 # Ne pas présenter QuickMuteMenu audio.
        for flags in (1,1,0):
            r.w32(EVENT+16,flags);r.w32(EVENT+20,lane+1)
            assert r.call('mlp_pad',obj+16,EVENT)==1
        assert r.u.mem_read(PAT+264*lane,1)==b'\0'
        off=((0x86+lane)<<24)|(60<<16)|4
        assert r.call('ml_take',RUNTIME)==off and r.call('ml_take',live)==off
        assert key(r,1,0)==1
        assert bytes(r.u.mem_read(RAW,722))==audio
    print('ok : FUNC appui/release B consommés, seul release hérité transmis une fois ; six sorties MIDI coupées sans données audio modifiées')
    print('ok : note-off séquence et clavier, press répété idempotent ; dispatch supérieur/physique à vérifier')


if __name__=='__main__':main()
