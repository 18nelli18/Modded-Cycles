#!/usr/bin/env python3
"""Note 57 : detour gestionnaire UI natif, file MIDI hors page active.

Exécute branchement et reprise OS réels ; périphériques, état de vue sale
et callbacks LED simulés. N'installe pas encore ce prototype au flasher.
"""
import argparse
import struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_midi_lane_page import make
from test_sdvintage import main_os_from_syx


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);args=ap.parse_args()
    stock=main_os_from_syx(args.cycles)
    r=make(stock);assert r.call('ml_prepare')==1
    ctx=r.r32(r.s['ml_context']);packets=[];callbacks=[];dirty=[0]
    def install(address,fn):
        r.stubs[address]=fn
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=address,end=address)
    install(0x400826b0,lambda a:packets.append((bytes(r.u.mem_read(a[1],a[0])),a[2])) or 0)
    install(0x40076bfa,lambda a:callbacks.append(('dirty',a[0])) or dirty[0])
    install(0x400cfaf4,lambda a:0x93009000)
    for address,tag in ((0x4000602a,'clear'),(0x40076ca2,'views'),(0x40006044,'flush')):
        install(address,lambda a,tag=tag:callbacks.append((tag,a[0])) or 0)
    r.w32(0x40fe4228,1)
    original=bytes(r.u.mem_read(0x40006a4a,8))
    assert original.hex()=='2f0a2f02242f000c'
    r.u.mem_write(0x40006a4a,b'\x4e\xf9'+struct.pack('>I',r.s['ml_ui_hook'])+b'\x4e\x71')
    r.u.ctl_remove_cache(0x40006a4a,0x40006a52)
    for lane in range(6):assert r.call('ml_edit',ctx,lane,0,3,1)==1
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
    r.call('ml_audio_tick',0,1);r.call('ml_audio_tick',1,0)
    assert r.r32(ctx+1584)==12 and not packets and not r.r32(r.s['mlp_obj'])
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    # La branche sans dessin doit tout de même drainer huit messages maximum.
    r.u.reg_write(mk.UC_M68K_REG_D2,0x12345678);r.u.reg_write(mk.UC_M68K_REG_A2,0x93001000)
    r.call(0x40006a4a,0x93008000)
    assert len(packets)==8 and r.r32(ctx+1584)==4 and r.r32(ctx+1588)==8
    assert callbacks==[('dirty',0x93008040)],callbacks
    assert r.u.reg_read(mk.UC_M68K_REG_D2)==0x12345678 and r.u.reg_read(mk.UC_M68K_REG_A2)==0x93001000
    dirty[0]=1;callbacks.clear()
    r.call(0x40006a4a,0x93008000)
    assert len(packets)==12 and [x[0] for x in callbacks]==['dirty','clear','views','flush']
    assert packets==[(bytes([0x96+i,60,100]),4) for i in range(6)]+[(bytes([0x86+i,60,0]),4) for i in range(6)],packets
    callbacks.clear();r.call(0x40006a4a,0x93008000);assert len(packets)==12
    # Stock vs detour : mêmes registres/pile/SR et branches OS, contexte absent.
    patched=bytes(r.u.mem_read(0x40006a4a,8));r.w32(r.s['ml_context'],0)
    r.w32(r.s['ml_preparing'],1)  # préparation indisponible : chemin sans contexte
    regs=[mk.UC_M68K_REG_D0,mk.UC_M68K_REG_D1,mk.UC_M68K_REG_D2,
          mk.UC_M68K_REG_A0,mk.UC_M68K_REG_A1,mk.UC_M68K_REG_A2,mk.UC_M68K_REG_SR]
    for level in (0x2000,0x2500):
      for flag in (0,1):
        dirty[0]=flag;outputs=[]
        for code in (original,patched):
          r.u.mem_write(0x40006a4a,code)
          r.u.ctl_remove_cache(0x40006a4a,0x40006a52)
          callbacks.clear()
          for reg in regs:r.u.reg_write(reg,level if reg==mk.UC_M68K_REG_SR else 0x12345678)
          r.call(0x40006a4a,0x93008000)
          outputs.append(([r.u.reg_read(reg) for reg in regs],list(callbacks)))
        assert outputs[0]==outputs[1],outputs
    assert len(packets)==12
    print('ok : préparation indisponible, branches propres/sales et IPL0/IPL5, registres/SR/pile identiques au stock')
    r.u.mem_write(0x40006a4a,patched)
    r.u.ctl_remove_cache(0x40006a4a,0x40006a52)
    r.w32(r.s['ml_preparing'],0);dirty[0]=0
    allocations=r.new_count
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2500)
    r.call(0x40006a4a,0x93008000)
    assert not r.r32(r.s['ml_context']) and r.new_count==allocations
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    r.fail_new=allocations+1
    r.call(0x40006a4a,0x93008000)
    assert not r.r32(r.s['ml_context']) and r.new_count==allocations+1
    r.fail_new=0
    r.call(0x40006a4a,0x93008000)
    ready=r.r32(r.s['ml_context'])
    assert ready and r.new_count==allocations+2 and not r.r32(r.s['mlp_obj'])
    assert not r.r32(ready+1584) and not r.r32(ready+1904)
    r.call(0x40006a4a,0x93008000)
    assert r.r32(r.s['ml_context'])==ready and r.new_count==allocations+2
    assert len(packets)==12
    print('ok : premier service UI prépare les voies sans ouvrir de vue ; refus IPL5, reprise après échec allocation, contexte réutilisé')
    print('ok : detour UI natif, vue MIDI fermée, huit puis quatre messages ; branches sans/avec dessin et reprise OS intactes')
    print('NOTE : horloge/transport natifs, chaîne complète de touches et placement firmware restent à intégrer')

if __name__=='__main__':main()
