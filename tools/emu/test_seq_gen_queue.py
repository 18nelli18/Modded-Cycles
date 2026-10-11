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
PAT=0x93130000
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
    r.w32(OBJ+32,PAT+index*722)
    r.u.mem_write(PAT,bytes(30710))
    for tr in range(6):r.call(0x4005b642,PAT+tr*722,RAW,0,0xffffffff,0xffffffff)
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
    r.u.mem_write(0x40a78860,bytes([step]))
    r.u.mem_write(0x40a78866,bytes([phase]))
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

def run(stock,base,tweak):
    # Mode commun natif : longueur masquée de piste 64, longueur effective 16.
    r=setup(stock,base,tweak,length=16)
    parent,pvt,pget,praw=0x931e0000,0x931e1000,0x931e2000,0x931e3000
    r.w32(OBJ+60,parent);r.w32(parent+44,pvt);r.w32(pvt+40,pget)
    r.u.mem_write(pget,b'\x20\x3c'+struct.pack('>I',praw)+b'\x4e\x75')
    r.u.mem_write(praw+20,struct.pack('>H',16));r.u.mem_write(praw+25,b'\0')
    r.u.mem_write(RAW+713,struct.pack('>H',64));r.original=bytes(r.u.mem_read(RAW,722))
    r.call(0x4005b642,PAT+3*722,RAW,0,0xffffffff,0xffffffff)
    r.initial_audio=bytes(r.u.mem_read(PAT,30710))
    assert r.call(0x40016402,OBJ)==16
    r.call('sg_action_generate')
    assert r.r32(r.s['sg_q_state'])==1,('shared hidden length',r.r32(r.s['sg_error']))
    boundary(r);assert r.r32(r.s['sg_q_state'])==2
    assert bytes(r.u.mem_read(RAW+713,2))==struct.pack('>H',64)
    r.call('sg_q_service');assert r.signals==list(range(16))
    print('ok : longueur effective native 16 avec longueur masquée piste 64 ; staging et commit')
    for fault,expected in [('mode','Q mod 00001'),('length','Q len 00000'),('speed','Q spd 00007'),('running','Q run 00000'),('chain','Queue: chain'),('audio','Queue: audio'),('data','Queue: data'),('locks','Queue: locks')]:
        r=setup(stock,base,tweak,index=5,length=16)
        if fault=='mode':r.u.mem_write(PAT+30667,b'\x01')
        elif fault=='length':r.u.mem_write(PAT+30662,b'\0\0')
        elif fault=='speed':r.u.mem_write(PAT+30668,b'\x07')
        elif fault=='running':r.w32(0x40a78848,0)
        elif fault=='chain':r.w32(0x40a78638,2)
        elif fault=='audio':r.w32(OBJ+32,0)
        elif fault=='data':r.w32(OBJ+16,0)
        elif fault=='locks':r.w32(POOL+16,0)
        audio_before=bytes(r.u.mem_read(PAT,30710))
        r.call('sg_action_generate');assert r.r32(r.s['sg_error'])
        r.u.reg_write(mk.UC_M68K_REG_D3,20);r.call('sg_q_label')
        assert r.string(r.u.reg_read(mk.UC_M68K_REG_A2))==expected,(fault,expected,r.string(r.u.reg_read(mk.UC_M68K_REG_A2)))
        assert bytes(r.u.mem_read(PAT,30710))==audio_before
    print('ok : piste 6, refus ciblés mode/chaîne/audio/données/locks, aucun changement audio')
    worst=0
    for index in range(6):
      for length in (1,16,64):
        r=setup(stock,base,tweak,index,length)
        for i in range(3):r.w32(r.s['sg_options']+i*4,1)
        r.w32(r.s['sg_config']+4,100)
        r.call('sg_action_generate')
        assert r.r32(r.s['sg_q_state'])==1,('stage',index,length,r.r32(r.s['sg_error']))
        assert bytes(r.u.mem_read(RAW,722))==r.original
        assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
        assert bytes(r.u.mem_read(PAT,30710))==r.initial_audio
        assert not r.signals and not r.pool_signals
        for step,phase,tick in [(1,0,0),(0,1,0),(0,0,1)]:
            boundary(r,step,phase,tick)
            assert r.r32(r.s['sg_q_state'])==1
            assert bytes(r.u.mem_read(RAW,722))==r.original
        worst=max(worst,boundary(r))
        assert r.r32(r.s['sg_q_state'])==2,('commit',index,length)
        generated=bytes(r.u.mem_read(RAW,722));assert generated!=r.original
        obj=r.r32(r.s['sg_obj'])
        assert bytes(r.u.mem_read(PAT+index*722,722))==bytes(r.u.mem_read(obj+10832,722))
        assert bytes(r.u.mem_read(PAT+4332+index*4385,4385))==bytes(r.u.mem_read(PRAW+index*4385,4385))
        for tr in range(6):
            if tr==index:continue
            assert bytes(r.u.mem_read(PAT+tr*722,722))==r.initial_audio[tr*722:(tr+1)*722]
        assert not r.signals and not r.pool_signals
        r.call('sg_q_service');assert r.r32(r.s['sg_q_state'])==0
        assert r.signals==list(range(length)) and len(r.pool_signals)==1
        r.w32(0x40a78874,0);r.w32(0x40a7883c,0)
        r.call('sg_action_undo')
        assert bytes(r.u.mem_read(RAW,722))==r.original
        assert bytes(r.u.mem_read(PRAW,6*4385))==r.pool_original
    print('ok : 6 pistes × longueurs 1/16/64 ; staging sans écriture/notification, frontière avant lecture, quatre copies, Undo ; ISR max',worst,'instructions')
    for mutation in ['raw','pool','audio','audio-pool','pattern','chain','stop','close','cancel','length','speed','raw-pointer','pool-pointer','stop-hook']:
        r=setup(stock,base,tweak);r.call('sg_action_generate');assert r.r32(r.s['sg_q_state'])==1
        if mutation=='raw':r.u.mem_write(RAW,b'\x12')
        elif mutation=='pool':r.u.mem_write(PRAW+3*4385,b'\x12')
        elif mutation=='audio':r.u.mem_write(PAT+3*722,b'\x12')
        elif mutation=='audio-pool':r.u.mem_write(PAT+4332+3*4385,b'\x12')
        elif mutation=='pattern':r.w32(0x40a7887c,PAT+0x8000)
        elif mutation=='chain':r.w32(0x40a78638,2)
        elif mutation=='stop':r.w32(0x40a7883c,0)
        elif mutation=='close':r.call('sg_dtor0',r.r32(r.s['sg_obj']))
        elif mutation=='cancel':r.call('sg_action_undo')
        elif mutation=='length':r.u.mem_write(PAT+30662,b'\x00\x20')
        elif mutation=='speed':r.u.mem_write(PAT+30668,b'\x03')
        elif mutation=='raw-pointer':r.w32(OBJ+16,RAW+0x800)
        elif mutation=='pool-pointer':r.w32(POOL+16,PRAW+0x10000)
        elif mutation=='stop-hook':
            r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
            r.w32(STACK+8,1)
            r.u.emu_start(0x40055f14,0x40055f1a,count=100)
            assert r.r32(r.s['sg_q_state'])==3
        before=bytes(r.u.mem_read(RAW,722));audio=bytes(r.u.mem_read(PAT,30710));pool=bytes(r.u.mem_read(PRAW,26310))
        boundary(r)
        assert bytes(r.u.mem_read(RAW,722))==before and bytes(r.u.mem_read(PAT,30710))==audio and bytes(r.u.mem_read(PRAW,26310))==pool,mutation
        assert r.r32(r.s['sg_q_state']) in (0,3),mutation
    print('ok : éditions concurrentes, changement/chaîne, arrêt, fermeture, Cancel queue : aucune écriture tardive')

def native_read(stock,base,tweak):
    # Vrai parcours horloge -> lecteur -> événement et copie des p-locks.
    for speed in range(7):
      for micro in (-23,0,23):
        r=setup(stock,base,tweak,index=5)
        r.u.mem_write(RAW,struct.pack('>H',513)*16)
        r.u.mem_write(RAW+192,bytes([micro&255])*64)
        r.u.mem_write(RAW+320,bytes([255])*64)
        r.u.mem_write(RAW+719,b'\xff')
        r.call(0x4005b642,PAT+5*722,RAW,0,0xffffffff,0xffffffff)
        r.u.mem_write(PAT+30668,bytes([speed]));r.u.mem_write(0x40a788b4,bytes([speed]))
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
                        0x400913a8:lambda a:1,0x400913f0:lambda a:0,
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
        assert struct.unpack_from('>H',event,22)[0]==70*256
        n=struct.unpack_from('>I',pool,8)[0]
        locks_read={struct.unpack_from('>H',pool,20+i*8)[0]:struct.unpack_from('>H',pool,22+i*8)[0] for i in range(n)}
        for param in (18,22):
            expected=struct.unpack('>H',r.u.mem_read(PAT+4332+5*4385+param*2,2))[0]
            assert locks_read[param]==expected,(param,locks_read,expected)
    print('ok : vrai ordonnanceur/lecteur/événement OS, 7 vitesses × microtiming -23/0/+23 ; note et locks neufs avant le premier trig')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt');a=ap.parse_args()
    stock=main_os_from_syx(a.cycles)
    for name,dep in [('scale-gen-queued','model-tg'),('scale-gen-st-queued','model-tg-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/experimental/queued/49-{name}.json').read_text())
        run(stock,base,tweak)
        native_read(stock,base,tweak)
    if a.syntakt:
        import build,syntakt,gen_flasher_tweaks as catalog
        tw=catalog.read_js((ROOT/'docs/flasher-test/tweaks.js').read_text())
        ids='6ch-usbup model-tg-st sample-preview-st trig-hold arp tempo-max boot-anim multiline-browser midi-live-both level-pan-values trigless-dim syntakt-tg-sd-cp-toy-bits-swarm-macro'.split()
        extras=[next(t for t in tw['tweaks'] if t['id']==i) for i in ids]
        base=next(t for t in extras if t['id']=='model-tg-st')
        tweak=json.loads((ROOT/'tweaks/model-cycles_OS1.13/experimental/queued/49-scale-gen-st-queued.json').read_text())
        scramble=json.loads((ROOT/'tweaks/model-cycles_OS1.13/experimental/scramble/50-scramble-st-gen-queued.json').read_text())
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
        run(stock,base,tweak);native_read(stock,base,tweak)
        print('ok : mêmes preuves sur la combinaison maximale, SCRAMBLE, 6ch, arp, MIDI et tous les moteurs inclus')
if __name__=='__main__':main()
