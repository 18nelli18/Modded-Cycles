#!/usr/bin/env python3
"""Preuve du staging privé, frontière anticipée native, annulation et Undo.

Setters notes/velocity/p-lock et conversion au format audio OS exécutés.
Allocations, notifications UI et périphériques simulés ; pas de boot complet.
Le compteur d'instructions borne le travail, pas la durée sur matériel.
"""
import argparse,json,struct
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID
from unicorn import m68k_const as mk
from test_seq_gen_dynamics import fixture,POOL,PRAW
from test_seq_gen_menu import Rig,ROOT,OBJ,RAW,STACK
from test_sdvintage import main_os_from_syx
PAT=0x406fa040
RIG=Rig

def setup(stock,base,tweak,index=3,length=16):
    r=fixture(stock,base,tweak,index=index,cls=RIG)
    # État déterministe : pas de conditions/retrig, notes et microtiming valides.
    raw=bytearray(722)
    raw[128:192]=bytes([90]*64);raw[192:580]=bytes([255]*388)
    raw[580:644]=bytes([60]*64);raw[644:708]=bytes(64)
    raw[713:715]=struct.pack('>H',length)
    r.u.mem_write(RAW,bytes(raw));r.original=bytes(raw)
    r.w32(OBJ+16,RAW);r.w32(POOL+16,PRAW)
    r.w32(OBJ+32,0x931a0004+index*722) # sauvegarde, distincte du lecteur
    r.u.mem_write(PAT,bytes(30710))
    for tr in range(6):r.u.mem_write(PAT+tr*722,bytes(raw))
    r.raw=RAW;r.praw=PRAW
    for addr,fn in {0x400cfd0e:lambda a:0x93005000,0x4006a96c:lambda a:0}.items():
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.u.mem_write(PAT+4332,r.pool_original)
    r.u.mem_write(PAT+30662,struct.pack('>H',length))
    r.u.mem_write(PAT+30668,b'\x02')
    r.w32(0x40a7887c,PAT);r.w32(0x40a78884,PAT)
    r.w32(0x40a78638,1);r.w32(0x40a7863c,PAT)
    r.w32(0x40a7883c,1);r.w32(0x40a78874,1)
    r.w32(0x40a78840,length-1)
    for tr in range(6):r.w32(0x40a78848+tr*4,1)
    r.u.mem_write(0x40a788b4,b'\x02')
    r.initial_audio=bytes(r.u.mem_read(PAT,30710))
    r.signals.clear();r.pool_signals.clear()
    r.count=0
    def count(u,a,s,d):r.count+=1
    r.u.hook_add(UC_HOOK_CODE,count)
    return r

def boundary(r,step=0,phase=0,tick=0):
    r.w32(0x40a78630,tick)
    index=r.r32(r.s['sg_q_index'])
    r.u.mem_write(0x40a78860+index,bytes([step]))
    r.u.mem_write(0x40a78866+index,bytes([phase]))
    regs=[mk.UC_M68K_REG_D0+i for i in range(8)]+[mk.UC_M68K_REG_A0+i for i in range(7)]
    before={reg:0x93700000+i*4 for i,reg in enumerate(regs)}
    for reg,val in before.items():r.u.reg_write(reg,val)
    r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2505)
    r.count=0;r.u.emu_start(0x400550da,0x400550e0,count=180000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC)==0x400550e0
    assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK
    assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2505,hex(r.u.reg_read(mk.UC_M68K_REG_SR))
    for reg,val in before.items():
        assert r.u.reg_read(reg)==(r.r32(0x40a7887c) if reg==mk.UC_M68K_REG_A2 else val),(reg,hex(r.u.reg_read(reg)),hex(val))
    return r.count

def audible_steps(stock,base,tweak):
    for playing in (False,True):
      for inherited,default,expected in ((0,90,90),(255,80,80),(255,0,100),(0,255,100),(50,0,50)):
        r=setup(stock,base,tweak,index=5)
        r.u.mem_write(r.raw+128,bytes([inherited])*64)
        r.u.mem_write(r.raw+708,bytes([default]))
        r.u.mem_write(r.raw+516,bytes([0])*64)
        r.u.mem_write(r.raw+644,bytes([0])*64)
        r.u.mem_write(r.raw,struct.pack('>H',0xfffe)*64)
        r.u.mem_write(PAT+5*722,bytes(r.u.mem_read(r.raw,722)))
        r.w32(r.s['sg_config']+4,100)
        if not playing:
            r.w32(0x40a78874,0);r.w32(0x40a7883c,0)
        r.call('sg_action_generate');assert not r.r32(r.s['sg_error'])
        if playing:boundary(r);assert r.r32(r.s['sg_q_state'])==2
        data=bytes(r.u.mem_read(r.raw,722))
        for i in range(16):
            assert struct.unpack_from('>H',data,2*i)[0]==513
            assert data[128+i]==expected
            assert 36<=data[580+i]<=96
            assert data[516+i]==100 and data[644+i]==255
        if playing:assert bytes(r.u.mem_read(PAT+5*722,722))==data
        r.w32(0x40a78874,0);r.w32(0x40a7883c,0)
        if playing:r.call('sg_q_service')
        r.call('sg_action_undo')
        assert bytes(r.u.mem_read(r.raw+128,64))==bytes([inherited])*64
    print('ok : arrêt/lecture, vélocité zéro/héritée/default muet ; trigs note explicites, conditions et presets neutralisés ; Undo exact')


def notification_roundtrip(stock,base,tweak):
    from test_seq_gen_sync import SyncRig
    global RIG
    previous=RIG
    try:
        RIG=SyncRig
        r=setup(stock,base,tweak,index=5)
    finally:RIG=previous
    r.w32(r.s['sg_config']+4,100)
    r.w32(r.s['sg_config']+8,70);r.w32(r.s['sg_config']+12,70)
    r.w32(r.s['sg_options'],1)
    r.u.mem_write(r.s['sg_advanced'],struct.pack('>2I',83,83))
    r.call('sg_action_generate');boundary(r)
    assert r.r32(r.s['sg_q_state'])==2
    playback=bytes(r.u.mem_read(PAT+5*722,722))
    r.call('sg_q_service');r.drain()
    assert bytes(r.u.mem_read(PAT+5*722,722))==playback
    assert bytes(r.u.mem_read(r.raw,722))==playback
    storage=r.r32(OBJ+32)
    assert bytes(r.u.mem_read(storage+128,16))==bytes([70])*16
    assert bytes(r.u.mem_read(storage+192,16))==bytes([83])*16
    # Les setters d'une édition ultérieure gardent leurs vrais champs.
    r.call(0x40016642,OBJ,1,75);r.call(0x400166c2,OBJ,1,99);r.drain()
    assert r.u.mem_read(r.raw+581,1)==b'K' and r.u.mem_read(r.raw+129,1)==b'c'
    assert r.u.mem_read(storage+129,1)==b'K' and r.u.mem_read(storage+193,1)==b'c'
    assert struct.unpack('>H',r.u.mem_read(r.raw+2,2))[0]==513
    print('ok : commit B puis vraies notifications/RTTI/conversion B→A différée ; champs stockage et édition ultérieure indépendants')


def run(stock,base,tweak):
    # Le lecteur peut différer de sa reconstruction UI avant la demande.
    for index in range(6):
        r=setup(stock,base,tweak,index=index)
        r.u.mem_write(PAT+index*722+128,bytes([73]))
        audio=bytes(r.u.mem_read(PAT+index*722,722))
        r.call('sg_action_generate')
        obj=r.r32(r.s['sg_obj'])
        assert bytes(r.u.mem_read(obj+11556,722))==audio
        assert r.r32(r.s['sg_q_state'])==1
        boundary(r);assert r.r32(r.s['sg_q_state'])==2
    print('ok : six pistes, lecteur différent de la conversion UI avant staging ; snapshot réel et commit')
    # Mode commun natif : longueur masquée de piste 64, longueur effective 16.
    r=setup(stock,base,tweak,length=16)
    parent,pvt,pget,praw=0x931e0000,0x931e1000,0x931e2000,0x931e3000
    r.w32(OBJ+60,parent);r.w32(parent+44,pvt);r.w32(pvt+40,pget)
    r.u.mem_write(pget,b'\x20\x3c'+struct.pack('>I',praw)+b'\x4e\x75')
    r.u.mem_write(praw+20,struct.pack('>H',16));r.u.mem_write(praw+25,b'\0')
    r.u.mem_write(r.raw+713,struct.pack('>H',64));r.original=bytes(r.u.mem_read(r.raw,722))
    r.u.mem_write(PAT+3*722,bytes(r.u.mem_read(r.raw,722)))
    r.initial_audio=bytes(r.u.mem_read(PAT,30710))
    assert r.call(0x40016402,OBJ)==16
    r.call('sg_action_generate')
    assert r.r32(r.s['sg_q_state'])==1,('shared hidden length',r.r32(r.s['sg_error']))
    boundary(r);assert r.r32(r.s['sg_q_state'])==2
    assert bytes(r.u.mem_read(r.raw+713,2))==struct.pack('>H',64)
    r.call('sg_q_service');assert r.signals==list(range(16))
    print('ok : longueur effective native 16 avec longueur masquée piste 64 ; staging et commit')
    for fault,expected in [('mode','Q mod 00003'),('length','Queue: data'),('speed','Queue: data'),('running','Queue: data'),('chain','Queue: chain'),('audio','Queue: chain'),('locks','Queue: locks')]:
        r=setup(stock,base,tweak,index=5,length=16)
        if fault=='mode':r.u.mem_write(PAT+30667,b'\x03')
        elif fault=='length':r.u.mem_write(PAT+30662,b'\0\0')
        elif fault=='speed':r.u.mem_write(PAT+30668,b'\x07')
        elif fault=='running':r.w32(0x40a78848+5*4,0)
        elif fault=='chain':r.w32(0x40a78638,2)
        elif fault=='audio':r.w32(0x40a7887c,PAT+30710);r.w32(0x40a7863c,PAT+30710)
        elif fault=='data':r.w32(OBJ+16,0)
        elif fault=='locks':r.w32(POOL+16,0)
        audio_before=bytes(r.u.mem_read(PAT,30710))
        r.call('sg_action_generate');assert r.r32(r.s['sg_error'])
        r.u.reg_write(mk.UC_M68K_REG_D3,20);r.call('sg_q_label')
        assert r.string(r.u.reg_read(mk.UC_M68K_REG_A2))==expected,(fault,expected,r.string(r.u.reg_read(mk.UC_M68K_REG_A2)))
        assert bytes(r.u.mem_read(PAT,30710))==audio_before
    print('ok : piste 6, refus ciblés mode/chaîne/audio/données/locks, aucun changement audio')
    # Le vrai setter de liaison +32 cible la sauvegarde, distincte du lecteur.
    r=setup(stock,base,tweak)
    r.call(0x400156d0,OBJ,0x931a0004)
    assert r.r32(OBJ+32)==0x931a0004 and r.r32(OBJ+32)!=PAT+3*722
    r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1
    boundary(r);assert r.r32(r.s['sg_q_state'])==2
    print('ok : liaison native +32 indépendante de la banque audio ; staging/commit sans faux refus')
    for mode in (1,2):
      for index in range(6):
        for speed in range(7):
          r=setup(stock,base,tweak,index,length=16)
          r.u.mem_write(PAT+30667,bytes([mode]))
          r.u.mem_write(PAT+30662,struct.pack('>H',64))
          r.u.mem_write(PAT+index*722+715,bytes([speed]))
          r.u.mem_write(r.raw+715,bytes([speed]))
          if mode==2:r.u.mem_write(PAT+30668,bytes([speed]))
          r.original=bytes(r.u.mem_read(r.raw,722))
          r.u.mem_write(0x40a78860,bytes([7]*6));r.u.mem_write(0x40a78866,bytes([1]*6))
          r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1,(mode,index,speed)
          assert r.r32(r.s['sg_q_length'])==16 and r.r32(r.s['sg_q_speed'])==speed
          boundary(r,1,0);assert r.r32(r.s['sg_q_state'])==1
          boundary(r,0,1);assert r.r32(r.s['sg_q_state'])==1
          boundary(r,0,0);assert r.r32(r.s['sg_q_state'])==2,(mode,index,speed)
          assert struct.unpack('>H',r.u.mem_read(r.raw+713,2))[0]==16
    print('ok : modes par piste 1/2, six pistes × sept vitesses, longueur cible 16/commune 64 ; frontière propre à la piste')
    worst=0
    for index in range(6):
      for length in (1,16,64):
        r=setup(stock,base,tweak,index,length)
        for i in range(3):r.w32(r.s['sg_options']+i*4,1)
        r.w32(r.s['sg_config']+4,100)
        r.call('sg_action_generate')
        assert r.r32(r.s['sg_q_state'])==1,('stage',index,length,r.r32(r.s['sg_error']))
        assert bytes(r.u.mem_read(r.raw,722))==r.original
        assert bytes(r.u.mem_read(r.praw,6*4385))==r.pool_original
        assert bytes(r.u.mem_read(PAT,30710))==r.initial_audio
        assert not r.signals and not r.pool_signals
        for step,phase,tick in [(1,0,0),(0,1,0),(0,0,1)]:
            boundary(r,step,phase,tick)
            assert r.r32(r.s['sg_q_state'])==1
            assert bytes(r.u.mem_read(r.raw,722))==r.original
        worst=max(worst,boundary(r))
        assert r.r32(r.s['sg_q_state'])==2,('commit',index,length)
        generated=bytes(r.u.mem_read(r.raw,722));assert generated!=r.original
        obj=r.r32(r.s['sg_obj'])
        assert bytes(r.u.mem_read(PAT+index*722,722))==bytes(r.u.mem_read(obj+10832,722))
        assert bytes(r.u.mem_read(PAT+4332+index*4385,4385))==bytes(r.u.mem_read(r.praw+index*4385,4385))
        for tr in range(6):
            if tr==index:continue
            assert bytes(r.u.mem_read(PAT+tr*722,722))==r.initial_audio[tr*722:(tr+1)*722]
        assert not r.signals and not r.pool_signals
        r.call('sg_q_service');assert r.r32(r.s['sg_q_state'])==0
        assert r.signals==list(range(length)) and len(r.pool_signals)==1
        r.w32(0x40a78874,0);r.w32(0x40a7883c,0)
        r.call('sg_action_undo')
        assert bytes(r.u.mem_read(r.raw,722))==r.original
        assert bytes(r.u.mem_read(r.praw,6*4385))==r.pool_original
    print('ok : 6 pistes × longueurs 1/16/64 ; staging sans écriture/notification, frontière avant lecture, quatre copies, Undo ; ISR max',worst,'instructions')
    for mutation in ['raw','pool','audio','audio-pool','pattern','chain','stop','close','cancel','length','speed','raw-pointer','pool-pointer','stop-hook']:
        r=setup(stock,base,tweak);r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1
        if mutation=='raw':r.u.mem_write(r.raw,b'\x12')
        elif mutation=='pool':r.u.mem_write(r.praw+3*4385,b'\x12')
        elif mutation=='audio':r.u.mem_write(PAT+3*722,b'\x12')
        elif mutation=='audio-pool':r.u.mem_write(PAT+4332+3*4385,b'\x12')
        elif mutation=='pattern':r.w32(0x40a7887c,PAT+0x8000)
        elif mutation=='chain':r.w32(0x40a78638,2)
        elif mutation=='stop':r.w32(0x40a7883c,0)
        elif mutation=='close':r.call('sg_dtor0',r.r32(r.s['sg_obj']))
        elif mutation=='cancel':r.call('sg_action_undo')
        elif mutation=='length':r.u.mem_write(PAT+30662,b'\x00\x20')
        elif mutation=='speed':r.u.mem_write(PAT+30668,b'\x03')
        elif mutation=='raw-pointer':r.w32(OBJ+16,r.raw+0x800)
        elif mutation=='pool-pointer':r.w32(POOL+16,r.praw+0x10000)
        elif mutation=='stop-hook':
            r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
            r.w32(STACK+8,1)
            r.u.emu_start(0x40055f14,0x40055f1a,count=100)
            assert r.r32(r.s['sg_q_state'])==3
        before=bytes(r.u.mem_read(r.raw,722));audio=bytes(r.u.mem_read(PAT,30710));pool=bytes(r.u.mem_read(r.praw,26310))
        boundary(r)
        assert bytes(r.u.mem_read(r.raw,722))==before and bytes(r.u.mem_read(PAT,30710))==audio and bytes(r.u.mem_read(r.praw,26310))==pool,mutation
        assert r.r32(r.s['sg_q_state']) in (0,3),mutation
        expected={'raw':'Q: UI data','pool':'Q: UI locks','audio':'Q: play data','audio-pool':'Q: play locks','pattern':'Q: pattern','chain':'Queue: chain','stop':'Queue: transport','length':'Queue: data','speed':'Queue: data','raw-pointer':'Queue: track','pool-pointer':'Queue: track'}.get(mutation)
        if expected:
            r.call('sg_q_service')
            r.u.reg_write(mk.UC_M68K_REG_D3,20);r.call('sg_q_label')
            actual=r.string(r.u.reg_read(mk.UC_M68K_REG_A2))
            assert actual==expected,(mutation,actual,expected)
    print('ok : éditions concurrentes, changement/chaîne, arrêt, fermeture, Cancel queue : aucune écriture tardive')

def native_read(stock,base,tweak,quick=False):
    # Vrai parcours horloge -> lecteur -> événement et copie des p-locks.
    for mode in ((0,) if quick else (0,1,2)):
      for speed in ((0,) if quick else range(7)):
        for micro in ((0,) if quick else (-23,0,23)):
          r=setup(stock,base,tweak,index=5)
          r.u.mem_write(PAT+30667,bytes([mode]))
          r.u.mem_write(r.raw,struct.pack('>H',513)*16)
          r.u.mem_write(r.raw+192,bytes([micro&255])*64)
          r.u.mem_write(r.raw+320,bytes([255])*64)
          r.u.mem_write(r.raw+719,b'\xff')
          r.u.mem_write(PAT+5*722,bytes(r.u.mem_read(r.raw,722)))
          r.u.mem_write(r.raw+715,bytes([speed]));r.u.mem_write(PAT+5*722+715,bytes([speed]));r.u.mem_write(0x40a788b5,bytes([speed]*6));r.u.mem_write(PAT+30668,bytes([speed]));r.u.mem_write(0x40a788b4,bytes([speed]))
          r.w32(r.s['sg_config']+4,100);r.w32(r.s['sg_config']+8,70);r.w32(r.s['sg_config']+12,70)
          for i in range(3):r.w32(r.s['sg_options']+i*4,1)
          r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1
          r.u.mem_map(0x4e200000,0x200000)
          evt,locks,kit=0x93160000,0x93161000,0x93150000
          r.w32(0x40a78888,kit);r.w32(0x40a78890,kit)
          emitted=[];read=[]
          def bad(u,access,addr,size,val,data):
              print('memory',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,'reads',read);return False
          r.u.hook_add(UC_HOOK_MEM_INVALID,bad)
          def scheduled(a):
              if a[0]==evt:emitted.append((bytes(r.u.mem_read(evt,76)),bytes(r.u.mem_read(locks,300)),a[1]))
              return 0
          for addr,fn in {0x40091eb6:lambda a:evt,0x40091e66:lambda a:locks,
                          0x40091f82:lambda a:0,0x40091fdc:lambda a:0,
                          0x4009203c:scheduled,0x40001fba:lambda a:0}.items():
              r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
          def reading(u,addr,size,data):
              sp=u.reg_read(mk.UC_M68K_REG_A7)
              track,pattern,_,step=struct.unpack('>4I',u.mem_read(sp+4,16))
              read.append((track,step,r.r32(r.s['sg_q_state'])))
          r.u.hook_add(UC_HOOK_CODE,reading,begin=0x400548ce,end=0x400548ce)
          r.u.reg_write(mk.UC_M68K_REG_A7,STACK-72)
          r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
          r.u.emu_start(0x400550da,0x4005542e,count=180000)
          assert r.u.reg_read(mk.UC_M68K_REG_PC)==0x4005542e
          assert read==[(tr,0,2) for tr in range(6)],(speed,micro,read)
          assert len(emitted)==1,(speed,micro,len(emitted))
          event,pool,when=emitted[0]
          assert struct.unpack_from('>I',event,28)[0]==70,('note',event.hex())
          assert struct.unpack_from('>H',event,22)[0]==r.u.mem_read(r.raw+128,1)[0]*256,('velocity',event.hex())
          n=struct.unpack_from('>I',pool,8)[0]
          locks_read={struct.unpack_from('>H',pool,20+i*8)[0]:struct.unpack_from('>H',pool,22+i*8)[0] for i in range(n)}
          for param in (18,22):
              expected=struct.unpack('>H',r.u.mem_read(PAT+4332+5*4385+param*2,2))[0]
              assert locks_read[param]==expected,(param,locks_read,expected)
    print('ok : vrai ordonnanceur/lecteur/événement OS et conditions natives ; note MIDI +28, vélocité +22 et locks vérifiés séparément')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt');ap.add_argument('--main',action='store_true');a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    for name,dep in [('scale-gen-queued','model-tg'),('scale-gen-st-queued','model-tg-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/{"" if a.main else "experimental/queued/"}49-{name}.json').read_text())
        audible_steps(stock,base,tweak)
        notification_roundtrip(stock,base,tweak)
        run(stock,base,tweak)
        native_read(stock,base,tweak)
    if a.syntakt:
        import build,syntakt,gen_flasher_tweaks as catalog
        tw=catalog.read_js((ROOT/('docs/flasher/tweaks.js' if a.main else 'docs/flasher-test/tweaks.js')).read_text())
        ids='6ch-usbup model-tg-st sample-preview-st trig-hold arp tempo-max boot-anim multiline-browser midi-live-both level-pan-values trigless-dim syntakt-tg-sd-cp-toy-bits-swarm-macro'.split()
        extras=[next(t for t in tw['tweaks'] if t['id']==i) for i in ids]
        base=next(t for t in extras if t['id']=='model-tg-st')
        tweak=json.loads((ROOT/('tweaks/model-cycles_OS1.13/49-scale-gen-st-queued.json' if a.main else 'tweaks/model-cycles_OS1.13/experimental/queued/49-scale-gen-st-queued.json')).read_text())
        scramble=json.loads((ROOT/('tweaks/model-cycles_OS1.13/50-scramble-st-gen-queued.json' if a.main else 'tweaks/model-cycles_OS1.13/experimental/scramble/50-scramble-st-gen-queued.json')).read_text())
        combined=extras+[tweak,scramble]
        image,_=build.apply_writes(stock,combined)
        payload,_=build.build_payload(combined,stock,a.syntakt)
        st_img=syntakt.dsp_image(a.syntakt)
        engines=next(t for t in extras if t.get('append',{}).get('syntakt'))
        runtime=build.payload_runtime(engines,stock,st_img)
        class FullRig(Rig):
            def __init__(self,stock,base,tweak):
                super().__init__(stock,base,tweak)
                self.u.mem_write(build.BASE,bytes(image)+payload)
                dest=int(engines['append']['dest'],16)
                self.u.mem_map(dest,0x100000);self.u.mem_write(dest,runtime)
        global RIG
        RIG=FullRig
        audible_steps(stock,base,tweak);run(stock,base,tweak);native_read(stock,base,tweak)
        print('ok : mêmes preuves sur la combinaison maximale, SCRAMBLE, 6ch, arp, MIDI et tous les moteurs inclus')
if __name__=='__main__':main()
