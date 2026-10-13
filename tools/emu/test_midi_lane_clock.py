#!/usr/bin/env python3
"""Note 57 : horloge privée des six voies MIDI avec vraie heure musicale OS.

Exécute le fragment natif 0x400593ec..0x40059490 qui avance l'heure audio,
puis l'ordonnanceur ColdFire. Pas de hook matériel ni de sortie physique.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_midi_both import Rig, STACK, STOP
from test_midi_lane_runtime import load, BANK, SIZE
from test_sdvintage import main_os_from_syx

PAT, STATE = 0x93010000, 0x93011000
DURATIONS = (21600000,10800000,5400000,3600000,2700000,1800000,1350000)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True)
    ap.add_argument('--conditions',action='store_true')
    ap.add_argument('--live-record',action='store_true')
    args=ap.parse_args()
    r=Rig(main_os_from_syx(args.cycles),0);u=r.uc;symbols=load(r,conditions=args.conditions,live_record=args.live_record)
    u.mem_map(0x80000000,0x20000)
    counts=[0];worst={}
    def tick(u,a,s,d):counts[0]+=1
    u.hook_add(UC_HOOK_CODE,tick)
    def call(name,*args):
        regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]
        regs += [getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
        saved={reg:0x93600000+reg*4 for reg in regs}
        for reg,value in saved.items():u.reg_write(reg,value)
        u.reg_write(mk.UC_M68K_REG_SR,0x2505)
        u.reg_write(mk.UC_M68K_REG_A7,STACK)
        u.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*args))
        counts[0]=0
        u.emu_start(symbols[name],STOP,count=20000)
        worst[name]=max(worst.get(name,0),counts[0])
        assert u.reg_read(mk.UC_M68K_REG_PC)==STOP
        assert u.reg_read(mk.UC_M68K_REG_A7)==STACK+4
        if not name.startswith('ml_cond_'):assert u.reg_read(mk.UC_M68K_REG_SR)==0x2505
        else:assert u.reg_read(mk.UC_M68K_REG_SR)&0xffe0==0x2500
        assert all(u.reg_read(reg)==value for reg,value in saved.items())
        return u.reg_read(mk.UC_M68K_REG_D0)
    def drain():
        result=[]
        while (p:=call('ml_take',BANK)):result.append(p)
        return result
    def reset(length=16,speed=2):
        u.mem_write(BANK,bytes(SIZE));u.mem_write(STATE,bytes(52))
        assert call('ml_init',PAT)==1
        for lane in range(6):
            assert call('ml_config',PAT,lane,4,length)==1
            assert call('ml_config',PAT,lane,5,speed)==1
            for step in range(64):
                assert call('ml_edit',PAT,lane,step,0,36+step)==1
                assert call('ml_edit',PAT,lane,step,3,1)==1
    def clock(now,playing=1):return call('ml_clock',BANK,PAT,STATE,now&0xffffffff,playing)
    def native_advance(tempo):
        before=struct.unpack('>I',u.mem_read(0x8000184c,4))[0]
        u.mem_write(0x40149310,struct.pack('>I',tempo))
        u.mem_write(0x80001854,struct.pack('>I',0x7fffffff))
        u.reg_write(mk.UC_M68K_REG_D0,0)
        u.emu_start(0x400593ec,0x40059490,count=100)
        assert u.reg_read(mk.UC_M68K_REG_PC)==0x40059490
        now=struct.unpack('>I',u.mem_read(0x8000184c,4))[0]
        assert now==(before+2*tempo)&0xffffffff
        return now

    if args.live_record:
        for fraction in (1,16,32,63):
            reset(length=2)
            assert call('ml_edit',PAT,0,1,3,1|(fraction<<2))==1
            duration=DURATIONS[2]
            assert clock(0)==6;drain()
            assert clock(duration)==5;drain()
            due=duration+(duration>>6)*fraction
            assert clock(due-1)==0;drain()
            assert clock(due)==1
            assert len([p for p in drain() if p>>28==9])==1
            assert clock(2*duration)==6;drain()
        print('ok : microtiming 1/64 indépendant par voie, émission retardée sans dérive au wrap')

    if args.conditions:
        hist=symbols['ml_cond_history']
        reset(length=2)
        u.mem_write(hist,b'\xff'*96)
        assert clock(0)==6;drain()
        assert bytes(u.mem_read(hist,96))==bytes(96)
        call('ml_cond_remember',hist,0,0,1)
        assert clock(DURATIONS[2],2)==0;drain()
        assert struct.unpack('>I',u.mem_read(hist,4))[0]==1
        assert clock(DURATIONS[2],1)==6;drain()
        assert struct.unpack('>I',u.mem_read(hist+4,4))[0]==1
        assert u.mem_read(hist+8,8)==bytes((0,1,1,1,1,1,1,1))
        assert clock(DURATIONS[2],0)==0;drain()
        assert clock(DURATIONS[2]*2,1)==6;drain()
        assert bytes(u.mem_read(hist,96))==bytes(96)
        reset()
        for lane in range(6):call('ml_config',PAT,lane,4,lane+1)
        assert clock(0)==6;drain()
        for lane in range(6):
            first=struct.unpack('>I',u.mem_read(hist+lane*16+4,4))[0]
            assert first==int(lane==0)
        print('ok : historique raccordé au vrai clock, Start réinitialise, pause conserve, wraps par voie indépendants')

    for speed,duration in enumerate(DURATIONS):
      reset(length=5,speed=speed)
      start=0xfffffff0
      for i in range(20):
        now=(start+i*duration)&0xffffffff
        assert clock(now)==6
        messages=drain()
        ons=[p for p in messages if p>>28==9]
        offs=[p for p in messages if p>>28==8]
        assert [p>>24 for p in ons]==list(range(0x96,0x9c))
        assert all((p>>16)&127==36+i%5 for p in ons)
        assert len(offs)==(6 if i else 0)
        assert clock(now)==0 and not drain()
        assert clock(now+duration-1)==0 and not drain()
      assert clock(now,0)==0 and len(drain())==6
      assert clock(now,0)==0 and not drain()
    print('ok : sept vitesses, longueurs indépendantes, rebouclage 32 bits, pas uniques et Stop sans note pendante')

    reset()
    for lane in range(6):
        call('ml_config',PAT,lane,5,lane)
        call('ml_config',PAT,lane,4,lane+1)
    pattern_before=bytes(u.mem_read(PAT,1584))
    for now in range(0,43200000+1,450000):
        due=[lane for lane in range(6) if now%DURATIONS[lane]==0]
        assert clock(now)==len(due)
        ons=[p for p in drain() if p>>28==9]
        assert [p>>24 for p in ons]==[0x96+lane for lane in due]
        assert [(p>>16)&127 for p in ons]==[36+(now//DURATIONS[lane])%(lane+1) for lane in due]
    assert bytes(u.mem_read(PAT,1584))==pattern_before
    print('ok : six vitesses et longueurs distinctes simultanées, données des patterns inchangées')

    # Pause : relâcher les notes, garder le prochain pas et son délai restant.
    for start in (0,0xfffffff0):
      reset()
      for lane in range(6):call('ml_config',PAT,lane,5,lane)
      assert clock(start)==6
      drain()
      elapsed=500000
      assert clock(start+elapsed,2)==0
      assert len(drain())==6
      paused=bytes(u.mem_read(STATE,52))
      assert struct.unpack('>I',paused[:4])[0]==2
      for lane in range(6):
          assert struct.unpack('>II',paused[4+8*lane:12+8*lane])==(DURATIONS[lane]-elapsed,1)
      assert clock(start+99999999,2)==0 and not drain()
      assert bytes(u.mem_read(STATE,52))==paused
      resumed=(start+100000000)&0xffffffff
      assert clock(resumed)==0 and not drain()
      for lane in reversed(range(6)):
          due=resumed+DURATIONS[lane]-elapsed
          # Les autres voies peuvent avancer ; vérifier la voie visée seulement.
          clock(due-1)
          assert not [p for p in drain() if p>>24==0x96+lane]
          clock(due)
          assert [((p>>16)&127) for p in drain() if p>>24==0x96+lane]==[37]
      clock(resumed+21600000,2);drain()
      assert clock(resumed+21600001,0)==0 and not drain()
      assert clock(resumed+21600002)==6
      assert all((p>>16)&127==36 for p in drain() if p>>28==9)
    print('ok : Pause/Continue conserve six délais/vitesses et prochains pas, relâche les notes une fois ; Stop réinitialise, y compris au rebouclage 32 bits')

    reset(length=16)
    for lane in range(6):call('ml_config',PAT,lane,4,lane+1)
    for i in range(20):
        assert clock(i*5400000)==6
        ons=[p for p in drain() if p>>28==9]
        assert [(p>>16)&127 for p in ons]==[36+i%(lane+1) for lane in range(6)]
    # Mute immédiat sans interrompre la phase des pas.
    call('ml_config',PAT,5,1,1)
    assert clock(19*5400000+1)==0
    assert drain()==[0x8b256404 & 0xefff00ff]  # note 37 du pas précédent, canal 12
    clock(20*5400000);drain()
    call('ml_config',PAT,5,1,0)
    assert clock(20*5400000+1)==0 and not drain()
    clock(21*5400000)
    assert [((p>>16)&127) for p in drain() if p>>24==0x9b]==[39]
    # MIDI OUT utilise enabled, même continuité sans changer mute (+1).
    call('ml_config',PAT,5,0,0)
    clock(21*5400000+1);drain()
    clock(22*5400000);drain()
    call('ml_config',PAT,5,0,1)
    assert clock(22*5400000+1)==0 and not drain()
    clock(23*5400000)
    assert [((p>>16)&127) for p in drain() if p>>24==0x9b]==[41]
    assert bytes(u.mem_read(PAT+5*264+1,1))==b'\x00'
    # Raccourcir un pattern normalise le prochain pas, sans le dupliquer.
    call('ml_config',PAT,5,4,2)
    clock(24*5400000);drain()
    clock(25*5400000)
    assert [((p>>16)&127) for p in drain() if p>>24==0x9b]==[37]
    # Appel tardif : aucun rattrapage non borné ni répétition au même timestamp.
    assert clock(200*5400000)==6
    drain();assert clock(200*5400000)==0 and not drain()
    print('ok : six longueurs distinctes, mute immédiat/phase conservée, changement de longueur et rattrapage borné')

    for bpm in (30,120,300,546):
        reset(length=16)
        u.mem_write(0x8000184c,bytes(4))
        clock(0);drain()
        emitted=[0]
        for block in range(1, (21600000*4)//(bpm*240)+2):
            now=native_advance(bpm*120)
            clock(now)
            ons=[p for p in drain() if p>>28==9]
            if ons:
                assert len(ons)==6
                emitted.append(now)
            if now>=21600000*4:break
        assert len(emitted)==17,(bpm,emitted)
        assert all(i*5400000 <= t < i*5400000+bpm*240 for i,t in enumerate(emitted))
    print('ok : vraie avance musicale OS à 30/120/300/546 BPM, seize pas par mesure, erreur bornée à un bloc audio')
    print('Instructions max observées',worst,'; pas une mesure matérielle')
    print('NOTE : horloge OS exécutée ; détection transport, hook, charge audio et transmission physique restent à valider')


if __name__=='__main__':main()
