#!/usr/bin/env python3
"""Slides CC : cible marquée comme Model-TG, wrap, popup et isolation des voies."""
import argparse,pathlib,subprocess,tempfile
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'plan.o'),str(root/'tools/machines/midi_lanes/knob_cc_slide_plan.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'arm.o'),str(root/'tools/machines/midi_lanes/knob_cc_slide_arm.s')],check=True)
        more=[]
        for name in ('knob_cc_slide_tick','knob_cc_slide_value'):
            obj=p/(name+'.o');more.append(str(obj))
            subprocess.run([cross+'as','-march=cfv4e','-o',str(obj),str(root/'tools/machines/midi_lanes'/(name+'.s'))],check=True)
        (p/'link.ld').write_text('mlkc_queue = 0x9306b500; mlkcq_put = 0x9306b108; mlkcq_owner = 0x9306b310; ml_play_pattern = 0x9306b314; ml_clock_state = 0x9306b318; mlkc_state = 0x9306b200; TG_blk_clk = 0x9306b300; mlkc_locks_for = 0x9306b104; TG_show_popup = 0x9306b100; SECTIONS { .text 0x93050000 : { *(.text*) *(.data*) } }')
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','mlkc_slide_find','-o',str(p/'plan.elf'),str(p/'plan.o'),str(p/'arm.o'),*more],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'plan.elf'),str(p/'plan.bin')],check=True)
        code=(p/'plan.bin').read_bytes();syms=symbols(cross,p/'plan.elf')
    r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}});r.s=syms;r.u.mem_write(0x93050000,code)
    pat=0x93070000;popups=[]
    r.stubs[0x9306b100]=lambda args:popups.append(r.string(args[0])) or 0
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9306b100,end=0x9306b100)
    for lane in range(6):
        track=pat+264*lane;r.u.mem_write(track,bytes((1,0,lane+6,4,16,2,0,0))+bytes(256))
        step=lambda i:track+8+4*i
        r.u.mem_write(step(0),bytes((72,100,1,1)))
        r.u.mem_write(step(4),bytes((72,100,1,3)))
        r.u.mem_write(step(2),bytes((72,100,1,2)))
        before=bytes(r.u.mem_read(pat,1584))
        assert r.call('mlkc_slide_find',pat,lane,0)==0x404
        assert before==bytes(r.u.mem_read(pat,1584))
        r.u.mem_write(step(3)+3,b'\x01')
        assert r.call('mlkc_slide_find',pat,lane,0)==0xffffffff
        r.u.mem_write(step(3)+3,b'\x00');r.u.mem_write(step(0)+3,b'\x03')
        assert r.call('mlkc_slide_find',pat,lane,14)==0x200
        r.u.mem_write(track+4,b'\x01')
        assert r.call('mlkc_slide_find',pat,lane,0)==0xffffffff
        assert r.call('mlkc_slide_find',pat,lane,1)==0xffffffff
        r.u.mem_write(track+4,b'\x10')
        for flags,want in ((0,3),(1,3),(3,1),(2,3),(0xfc,0xff),(0xff,0xfd)):
            r.u.mem_write(step(5)+3,bytes((flags,)))
            before=bytes(r.u.mem_read(pat,1584))
            assert r.call('mlkc_slide_toggle',step(5))==want
            after=bytearray(before);after[264*lane+8+4*5+3]=want
            if not flags&1:after[264*lane+8+4*5:264*lane+8+4*5+3]=bytes((72,100,1))
            assert bytes(r.u.mem_read(pat,1584))==bytes(after)
            assert popups[-1]==('Slide on' if want&2 else 'Slide off')
    # Armement à120BPM : quatre doubles croches =750blocs audio.
    locks=0x93078000;r.u.mem_write(locks,b'\xff'*9216)
    r.stubs[0x9306b104]=lambda args:locks
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9306b104,end=0x9306b104)
    r.w32(0x40149310,14400);r.w32(0x9306b300,100)
    r.u.mem_write(0x9306b200,bytes((255,64))*72)
    for lane in range(6):
        track=pat+264*lane
        r.u.mem_write(track,bytes((1,0,lane+6,4,16,2,0,0))+bytes(256))
        r.u.mem_write(track+8,bytes((72,100,1,2))) # source trigless
        r.u.mem_write(track+8+4*4,bytes((72,100,1,3)))
        maps=0x9306b200+24*lane
        r.u.mem_write(maps,bytes((74,64,71,80,72,64,255,64,7,64,0,64)))
        def lock(step,knob,cc,value):r.u.mem_write(locks+1536*lane+24*step+2*knob,bytes((cc,value)))
        lock(0,0,74,20);lock(4,0,74,100)
        lock(4,1,71,10);lock(0,2,73,30);lock(4,2,72,100)
        lock(0,5,0,0);lock(4,5,0,127)
        before=bytes(r.u.mem_read(pat,1584))+bytes(r.u.mem_read(locks,9216))+bytes(r.u.mem_read(0x9306b200,144))
        r.call('mlkc_slide_arm',pat,lane,0)
        state=syms['mlkc_slide_states']+64*lane
        assert r.r32(state)==pat and r.r32(state+4)==100 and r.r32(state+8)==750
        assert r.r32(state+12)==((lane+6)<<24)|(4<<16)|0x23
        assert bytes(r.u.mem_read(state+16,4))==bytes((74,20,100,20))
        assert bytes(r.u.mem_read(state+20,4))==bytes((71,80,10,80))
        assert bytes(r.u.mem_read(state+36,4))==bytes((0,0,127,0))
        assert before==bytes(r.u.mem_read(pat,1584))+bytes(r.u.mem_read(locks,9216))+bytes(r.u.mem_read(0x9306b200,144))
    # Le producteur IRQ ne fait qu'un put borné, sans API de sortie physique.
    clock=0x9306b400;r.w32(clock,1)
    r.w32(0x9306b310,pat);r.w32(0x9306b314,pat);r.w32(0x9306b318,clock)
    queued=[]
    r.stubs[0x9306b108]=lambda args:queued.append(tuple(args[:6])) or 1
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x9306b108,end=0x9306b108)
    state=syms['mlkc_slide_states']
    # Seulement le premier CC de la première voie pour mesurer une rampe.
    for lane in range(6):r.w32(state+64*lane+12,((lane+6)<<24)|(4<<16)|(1 if lane==0 else 0))
    for now in range(101,854):
        r.w32(0x9306b300,now)
        before=len(queued);r.call('mlkc_slide_tick')
        assert len(queued)-before<=1
        if len(queued)>before:
            if 'last_put' in locals():assert now-last_put>=3
            last_put=now
    assert queued and all(q[:4]==(0x9306b500,0,6,74) and q[5]==4 for q in queued)
    values=[q[4] for q in queued]
    assert values==sorted(values) and values[-1]==100 and len(set(values))>60
    assert not (r.r32(state+12)&1)
    # Canal modifié : abandonner, ne jamais détourner la rampe vers le nouveau canal.
    r.w32(0x9306b300,100);r.call('mlkc_slide_arm',pat,0,0)
    r.u.mem_write(pat+2,b'\x07');before=len(queued)
    r.w32(0x9306b300,500)
    for _ in range(3):r.call('mlkc_slide_tick')
    assert len(queued)==before and r.r32(state+12)==0
    r.u.mem_write(pat+2,b'\x06')
    r.call('mlkc_slide_arm',pat,0,0);r.w32(clock,0)
    r.call('mlkc_slide_tick');assert all(r.r32(state+64*i+12)==0 for i in range(6))
    print('ok : rampe CC monotone et endpoint, au plus un put par appel, route modifiée/Stop annulent sans émission')
    r.call('mlkc_slide_cancel')
    assert all(r.r32(syms['mlkc_slide_states']+64*i+12)==0 for i in range(6))
    r.w32(0x40149310,0);r.call('mlkc_slide_arm',pat,0,0)
    assert r.r32(syms['mlkc_slide_states']+12)==0
    print('ok : armement750blocs à120BPM, source trigless, valeurs lock/base, CC0, destinations différentes exclues, six voies isolées, tempo nul refusé')
    for lane,stepnum in ((6,0),(0,64),(0,0xffffffff)):
        assert r.call('mlkc_slide_find',pat,lane,stepnum)==0xffffffff
    print('ok : six voies, cible slide suivante, arrêt sur note normale, trigless source, wrap, limites, popups Model-TG exacts et microtiming préservé')
    print('Prototype : raccordement au séquenceur et cadence CC encore à intégrer.')

if __name__=='__main__':main()
