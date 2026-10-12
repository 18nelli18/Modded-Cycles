#!/usr/bin/env python3
"""Note 57 : REC stock et clavier MIDI privé, aucun writer ni donnée sonore.

Getter REC natif exécuté ; octave/environnement et sortie physique simulés.
Teste releases après changement REC/voie, dernière touche, fermeture et worker.
"""
import argparse
from unicorn import UC_HOOK_CODE
from test_midi_lane_page import make,key,PAT,RUNTIME
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    a=ap.parse_args();r=make(main_os_from_syx(a.cycles));assert r.call('mlp_open')==1
    state=0x930a0000
    for addr,fn in ((0x400cf9a8,lambda a:state),(0x4000f208,lambda a:0x930a1000),
                    (0x4000cfcc,lambda a:0x930a2000),(0x40016da6,lambda a:8)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    live=r.s['ml_live_runtime'];sound=bytes(r.u.mem_read(0x93002000,722))
    def take():return r.call('ml_take',live)
    for lane in range(6):r.u.mem_write(PAT+264*lane+6,b'\x08')
    before=bytes(r.u.mem_read(PAT,1584));runtime=bytes(r.u.mem_read(RUNTIME,320))
    for lane in range(6):
        r.w32(r.s['mlp_track'],lane)
        for i in range(16):
            key(r,16+i)
            assert take()==((0x96+lane)<<24)|((60+i)<<16)|(100<<8)|4
            key(r,16+i,9);assert take()==0
            key(r,16+i,0)
            assert take()==((0x86+lane)<<24)|((60+i)<<16)|4
            assert take()==0
    assert bytes(r.u.mem_read(PAT,1584))==before
    assert bytes(r.u.mem_read(RUNTIME,320))==runtime
    # Deux touches : release de l'ancienne ne coupe pas la suivante.
    r.w32(r.s['mlp_track'],0)
    key(r,16);assert take()==0x963c6404
    key(r,20);assert [take(),take()]==[0x863c0004,0x96406404]
    key(r,16,0);assert take()==0
    r.w32(r.s['mlp_track'],5)
    r.u.mem_write(state+357,b'\x01\x01')
    key(r,20,0);assert take()==0x86400004
    # REC activé : chemin d'édition ; REC éteint : aucune écriture musicale.
    key(r,16);key(r,16,0)
    assert take()==0 and not r.r32(r.s['mlp_live_held'])
    r.u.mem_write(state+357,b'\x00\x00')
    # Tap avant consommation : aucun Note On retardé après le relâchement.
    key(r,16);key(r,16,0)
    assert [take(),take(),take()]==[0x8b3c0004,0x8b3c0004,0]
    key(r,17);assert take()==0x9b3d6404
    r.call('mlp_keyboard_cancel');assert take()==0x8b3d0004
    assert not r.r32(r.s['mlp_live_held'])
    # Les pages natives peuvent absorber la release : annuler avant transfert.
    for button in (3,8,9):
        key(r,17);assert take()==0x9b3d6404
        assert key(r,button)==0
        assert take()==0x8b3d0004 and take()==0
        assert not r.r32(r.s['mlp_live_held'])
        key(r,17,0)
    assert bytes(r.u.mem_read(0x93002000,722))==sound
    # Le worker doit aussi se réveiller quand seule la file clavier est pleine.
    worker=0x930a3000;posts=[];sent=[]
    r.w32(0x40fe4228,1)
    r.stubs[0x40001bb0]=lambda a:posts.append(a[0]) or 0
    r.stubs[0x400826b0]=lambda a:sent.append(bytes(r.u.mem_read(a[1],a[0]))) or 0
    for addr in (0x40001bb0,0x400826b0):r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.call('ml_worker_init',worker,RUNTIME)
    key(r,18);r.call('ml_worker_notify',worker)
    assert posts==[worker]
    assert r.call('ml_worker_once',worker)==1 and sent==[b'\x9b\x3e\x64']
    key(r,18,0);r.call('ml_worker_once',worker)
    assert sent[-1]==b'\x8b\x3e\x00'
    # Pad et clavier : seule la dernière source possède le Note Off de la voie.
    key(r,18);assert take()==0x9b3e6404
    r.call('mlp_pad_note',5,1);assert [take(),take()]==[0x8b3e0004,0x9b486404]
    key(r,18,0);assert take()==0
    r.call('mlp_pad_note',5,0);assert take()==0x8b480004
    r.call('mlp_pad_note',5,1);assert take()==0x9b486404
    key(r,18);assert [take(),take()]==[0x8b480004,0x9b3e6404]
    r.call('mlp_pad_note',5,0);assert take()==0
    key(r,18,0);assert take()==0x8b3e0004
    # Track Setup reste clavier, même REC actif, canal assigné et KbT privés.
    r.w32(r.s['mlp_setup'],3)
    r.u.mem_write(state+357,b'\x01\x01')
    r.u.mem_write(PAT+264*5+2,bytes([12]))
    before_menu=bytes(r.u.mem_read(PAT,1584))
    key(r,19);assert take()==0x9c3f6404
    key(r,19,0);assert take()==0x8c3f0004 and take()==0
    for channel in range(16):
        r.u.mem_write(PAT+264*5+2,bytes([channel]))
        key(r,19);assert take()==((0x90|channel)<<24)|0x3f6404
        key(r,19,0);assert take()==((0x80|channel)<<24)|0x3f0004
        assert take()==0
    r.u.mem_write(PAT+264*5+2,bytes([12]))
    assert bytes(r.u.mem_read(PAT,1584))==before_menu
    assert r.r32(r.s['mlp_setup'])==3
    key(r,12);assert r.r32(r.s['mlp_setup'])==0
    print('ok : clavier actif derrière Track Setup avec REC actif, canal assigné13, aucun trig écrit')
    print('ok : 6 voies × 16 touches, REC natif, notes chromatiques, releases/taps/sortie, aucune écriture audio ou pattern hors REC')
    print('ok : file clavier indépendante, worker réveille/consomme sans file séquence, Note Off conservés')
    print('Limites : octave/environnement simulés ; gamme musicale et chemin global REC à raccorder/valider')


if __name__=='__main__':main()
