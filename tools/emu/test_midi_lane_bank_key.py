#!/usr/bin/env python3
"""Note 57 : bascule FUNC + SETTINGS + TRACK, contexte indépendant.

Exécute adaptateur ColdFire, constructeur OS et getter natif. Fermeture,
allocation, affichage et sortie physique simulés. Aucun hook installé ici.
"""
import argparse
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_midi_lane_page import make
from test_seq_gen_menu import EVENT, RAW
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
    r=make(main_os_from_syx(args.cycles));saved=bytes(r.u.mem_read(RAW,722))
    r.w32(0x93082000,1)
    stamp=0
    def key(code,flags=1,repeat=3):
        nonlocal stamp
        stamp+=1
        r.event(code,flags,stamp)
        results=[r.call('ml_key',EVENT) for _ in range(repeat)]
        assert len(set(results))==1,results
        return results[0]
    for code in range(33):
        if code!=2:assert key(code,3)==code
    for flags in (0,1,2,9,11):assert key(2,flags)==2
    r.w32(0x93082000,0)
    assert key(2,3)==2 and not r.r32(r.s['mlp_obj'])
    r.w32(0x93082000,1)
    assert key(2,3)==0
    obj=r.r32(r.s['mlp_obj']);context=r.r32(r.s['ml_context'])
    assert obj and context and r.r32(0x93082004)==1
    assert r.r32(r.s['ml_key_taken'])==1
    assert key(2,11)==0 and r.r32(r.s['mlp_obj'])==obj
    assert key(2,2)==0 and not r.r32(r.s['ml_key_taken'])
    # SETTINGS+FUNC ne ferme pas la vue avant le troisième bouton.
    r.event(13,3,stamp+1)
    assert r.call('mlp_menu_key',obj,EVENT)==0 and r.r32(r.s['mlp_obj'])==obj
    close=r.r32(r.r32(obj)+0x28);closed=[]
    # Le stub doit garder sa pile : le destructeur s'exécute séparément ensuite.
    r.stubs[close]=lambda a:closed.append(a[0]) or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=close,end=close)
    private=bytes(r.u.mem_read(context,1956))
    # FUNC B consommé : le getter reçoit TRACK sans bit FUNC natif.
    r.w32(r.s['mlp_func'],1)
    assert key(2,1)==0 and closed==[obj]
    r.call('mlp_dtor1',obj)
    assert not r.r32(r.s['mlp_obj'])
    assert bytes(r.u.mem_read(context,1956))==private
    assert key(2,0)==0
    assert key(2,3)==0 and r.r32(r.s['mlp_obj'])
    assert r.r32(r.s['ml_context'])==context
    assert bytes(r.u.mem_read(context,1956))==private
    assert bytes(r.u.mem_read(RAW,722))==saved and r.r32(0x93005304)==5
    print('ok : ouverture/fermeture/réouverture, lectures répétées et relâchements ; contexte conservé, six pistes audio intactes')
    # Horloge en arrière-plan après fermeture, sortie UI seule.
    r.call('mlp_dtor1',r.r32(r.s['mlp_obj']))
    assert not r.r32(r.s['mlp_obj'])
    r.w32(0x40fe4228,1);packets=[]
    r.stubs[0x400826b0]=lambda a:packets.append((bytes(r.u.mem_read(a[1],a[0])),a[2])) or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
    for lane in range(6):assert r.call('ml_edit',context,lane,0,3,1)==1
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2505)
    r.call('ml_audio_tick',0,1)
    assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2505 and not packets
    assert r.r32(context+1584)==6
    r.call('ml_ui_drain');assert not packets
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2005)
    r.call('ml_ui_drain')
    assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2005
    assert packets==[(bytes([0x96+i,60,100]),4) for i in range(6)],packets
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2505);r.call('ml_audio_tick',1,0)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2005);r.call('ml_ui_drain')
    assert packets[6:]==[(bytes([0x86+i,60,0]),4) for i in range(6)]
    print('ok : contexte publié -> horloge IPL5 -> file six canaux 7..12 -> drain UI ; Stop libère six notes, SR conservé')
    print('NOTE : gardes et callbacks prouvés ; branchement global de touches/audio/UI et sauvegarde persistante restent à faire')

if __name__=='__main__':main()
