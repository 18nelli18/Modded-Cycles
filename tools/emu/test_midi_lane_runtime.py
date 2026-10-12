#!/usr/bin/env python3
"""Prototype MIDI secondaire : six voies monophoniques, gates et file bornée.

Exécute l'assembleur ColdFire original en émulation. Aucune intégration à
l'horloge native ni interface ; ports déjà résolus USB/DIN/both (2/3/4).
"""
import argparse
import pathlib
import struct
import subprocess
import tempfile
from unicorn import m68k_const as mk
from unicorn import UC_HOOK_CODE
from test_midi_both import Rig, STACK, STOP
from test_sdvintage import main_os_from_syx

BANK=0x93000000
ENTRY=0x93020000
SIZE=320


def load(rig,conditions=False):
    root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'r.o'),str(root/'tools/machines/midi_lanes/runtime.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'pattern.o'),str(root/'tools/machines/midi_lanes/pattern.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'service.o'),str(root/'tools/machines/midi_lanes/service.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_CONDITIONS=1'] if conditions else []),'-o',str(p/'clock.o'),str(root/'tools/machines/midi_lanes/clock.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'worker.o'),str(root/'tools/machines/midi_lanes/worker.s')],check=True)
        extra=[]
        if conditions:
            subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'history.o'),str(root/'tools/machines/midi_lanes/condition_history.s')],check=True)
            extra=['--defsym=ml_cond_history=0x93019000',str(p/'history.o')]
        subprocess.run([cross+'ld','-Ttext='+hex(ENTRY),'-e','ml_step','-o',str(p/'r.elf'),str(p/'r.o'),str(p/'pattern.o'),str(p/'service.o'),str(p/'clock.o'),str(p/'worker.o'),*extra],check=True)
        subprocess.run([cross+'objcopy','-O','binary','--only-section=.text',str(p/'r.elf'),str(p/'r.bin')],check=True)
        rig.uc.mem_write(ENTRY,(p/'r.bin').read_bytes())
        return {line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output([cross+'nm',str(p/'r.elf')],text=True).splitlines() if len(line.split())==3}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);a=ap.parse_args()
    r=Rig(main_os_from_syx(a.cycles),0);u=r.uc;symbols=load(r)
    instructions=[0];worst={}
    def tick(u,a,s,d):instructions[0]+=1
    u.hook_add(UC_HOOK_CODE,tick)
    def call(name,*args):
        u.reg_write(mk.UC_M68K_REG_SR,0x2505)
        u.reg_write(mk.UC_M68K_REG_A7,STACK)
        saved={reg:0x93600000+reg*4 for reg in [getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]}
        for reg,value in saved.items():u.reg_write(reg,value)
        u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args))
        instructions[0]=0
        u.emu_start(symbols[name],STOP,count=20000)
        worst[name]=max(worst.get(name,0),instructions[0])
        assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
        assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
        assert u.reg_read(mk.UC_M68K_REG_SR)==0x2505
        assert all(u.reg_read(reg)==value for reg,value in saved.items())
        count,head,tail,held=struct.unpack('>4I',u.mem_read(BANK,16))
        assert count+held<=64 and head<64 and tail<64
        return u.reg_read(mk.UC_M68K_REG_D0)
    def reset():u.mem_write(BANK,bytes(SIZE))
    def packet(channel,note,velocity=100,port=4):return ((0x90|channel)<<24)|(note<<16)|(velocity<<8)|port
    def off(p):return p&0xefff00ff
    def take():return call('ml_take',BANK)
    pattern=0x93010000
    u.mem_write(pattern,b'\xa5'*(6*264))
    assert call('ml_init',pattern)==1
    for lane in range(6):
        for field,value in enumerate((1,0,lane+6,2+lane%3,64,2)):
            assert call('ml_config',pattern,lane,field,value)==1
        for step in range(64):
            for field,value in enumerate((36+lane+step%12,50+step,1+step%4,int(step%4==0))):
                assert call('ml_edit',pattern,lane,step,field,value)==1
    expected_pattern=bytes(u.mem_read(pattern,6*264))
    for lane in range(6):
        reset()
        for step in range(64):
            assert call('ml_pattern_tick',BANK,pattern,lane,step)==1
            messages=[]
            while (p:=take()):messages.append(p)
            note=36+lane+step%12
            if step%4==0:
                assert messages==[packet(lane+6,note,50+step,2+lane%3)],(lane,step,messages)
            elif step%4==1:
                assert messages==[off(packet(lane+6,note-1,49+step,2+lane%3))]
            else:assert not messages
        assert bytes(u.mem_read(pattern,6*264))==expected_pattern
    # Slide : note suivante avant note-off, sans changer le gate ni la réserve.
    for lane in range(6):
        reset()
        first,second=packet(lane+6,60),packet(lane+6,64)
        assert call('ml_step',BANK,lane,first,1)==1 and take()==first
        assert call('ml_step',BANK,lane,second,0x80000001)==1
        assert [take(),take(),take()]==[second,off(first),0]
        call('ml_stop',BANK,lane)
        assert take()==off(second) and take()==0
        reset()
        assert call('ml_step',BANK,lane,first,1)==1 and take()==first
        assert call('ml_step',BANK,lane,first,0x80000001)==1
        assert [take(),take(),take()]==[off(first),first,0]
    print('ok : slide six canaux, Note On avant ancien Note Off ; même hauteur retrigger, Stop libère la note')
    # Changer route/canal et muter doit libérer la note sur son ancien port.
    reset();assert call('ml_pattern_tick',BANK,pattern,0,0)==1
    original=take()
    assert call('ml_config',pattern,0,2,15)==1
    assert call('ml_config',pattern,0,3,4)==1
    assert call('ml_config',pattern,0,1,1)==1
    call('ml_pattern_tick',BANK,pattern,0,1)
    assert take()==off(original) and take()==0
    for args in [(6,0,0,60),(0,64,0,60),(0,0,4,1),(0,0,0,128),(0,0,1,0),(0,0,2,65),(0,0,3,4)]:
        before=bytes(u.mem_read(pattern,6*264))
        assert call('ml_edit',pattern,*args)==0
        assert bytes(u.mem_read(pattern,6*264))==before
    for field,value in [(0,2),(1,2),(2,16),(3,1),(4,0),(4,65),(5,7),(6,0)]:
        before=bytes(u.mem_read(pattern,6*264))
        assert call('ml_config',pattern,0,field,value)==0
        assert bytes(u.mem_read(pattern,6*264))==before
    print('ok : édition six voies × 64 pas, réglages indépendants, lecture note/gate et mute avec ancien port ; valeurs invalides sans écriture')
    for channel in range(16):
      for port in (2,3,4):
        reset();p=packet(channel,60,port=port)
        assert call('ml_step',BANK,0,p,3)==1
        assert take()==p and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==0
        assert call('ml_step',BANK,0,0,0)==1 and take()==off(p)
        assert take()==0
    print('ok : 16 canaux × USB/DIN/both, gate trois pas, note-off exact et registres/SR')
    reset();expected=[]
    for lane in range(6):
        p=packet(lane+6,60+lane)
        assert call('ml_step',BANK,lane,p,64)==1;expected.append(p)
    for lane in range(6):call('ml_stop',BANK,lane)
    expected += [off(p) for p in expected]
    assert [take() for _ in expected]==expected and take()==0
    print('ok : six voies indépendantes, canaux 7–12 et Stop de toutes les notes')
    reset();p=packet(0,60)
    assert call('ml_step',BANK,0,p,64)==1
    before=bytes(u.mem_read(BANK,SIZE))
    assert call('ml_step',BANK,1,p,64)==0 and bytes(u.mem_read(BANK,SIZE))==before
    for bad in (packet(0,128),packet(0,60,0),packet(0,60,port=1),packet(0,60,port=5),0x803c6404):
        before=bytes(u.mem_read(BANK,SIZE));assert call('ml_step',BANK,1,bad,2)==0
        assert bytes(u.mem_read(BANK,SIZE))==before
    # Collision répétée : l'ancienne note doit quand même arriver à son Off.
    reset();first,blocked=packet(0,60),packet(0,62)
    assert call('ml_step',BANK,0,first,2)==1
    assert call('ml_step',BANK,1,blocked,64)==1
    assert [take(),take()]==[first,blocked]
    assert call('ml_step',BANK,0,blocked,1)==0 and take()==0
    assert call('ml_step',BANK,0,blocked,1)==0 and take()==off(first)
    assert take()==0
    call('ml_stop',BANK,1);assert take()==off(blocked)
    # Le tick utilise réellement le canal modifié, pas le canal par défaut.
    for channel in range(16):
        reset()
        assert call('ml_config',pattern,0,1,0)==1
        assert call('ml_config',pattern,0,2,channel)==1
        assert call('ml_pattern_tick',BANK,pattern,0,0)==1
        emitted=take();assert emitted>>24==0x90+channel
        call('ml_stop',BANK,0);assert take()==off(emitted) and take()==0
    print('ok : collision ne retarde plus Off, seize canaux édités vérifiés au tick/Stop')
    print('ok : collision canal/note refusée, messages invalides refusés sans modifier les voies')
    reset();accepted=[]
    for tick in range(100):
        lane=tick%6;p=packet(lane+6,40+(tick%60),port=2+lane%3)
        result=call('ml_step',BANK,lane,p,64)
        if result:accepted.append(p)
    for lane in range(6):call('ml_stop',BANK,lane)
    result=[]
    while True:
        p=take()
        if not p:break
        result.append(p)
    active=set();ons=[]
    for p in result:
        key=p&0x0fff00ff
        if p>>28==9:assert key not in active;active.add(key);ons.append(p)
        else:assert key in active;active.remove(key)
    assert not active and ons==accepted and len(result)==2*len(accepted)
    # Dépasser plusieurs fois la fin du ring sans perdre d'événement.
    for tick in range(150):
        p=packet(tick%16,tick%128)
        assert call('ml_step',BANK,0,p,1)==1 and take()==p
        call('ml_stop',BANK,0);assert take()==off(p) and take()==0
    print('ok : saturation sans note-off perdu, refus de nouveaux note-on, 150 tours de lecture/écriture')
    print('Instructions max par API',worst,'; pas une mesure du temps matériel')
    print('NOTE : horloge, page d’édition, stockage et envoi matériel non intégrés')


if __name__=='__main__':main()
