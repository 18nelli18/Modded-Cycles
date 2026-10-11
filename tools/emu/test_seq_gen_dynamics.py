#!/usr/bin/env python3
"""Options et Undo sur le vrai stockage p-lock de l'OS 1.13.

Les setters velocity/p-lock, comptes et indicateurs sont exécutés sans stub.
Seuls allocation, dessin et observateurs externes restent simulés (Rig).
"""
import argparse
import itertools
import json
import random
import struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig, ROOT, OBJ, RAW, EVENT
from test_sdvintage import main_os_from_syx

POOL, PVT, PGET, PSIGNAL, PRAW = 0x93010000,0x93010100,0x93010200,0x93010300,0x93020000

def fixture(stock, base, tweak, index=3, cls=Rig):
    r=cls(stock,base,tweak)
    r.w32(OBJ+44,POOL);r.w32(OBJ+56,index)
    r.w32(POOL,PVT);r.w32(PVT+40,PGET);r.w32(PVT+16,PSIGNAL)
    r.u.mem_write(PGET,b'\x20\x3c'+struct.pack('>I',PRAW)+b'\x4e\x75')
    r.pool_signals=[]
    def observer(a):
        assert a[0]==POOL
        r.pool_signals.append(None if not a[1] else tuple(struct.unpack('>3I',r.u.mem_read(a[1],12))))
        return 0
    r.stubs[PSIGNAL]=observer;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=PSIGNAL,end=PSIGNAL)
    rng=random.Random(813)
    pool=bytearray(6*4385)
    for tr,step in itertools.product(range(6),range(64)):
        n=0
        for param in range(33):
            value=-1 if rng.randrange(4) else rng.randrange(128)*256
            struct.pack_into('>h',pool,tr*4385+step*68+param*2,value)
            n+=value>=0
        struct.pack_into('>H',pool,tr*4385+step*68+66,n)
    for tr,param in itertools.product(range(6),range(33)):
        pool[tr*4385+4352+param]=int(any(struct.unpack_from('>h',pool,tr*4385+step*68+param*2)[0]>=0 for step in range(64)))
    r.u.mem_write(PRAW,bytes(pool));r.pool_original=bytes(pool)
    # Les anciens pas peuvent conserver une note, même quand Generate écrit un repos.
    r.u.mem_write(RAW+580,bytes(rng.randrange(128) for _ in range(64)))
    r.original=bytes(r.u.mem_read(RAW,722))
    r.call('sg_open');r.obj=r.r32(r.s['sg_obj'])
    return r

def preview(r):
    # Vraie chaîne ViewController → vtable générateur → vue transport OS.
    ctl,n1,n2,transport,tvt,fun,capture,empty=(0x93040000+i*256 for i in range(8))
    r.w32(ctl+20,n2);r.w32(ctl+24,n1)
    r.w32(n1+4,n2);r.w32(n1+8,r.obj)
    r.w32(n2+4,ctl+20);r.w32(n2+8,transport)
    r.w32(transport,tvt);r.w32(tvt+8,0x4002439a)
    r.w32(fun,capture);r.w32(fun+8,1);r.w32(fun+12,0x400764ec)
    r.w32(capture,EVENT)
    actions=[]
    def start(a):
        actions.append('play');r.w32(0x40a78874,1);return 0
    def stop(a):
        actions.append('stop');r.w32(0x40a78874,0);return 0
    # Frontières matérielles seulement : le routage et le handler sont réels.
    for addr,fn in {0x400e8684:lambda a:0,0x400d08ce:lambda a:0,
                    0x400cf9a8:lambda a:0x93041000,0x4007faf4:lambda a:0,
                    0x4006ba76:lambda a:0,0x4006ba90:lambda a:0,
                    0x400cfd0e:lambda a:0x93041000,0x4006a938:lambda a:0,
                    0x400542dc:start,0x40055f14:stop}.items():
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.call('sg_action_generate');before=bytes(r.u.mem_read(RAW,722))
    for code,want in ((10,'play'),(11,'stop')):
        r.event(code,1)
        assert r.call(0x4007739e,ctl,fun,empty,empty)&255==1
        assert actions[-1]==want
        assert r.r32(r.s['sg_obj'])==r.obj and r.r32(r.s['sg_undo_valid'])==1
        assert bytes(r.u.mem_read(RAW,722))==before
    r.call('sg_action_undo');assert bytes(r.u.mem_read(RAW,722))==r.original

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    for variant,dep in [('scale-gen','model-tg'),('scale-gen-st','model-tg-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/dynamics/49-{variant}.json').read_text())
        for bits,length in itertools.product(range(8),(1,16,64)):
            r=fixture(stock,base,tweak)
            r.u.mem_write(RAW+713,struct.pack('>H',length))
            before=bytes(r.u.mem_read(RAW,722))
            for i in range(3):r.w32(r.s['sg_options']+i*4,(bits>>i)&1)
            r.call('sg_action_generate')
            assert r.r32(r.s['sg_undo_valid'])==1,(bits,length,r.r32(r.s['sg_error']))
            raw=bytes(r.u.mem_read(RAW,722));pool=bytes(r.u.mem_read(PRAW,6*4385))
            for tr,step in itertools.product(range(6),range(64)):
                active=tr==3 and step<length and struct.unpack_from('>H',raw,step*2)[0]&1
                for param in range(33):
                    o=tr*4385+step*68+param*2
                    if active and ((param==18 and bits&2) or (param==22 and bits&4)):
                        value=struct.unpack_from('>h',pool,o)[0]
                        assert 0<=value<=127*256 and value%256==0
                    else:assert pool[o:o+2]==r.pool_original[o:o+2],(bits,tr,step,param)
                o=tr*4385+step*68
                assert struct.unpack_from('>H',pool,o+66)[0]==sum(struct.unpack_from('>h',pool,o+p*2)[0]>=0 for p in range(33))
            for step in range(64):
                if step<length and struct.unpack_from('>H',raw,step*2)[0]&1 and bits&1:
                    assert 1<=raw[128+step]<=127
                else:assert raw[128+step]==before[128+step]
            # Audition ne ferme pas la page et ne touche pas à la transaction.
            for code in (10,11):
                for flags in (1,16,9):
                    assert r.call('sg_menu_key',r.obj,r.event(code,flags))==0
                    assert r.r32(r.s['sg_obj'])==r.obj and r.r32(r.s['sg_undo_valid'])==1
                assert r.call('sg_menu_key',r.obj,r.event(code,3))==1
            assert r.call('sg_menu_key',r.obj,r.event(9,1))==1
            r.w32(0x40a78874,1);r.call('sg_action_undo')
            assert r.r32(r.s['sg_undo_valid'])==1
            assert bytes(r.u.mem_read(RAW,722))==raw and bytes(r.u.mem_read(PRAW,6*4385))==pool
            r.w32(0x40a78874,0);r.call('sg_action_undo')
            assert r.r32(r.s['sg_undo_valid'])==0
            assert bytes(r.u.mem_read(RAW,722))==before
            assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
        for index in range(6):
            r=fixture(stock,base,tweak,index=index)
            for i in range(3):r.w32(r.s['sg_options']+i*4,1)
            r.call('sg_action_generate');r.call('sg_action_undo')
            assert bytes(r.u.mem_read(RAW,722))==r.original
            assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
        r=fixture(stock,base,tweak)
        preview(r)
        labels=['Scale','Root','Low note','High note','Density %','Rand velocity','Rand decay','Rand pan','Generate','Undo']
        for row in range(10):
            r.w32(r.s['sg_row'],row);r.texts=[];r.rects=[]
            r.call('sg_render',r.obj,0x93006000)
            first=min(6,max(0,row-2))
            assert [t[2] for t in r.texts if t[0]==2]==labels[first:first+4]
            assert all(t[1] in (49,34,19,4) for t in r.texts)
        for row in (5,6,7):
            r.w32(r.s['sg_row'],row);r.click()
            assert r.r32(r.s['sg_options']+(row-5)*4)==1
            r.click();assert r.r32(r.s['sg_options']+(row-5)*4)==0
        # Vraies notifications et copie différée des paramètres directs.
        from test_seq_gen_sync import SyncRig, DEST
        r=fixture(stock,base,tweak,cls=SyncRig)
        r.call(0x4005b642,DEST,RAW,0,0xffffffff,0xffffffff)
        initial=bytes(r.u.mem_read(DEST,722))
        for i in range(3):r.w32(r.s['sg_options']+i*4,1)
        r.call('sg_action_generate');r.drain()
        changed=bytes(r.u.mem_read(RAW,722))
        for getter,newptr in ((PGET,PRAW+0x10000),):
            r.u.mem_write(getter+2,struct.pack('>I',newptr))
            r.u.ctl_remove_cache(getter,getter+8)
            r.call('sg_action_undo')
            assert r.r32(r.s['sg_undo_valid'])==1
            assert bytes(r.u.mem_read(RAW,722))==changed
            r.u.mem_write(getter+2,struct.pack('>I',PRAW))
            r.u.ctl_remove_cache(getter,getter+8)
        # Objet de piste identique, mais nouvelles données : refus sans écriture.
        r.w32(OBJ+16,RAW+0x800);r.u.mem_write(RAW+0x800,changed)
        r.call('sg_action_undo')
        assert r.r32(r.s['sg_undo_valid'])==1
        assert bytes(r.u.mem_read(RAW+0x800,722))==changed
        r.w32(OBJ+16,RAW)
        actual=bytes(r.u.mem_read(DEST,722))
        r.call(0x4005b642,DEST,RAW,0,0xffffffff,0xffffffff)
        assert bytes(r.u.mem_read(DEST,722))==actual
        r.w32(OBJ+56,6);r.call('sg_action_generate')
        assert r.r32(r.s['sg_error'])==1 and r.r32(r.s['sg_undo_valid'])==1
        r.w32(OBJ+56,3);r.call('sg_action_undo');r.drain()
        assert bytes(r.u.mem_read(DEST,722))==initial
        assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
        print('ok :',variant,'24 transactions, 3 options, p-locks OS, Undo exact, transport et 10 lignes')

if __name__=='__main__':main()
