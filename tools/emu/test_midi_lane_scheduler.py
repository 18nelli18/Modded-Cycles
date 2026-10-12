#!/usr/bin/env python3
"""Note 57 : tâche MIDI avec wait/post et changement de contexte natifs.

Le handler OS 40000410 sauvegarde/restaure réellement les TCB et piles.
TRAP/RTE ColdFire sont des adaptateurs de trame format 4, car Unicorn est
un moteur m68k générique. Allocation et writer physiques simulés.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK
from test_midi_lane_page import load
from test_sdvintage import main_os_from_syx

UI,IDLE,UISEM=0x93010000,0x93010100,0x93010200
UISTACK,IDLESTACK=0x93014000,0x93016000
UIRETURN,IDLERUN=0x9301e000,0x9301f000
CURRENT,HIGHEST=0x422fef30,0x4049fd60


def prove(r):
    u=r.u
    u.mem_map(0xfc050000,0x1000);u.mem_map(0xfc080000,0x1000)
    r.w32(0x40fe4228,1)
    r.w32(HIGHEST,0x422feec8)
    assert r.call('ml_prepare')==1
    ctx=r.r32(r.s['ml_context'])
    # Deux tâches de fixture, initialisées/insérées par les APIs natives.
    for task,entry,priority,stack in ((IDLE,IDLERUN,0,IDLESTACK),(UI,UIRETURN,6,UISTACK)):
        u.mem_write(task,bytes(84))
        assert r.call(0x400019ec,task,entry,priority,stack,4096)==1
        r.call(0x40001a38,task)
    assert r.call('ml_worker_prepare')==1
    worker=r.r32(r.s['ml_worker_context']);task=worker+16
    r.w32(CURRENT,UI);u.mem_write(UISEM,bytes(8))
    output=[];switches=[];traps=[];rtes=[]
    def writer(args):
        assert r.r32(CURRENT)==task
        assert not u.reg_read(mk.UC_M68K_REG_SR)&0x700
        assert worker+100<=u.reg_read(mk.UC_M68K_REG_A7)<worker+16484
        output.append(bytes(u.mem_read(args[1],args[0])))
        return 0
    r.stubs[0x400826b0]=writer
    u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
    def frame(pc):
        sr=u.reg_read(mk.UC_M68K_REG_SR)&0xffff
        sp=u.reg_read(mk.UC_M68K_REG_A7)-8
        u.mem_write(sp,struct.pack('>II',0x40800000|sr,pc))
        u.reg_write(mk.UC_M68K_REG_A7,sp)
        u.reg_write(mk.UC_M68K_REG_PC,0x40000410)
    def trap(u,addr,size,data):
        traps.append(r.r32(CURRENT));frame(addr+2)
    def rte(u,addr,size,data):
        sp=u.reg_read(mk.UC_M68K_REG_A7)
        header,pc=struct.unpack('>II',u.mem_read(sp,8))
        assert header>>28==4
        rtes.append(r.r32(CURRENT))
        u.reg_write(mk.UC_M68K_REG_A7,sp+8)
        u.reg_write(mk.UC_M68K_REG_SR,header&0xffff)
        u.reg_write(mk.UC_M68K_REG_PC,pc)
    def entered(u,addr,size,data):switches.append(r.r32(CURRENT))
    u.hook_add(UC_HOOK_CODE,trap,begin=0x40001b38,end=0x40001b38)
    u.hook_add(UC_HOOK_CODE,rte,begin=0x40000458,end=0x40000458)
    u.hook_add(UC_HOOK_CODE,entered,begin=0x40000410,end=0x40000410)
    # UI attend ; le scheduler lance le vrai entry du worker, qui attend
    # à son tour. IDLE reste seul prêt ; aucun writer ni boucle active.
    sp=UISTACK+4096-32
    u.mem_write(sp,struct.pack('>II',UIRETURN,UISEM))
    u.reg_write(mk.UC_M68K_REG_A7,sp);u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    u.emu_start(0x40001aca,IDLERUN,count=20000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==IDLERUN
    assert traps==[UI,task] and rtes==[task,IDLE] and not output
    assert r.r32(CURRENT)==IDLE and r.r32(worker+4)==task and r.r32(UISEM+4)==UI
    regs=[getattr(mk,'UC_M68K_REG_'+kind+str(i)) for kind in ('D','A') for i in range(8)]
    regs += [mk.UC_M68K_REG_SR,mk.UC_M68K_REG_PC]
    def preserve_call(name,*args,sr=0x2000):
        saved={reg:u.reg_read(reg) for reg in regs}
        u.reg_write(mk.UC_M68K_REG_SR,sr)
        value=r.call(name,*args)
        for reg,val in saved.items():u.reg_write(reg,val)
        return value
    for cycle in range(20):
        packet=0x963c6404
        assert preserve_call('ml_step',ctx+1584,0,packet,1)==1
        preserve_call('ml_stop',ctx+1584,0)
        preserve_call('ml_worker_kick',sr=0x2500)
        assert r.r32(HIGHEST)==0x422feec8+20 and r.r32(0xfc050014)&0x2000
        assert not r.r32(worker+4)
        frame(IDLERUN)
        u.emu_start(0x40000410,IDLERUN,count=20000)
        assert u.reg_read(mk.UC_M68K_REG_PC)==IDLERUN
        assert r.r32(CURRENT)==IDLE and r.r32(worker+4)==task
        assert not r.r32(ctx+1584) and not r.r32(worker+8)
        assert output[-2:]==[b'\x96\x3c\x64',b'\x86\x3c\x00']
        assert r.r32(HIGHEST)==0x422feec8 and not r.r32(0xfc050014)&0x2000
    assert len(output)==40
    # Réveiller l'UI : sa priorité 6 repasse au-dessus du worker à 5.
    preserve_call(0x40001bb0,UISEM)
    assert r.r32(HIGHEST)==0x422feec8+24
    frame(IDLERUN);u.emu_start(0x40000410,UIRETURN,count=20000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==UIRETURN and r.r32(CURRENT)==UI
    assert u.reg_read(mk.UC_M68K_REG_A7)==sp+4
    assert u.reg_read(mk.UC_M68K_REG_SR)==0x2000
    print('ok : handler scheduler natif sauvegarde/restaure TCB, piles UI/worker/idle ; worker démarre et dort sur wait natif')
    print('ok : vingt réveils IRQ, quarante messages IPL0 sur pile dédiée, retours idle sans spin ; UI priorité 6 restaurée')
    print('NOTE : entrée TRAP/RTE format ColdFire adaptée, périphériques/writer simulés ; timing matériel non mesuré')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    args=ap.parse_args()
    r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    load(r,worker=True);prove(r)


if __name__=='__main__':main()
