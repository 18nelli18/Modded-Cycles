#!/usr/bin/env python3
"""Note 57 : création de tâche MIDI, APIs scheduler natives, sorties simulées.

Initialisation TCB et listes prêtes réelles ; pas de changement de pile par
le scheduler émulé. Allocation/dessin/sortie physique simulés. La tâche est
rejouée directement jusqu'à sa prochaine attente quand sa file est vide.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig,STACK,STOP
from test_midi_lane_page import load
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);a=ap.parse_args()
    r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    load(r,worker=True);u=r.u
    u.mem_map(0xfc050000,0x1000)
    sent=[]
    r.stubs[0x400826b0]=lambda args:sent.append((bytes(u.mem_read(args[1],args[0])),args[2])) or 0
    u.hook_add(UC_HOOK_CODE,r.stub,begin=0x400826b0,end=0x400826b0)
    r.w32(0x40fe4228,1);r.w32(0x4049fd60,0x422feec8+24)
    r.w32(r.s['ml_preparing'],0)
    assert r.call('ml_prepare')==1
    ctx=r.r32(r.s['ml_context'])
    # Échec allocation réessayable, refus depuis IRQ avant toute allocation.
    u.reg_write(mk.UC_M68K_REG_SR,0x2500);n=r.new_count
    assert r.call('ml_worker_prepare')==0 and r.new_count==n
    u.reg_write(mk.UC_M68K_REG_SR,0x2000);r.fail_new=n+1
    assert r.call('ml_worker_prepare')==0 and not r.r32(r.s['ml_worker_context'])
    assert not r.r32(r.s['ml_worker_preparing'])
    r.fail_new=0;assert r.call('ml_worker_prepare')==1
    worker=r.r32(r.s['ml_worker_context']);task=worker+16;stack=worker+100
    assert worker and r.new_count==n+2
    assert bytes(u.mem_read(worker,16))==bytes(12)+struct.pack('>I',ctx+1584)
    assert r.r32(task+8)==0x422feec8+20
    top=stack+16384-12
    assert r.r32(task+72)==top
    assert r.r32(top+4)==r.s['ml_worker_run'] and r.r32(top+8)==0x40001a68
    assert r.r32(0x422feec8+20)==task
    assert r.r32(task)==task and r.r32(task+4)==task
    assert r.r32(0x4049fd60)==0x422feec8+24  # UI (6) reste prioritaire.
    assert r.call('ml_worker_prepare')==1 and r.new_count==n+2
    for lane in range(6):r.call('ml_edit',ctx,lane,0,3,1)
    u.reg_write(mk.UC_M68K_REG_SR,0x2500)
    r.call('ml_audio_tick',0,1);r.call('ml_audio_tick',1,0)
    assert r.r32(ctx+1584)==12 and r.r32(worker)==1 and not sent
    # UI : ne consomme plus aucun paquet, dessin ou non.
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    r.call('ml_ui_drain');assert r.r32(ctx+1584)==12 and not sent
    waits=[]
    def wait(u,address,size,data):
        waits.append(r.r32(worker))
        if not r.r32(worker):u.emu_stop()
    h=u.hook_add(UC_HOOK_CODE,wait,begin=0x40001aca,end=0x40001aca)
    u.reg_write(mk.UC_M68K_REG_A7,STACK)
    u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    u.emu_start(r.s['ml_worker_run'],STOP,count=10000)
    u.hook_del(h)
    assert waits==[1,1,0] and len(sent)==12
    assert sent==[(bytes([0x96+i,60,100]),4) for i in range(6)]+[(bytes([0x86+i,60,0]),4) for i in range(6)]
    assert not r.r32(ctx+1584) and not r.r32(worker+8)
    # Routeur indisponible : conserver la file sans boucle de réarmement.
    r.w32(0x40fe4228,0)
    assert r.call('ml_step',ctx+1584,0,0x963c6404,1)==1
    r.call('ml_worker_kick')
    assert not r.r32(worker) and not r.r32(worker+8)
    assert r.call('ml_worker_once',worker)==0 and r.r32(ctx+1584)==1
    assert not r.r32(worker) and not r.r32(worker+8) and len(sent)==12
    r.w32(0x40fe4228,1);r.call('ml_ui_drain')
    assert r.r32(worker)==1 and r.r32(worker+8)==1
    waits.clear()
    h=u.hook_add(UC_HOOK_CODE,wait,begin=0x40001aca,end=0x40001aca)
    u.reg_write(mk.UC_M68K_REG_A7,STACK)
    u.emu_start(r.s['ml_worker_run'],STOP,count=10000)
    u.hook_del(h)
    assert waits==[1,0] and len(sent)==13 and not r.r32(ctx+1584)
    print('ok : TCB/pile de 16 KiB/listes prêtes natifs, priorité sous UI, allocation réessayée, refus IRQ, publication unique')
    print('ok : horloge IRQ réveille la tâche ; aucun drain UI ; boucle attend/rend huit puis quatre paquets et se rendort')
    print('ok : routeur indisponible sans spin ; file conservée et réveil après publication du singleton')
    print('NOTE : scheduler complet et sorties physiques simulés ; placement et timing matériel à valider')

if __name__=='__main__':main()
