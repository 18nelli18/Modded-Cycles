#!/usr/bin/env python3
"""Preuves de l'extension (notes/54), setters OS réels ; frontières UI simulées."""
import argparse,itertools,json,struct,subprocess
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_seq_gen_dynamics import fixture,PRAW
from test_seq_gen_menu import ROOT,RAW,OBJ,VT,GET,SIGNAL,EVENT
from test_sdvintage import main_os_from_syx

def configure(r,length=16,target=0,mutation=100,euclid=0,hits=4,rotation=0):
    raw=bytearray(r.original)
    for i in range(64):
        struct.pack_into('>H',raw,i*2,0x200|(1 if i%3==0 else 2))
        raw[580+i]=48+i%12
    struct.pack_into('>H',raw,713,length)
    r.u.mem_write(RAW,bytes(raw));r.before=bytes(raw)
    r.u.mem_write(PRAW,r.pool_original)
    for i in range(3):r.w32(r.s['sg_options']+i*4,1)
    values=[40,80,12,36,48,80,target,mutation,euclid,hits,rotation,25]
    r.u.mem_write(r.s['sg_advanced'],struct.pack('>12I',*values))
    r.w32(r.s['sg_config']+4,50);r.w32(r.s['sg_config']+24,0x12345678)
    r.w32(r.s['sg_intro'],0)


def sequence(r):
    for length in (1,7,16,31,64):
        for target,mutation in itertools.product(range(3),(0,25,100)):
            configure(r,length,target,mutation)
            r.call('sg_action_generate');assert r.r32(r.s['sg_error'])==0
            after=bytes(r.u.mem_read(RAW,722));pool=bytes(r.u.mem_read(PRAW,6*4385))
            assert after[2*length:128]==r.before[2*length:128]
            if not mutation:assert after==r.before and pool==r.pool_original
            for i in range(length):
                beforeflag=struct.unpack_from('>H',r.before,i*2)[0]
                flag=struct.unpack_from('>H',after,i*2)[0]
                if target==2:assert flag==beforeflag
                if target==1 and flag&1 and beforeflag&1:assert after[580+i]==r.before[580+i]
                if flag&1:
                    assert 48<=after[580+i]<=72,(length,target,mutation,i,after[580+i],r.s)
                    if after[128+i]!=r.before[128+i]:assert 40<=after[128+i]<=80
                    for p,lo,hi in [(18,12,36),(22,48,80)]:
                        o=3*4385+i*68+p*2
                        if pool[o:o+2]!=r.pool_original[o:o+2]:assert lo*256<=struct.unpack_from('>h',pool,o)[0]<=hi*256
            r.call('sg_action_undo')
            assert bytes(r.u.mem_read(RAW,722))==r.before
            assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
    for length in (1,7,16,31,64):
        for hits in sorted({0,1,length//3,length,length+8}):
            for rotation in (0,1,length-1):
                configure(r,length,0,100,1,hits,rotation)
                r.call('sg_action_generate');assert r.r32(r.s['sg_error'])==0
                raw=bytes(r.u.mem_read(RAW,722));n=min(hits,length)
                flags=[struct.unpack_from('>H',raw,i*2)[0]&1 for i in range(length)]
                assert flags==[int(((i-rotation)%length*n)%length<n) for i in range(length)],(length,hits,rotation,flags)
                assert sum(flags)==n
                r.call('sg_action_undo');assert bytes(r.u.mem_read(RAW,722))==r.before
    print('ok : modes Both/Rhythm/Notes, mutation 0/25/100, plages, Euclid exact/rotation, Undo')


def sound(r):
    from test_seq_gen_menu import HEAP
    # Getter sélection courant : vrai calcul de handle, seul index UI simulé.
    kit=0x93005000;handle=kit+212;vt=0x93060000;raw=0x93061000;get=0x93062000;signal=0x93063000
    r.w32(handle,vt);r.w32(vt+40,get);r.w32(vt+16,signal)
    r.u.mem_write(get,b'\x20\x3c'+struct.pack('>I',raw)+b'\x4e\x75')
    r.stubs[0x40012412]=lambda a:0
    r.stubs[signal]=lambda a:0
    for addr in (0x40012412,signal):r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.call(0x4005a274)
    for machine in range(6):
        for amount in (0,25,100):
            before=bytearray(100)
            for i in range(33):struct.pack_into('>H',before,20+2*i,64*256)
            before[38]=machine
            r.u.mem_write(raw,bytes(before));r.w32(r.s['sg_advanced']+44,amount)
            r.w32(r.s['sg_sound_valid'],0);r.call('sg_sound_generate')
            assert r.r32(r.s['sg_error'])==0,(machine,amount)
            after=bytes(r.u.mem_read(raw,100))
            for i in range(100):
                if i not in {20+2*p+j for p in (11,12,13,14,18) for j in (0,1)}:assert after[i]==before[i]
            if not amount:assert after==bytes(before)
            else:
                assert r.r32(r.s['sg_sound_valid'])==1
                r.call('sg_sound_undo');assert bytes(r.u.mem_read(raw,100))==bytes(before)
    print('ok : Random sound, six machines, intensité, vrai setter OS, Undo indépendant')


def menu(r):
    # Toutes les lignes restent dans les marges du menu défilant.
    labels=['Scale','Root','Low note','High note','Density %','Rand velocity',
            'Vel min','Vel max','Rand decay','Decay min','Decay max','Rand pan',
            'Pan min','Pan max','Regenerate','Mutation %','Rhythm','Euclid hits',
            'Rotation','Sound amount %','Generate','Undo','Random sound','Undo sound']
    r.w32(r.s['sg_intro'],0)
    for row in range(24):
        for editing in (0,1):
            r.w32(r.s['sg_row'],row);r.w32(r.s['sg_edit'],editing)
            r.texts.clear();r.rects.clear()
            r.call('sg_render',r.obj,0x93006000)
            first=min(20,max(0,row-2))
            shown=[t for t in r.texts if t[0]==2]
            assert [t[2] for t in shown]==labels[first:first+4],(row,r.texts)
            assert [t[1] for t in shown]==[49,34,19,4]
            assert all(4<=t[1]<=49 for t in r.texts)
    r.w32(r.s['sg_intro'],1);r.texts.clear();r.rects.clear()
    r.call('sg_render',r.obj,0x93006000)
    assert r.texts==[(64,37,'SEQ.'),(64,21,'GEN.')],r.texts
    assert r.rects[-1][1:]==(29,10,98,53,0xffffffff),r.rects
    # Le clavier de transport traverse la page ; Undo reste disponible.
    from test_seq_gen_dynamics import preview
    configure(r)
    r.original=r.before
    preview(r)
    print('ok : 24 lignes, marges, cartouche deux lignes, Play/Stop et Undo conservé')


def pads(r):
    # Vrai toggle, getter et setter du bitmap OS ; observateurs/MIDI simulés.
    kit=0x93005000;handle=kit+48;vt=0x93070000;raw=0x93071000;get=0x93072000;signal=0x93073000
    r.w32(handle,vt);r.w32(vt+40,get);r.w32(vt+16,signal)
    r.u.mem_write(get,b'\x20\x3c'+struct.pack('>I',raw)+b'\x4e\x75')
    events=[]
    def observer(a):
        assert a[0]==handle
        assert r.r32(a[1])==0x400fe748
        events.append(r.r32(a[1]+4))
        return 0
    for addr,fn in {signal:observer,0x4000f208:lambda a:0x93074000,0x4000cfcc:lambda a:0,0x40016e90:lambda a:0}.items():
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.w32(raw+20,0)
    r.w32(0x40a78874,1)
    for round in range(2):
        for track in range(6):
            before=r.r32(raw+20)
            r.call('sg_menu_key',r.obj,r.event(1,16))
            assert r.r32(r.s['sg_func'])==0
            r.event(0,1);r.w32(EVENT+20,track+1)
            assert r.call('sg_pad',r.obj+16,EVENT)==0
            assert r.r32(raw+20)==before
            r.call('sg_menu_key',r.obj,r.event(1,1))
            assert r.r32(r.s['sg_func'])==1
            r.event(0,1);r.w32(EVENT+20,track+1)
            try: result=r.call('sg_pad',r.obj+16,EVENT)
            except Exception:
                print('PC mute',hex(r.u.reg_read(mk.UC_M68K_REG_PC)));raise
            assert result==1
            assert r.r32(raw+20)==before^(1<<track)
            count=len(events)
            assert r.call('sg_pad',r.obj+16,EVENT)==1
            assert len(events)==count and r.r32(raw+20)==before^(1<<track)
            r.call('sg_menu_key',r.obj,r.event(1,16))
            r.event(0,0);r.w32(EVENT+20,track+1)
            assert r.call('sg_pad',r.obj+16,EVENT)==1
            assert r.r32(r.s['sg_pads'])==0
            assert r.call('sg_pad',r.obj+16,EVENT)==0
    assert events==list(range(6))*2 and r.r32(raw+20)==0
    r.w32(0x40a78874,0)
    print('ok : vrai bitmap mute stock, six pistes mute/unmute, toggle unique, relâchement FUNC avant pad')


def shortcut(r):
    r.call('sg_dtor0',r.obj)
    r.call(0x4007240c,r.event(13,1,100))
    event=r.event(2,1,101)
    assert r.call(0x4007240c,event)==0
    obj=r.r32(r.s['sg_obj']);assert obj
    assert r.r32(r.s['sg_row'])==19 and r.r32(r.s['sg_intro'])==0
    count=len(r.present)
    for _ in range(3):assert r.call(0x4007240c,event)==0
    assert len(r.present)==count
    r.call(0x4007240c,r.event(13,16,102))
    event=r.event(2,16,103)
    for _ in range(3):assert r.call(0x4007240c,event)==0
    r.call('sg_dtor0',obj)
    # SETTINGS + PAGE garde son entrée au début du générateur et le cartouche.
    r.call(0x4007240c,r.event(13,1,104))
    assert r.call(0x4007240c,r.event(15,1,105))==0
    r.obj=r.r32(r.s['sg_obj'])
    assert r.obj and r.r32(r.s['sg_row'])==0 and r.r32(r.s['sg_intro'])==1
    r.call(0x4007240c,r.event(15,16,106))
    r.call(0x4007240c,r.event(13,16,107))
    print('ok : vrais lecteurs SETTINGS + TRACK/PAGE, ouvertures distinctes, lectures répétées, relâchements consommés')


def timer(r):
    # L'horloge audio est lue ; le hook reste dans la tâche UI.
    tg=ROOT.parent/'model-tg/build/_b.elf'
    syms={line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output([str(ROOT.parent/'toolchain/bin/m68k-elf-nm'),str(tg)],text=True).splitlines() if len(line.split())==3}
    led,clock=syms['led_hook'],syms['blk_clk']
    calls=[]
    r.stubs[led]=lambda a:calls.append('led') or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=led,end=led)
    redraw=[]
    r.stubs[0x40076082]=lambda a:redraw.append(a[0]) or 0
    for start in (100,0xffffff00):
        r.w32(r.s['sg_intro_time'],start);r.w32(r.s['sg_intro'],1)
        for delta,want in ((0,1),(1499,1),(1500,0),(2000,0)):
            r.w32(clock,start+delta)
            r.call('sg_tick')
            assert r.r32(r.s['sg_intro'])==want,(start,delta)
    assert redraw==[r.obj,r.obj] and len(calls)==8
    print('ok : cartouche 1500 blocs = 1 seconde, débordement horloge, redraw unique, hook Model-TG conservé')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    for variant,dep in [('scale-gen','model-tg'),('scale-gen-st','model-tg-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/advanced/49-{variant}.json').read_text())
        r=fixture(stock,base,tweak)
        sequence(r)
        menu(r)
        pads(r)
        timer(r)
        shortcut(r)
        if dep=='model-tg':sound(r)
        print('ok :',variant)
if __name__=='__main__':main()
