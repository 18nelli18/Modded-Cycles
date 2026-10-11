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
        for name in ('update', 'mix', 'dispatch', 'edit', 'init', 'prepare', 'launch', 'key', 'page'):
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
        assert len(r.texts) == 7 and r.texts[0][2] == 'LFO 2'
        assert all(0 <= x <= 127 and 0 <= y <= 49 for x, y, _ in r.texts)
        assert sorted(set(y for _, y, _ in r.texts)) == [7, 21, 35, 49]
        assert len(r.rects) == 2
        for _, x1, y1, x2, y2, mode in r.rects:
            assert 0 <= x1 <= x2 <= 127 and 0 <= y1 <= y2 <= 63
        assert r.rects[-1][1] == (64 if editing else 0)
    print('ok : six pistes × neuf positions × édition/navigation, titre et trois lignes, coordonnées sans débordement')

    r.w32(r.s['lf2p_track'],0)
    for field,names in ((4,('TRI','SIN','SQR','SAW','EXP','RMP','RND')),
                        (6,('FRE','TRG','HLD','ONE','HLF'))):
        for index,name in enumerate(names):
            assert r.call('lf2_edit',CTX,0,field,index)==1
            r.w32(r.s['lf2p_row'],field+1)
            r.texts.clear()
            r.call('lf2p_render',obj,0x93006000)
            assert any(x==125 and text==name for x,y,text in r.texts)
    print('ok : noms des sept formes et cinq modes lus dans les tables natives')

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
    r.w32(r.s['lf2p_row'], 0)
    knob(r, -1); assert r.r32(r.s['lf2p_row']) == 0
    for _ in range(12): knob(r, 1)
    assert r.r32(r.s['lf2p_row']) == 8
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
    print('NOTE : interface en émulation, dessin/présentation simulés ; libellés destinations/multiplicateurs, persistance, budget audio combiné et catalogue flasher restent à finaliser')


if __name__ == '__main__':
    main()
