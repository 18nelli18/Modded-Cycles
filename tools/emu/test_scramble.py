#!/usr/bin/env python3
"""SCRAMBLE : CC, setter sonore OS, touches ; frontières UI/observateurs simulées.

La route Project::setParameter et le backend SoundParameterContext sont réels.
La sélection du contexte sans verrous, l'allocation et la présentation du popup
restent simulées : ce n'est pas un boot complet ni une preuve matérielle.
"""
import argparse,json,struct
import build,gen_flasher_tweaks as catalog,syntakt
from gen_scramble import check_index_modes
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_seq_gen_menu import Rig,ROOT,EVENT
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols
KIT,SVT,SRAW,SGET,NOTIFY,CTX,ZVT,ZERO=(0x93050000+i*0x1000 for i in range(8))

def setup(stock,base,tweak,index=0, extras=None, syntakt_path=None):
    sequence=next((t for t in (extras or []) if t['id'] in ('scale-gen','scale-gen-st')),None)
    r=Rig(stock,base,sequence or tweak)
    if extras:
        all_tweaks=[base]+[t for t in extras if t['id']!=base['id']]+[tweak]
        image,_=build.apply_writes(stock,all_tweaks)
        payload,_=build.build_payload(all_tweaks,stock,syntakt_path)
        r.u.mem_write(build.BASE,bytes(image)+payload)
        st_img=syntakt.dsp_image(syntakt_path)
        for t in all_tweaks:
            if t.get('append',{}).get('syntakt'):
                dest=int(t['append']['dest'],16);r.u.mem_map(dest,0x100000)
                r.u.mem_write(dest,build.payload_runtime(t,stock,st_img))
        r.s.update({k:int(v,16) for k,v in tweak['symbols'].items()})
    handle=KIT+212+68*index
    r.stubs[0x400cf866]=lambda a:KIT
    r.stubs[0x40012412]=lambda a:index
    r.stubs[0x4000f26c]=lambda a:CTX
    r.stubs[ZERO]=lambda a:0
    r.stubs[0x400802ec]=lambda a:0
    r.notifications=[];r.popup=[]
    def notify(a):
        r.notifications.append(bytes(r.u.mem_read(a[1],8)) if a[1] else None);return 0
    r.stubs[NOTIFY]=notify
    tg=symbols(str(ROOT.parent/'toolchain/bin/m68k-elf-'),ROOT.parent/'model-tg/build/_b.elf')
    r.stubs[tg['show_popup']]=lambda a:r.popup.append(r.string(a[0])) or 0
    for addr in (0x40012412,0x4000f26c,0x400802ec,ZERO,NOTIFY,tg['show_popup']):
        r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.w32(handle,SVT);r.w32(SVT+40,SGET);r.w32(SVT+16,NOTIFY)
    r.u.mem_write(SGET,b'\x20\x3c'+struct.pack('>I',SRAW)+b'\x4e\x75')
    r.w32(CTX,0x400fd134);r.w32(CTX+4,handle)
    r.w32(KIT+116+8*(63+index),ZVT);r.w32(KIT+116+620,ZVT);r.w32(ZVT+80,ZERO)
    r.trace=[]
    def trace(u,addr,size,data):
        r.trace.append(addr)
        if len(r.trace)>40:r.trace.pop(0)
    r.u.hook_add(UC_HOOK_CODE,trace)
    r.call(0x4005a274)
    r.tg=tg;r.handle=handle
    return r

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt');ap.add_argument('--main',action='store_true');a=ap.parse_args()
    folder='' if a.main else 'experimental/scramble/'
    try:check_index_modes("4018b1c6: 2980 2e00 movel %d0,%a4@(0,%d2:l:8)")
    except AssertionError:pass
    else:raise AssertionError("la régression matérielle v03 doit être refusée")
    check_index_modes("movel %d0,%a4@")
    print("ok : instruction fautive matérielle 4018B1C6 refusée par le contrôle ColdFire")
    stock=main_os_from_syx(a.cycles)
    for dep,suffix in [('model-tg',''),('model-tg-st','-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/{folder}50-scramble{suffix}.json').read_text())
        for index in range(6):
            r=setup(stock,base,tweak,index)
            for machine in range(6):
                before=bytearray([0xa5]*100)
                for p in range(33):struct.pack_into('>H',before,20+2*p,64*256)
                before[38]=machine
                r.u.mem_write(SRAW,bytes(before));r.notifications.clear();r.popup.clear()
                try:r.call('sc_run')
                except Exception:
                    print('PC',hex(r.u.reg_read(mk.UC_M68K_REG_PC)),'SP',hex(r.u.reg_read(mk.UC_M68K_REG_A7)),[hex(x) for x in r.trace]);raise
                assert r.r32(r.s['sc_result'])==1,(dep,index,machine,r.r32(r.s['sc_result']))
                after=bytes(r.u.mem_read(SRAW,100))
                allowed={20+2*p+j for p in range(11,15) for j in (0,1)}
                assert all(after[i]==before[i] for i in range(100) if i not in allowed),(index,machine,'outside')
                assert any(after[i]!=before[i] for i in allowed),(index,machine,'no changes')
                for p in range(11,15):
                    descriptor=r.call(0x4005a692,p,machine)
                    value=struct.unpack_from('>H',after,20+2*p)[0]
                    assert r.call(0x4000aa4e,CTX,descriptor,value), (p,machine,value)
                assert len(r.notifications)==4 and r.popup==['SCRAMBLE'],(len(r.notifications),r.popup)
            before=bytes(before[:38]+bytes([6])+before[39:]);r.u.mem_write(SRAW,before);r.popup.clear()
            r.call('sc_run');assert r.r32(r.s['sc_result'])==0
            assert bytes(r.u.mem_read(SRAW,100))==before and not r.popup
        r=setup(stock,base,tweak);r.u.mem_write(SRAW,bytes(100));r.call('sc_run')
        r.popup.clear();r.w32(r.tg['set_held'],0)
        r.call(0x4007240c,r.event(2,1,1));assert not r.popup
        r.w32(r.tg['set_held'],1);r.call(0x4007240c,r.event(2,1,2));assert r.popup==['SCRAMBLE']
        r.call(0x4007240c,EVENT);assert r.popup==['SCRAMBLE']
        r.w32(r.tg['set_held'],0);r.call(0x4007240c,r.event(2,16,3));assert r.r32(r.s['sc_taken'])==0
        print('ok :',dep,'6 pistes × 6 machines, vrai setter OS quatre valeurs seulement, bornes, Sampler refusé, combo idempotent sans menu')
    if a.syntakt:
        tw=catalog.read_js((ROOT/('docs/flasher/tweaks.js' if a.main else 'docs/flasher-test/tweaks.js')).read_text())
        ids='6ch-usbup model-tg-st sample-preview-st trig-hold arp tempo-max boot-anim multiline-browser midi-live-both level-pan-values trigless-dim syntakt-tg-sd-cp-toy-bits-swarm-macro scale-gen-st'.split()
        extras=[next(t for t in tw['tweaks'] if t['id']==i) for i in ids]
        base=next(t for t in extras if t['id']=='model-tg-st')
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/{folder}50-scramble-st-gen.json').read_text())
        for index in range(6):
            r=setup(stock,base,tweak,index,extras,a.syntakt)
            for machine in [0,1,2,3,4,5,7,8,9,10,11,12]:
                before=bytearray(100)
                for p in range(33):struct.pack_into('>H',before,20+2*p,64*256)
                before[38]=machine;r.u.mem_write(SRAW,bytes(before));r.popup.clear();r.notifications.clear()
                r.call('sc_run')
                assert r.r32(r.s['sc_result'])==1,('all mods',index,machine)
                after=bytes(r.u.mem_read(SRAW,100))
                assert after[42:50]!=before[42:50] and after[:42]==before[:42] and after[50:]==before[50:]
                for p in range(11,15):
                    descriptor=r.call(0x4005a692,p,machine)
                    value=struct.unpack_from('>H',after,20+2*p)[0]
                    assert r.call(0x4000aa4e,CTX,descriptor,value),(machine,p,value)
                assert len(r.notifications)==4 and r.popup==['SCRAMBLE']
            r.w32(r.tg['set_held'],1);r.popup.clear()
            r.call(0x4007240c,r.event(2,1,20));assert r.popup==['SCRAMBLE']
            r.call(0x4007240c,r.event(2,16,21))
            r.call(0x4007240c,r.event(15,1,22));assert r.r32(r.s['sg_obj'])
        print('ok : maximum all-mods combination, 6 tracks × 12 synthesis machines, SCRAMBLE and generator hook chain')
if __name__=='__main__':main()
