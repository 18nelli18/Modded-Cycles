#!/usr/bin/env python3
"""Note 58 : page d'édition LFO 2, vraie construction/destruction OS.

Assemble la page et ses callbacks, exécute l'OS 1.13. Allocation, présentation,
dessin, delta encodeur et fermeture du gestionnaire sont simulés. Aucune
installation du hook audio ni sauvegarde persistante dans cette preuve.
"""
import argparse
import json
import pathlib
import struct
import subprocess
import tempfile
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig, EVENT
from test_sdvintage import main_os_from_syx
import build

ENTRY, DATA, CTX, FRAME, PARENT, PARENT_VT, CLOSE = (
    0x93050000, 0x93060000, 0x93070000, 0x93071000, 0x93080000, 0x93081000, 0x93082000)
PLACED=None


def load(r):
    if PLACED:
        tweak=json.loads(pathlib.Path(PLACED).read_text())
        for write in tweak['writes']:
            r.u.mem_write(build.BASE+write['off'],bytes.fromhex(write['new']))
        r.s={name:int(value,16) for name,value in tweak['symbols'].items()}
        assert r.r32(0x401016c8)==r.s['lf2_key']
        assert r.r32(0x401016e4)==r.s['lf2_key_sub']
        assert r.r32(r.s['lf2_open_callback'])==r.s['lf2_launch']
        return
    root = pathlib.Path(__file__).resolve().parents[2]
    cross = str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as temp:
        p = pathlib.Path(temp)
        objects = []
        for name in ('update', 'mix', 'dispatch', 'edit', 'init', 'prepare', 'launch', 'key', 'page', 'layout'):
            obj = p/(name+'.o')
            subprocess.run([cross+'as', '-march=cfv4e', '-o', str(obj),
                            str(root/'tools/machines/lfo_secondary'/(name+'.s'))], check=True)
            objects.append(str(obj))
        (p/'link.ld').write_text('SECTIONS { .text '+hex(ENTRY)+' : { *(.text*) } '
                                '.data '+hex(DATA)+' : { *(.data*) *(.rodata*) } }')
        subprocess.run([cross+'ld', '-T', str(p/'link.ld'), '-e', 'lf2p_open',
                        '-o', str(p/'page.elf'), *objects], check=True)
        subprocess.run([cross+'objcopy', '-O', 'binary', str(p/'page.elf'), str(p/'page.bin')], check=True)
        r.u.mem_write(ENTRY, (p/'page.bin').read_bytes())
        r.s = {line.split()[2]: int(line.split()[0], 16) for line in
               subprocess.check_output([cross+'nm', str(p/'page.elf')], text=True).splitlines()
               if len(line.split()) == 3}


def make(stock, real=True):
    r = Rig(stock, {'writes': []}, {'writes': [], 'symbols': {}}, real_ui=real)
    load(r)
    allocations=set();freed=set();original_new=r.stubs[0x400802e0]
    def allocate(a):
        pointer=original_new(a)
        if pointer:allocations.add(pointer)
        return pointer
    def release(a):
        pointer=a[0]
        assert pointer==0 or pointer in allocations, ('invalid free',hex(pointer))
        assert pointer==0 or pointer not in freed, ('double free',hex(pointer))
        if pointer:freed.add(pointer)
        r.free.append(pointer)
        return 0
    r.stubs[0x400802e0]=allocate
    r.stubs[0x400802ec]=release
    if not real:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400802ec,end=0x400802ec)
    def formatted(a):
        f=r.string(a[5])
        r.texts.append((a[2],a[3],r.string(a[6]) if f=='%s' else str(a[6]) if f=='%d' else chr(a[6])+str(a[7])+('k' if f.endswith('k') else '') if f in ('%c%d','%c%dk') else f))
    native_stubs={
        0x40070f6e:lambda a:0,0x40071da4:lambda a:0,
        0x4007199c:lambda a:r.texts.append((a[2],a[3],r.string(a[5]))) or 0,
        0x40072204:lambda a:r.r32(r.r32(a[2])-12),
        0x40070efc:lambda a:r.rects.append(a[:6]) or 0,
    }
    r.stubs[0x40071a04]=formatted
    for addr,fn in native_stubs.items():
        r.stubs[addr]=fn
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.u.mem_write(CTX, bytes(1240))
    frame = bytearray(476)
    for track in range(6):
        struct.pack_into('>8H', frame, track*66+16, 16384, 9<<8, 16384, 11<<8,
                         0, 0, 0, 16384)
    r.u.mem_write(FRAME, bytes(frame))
    assert r.call('lf2_init', CTX, FRAME) == 1
    r.w32(r.s['lf2_context'], CTX)
    r.w32(r.s['lf2_open_callback'], r.s['lf2p_open'])
    # Le getter de sélection natif (objet embarqué manager +48, vtable +40).
    r.w32(0x93005030,0x93005100)
    r.w32(0x93005128,0x93005200)
    r.u.mem_write(0x93005200,b'\x20\x3c'+struct.pack('>I',0x93005300)+b'\x4e\x75')
    r.w32(0x93005304,5)
    # Contexte des noms : tables boot et backend sonore réels, getters simulés.
    kit=0x93090000;vt=0x93098000;getter=0x93099000
    r.stubs[0x400cf866]=lambda a:kit
    r.w32(kit+48,0x93005100)
    r.w32(vt+40,getter)
    r.u.mem_write(getter,b'\x20\x6f\x00\x04\x20\x28\x00\x04\x4e\x75')
    for track in range(6):
        handle=kit+212+68*track;raw=0x930a0000+track*128
        owner=kit+116+8*(63+track)
        r.w32(owner,0x400fd134);r.w32(owner+4,handle)
        r.w32(handle,vt);r.w32(handle+4,raw)
        r.u.mem_write(raw,bytes(100));r.u.mem_write(raw+38,bytes([track]))
    r.call(0x4005a274)
    return r


def event(r, code, flags=0):
    r.w32(EVENT+12, code)
    r.w32(EVENT+16, flags)


def page(r):
    return r.r32(r.s['lf2p_obj'])


def knob(r, delta, thunk=False):
    r.delta = delta
    event(r, 1)
    assert r.call('lf2p_enc_th' if thunk else 'lf2p_enc', page(r)+(4 if thunk else 0), EVENT) == 1


def value(r, track, field):
    word = struct.unpack('>H', r.u.mem_read(CTX+192+16*track+2*field, 2))[0]
    return word>>8 if field in (1, 3, 4, 6) else word


def main():
    global PLACED
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    ap.add_argument('--tweak',help='Tester les octets réellement placés dans les masques du firmware')
    args = ap.parse_args()
    PLACED=args.tweak
    stock = main_os_from_syx(args.cycles)
    # Régression : l'ancien retour statique doit être refusé par le heap simulé.
    bad=make(stock)
    assert bad.call('lf2p_open') == 1
    bad.w32(bad.s['lf2p_row'],1)
    borrowed=bad.r32(bad.s['lf2l_labels'])
    bad.u.mem_write(bad.s['lf2l_label'],b'\x20\xbc'+struct.pack('>I',borrowed)+b'\x4e\x75')
    try:
        bad.call('lf2p_render',page(bad),0x93006000)
    except AssertionError as failure:
        assert failure.args[0][0] == 'invalid free', failure
    else:
        raise AssertionError('Le renderer doit détruire le résultat de libellé')
    print('ok : régression ancien libellé statique détectée comme libération invalide')
    b=make(stock)
    b.w32(b.s['lf2_context'],0)
    allocations=b.new_count
    observations=[]
    def unpublished(u,addr,size,data):
        observations.append(addr)
        assert b.r32(b.s['lf2_context'])==0
        assert b.r32(b.s['lf2_preparing'])==1
    b.u.hook_add(UC_HOOK_CODE,unpublished,begin=b.s['lf2_init'],end=b.s['lf2_init'])
    assert b.call('lf2_prepare',FRAME)==1
    context=b.r32(b.s['lf2_context'])
    assert context and observations and b.new_count==allocations+1
    expected=bytes(b.u.mem_read(CTX,1240))
    assert bytes(b.u.mem_read(context,1240))==expected
    b.u.mem_write(context+192,b'\x12\x34')
    retained=bytes(b.u.mem_read(context,1240))
    assert b.call('lf2_prepare',FRAME)==1 and b.new_count==allocations+1
    assert bytes(b.u.mem_read(context,1240))==retained
    for reason in ('ipl','frame','busy','allocation'):
        b=make(stock)
        b.w32(b.s['lf2_context'],0)
        argument=FRAME
        if reason=='ipl':b.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        if reason=='frame':argument=0
        if reason=='busy':b.w32(b.s['lf2_preparing'],1)
        if reason=='allocation':b.fail_new=1
        assert b.call('lf2_prepare',argument)==0
        assert b.r32(b.s['lf2_context'])==0
        assert b.new_count==(reason=='allocation')
        assert b.r32(b.s['lf2_preparing'])==(reason=='busy')
    print('ok : allocation unique UI, publication après initialisation, réouverture sans reset ; gardes IPL/frame/réentrance et échec allocation')
    # Parcours complet touche -> préparation -> page, et repli natif si refus.
    for subobject in (False,True):
        for failure in (False,True):
            b=make(stock)
            b.u.mem_map(0x80000000,0x10000)
            b.u.mem_write(0x8000100c,bytes(b.u.mem_read(FRAME,476)))
            b.w32(b.s['lf2_context'],0)
            b.w32(b.s['lf2_open_callback'],b.s['lf2_launch'])
            b.w32(PARENT,PARENT_VT);b.w32(PARENT_VT+124,CLOSE)
            closed=[]
            b.stubs[CLOSE]=lambda a:closed.append(a[0]) or 0
            b.u.hook_add(UC_HOOK_CODE,b.stub,begin=CLOSE,end=CLOSE)
            if failure:b.fail_new=1
            before=bytes(b.u.mem_read(0x8000100c,476))
            event(b,8,0)
            handler=b.r32(0x401016e4 if subobject else 0x401016c8) if PLACED else b.s['lf2_key_sub' if subobject else 'lf2_key']
            assert b.call(handler,PARENT+(56 if subobject else 0),EVENT)==1
            assert bytes(b.u.mem_read(0x8000100c,476))==before
            if failure:
                assert closed==[PARENT] and not page(b)
                assert not b.r32(b.s['lf2_context'])
                # Une nouvelle tentative fonctionne après refus de l'allocateur.
                b.fail_new=0
                assert b.call('lf2_key',PARENT,EVENT)==1 and page(b)
            else:
                assert not closed and page(b)
            context=b.r32(b.s['lf2_context'])
            assert context and bytes(b.u.mem_read(context,1240))==expected
            b.u.mem_write(context+192,b'\x12\x34')
            b.call('lf2p_dtor1',page(b))
            assert b.call('lf2_key',PARENT,EVENT)==1 and page(b)
            assert b.r32(b.s['lf2_context'])==context
            assert b.u.mem_read(context+192,2)==b'\x12\x34'
    print('ok : deuxième appui principal/sous-objet initialise et ouvre ; échec revient à la fermeture native, retry/réouverture gardent le contexte')
    r = make(stock)
    # Deuxième appui via l'adaptateur et les vrais lecteurs d'événements.
    r.w32(PARENT, PARENT_VT)
    r.w32(PARENT_VT+124, CLOSE)
    r.u.mem_write(PARENT+604, bytes(1))
    event(r, 8, 1)
    assert r.call('lf2_key', PARENT, EVENT) == 1 and not page(r)
    event(r, 8, 0)
    assert r.call('lf2_key', PARENT, EVENT) == 1
    obj = page(r)
    assert obj and r.present and r.r32(obj) == r.s['lf2p_vt']+8
    assert r.r32(r.s['lf2p_track']) == 5 and r.r32(0x93005304) == 5
    assert r.r32(obj+4) == r.s['lf2p_vt']+0x58
    assert r.r32(obj+16) == r.s['lf2p_vt']+0x94
    assert r.r32(obj+104) and r.r32(obj+108)
    allocations=r.new_count
    assert r.call('lf2p_open') == 0 and page(r) == obj and r.new_count == allocations
    print('ok : deuxième appui LFO ouvre la page, constructeur OS réel et trois vtables privées ; ouverture doublée refusée')

    for track in range(6):
      r.w32(r.s['lf2p_track'], track)
      for row in range(9):
       for editing in (0, 1):
        r.w32(r.s['lf2p_row'], row)
        r.w32(r.s['lf2p_edit'], editing)
        r.texts.clear(); r.rects.clear()
        r.call('lf2p_render', obj, 0x93006000)
        assert len(r.texts) == 9 and r.texts[0][2] == 'LFO 2'
        labels=('Trk','Spd','Mul','Fad','Dst','Wav','SPH','Rst','Dep')
        order=(5,2,4,8,1,3,6,7,0);scroll=max(0,min(5,order.index(row)-1))
        assert [text for x,y,text in r.texts if x==72]==[labels[i] for i in order[scroll:scroll+4]]
        assert all(0 <= x <= 127 and 0 <= y <= 55 for x, y, _ in r.texts)
        assert sorted(set(y for _, y, _ in r.texts)) == [8, 21, 34, 47]
        assert len(r.rects) == 3
        for _, x1, y1, x2, y2, mode in r.rects:
            assert 0 <= x1 <= x2 <= 127 and 0 <= y1 <= y2 <= 63
        assert r.rects[1][1] == (95 if editing else 70)
    print('ok : six pistes × neuf positions × édition/navigation, rendu natif avec quatre lignes, coordonnées sans débordement')

    r.w32(r.s['lf2p_track'],0)
    for field,names in ((4,('TRI','SIN','SQR','SAW','EXP','RMP','RND')),
                        (6,('FRE','TRG','HLD','ONE','HLF'))):
        for index,name in enumerate(names):
            assert r.call('lf2_edit',CTX,0,field,index)==1
            r.w32(r.s['lf2p_row'],field+1)
            r.texts.clear()
            r.call('lf2p_render',obj,0x93006000)
            assert any(x==120 and text==name for x,y,text in r.texts)
    print('ok : noms des sept formes et cinq modes lus dans les tables natives')

    for track in range(6):
        r.w32(r.s['lf2p_track'],track);r.w32(r.s['lf2p_row'],4)
        for destination in (*range(33),127):
            assert r.call('lf2_edit',CTX,track,3,destination)==1
            r.texts.clear();r.call('lf2p_render',obj,0x93006000)
            descriptor=r.call(0x4005a692,destination,track) if destination!=127 else 0
            expected='OFF' if destination==127 else r.string(r.r32(0x4010dce0+56*descriptor+52))
            assert any(x==120 and text==expected for x,y,text in r.texts),(track,destination,expected,r.texts)
    r.w32(r.s['lf2p_track'],0);r.w32(r.s['lf2p_row'],2)
    for index in range(24):
        assert r.call('lf2_edit',CTX,0,1,index)==1
        r.texts.clear();r.call('lf2p_render',obj,0x93006000)
        r.call(0x400459f4,0,index<<8,0x930b0000)
        expected=r.string(0x930b0000)
        assert any(x==120 and text==expected for x,y,text in r.texts),(index,expected,r.texts)
    print('ok : noms natifs des 33 destinations + OFF sur six machines ; 24 multiplicateurs musicaux, libellés à gauche des valeurs')

    maximum = (32767, 23, 32767, 127, 6, 32767, 4, 32767)
    for track in range(6):
      r.w32(r.s['lf2p_track'], track)
      r.w32(r.s['lf2p_edit'], 1)
      for field, hi in enumerate(maximum):
        r.w32(r.s['lf2p_row'], field+1)
        before = bytearray(r.u.mem_read(CTX, 1240))
        for _ in range(130): knob(r, -1, thunk=bool(field%2))
        assert value(r, track, field) == 0, (track, field, value(r, track, field))
        for _ in range(130): knob(r, 1, thunk=bool(field%2))
        assert value(r, track, field) == hi, (track, field, value(r, track, field))
        struct.pack_into('>H', before, 192+16*track+2*field, hi<<8 if field in (1, 3, 4, 6) else hi)
        assert bytes(r.u.mem_read(CTX, 1240)) == bytes(before)
    print('ok : édition ColdFire huit champs × six pistes, deux sens, clamps et destination OFF ; phases/buffers et autres champs intacts')

    r.w32(r.s['lf2p_edit'], 0)
    r.w32(r.s['lf2p_row'], 5)
    knob(r, -1); assert r.r32(r.s['lf2p_row']) == 5
    for _ in range(12): knob(r, 1)
    assert r.r32(r.s['lf2p_row']) == 0
    event(r, 32, 16)
    r.call('lf2p_menu_key', obj, EVENT)
    assert r.r32(r.s['lf2p_edit']) == 1
    for pad in range(1, 7):
        r.w32(EVENT+20, pad);r.w32(EVENT+16, 1)
        assert r.call('lf2p_pad', obj+16, EVENT) == 1
        assert r.r32(r.s['lf2p_track']) == pad-1
    for pad in (0, 7, 0xffffffff):
        r.w32(EVENT+20, pad)
        r.call('lf2p_pad', obj+16, EVENT)
        assert r.r32(r.s['lf2p_track']) == 5
    for code in (10, 11):
        event(r, code, 1)
        assert r.call('lf2p_menu_key', obj, EVENT) == 0
        event(r, code, 3)
        assert r.call('lf2p_menu_key', obj, EVENT) == 1
    close_calls=[]
    close_ptr=r.r32(r.r32(obj)+0x28)
    def close_hook(u, addr, size, data):
        sp=u.reg_read(mk.UC_M68K_REG_A7)
        close_calls.append(r.r32(sp+4))
        u.reg_write(mk.UC_M68K_REG_PC,r.r32(sp));u.reg_write(mk.UC_M68K_REG_A7,sp+4)
    handle=r.u.hook_add(UC_HOOK_CODE,close_hook,begin=close_ptr,end=close_ptr)
    event(r, 8, 1);r.call('lf2p_menu_key', obj, EVENT)
    assert not close_calls
    event(r, 8, 0);r.call('lf2p_menu_key', obj, EVENT)
    assert close_calls == [obj]
    r.u.hook_del(handle)
    retained=bytes(r.u.mem_read(CTX,1240))
    r.call('lf2p_dtor1', obj)
    assert not page(r) and obj in r.free
    assert r.r32(r.s['lf2_context']) == CTX and bytes(r.u.mem_read(CTX,1240)) == retained
    assert r.call('lf2p_open') == 1
    assert bytes(r.u.mem_read(CTX,1240)) == retained
    print('ok : navigation/clic, pads sans jeu, transport simple, troisième appui LFO ferme ; destruction OS réelle sans libérer le contexte audio')

    for fail in (1, 2):
        b=make(stock,real=False);b.fail_new=fail
        assert b.call('lf2p_open') == 0 and not page(b) and not b.present
        assert len(b.free) == (fail == 2)
    for reason in ('ipl','context','manager'):
        b=make(stock)
        if reason=='ipl':b.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
        if reason=='context':b.w32(b.s['lf2_context'],0)
        if reason=='manager':b.w32(0x40fe4178,0)
        assert b.call('lf2p_open') == 0 and not page(b) and b.new_count == 0
    print('ok : allocations refusées et gardes IPL/contexte/gestionnaire sans page pendante')
    print('NOTE : interface en émulation, dessin/présentation simulés ; persistance et budget audio matériel combiné restent à finaliser')


if __name__ == '__main__':
    main()
