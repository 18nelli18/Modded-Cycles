#!/usr/bin/env python3
"""Genie B : générateur/Euclide natifs, undo et frontière privée sans piste audio."""
import argparse
import pathlib
import json
import struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
import build
import gen_midi_bank_bundle as gen
from test_seq_gen_menu import Rig,RAW,EVENT
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--model-tg',required=True)
    ap.add_argument('--tweak');ap.add_argument('--syntakt',help='Tester les callbacks du bundle réellement placé')
    a=ap.parse_args();root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    stock=main_os_from_syx(a.cycles);catalog=build.load_catalog()['model-cycles_OS1.13'][1]
    chosen=sorted((catalog[x] for x in gen.IDS),key=lambda t:t['order'])
    patched,_=build.apply_writes(stock,chosen)
    tg=gen.symbols(cross,pathlib.Path(a.model_tg)/'build/_b.elf')
    placed=json.loads(pathlib.Path(a.tweak).read_text() if a.tweak else gen.OUT.read_text())
    s={k:int(v,16) for k,v in placed['symbols'].items()}
    blob=bytes.fromhex(placed['append']['parts'][0]['hex'])
    patched,_=build.apply_writes(stock,chosen+[placed])
    if a.syntakt and not a.tweak:
        placed,_,image=gen.generate(stock,a.syntakt,a.model_tg,cross,True,True)
        s={k:int(v,16) for k,v in placed['symbols'].items()}
        blob=bytes.fromhex(placed['append']['parts'][0]['hex']);patched=image
    r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}})
    r.u.mem_write(build.BASE,patched);r.u.mem_write(s['ML_BANK_START'],blob);r.s=s
    if a.tweak:
        a.syntakt=True
        for part in placed['append']['parts']:r.u.mem_write(int(part['dest'],16),bytes.fromhex(part['hex']))
    pattern,other,runtime=0x93070000,0x93072000,0x93074000
    r.call('ml_init',pattern);r.call('ml_init',other)
    r.w32(s['ml_pattern'],pattern);r.w32(s['ml_play_pattern'],pattern)
    r.w32(s['mlp_obj'],0x93075000);r.w32(s['ml_runtime'],runtime)
    r.u.mem_write(tg['scale_state'],b'\0\0')
    cfg=s['SG_config'];adv=s['SG_advanced'];opts=s['SG_options']
    for off,val in ((4,100),(8,48),(12,72),(24,123456)) :r.w32(cfg+off,val)
    for off,val in ((0,80),(4,110),(24,0),(28,100),(32,0),(36,4),(40,0)):r.w32(adv+off,val)
    for off in (0,4,8):r.w32(opts+off,0)
    audio=bytes(r.u.mem_read(RAW,722))
    if 'ml_gc_capture' in s:
        r.call('ml_repeat_prepare_ui');locks=r.r32(s['ml_repeat_edit_settings']);assert locks
        for lane in range(6):
            r.w32(s['mlp_track'],lane)
            for target,mutation,euclid in ((0,100,0),(1,100,0),(2,100,0),(0,25,0),(2,25,0),(0,100,1)):
                r.w32(adv+24,target);r.w32(adv+28,mutation);r.w32(adv+32,euclid)
                for i in range(64):r.u.mem_write(locks+lane*520+15+i*8,bytes((102+i,)))
                before_locks=bytes(r.u.mem_read(locks,3120));before_notes=bytes(r.u.mem_read(pattern,1584))
                r.call('ml_genie_generate');assert r.r32(s['SG_error'])==0
                expected=bytearray(before_locks)
                for i in range(64):expected[lane*520+15+i*8]=0
                assert bytes(r.u.mem_read(locks,3120))==expected,(lane,target,mutation,euclid)
                r.call('ml_genie_undo')
                assert bytes(r.u.mem_read(locks,3120))==before_locks
                assert bytes(r.u.mem_read(pattern,1584))==before_notes
            r.w32(0x40a7883c,1);r.call('ml_genie_generate')
            assert bytes(r.u.mem_read(locks,3120))==before_locks
            r.u.mem_write(locks+lane*520+15,b'\x65');edited=bytes(r.u.mem_read(locks,3120))
            # Appel audio avec les registres de la vraie frontière de voie.
            r.u.reg_write(mk.UC_M68K_REG_A0,pattern+lane*264)
            r.u.reg_write(mk.UC_M68K_REG_D0,lane);r.u.reg_write(mk.UC_M68K_REG_D1,0)
            r.call('ml_genie_boundary')
            assert r.r32(s['ml_gq_state'])==0
            assert bytes(r.u.mem_read(pattern,1584))==before_notes and bytes(r.u.mem_read(locks,3120))==edited
            # Nouvelle demande sans édition : commit puis Undo en lecture.
            r.call('ml_genie_generate')
            r.u.reg_write(mk.UC_M68K_REG_A0,pattern+lane*264)
            r.u.reg_write(mk.UC_M68K_REG_D0,lane);r.u.reg_write(mk.UC_M68K_REG_D1,0);r.call('ml_genie_boundary')
            assert all(r.u.mem_read(locks+lane*520+15+i*8,1)==b'\0' for i in range(64))
            r.call('ml_genie_undo')
            r.u.reg_write(mk.UC_M68K_REG_A0,pattern+lane*264)
            r.u.reg_write(mk.UC_M68K_REG_D0,lane);r.u.reg_write(mk.UC_M68K_REG_D1,0);r.call('ml_genie_boundary')
            assert bytes(r.u.mem_read(locks,3120))==edited and bytes(r.u.mem_read(pattern,1584))==before_notes
            r.w32(0x40a7883c,0)
        r.w32(adv+24,0);r.w32(adv+28,100);r.w32(adv+32,0)
        print('ok : tous les modes Genie effacent 64 chances, Undo les restaure ; édition chance annule le commit, six voies isolées')
    for lane in range(6):
        r.w32(s['mlp_track'],lane);before=bytes(r.u.mem_read(pattern,1584))
        r.call('ml_genie_generate');assert r.r32(s['SG_error'])==0
        got=bytes(r.u.mem_read(pattern,1584));lo=264*lane
        assert before[:lo]==got[:lo] and before[lo+264:]==got[lo+264:]
        assert all(got[lo+8+4*i+3]&1 and got[lo+8+4*i+1] for i in range(16))
        r.call('ml_genie_undo');assert bytes(r.u.mem_read(pattern,1584))==before
        # Pendant lecture : aucune modification avant le pas zéro ciblé.
        r.w32(0x40a7883c,1);r.call('ml_genie_generate')
        assert r.r32(s['ml_gq_state'])==1 and bytes(r.u.mem_read(pattern,1584))==before
        for bank,track,step in ((other,lane,0),(pattern,(lane+1)%6,0),(pattern,lane,1)):
            r.call('ml_pattern_tick',runtime,bank,track,step)
            assert r.r32(s['ml_gq_state'])==1
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        r.call('ml_pattern_tick',runtime,pattern,lane,0)
        assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2500
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        assert r.r32(s['ml_gq_state'])==0 and bytes(r.u.mem_read(pattern,1584))!=before
        r.call('ml_genie_undo');assert r.r32(s['ml_gq_state'])==1
        r.call('ml_pattern_tick',runtime,pattern,lane,0)
        assert bytes(r.u.mem_read(pattern,1584))==before
        # Une édition intervenue après Generate annule le candidat entier.
        r.call('ml_genie_generate');r.u.mem_write(pattern+lo+8,b'\x3f')
        edited=bytes(r.u.mem_read(pattern,1584))
        r.call('ml_pattern_tick',runtime,pattern,lane,0)
        assert r.r32(s['ml_gq_state'])==0 and bytes(r.u.mem_read(pattern,1584))==edited
        r.w32(0x40a7883c,0)
    assert bytes(r.u.mem_read(RAW,722))==audio
    # Euclide 4/16 et vélocités 80..110, sur la voie B seulement.
    r.w32(adv+32,1);r.w32(opts,1);r.call('ml_genie_generate')
    lane=bytes(r.u.mem_read(pattern+264*5,264))
    hits=[lane[8+i*4:12+i*4] for i in range(16) if lane[11+i*4]&1]
    assert len(hits)==4 and all(80<=x[1]<=110 for x in hits)
    # Le vrai menu appelle les adaptateurs, pas les setters de piste audio.
    sg=catalog['scale-gen-st-queued']['symbols']
    for native,ours in (('sg_action_generate','ml_genie_generate'),('sg_action_undo','ml_genie_undo')):
        needle=b'\x4e\xb9'+struct.pack('>I',s[ours] if a.syntakt else int(sg[native],16))
        menu=int(sg['sg_menu_key'],16)
        sites=[at for at in range(menu,menu+0x400,2) if bytes(r.u.mem_read(at,6))==needle]
        assert len(sites)==1
        r.u.mem_write(sites[0],b'\x4e\xb9'+struct.pack('>I',s[ours]))
    # Compter seulement les allocations du menu, hors tables de locks privées.
    r.new_count=0
    # Reproduire le groupe 2 ajouté par le constructeur natif MACHINES.
    construct=r.construct
    def grouped_construct(args):
        obj=construct(args);vec=obj+0x200
        r.w32(vec,2);r.w32(obj+28,vec);r.w32(obj+32,vec+4);r.w32(obj+36,vec+4)
        return obj
    r.stubs[0x400a22b0]=grouped_construct
    def grouped_show(args):
        obj=r.r32(args[1])
        # Présentation simulée : un groupe 2 non masqué détruirait la vue B.
        lo,hi=r.r32(obj+28),r.r32(obj+32)
        if any(r.r32(at)==2 for at in range(lo,hi,4)):
            r.w32(s['mlp_obj'],0)
        return r.show(args)
    r.stubs[0x4007700e]=grouped_show
    lo=int(sg['sg_o_allocate'],16);hi=int(sg['sg_o_done'],16)
    target=b'\x4e\xb9'+struct.pack('>I',s['ml_genie_present'] if a.syntakt else 0x4007700e)
    sites=[at for at in range(lo,hi,2) if bytes(r.u.mem_read(at,6))==target]
    assert len(sites)==1
    r.u.mem_write(sites[0],b'\x4e\xb9'+struct.pack('>I',s['ml_genie_present']))
    r.stubs[0x4007240c]=lambda a:r.r32(a[0]+12)
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x4007240c,end=0x4007240c)
    # Raccourci réel B : SETTINGS+PAGE, sans état TG ni touche PATTERN.
    for addr in (s['ml_key_next'],s['ML_original_key']):
        r.stubs[addr]=lambda a:r.r32(a[0]+12)
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    # Le menu B reçoit aussi les événements bruts sans passer par ml_key.
    addr=s['ml_bank_ui_sync'];r.stubs[addr]=lambda a:1
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.event(13,1,90);r.call('mlp_menu_key',0x93075000,EVENT)
    assert r.r32(s['ml_genie_settings'])==1
    r.event(15,1,91);assert r.call('mlp_menu_key',0x93075000,EVENT)==1
    assert r.r32(s['SG_obj']) and r.new_count==2
    assert r.r32(s['mlp_obj'])==0x93075000
    opened=r.r32(s['SG_obj'])
    assert r.r32(opened+32)==r.r32(opened+28)+4
    r.s['native_group_contains']=0x40076102
    assert r.call('native_group_contains',opened,2)==1
    r.w32(s['SG_obj'],0)
    r.event(13,0,92);r.call('mlp_menu_key',0x93075000,EVENT)
    assert r.r32(s['ml_genie_settings'])==0
    r.w32(s['TG_set_held'],0)
    r.event(3,1,100);assert r.call('ml_key',EVENT)==3
    r.event(15,1,101);assert r.call('ml_key',EVENT)==15
    assert r.r32(int(sg['sg_obj'],16))==0
    r.event(13,1,102);assert r.call('ml_key',EVENT)==13
    r.event(13,32,102);r.call('ml_key',EVENT)
    assert r.r32(s['ml_genie_settings'])==1
    r.w32(s['mlp_func'],1)
    r.event(15,1,103);assert r.call('ml_key',EVENT)==15
    r.w32(s['mlp_func'],0)
    r.event(15,1,104)
    for _ in range(3):assert r.call('ml_key',EVENT)==0
    obj=r.r32(int(sg['sg_obj'],16));assert obj and r.new_count==4
    r.event(15,0,105)
    for _ in range(3):assert r.call('ml_key',EVENT)==0
    r.event(13,0,106);r.call('ml_key',EVENT)
    assert r.r32(s['ml_genie_settings'])==0
    before=bytes(r.u.mem_read(pattern,1584));r.w32(int(sg['sg_row'],16),19)
    r.event(32,16);r.call('ml_genie_menu_key',obj,EVENT)
    assert bytes(r.u.mem_read(pattern,1584))!=before and r.r32(s['SG_error'])==0
    r.w32(int(sg['sg_row'],16),20);r.event(32,16)
    r.call('ml_genie_menu_key',obj,EVENT)
    assert bytes(r.u.mem_read(pattern,1584))==before
    assert bytes(r.u.mem_read(RAW,722))==audio
    # Perte de l'objet UI sous overlay : conserver explicitement la destination B.
    assert r.r32(s['ml_genie_b_owner'])==obj
    saved_b=r.r32(s['mlp_obj']);r.w32(s['mlp_obj'],0)
    before=bytes(r.u.mem_read(pattern,1584));r.w32(int(sg['sg_row'],16),19)
    r.event(32,16);r.call('ml_genie_menu_key',obj,EVENT)
    assert bytes(r.u.mem_read(pattern,1584))!=before
    assert bytes(r.u.mem_read(RAW,722))==audio
    r.w32(int(sg['sg_row'],16),20);r.event(32,16)
    r.call('ml_genie_menu_key',obj,EVENT)
    assert bytes(r.u.mem_read(pattern,1584))==before
    assert bytes(r.u.mem_read(RAW,722))==audio
    r.w32(s['mlp_obj'],saved_b)
    # Le callback supérieur route FUNC+pad vers B et synchronise le release.
    redraw=[]
    for addr,fn in ((0x400760ba,lambda a:redraw.append(a[0]) or 0),
                    (0x40013904,lambda a:(_ for _ in ()).throw(AssertionError('mute audio')))):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.event(1,1);r.call('ml_genie_menu_key',obj,EVENT)
    assert r.r32(s['mlp_func'])==1
    r.event(0,1);r.w32(EVENT+20,1)
    assert r.call('ml_genie_pad',obj+16,EVENT)==1
    assert r.u.mem_read(pattern,1)==b'\0' and redraw==[0x93075000]
    r.event(0,0);r.w32(EVENT+20,1);r.call('ml_genie_pad',obj+16,EVENT)
    r.event(1,0);r.call('ml_genie_menu_key',obj,EVENT)
    assert r.r32(s['mlp_func'])==0
    # Stop et changement de pattern suivent le service UI, jamais un writer IRQ.
    r.w32(0x40a7883c,1);r.call('ml_genie_generate')
    r.w32(0x40a7883c,0);r.call('ml_genie_service')
    assert r.r32(s['ml_gq_state'])==0
    assert bytes(r.u.mem_read(pattern,1584))!=before
    r.w32(0x40a7883c,1);r.call('ml_genie_generate')
    r.w32(s['ml_pattern'],other);r.call('ml_genie_service')
    assert r.r32(s['ml_gq_state'])==0 and r.r32(s['SG_undo_valid'])==0
    r.w32(s['ml_pattern'],pattern)
    # Fermer Genie ne détruit pas l'éditeur B ni sa voie sélectionnée.
    r.s['native_genie_dtor']=int(sg['sg_dtor0'],16)
    r.call('native_genie_dtor',obj)
    assert r.r32(s['SG_obj'])==0 and r.r32(s['mlp_obj'])==0x93075000
    assert r.r32(s['mlp_track'])==5 and r.r32(s['ml_pattern'])==pattern
    # Sans B, les actions originales sont déléguées avec la pile inchangée.
    calls=[];r.w32(s['mlp_obj'],0)
    for native,router in (('SG_action_generate','ml_genie_generate'),('SG_action_undo','ml_genie_undo'),('SG_pad','ml_genie_pad')):
        addr=s[native];r.stubs[addr]=lambda args,n=native:calls.append(n) or 77
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
        assert r.call(router,0,EVENT)==77
    assert calls==['SG_action_generate','SG_action_undo','SG_pad']
    print('ok : six voies B isolées, Generate/Undo arrêtés et en lecture, frontière de voie, annulation après édition, SR conservé')
    print('ok : algorithmes Genie natifs, Euclide 4/16, vélocité positive 80..110 ; aucune donnée audio modifiée')
    print('ok : ouverture/menu natifs, clic Generate/Undo vers B ; getter de touche synthétique')
    print('ok : callback brut B SETTINGS+PAGE sans getter : construction du menu natif')
    print('ok : getter B SETTINGS+PAGE sans PATTERN ni état TG ; FUNC+PAGE reste natif, lectures répétées/release idempotents')
    print('ok : groupe de fermeture masqué pendant présentation seulement ; fermeture Genie conserve B et voie TR12')
    print('ok : Stop applique, changement de pattern annule ; actions A déléguées sans changement de pile')


if __name__=='__main__':main()
