#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEMPO B : touches réelles, pile native de vues, retour B et garde du combo."""
import argparse,json,pathlib,struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig,EVENT
from test_sdvintage import main_os_from_syx
import build

class NativeRig(Rig):
    def stub(self,u,addr,size,data):
        if addr==0x4007700e:return  # exécuter le vrai ViewManager::present
        return super().stub(u,addr,size,data)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--base',required=True);p.add_argument('--tweak',required=True);a=p.parse_args()
    stock=main_os_from_syx(a.cycles);base=json.loads(pathlib.Path(a.base).read_text());t=json.loads(pathlib.Path(a.tweak).read_text())
    s={k:int(v,16) for k,v in t['symbols'].items()};r=NativeRig(stock,{'writes':[]},{'writes':[],'symbols':{}});r.s=s
    for part in t['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
    for wr in t['writes']:r.u.mem_write(build.BASE+wr['off'],bytes.fromhex(wr['new']))
    def stub(addr,fn):
        fresh=addr not in r.stubs;r.stubs[addr]=fn
        if fresh:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    # Le bug d’origine avale TEMPO14 ; désormais appui/release passent au stock.
    stub(s['ml_bank_ui_sync'],lambda a:1);stub(s['mlp_clip_key'],lambda a:0)
    cancelled=[];stub(s['mlp_keyboard_cancel'],lambda a:cancelled.append(1) or 0);stub(s['ml_worker_kick'],lambda a:0)
    r.w32(s['ml_store_load_ready'],1)
    assert r.call('mlp_menu_key',0x93070000,r.event(14,1))==0
    assert r.call('mlp_menu_key',0x93070000,r.event(14,0))==0 and len(cancelled)==1
    for key in (3,9,13):assert r.call('mlp_menu_key',0x93070000,r.event(key,0))==0
    # Contraste sur les octets propres publiés avant la correction.
    dest=int(base['append']['parts'][0]['dest'],16);old=bytes.fromhex(base['append']['parts'][0]['hex'])
    at=s['ml_tempo_dispatch'];r.u.mem_write(at,old[at-dest:at-dest+20]);r.u.ctl_remove_cache(at,at+20)
    assert r.call('mlp_menu_key',0x93070000,r.event(14,1))&255!=0
    part=t['append']['parts'][0];raw=bytes.fromhex(part['hex']);r.u.mem_write(at,raw[at-dest:at-dest+20]);r.u.ctl_remove_cache(at,at+20)
    # Manager natif : liste double réelle, groupes réels ; seules les frontières
    # mutex/refcount/focus et callbacks des vues sont simulées.
    ctx,bank,bankvt,bnode,tempo,ref,groups=0x93071000,0x93072000,0x93073000,0x93074000,0x93075000,0x93076000,0x93077000
    manager=ctx+64;sentinel=manager+20
    r.w32(0x40fe4178,ctx);r.w32(s['mlp_obj'],bank);r.w32(bank,bankvt)
    r.w32(sentinel,bnode);r.w32(sentinel+4,bnode);r.w32(bnode,sentinel);r.w32(bnode+4,sentinel);r.w32(bnode+8,bank)
    r.w32(ref,tempo);r.w32(ref+4,0);r.w32(tempo,0x40107d50);r.w32(tempo+28,groups);r.w32(tempo+32,groups+4);r.w32(groups,2);r.w32(tempo+44,0)
    for addr in (0x400e8684,0x400d08ce,0x40076f2a):stub(addr,lambda a:0)
    stub(0x400cfae0,lambda a:r.w32(a[0],r.r32(a[1])) or 0)
    displayed=[];stub(r.r32(0x40107d50+24),lambda a:displayed.append(a[0]) or 0)
    closed=[]
    def close_tempo(args):
        assert args[0]==tempo
        node=r.r32(sentinel+4);assert r.r32(node+8)==tempo
        before=r.r32(node+4);r.w32(before,sentinel);r.w32(sentinel+4,before);closed.append(tempo);return 1
    stub(r.r32(0x40107d50+40),close_tempo)
    for _ in range(4):
        assert r.call('ml_tempo_toggle',manager,ref,1)&255==1
        top=r.r32(sentinel+4);assert r.r32(top+8)==tempo and r.r32(bnode+8)==bank
        assert r.r32(tempo+32)==groups+4 and r.r32(s['mlp_obj'])==bank
        # Le combo n’efface pas B derrière TEMPO ni derrière un autre menu.
        assert r.call('ml_toggle') is not None and r.r32(s['mlp_obj'])==bank
        # Nouvelle instance créée par le stock à chaque appui TEMPO : fermeture
        # par type de menu, pas seulement par égalité de pointeur.
        r.w32(ref,tempo+0x400);r.w32(tempo+0x400,0x40107d50)
        r.call('ml_tempo_toggle',manager,ref,1);assert r.r32(sentinel+4)==bnode
        assert r.r32(s['mlp_obj'])==bank;r.w32(ref,tempo)
    assert len(displayed)==4 and len(closed)==4
    r.call('ml_tempo_toggle',manager,ref,1)
    # Handler TEMPO natif réel : BACK appelle le slot Close, sans toucher B.
    stub(0x4007240c,lambda a:r.r32(a[0]+12))
    assert r.call(0x4003d99e,tempo,r.event(12,16))&255==1
    assert r.r32(s['mlp_obj'])==bank and r.r32(sentinel+4)==bnode
    exit_calls=[];exit_pc=0x93078000;r.w32(bankvt+40,exit_pc)
    for key in ('mlp_setup','SG_obj','mlccp_obj'):r.w32(s[key],0)
    stub(exit_pc,lambda a:exit_calls.append(a[0]) or r.w32(s['mlp_obj'],0) or 0)
    r.call('ml_toggle');assert exit_calls==[bank] and r.r32(s['mlp_obj'])==0
    # A sans B : contrat et arguments du toggle stock inchangés.
    calls=[];stub(0x40077da8,lambda a:calls.append(a[:3]) or 23)
    assert r.call('ml_tempo_toggle',manager,ref,1)==23 and calls==[(manager,ref,1)]
    # Le menu, options et moteur tempo stock ne reçoivent aucune écriture.
    assert not any(0x4003d000<=build.BASE+x['off']<0x4003df00 for x in t['writes'])
    for key in ('ml_store_service','ml_store_bootstrap','ml_store_save_notice'):assert bytes(r.u.mem_read(s[key],2))==b'\x4e\x75'
    assert all(build.BASE+x['off'] not in (0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6) for x in t['writes'])
    print('ok : avant TEMPO14 consommé / après transmis ; REC, SETTINGS et PATTERN conservés')
    print('ok : empilement ViewManager natif, groupes restaurés, TEMPO referme par type, BACK revient B, combo bloqué sous menu puis autorisé à l’accueil')
    print('ok : A inchangé, aucun hook MIDI Save/Load ; écran/options/moteur TEMPO natifs intacts')
    print('Limite : callbacks de vues/mutex/focus simulés ; test matériel du menu TEMPO requis')
if __name__=='__main__':main()
