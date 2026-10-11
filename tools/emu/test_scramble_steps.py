#!/usr/bin/env python3
"""SCRAMBLE par pas : setters, sérialisation et constructeur d'événement natifs.

Allocations, file temporelle et observateurs simulés ; aucune preuve matérielle.
"""
import argparse,json,struct
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_scramble import setup,SRAW
from test_seq_gen_menu import ROOT,OBJ,RAW,STACK
from test_sdvintage import main_os_from_syx

def execute(r,event,locks):
    r.u.reg_write(mk.UC_M68K_REG_A2,event)
    r.u.reg_write(mk.UC_M68K_REG_A6,locks)
    r.u.reg_write(mk.UC_M68K_REG_A7,STACK)
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2505)
    regs=[mk.UC_M68K_REG_D0+i for i in range(8)]+[mk.UC_M68K_REG_A0+i for i in range(7)]
    before={reg:r.u.reg_read(reg) for reg in regs}
    r.u.emu_start(0x40054c0e,0x40054c14,count=10000)
    assert r.u.reg_read(mk.UC_M68K_REG_PC)==0x40054c14
    assert r.u.reg_read(mk.UC_M68K_REG_A7)==STACK
    assert r.u.reg_read(mk.UC_M68K_REG_SR)==0x2508,hex(r.u.reg_read(mk.UC_M68K_REG_SR))
    for reg,value in before.items():
        assert r.u.reg_read(reg)==(event if reg==mk.UC_M68K_REG_D0 else value),(reg,hex(value),hex(r.u.reg_read(reg)))

def check(r,machines=tuple(range(6))):
    # Même police et mesure natives que le popup ; les espaces élargissent le cadre.
    widths=[]
    for text in ('SCRAMBLE',r.string(r.s['sc_text'])):
        s,p=0x9319000c,0x93191000
        r.u.mem_write(s-12,struct.pack('>III',len(text),len(text),0)+text.encode()+b'\0')
        r.w32(p,s)
        widths.append(r.call(0x40072102,0x40140ab0,0xffffffff,p))
    assert widths==[47,59],widths
    print('ok : police et mesure natives du popup, largeur texte 47 → 59 pixels')
    event,locks,sound=0x93180000,0x93181000,0x93182000
    for machine in machines:
      for count in (0,2,33):
        r.u.mem_write(sound,bytes(100));r.u.mem_write(sound+38,bytes([machine]))
        original=bytes(r.u.mem_read(sound,100));seen=[]
        for repeat in range(3):
            r.u.mem_write(event,bytes(76));r.w32(event+40,513|64);r.w32(event+44,sound)
            r.u.mem_write(locks,bytes(300));r.w32(locks+8,count)
            for i in range(count):r.u.mem_write(locks+20+i*8,struct.pack('>HHI',i,1234,0))
            execute(r,event,locks)
            n=r.r32(locks+8);assert n==count+len([p for p in range(11,15) if p>=count])
            got={struct.unpack('>H',r.u.mem_read(locks+20+i*8,2))[0]:struct.unpack('>H',r.u.mem_read(locks+22+i*8,2))[0] for i in range(n)}
            assert r.r32(event+40)==513
            for param in range(11,15):
                desc=r.call(0x4005a692,param,machine)
                # Même getter de bornes natif utilisé par le runtime.
                bounds=0x93183000
                r.u.reg_write(mk.UC_M68K_REG_A0,bounds);r.call(0x4005a65a,desc)
                lo,hi=struct.unpack('>II',r.u.mem_read(bounds,8))
                assert lo<=got[param]<=hi,(machine,param,lo,got[param],hi)
            assert all(v==1234 for p,v in got.items() if p not in range(11,15))
            assert bytes(r.u.mem_read(sound,100))==original
            seen.append(tuple(got[p] for p in range(11,15)))
        assert len(set(seen))==3,(machine,count,seen)
    r.u.mem_write(event,bytes(76));r.w32(event+40,513);r.w32(event+44,sound)
    before=bytes(r.u.mem_read(locks,300));execute(r,event,locks)
    assert bytes(r.u.mem_read(locks,300))==before
    r.u.mem_write(sound+38,b'\x06');r.w32(event+40,577);execute(r,event,locks)
    assert bytes(r.u.mem_read(locks,300))==before and r.r32(event+40)==513
    print(f'ok : {len(machines)} machines × pools 0/2/33 × trois passages frais ; autres locks/son inchangés, Sampler et pas non marqué, registres/SR')

    # Vrai constructeur : marque convertie, valeurs intégrées aux locks du trig.
    pat,kit,ui=0x406fa040,0x931d0000,0x931c0000
    r.u.mem_write(pat,bytes(30710));r.u.mem_write(pat+4332,b'\xff'*4352+bytes(33))
    raw=bytearray(722);raw[0:2]=struct.pack('>H',577)
    raw[128:192]=bytes([90]*64);raw[192:580]=bytes([255]*388)
    raw[580:644]=bytes([70]*64);raw[713:715]=struct.pack('>H',16)
    raw[719]=255
    r.u.mem_write(ui,bytes(raw));r.call(0x4005b642,pat,ui,0,0xffffffff,0xffffffff)
    r.u.mem_write(pat+30662,struct.pack('>H',16));r.u.mem_write(pat+30668,b'\x02')
    for addr,fn in {0x40091eb6:lambda a:event,0x40091e66:lambda a:locks,
                    0x400913a8:lambda a:1,0x400913f0:lambda a:0}.items():
        known=addr in r.stubs;r.stubs[addr]=fn
        if not known:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    for machine in machines:
        r.u.mem_write(kit,bytes(7094));r.u.mem_write(kit+28+38,bytes([machine]))
        fresh=[]
        for repeat in range(3):
            assert r.call(0x400548ce,0,pat,kit,0,0,0)==event
            assert r.r32(event+44)==kit+28
            assert r.r32(event+40)&64==0
            assert r.r32(locks+8)==4
            fresh.append(bytes(r.u.mem_read(locks+20,32)))
        assert len(set(fresh))==3
    print(f'ok : vrai constructeur natif + conversion fichier, {len(machines)} machines, trois passes fraîches, quatre locks, marque masquée avant moteur')

    # Toggle réel sur les pas tenus 0, 15, 32, 63 ; action de relâchement neutralisée.
    edit=0x93190000
    for addr,fn in {0x400cf9a8:lambda a:edit,0x40069b84:lambda a:0}.items():
        known=addr in r.stubs;r.stubs[addr]=fn
        if not known:r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    raw=bytearray(722);raw[713:715]=struct.pack('>H',64)
    r.u.mem_write(RAW,bytes(raw));r.w32(OBJ+60,0)
    r.w32(r.r32(OBJ)+60,0x400d63ce)
    r.w32(edit+352,(1<<0)|(1<<15));r.w32(edit+348,(1<<0)|(1<<31))
    for step in (0,15,32,63):
        r.u.mem_write(RAW+step*2,struct.pack('>H',513));r.w32(edit+92+step*4,1)
    try: result=r.call('sc_steps_toggle')
    except Exception:
        print('toggle PC',hex(r.u.reg_read(mk.UC_M68K_REG_PC)),[hex(x) for x in r.trace]);raise
    assert result==1
    for step in (0,15,32,63):
        assert struct.unpack('>H',r.u.mem_read(RAW+step*2,2))[0]==577
        assert r.r32(edit+92+step*4)==0
    saved,loaded=0x931a0000,0x931b0000
    r.call(0x4005b642,saved,RAW,0,0xffffffff,0xffffffff)
    r.call(0x4005b4ec,loaded,saved)
    for step in (0,15,32,63):assert struct.unpack('>H',r.u.mem_read(loaded+step*2,2))[0]==577
    assert r.call('sc_steps_toggle')==1
    for step in (0,15,32,63):assert struct.unpack('>H',r.u.mem_read(RAW+step*2,2))[0]==513
    r.w32(edit+352,0);r.w32(edit+348,0);assert r.call('sc_steps_toggle')==0
    print('ok : vrais setters toggle, quatre pas tenus sur deux mots, relâchement neutralisé, sauvegarde/chargement natifs, retrait de marque')

    # Chemin panneau complet : maintenir trig, puis SETTINGS, puis TRACK.
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000) # retour au contexte UI, hors ISR
    r.w32(edit+352,1);r.w32(r.tg['set_held'],0);r.popup.clear()
    before=bytes(r.u.mem_read(SRAW,100))
    r.call(0x4007240c,r.event(2,1,100))
    assert struct.unpack('>H',r.u.mem_read(RAW,2))[0]==513 and not r.popup
    r.w32(r.tg['set_held'],1)
    event=r.event(2,1,101)
    r.call(0x4007240c,event)
    assert struct.unpack('>H',r.u.mem_read(RAW,2))[0]==577
    assert r.popup==['SCRAMBLE'] and bytes(r.u.mem_read(SRAW,100))==before
    r.call(0x4007240c,event)
    assert struct.unpack('>H',r.u.mem_read(RAW,2))[0]==577 and len(r.popup)==1
    r.call(0x4007240c,r.event(2,16,102))
    assert r.r32(r.s['sc_taken'])==0
    r.call(0x4007240c,r.event(2,1,103))
    assert struct.unpack('>H',r.u.mem_read(RAW,2))[0]==513 and len(r.popup)==2
    assert bytes(r.u.mem_read(SRAW,100))==before
    print('ok : combo panneau SETTINGS + TRACK avec trig tenu, sans changer le son de base ; doublon ignoré, relâchement et retrait')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--syntakt');ap.add_argument('--main',action='store_true');a=ap.parse_args()
    folder='' if a.main else 'experimental/scramble/'
    stock=main_os_from_syx(a.cycles)
    for dep,suffix in [('model-tg',''),('model-tg-st','-st')]:
        base=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/30-{dep}.json').read_text())
        tweak=json.loads((ROOT/f'tweaks/model-cycles_OS1.13/{folder}50-scramble{suffix}.json').read_text())
        r=setup(stock,base,tweak);check(r)
    if a.syntakt:
        import gen_flasher_tweaks as catalog
        tw=catalog.read_js((ROOT/('docs/flasher/tweaks.js' if a.main else 'docs/flasher-test/tweaks.js')).read_text())
        ids='6ch-usbup model-tg-st sample-preview-st trig-hold arp tempo-max boot-anim multiline-browser midi-live-both level-pan-values trigless-dim syntakt-tg-sd-cp-toy-bits-swarm-macro'.split()
        extras=[next(t for t in tw['tweaks'] if t['id']==i) for i in ids]
        extras.append(json.loads((ROOT/('tweaks/model-cycles_OS1.13/49-scale-gen-st.json' if a.main else 'tweaks/model-cycles_OS1.13/experimental/queued/49-scale-gen-st-queued.json')).read_text()))
        base=next(t for t in extras if t['id']=='model-tg-st')
        tweak=json.loads((ROOT/('tweaks/model-cycles_OS1.13/50-scramble-st-gen.json' if a.main else 'tweaks/model-cycles_OS1.13/experimental/scramble/50-scramble-st-gen-queued.json')).read_text())
        check(setup(stock,base,tweak,extras=extras,syntakt_path=a.syntakt),tuple(range(6))+tuple(range(7,13)))
        print('ok : SCRAMBLE par pas et combo avec générateur sélectionné, tous moteurs et mods compatibles')
if __name__=='__main__':main()
