#!/usr/bin/env python3
"""Note 57 : interface banque MIDI, constructeur/destructeur OS réels.

Allocation, présentation, dessin et delta encodeur simulés. Exécute édition,
file note-off, lecteurs de sélection natifs, pads et saisie des 64 pas.
Aucun hook global ni firmware flashable livré par cette preuve.
"""
import argparse
import pathlib
import struct
import subprocess
import tempfile
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig, EVENT, RAW
from test_sdvintage import main_os_from_syx

ENTRY, DATA, PAT, RUNTIME = 0x93050000,0x93060000,0x93070000,0x93071000


def load(r,worker=False):
    root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as temp:
        p=pathlib.Path(temp);objects=[]
        for name in ('runtime','pattern','clock','service','prepare','page','integration','key','led','ui_hook','transport','worker'):
            obj=p/(name+'.o')
            subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_WORKER=1'] if worker else []),'-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
            objects.append(str(obj))
        (p/'link.ld').write_text('SECTIONS { .text '+hex(ENTRY)+' : { *(.text*) } .data '+hex(DATA)+' : { *(.data*) *(.rodata*) } } TG_set_held = 0x93082000; TG_mod_used = 0x93082004; ml_key_next = 0x4007240c;' )
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlp_open','-o',str(p/'page.elf'),*objects],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'page.elf'),str(p/'page.bin')],check=True)
        r.u.mem_write(ENTRY,(p/'page.bin').read_bytes())
        r.s={line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output([cross+'nm',str(p/'page.elf')],text=True).splitlines() if len(line.split())==3}


def make(stock,real=True):
    r=Rig(stock,{'writes':[]},{'writes':[],'symbols':{}},real_ui=real)
    load(r)
    assert r.call('ml_init',PAT)==1
    r.u.mem_write(RUNTIME,bytes(320))
    r.w32(r.s['ml_pattern'],PAT);r.w32(r.s['ml_runtime'],RUNTIME)
    r.w32(0x93005030,0x93005100);r.w32(0x93005128,0x93005200)
    r.u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75')
    r.w32(0x93005304,5)
    return r


def key(r,code,flags=1):
    r.w32(EVENT+12,code);r.w32(EVENT+16,flags)
    return r.call('mlp_menu_key',r.r32(r.s['mlp_obj']),EVENT)


def knob(r,delta,thunk=False):
    r.delta=delta;r.w32(EVENT+12,1)
    return r.call('mlp_enc_th' if thunk else 'mlp_enc',r.r32(r.s['mlp_obj'])+(4 if thunk else 0),EVENT)


def raw(r,row,track=None,step=None):
    track=r.r32(r.s['mlp_track']) if track is None else track
    step=r.r32(r.s['mlp_step']) if step is None else step
    if row==0:return track
    if row==1:return track+7
    if row==5:return step
    field={2:3,3:4,4:5,6:3,7:0,8:1,9:2,10:0}[row]
    addr=PAT+264*track+field+(8+4*step if row in (6,7,8,9) else 0)
    return r.u.mem_read(addr,1)[0]


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
    stock=main_os_from_syx(args.cycles);r=make(stock)
    expected=bytes(r.u.mem_read(PAT,1584))
    observations=[]
    def unpublished(u,addr,size,data):
        observations.append(addr)
        assert r.r32(r.s['ml_context'])==0
        assert r.r32(r.s['ml_preparing'])==1
    handle=r.u.hook_add(UC_HOOK_CODE,unpublished,begin=r.s['ml_init'],end=r.s['ml_init'])
    assert r.call('ml_prepare')==1
    r.u.hook_del(handle)
    context=r.r32(r.s['ml_context'])
    assert context and observations and r.new_count==1
    assert r.r32(r.s['ml_pattern'])==context
    assert r.r32(r.s['ml_runtime'])==context+1584
    assert r.r32(r.s['ml_clock_state'])==context+1904
    assert bytes(r.u.mem_read(context,1956))==expected+bytes(372)
    r.u.mem_write(context+8,b'\x48\x64\x01\x01')
    retained=bytes(r.u.mem_read(context,1956))
    assert r.call('ml_prepare')==1 and r.new_count==1
    assert bytes(r.u.mem_read(context,1956))==retained
    for reason in ('ipl','busy','allocation'):
        b=make(stock)
        if reason=='ipl':b.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        if reason=='busy':b.w32(b.s['ml_preparing'],1)
        if reason=='allocation':b.fail_new=1
        assert b.call('ml_prepare')==0 and not b.r32(b.s['ml_context'])
        assert b.new_count==(reason=='allocation')
        assert b.r32(b.s['ml_preparing'])==(reason=='busy')
        if reason=='allocation':
            b.fail_new=0
            assert b.call('ml_prepare')==1 and b.r32(b.s['ml_context'])
            assert b.new_count==2
    print('ok : contexte MIDI unique 1956 octets, publication après pattern/file/horloge initialisés ; conservation et gardes IPL/réentrance/échec allocation')
    r=make(stock)
    original_sound=bytes(r.u.mem_read(RAW,722))
    forbidden=[]
    def no_sound(u,a,s,d):forbidden.append(a);raise AssertionError('chemin sonore atteint')
    for addr in (0x4005894a,0x400548ce,0x40058e28):
        r.u.hook_add(UC_HOOK_CODE,no_sound,begin=addr,end=addr)
    assert r.call('mlp_open')==1
    obj=r.r32(r.s['mlp_obj'])
    assert obj and r.r32(obj)==r.s['mlp_vt']+8
    assert r.r32(obj+4)==r.s['mlp_vt']+0x58 and r.r32(obj+16)==r.s['mlp_vt']+0x94
    assert r.r32(obj+104) and r.r32(obj+108)
    assert r.r32(r.s['mlp_track'])==5 and r.r32(0x93005304)==5
    allocs=r.new_count
    assert r.call('mlp_open')==0 and r.new_count==allocs
    print('ok : constructeur OS réel, vtables privées, sélection initiale et ouverture doublée refusée')

    r.w32(r.s['mlp_setup'],1)
    for track in range(6):
      r.w32(r.s['mlp_track'],track)
      for row in range(11):
       for editing in (0,1):
        r.w32(r.s['mlp_row'],row);r.w32(r.s['mlp_edit'],editing)
        r.texts.clear();r.rects.clear()
        r.call('mlp_render',obj,0x93006000)
        assert len(r.texts)==7 and r.texts[0][2]=='MIDI BANK'
        assert sorted(set(y for _,y,_ in r.texts))==[7,21,35,49]
        for _,x1,y1,x2,y2,mode in r.rects:assert 0<=x1<=x2<=127 and 0<=y1<=y2<=63
        if row in (0,1,2):assert any(x==125 and text==str(track+7) for x,y,text in r.texts)
    print('ok : 132 vues de rendu, titre/trois lignes, canaux affichés immuables 7..12')

    minimum=(0,7,2,1,0,0,0,0,1,1,0)
    maximum=(5,12,4,64,6,63,1,127,127,64,1)
    for track in range(6):
      for row in (2,3,4,6,7,8,9,10):
        r.w32(r.s['mlp_track'],track);r.w32(r.s['mlp_step'],track*10)
        r.w32(r.s['mlp_row'],row);r.w32(r.s['mlp_edit'],1)
        before=bytearray(r.u.mem_read(PAT,1584))
        for _ in range(140):assert knob(r,-1,thunk=bool(row%2))==1
        assert raw(r,row)==minimum[row],(track,row,raw(r,row))
        for _ in range(140):knob(r,1,thunk=bool(row%2))
        assert raw(r,row)==maximum[row],(track,row,raw(r,row))
        field={2:3,3:4,4:5,6:3,7:0,8:1,9:2,10:0}[row]
        offset=264*track+field+(8+4*track*10 if row in (6,7,8,9) else 0)
        before[offset]=maximum[row]
        assert bytes(r.u.mem_read(PAT,1584))==bytes(before)
    # Le canal ne devient pas éditable, même en forçant le flag d'édition.
    for track in range(6):
        r.w32(r.s['mlp_track'],track);r.w32(r.s['mlp_row'],1);r.w32(r.s['mlp_edit'],0)
        key(r,32,16);assert r.r32(r.s['mlp_edit'])==0
        r.w32(r.s['mlp_edit'],1)
        before=bytes(r.u.mem_read(PAT,1584))
        knob(r,-1);knob(r,1)
        assert bytes(r.u.mem_read(PAT,1584))==before and raw(r,1)==track+7
    print('ok : huit champs × six voies, clamps, vitesse/port/longueur et pas ; canal non éditable, autres données intactes')

    # Nouvelle banque pour saisie des pas : trigs et pages 16 pas, aucune voix.
    r.call('ml_init',PAT);r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_step'],0)
    for bank in range(4):
        for trig in range(16):
            key(r,16+trig)
            assert r.r32(r.s['mlp_step'])==bank*16+trig
            assert raw(r,6)==1
            key(r,16+trig,0)
            assert raw(r,6)==1
            key(r,16+trig,9)
            assert raw(r,6)==1
        key(r,15)
    assert r.r32(r.s['mlp_step'])==15
    assert all(r.u.mem_read(PAT+8+4*step+3,1)==b'\x01' for step in range(64))
    key(r,31);assert raw(r,6)==1
    key(r,31,0);assert raw(r,6)==0
    r.w32(r.s['mlp_setup'],1)
    r.w32(r.s['mlp_row'],6);key(r,32,16);assert raw(r,6)==1
    print('ok : saisie des 64 pas par quatre pages, sélection/toggle, releases/répétitions consommées et clic booléen')

    # Tenir un trig et tourner DATA : notes directes, sans éteindre le trig.
    for page in range(4):
        r.w32(r.s['mlp_step'],page*16)
        for lane in range(6):
            r.w32(r.s['mlp_track'],lane)
            for trig in (0, 7, 15):
                step=page*16+trig
                r.u.mem_write(PAT+lane*264+8+step*4,bytes([60,100,1,1]))
                before=bytes(r.u.mem_read(RAW,722))
                key(r,16+trig)
                assert raw(r,6)==1 and r.r32(r.s['mlp_row'])==7
                knob(r,1);assert raw(r,7)==61
                key(r,16+trig,0);assert raw(r,6)==1
                assert bytes(r.u.mem_read(RAW,722))==before
                key(r,16+trig);key(r,16+trig,0);assert raw(r,6)==0
    r.w32(r.s['mlp_step'],0)
    key(r,16);key(r,17)
    n0,n1=raw(r,7,step=0),raw(r,7,step=1)
    knob(r,1)
    assert raw(r,7,step=0)==min(127,n0+1)
    assert raw(r,7,step=1)==min(127,n1+1)
    key(r,16,0);key(r,17,0)
    assert raw(r,6,step=0)==raw(r,6,step=1)==1
    print('ok : trig tenu + DATA, six voies × quatre pages ; notes directes, maintien actif, tap pour retirer, deux trigs tenus, piste audio intacte')

    # Vue musicale par défaut et accès/retour au menu sans fermer la banque.
    original_draw=r.stubs[0x40071a04]
    def overview_text(args):
        ctx,font,x,y,flags,fmt,value,last=args
        f=r.string(fmt)
        if f=='%s%d':text=r.string(value)+str(last if last<0x80000000 else last-0x100000000)
        elif f=='Ch%d':text='Ch'+str(value)
        elif f=='S%02d':text='S'+str(value).zfill(2)
        else:return original_draw(args)
        r.texts.append((x,y,text));return 0
    r.stubs[0x40071a04]=overview_text
    r.w32(r.s['mlp_setup'],0)
    r.w32(r.s['mlp_step'],0)
    for note,name in ((0,'C-1'),(60,'C4'),(61,'C#4'),(127,'G9')):
        lane=r.r32(r.s['mlp_track'])
        r.u.mem_write(PAT+lane*264+8,bytes([note,100,1,1]))
        r.texts.clear();r.rects.clear()
        r.call('mlp_render',obj,0x93006000)
        assert (5,24,name) in r.texts and (51,47,'Vol') in r.texts
        assert (54,24,'100') in r.texts
        assert any(rect[1:]==(1,15,42,43,0xffffffff) for rect in r.rects)
    key(r,32,16);assert r.r32(r.s['mlp_setup'])==1
    key(r,12);assert r.r32(r.s['mlp_setup'])==0 and r.r32(r.s['mlp_obj'])==obj
    r.stubs[0x40071a04]=original_draw
    r.w32(r.s['mlp_setup'],1)
    print('ok : vue musicale, note inversée gauche C-1/C4/C#4/G9, Vol/vélocité centre, DATA ouvre les réglages et EXIT revient')

    def pad(index,state):
        r.w32(EVENT+20,index);r.w32(EVENT+16,state)
        return r.call('mlp_pad',obj+16,EVENT)
    for lane in range(6):
        pad(lane+1,1);assert r.r32(r.s['mlp_track'])==lane
        pad(lane+1,0)
    r.w32(r.s['mlp_track'],0)
    packet=0x983c6404
    assert r.call('ml_step',RUNTIME,2,packet,8)==1
    assert r.call('ml_take',RUNTIME)==packet
    key(r,1,1)
    pad(3,1)
    assert r.u.mem_read(PAT+264*2,1)==b'\x00'
    assert r.r32(r.s['mlp_track'])==0
    assert r.call('ml_take',RUNTIME)==0x883c0004
    pad(3,1);assert r.u.mem_read(PAT+264*2,1)==b'\x00'
    pad(3,2);assert r.u.mem_read(PAT+264*2,1)==b'\x00'
    pad(3,0);pad(3,1)
    assert r.u.mem_read(PAT+264*2,1)==b'\x01'
    key(r,1,0);pad(3,0)
    # Couper avant livraison retire les note-ons de cette voie seulement.
    assert r.call('ml_step',RUNTIME,2,0x983d6402,8)==1
    assert r.call('ml_step',RUNTIME,3,0x993e6403,8)==1
    key(r,1,1);pad(3,1);key(r,1,0);pad(3,0)
    assert r.call('ml_take',RUNTIME)==0x883d0002
    assert r.call('ml_take',RUNTIME)==0x993e6403
    assert r.call('ml_take',RUNTIME)==0x883d0002
    assert r.call('ml_take',RUNTIME)==0
    assert r.u.mem_read(PAT+264*2+1,1)==b'\x00'
    # Même commande dans la page, sans changer le drapeau mute réservé.
    r.w32(r.s['mlp_track'],2);r.w32(r.s['mlp_row'],10);r.w32(r.s['mlp_edit'],1)
    knob(r,1);assert raw(r,10)==1
    knob(r,-1);assert raw(r,10)==0
    assert r.u.mem_read(PAT+264*2+1,1)==b'\x00'
    # Changer de port libère sur l'ancien port, mais tourner à la borne ne coupe pas.
    r.w32(r.s['mlp_track'],0);r.w32(r.s['mlp_row'],2);r.w32(r.s['mlp_edit'],1)
    assert r.call('ml_step',RUNTIME,0,0x963c6404,8)==1
    assert r.call('ml_take',RUNTIME)==0x963c6404
    knob(r,1);assert r.call('ml_take',RUNTIME)==0
    knob(r,-1);assert r.call('ml_take',RUNTIME)==0x863c0004
    assert raw(r,2)==3
    for code in (10,11):
        assert key(r,code,1)==0 and key(r,code,3)==1
    assert bytes(r.u.mem_read(RAW,722))==original_sound and not forbidden
    assert r.r32(0x93005304)==5
    print('ok : pads, FUNC+pad MIDI OUT idempotent et note-off immédiat, ancien port conservé, Play/Stop ; piste sonore et sélection natives intactes')

    before=bytes(r.u.mem_read(PAT,1584))
    r.call('mlp_dtor1',obj)
    assert not r.r32(r.s['mlp_obj']) and obj in r.free
    assert r.r32(r.s['ml_pattern'])==PAT and r.r32(r.s['ml_runtime'])==RUNTIME
    assert bytes(r.u.mem_read(PAT,1584))==before
    assert r.call('mlp_open')==1
    for fail in (1,2):
        b=make(stock,real=False);b.fail_new=fail
        assert b.call('mlp_open')==0 and not b.r32(b.s['mlp_obj']) and not b.present
        assert len(b.free)==(fail==2)
    print('ok : destructeur OS réel, réouverture sans perdre les données RAM ; refus allocation page/détenteur nettoyés')
    for reason in ('ipl','pattern','runtime','manager'):
        b=make(stock)
        before=bytes(b.u.mem_read(PAT,1584))
        if reason=='ipl':b.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        if reason=='pattern':b.w32(b.s['ml_pattern'],0)
        if reason=='runtime':b.w32(b.s['ml_runtime'],0)
        if reason=='manager':b.w32(0x40fe4178,0)
        assert b.call('mlp_open')==0 and not b.r32(b.s['mlp_obj'])
        assert b.new_count==0 and not b.present
        assert bytes(b.u.mem_read(PAT,1584))==before
    print('ok : gardes IPL/pattern/runtime/gestionnaire sans allocation ni modification des données')
    print('NOTE : pages en émulation, dessin/présentation simulés ; LED/raccourci couverts séparément ; persistance et installation globale des hooks restent à faire')


if __name__=='__main__':main()
