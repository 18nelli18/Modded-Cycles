#!/usr/bin/env python3
"""Recherche LFO 2 : deux banques de phase exécutant la vraie routine native.

Entrée assembleur indépendante avec banque fournie en quatrième argument.
Aucun firmware livré ; phases et mélange de destinations éprouvés séparément.
"""
import argparse
import json
import struct
import pathlib
import subprocess
import tempfile
from test_tempo_max import Rig, LFO, LFO_PHASE, OBJ, C, STACK, lfo_params
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
from test_sdvintage import main_os_from_syx

SECOND = 0x93010000
PARAM2 = 0x93011000
BANK_SIZE = 6 * 32


ENTRY = 0x93020000
PLACED=None


def install_entry(rig):
    global ENTRY
    if PLACED:
        tweak=json.loads(pathlib.Path(PLACED).read_text())
        for write in tweak['writes']:
            rig.uc.mem_write(0x40000400+write['off'],bytes.fromhex(write['new']))
        rig.lf2_symbols={name:int(value,16) for name,value in tweak['symbols'].items()}
        ENTRY=rig.lf2_symbols['lf2_update']
        return rig.lf2_symbols['lf2_mix']
    root = pathlib.Path(__file__).resolve().parents[2]
    cross = str(root.parent / 'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        subprocess.run([cross+'as', '-march=cfv4e', '-o', str(p/'entry.o'),
                        str(root/'tools/machines/lfo_secondary/update.s')], check=True)
        subprocess.run([cross+'as','-march=cfv4e',
                        '-o',str(p/'mix.o'),str(root/'tools/machines/lfo_secondary/mix.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'dispatch.o'),
                        str(root/'tools/machines/lfo_secondary/dispatch.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'edit.o'),str(root/'tools/machines/lfo_secondary/edit.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'init.o'),str(root/'tools/machines/lfo_secondary/init.s')],check=True)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'key.o'),str(root/'tools/machines/lfo_secondary/key.s')],check=True)
        subprocess.run([cross+'ld', '-Ttext='+hex(ENTRY), '-e', 'lf2_update',
                        '-o', str(p/'entry.elf'), str(p/'entry.o'),str(p/'mix.o'),str(p/'dispatch.o'),str(p/'edit.o'),str(p/'init.o'),str(p/'key.o')], check=True)
        subprocess.run([cross+'objcopy', '-O', 'binary', '--only-section=.text',
                        str(p/'entry.elf'), str(p/'entry.bin')], check=True)
        rig.uc.mem_write(ENTRY, (p/'entry.bin').read_bytes())
        symbols=subprocess.check_output([cross+'nm',str(p/'entry.elf')],text=True)
        rig.lf2_symbols={line.split()[2]:int(line.split()[0],16) for line in symbols.splitlines() if len(line.split())==3}
        return rig.lf2_symbols['lf2_mix']


def destinations(rig, mix):
    clipping_difference = False
    # Les quatre contrôles machine se trouvent hors des réglages LFO.
    for base in (0, 16384, 32512):
      for dest1, dest2 in ((11,11),(11,14),(14,11)):
        rig.uc.mem_write(LFO_PHASE, bytes(BANK_SIZE))
        rig.uc.mem_write(SECOND, bytes(BANK_SIZE))
        seen = set()
        for tick in range(48):
            blobs = []
            for dest, speed in ((dest1,19000),(dest2,22000)):
                blob = bytearray(lfo_params([speed]*6,[9]*6))
                for track in range(6):
                    struct.pack_into('>H',blob,track*66+30,28000)
                    for control in (11,14):
                        struct.pack_into('>H',blob,track*66+14+control*2,base)
                    blob[track*66+22] = dest
                blobs.append(bytes(blob))
            rig.uc.mem_write(OBJ, blobs[0]);rig.uc.mem_write(PARAM2, blobs[1])
            secondary_before = bytes(rig.uc.mem_read(SECOND,BANK_SIZE))
            rig.call(LFO,OBJ,14400,0)
            assert bytes(rig.uc.mem_read(SECOND,BANK_SIZE)) == secondary_before
            first_before = bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))
            params_before = bytes(rig.uc.mem_read(OBJ,len(blobs[0])))
            rig.call(ENTRY,PARAM2,14400,0,SECOND)
            assert bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE)) == first_before
            assert bytes(rig.uc.mem_read(OBJ,len(blobs[0]))) == params_before
            baseptr,outptr=0x93012000,0x93013000
            rig.uc.mem_write(baseptr,blobs[0])
            rig.uc.mem_write(outptr,b'\xa5'*len(blobs[0]))
            rig.call(mix,outptr,baseptr,len(blobs[0])//2,LFO_PHASE,SECOND)
            expected=bytearray(blobs[0])
            for track in range(6):
                deltas = [struct.unpack('>i',rig.uc.mem_read(bank+32*track+20,4))[0]
                          for bank in (LFO_PHASE,SECOND)]
                for index, (ptr, dest) in enumerate(((OBJ,dest1),(PARAM2,dest2))):
                    actual = rig.r16(ptr+track*66+14+dest*2)
                    assert actual == max(0,min(32512,base+deltas[index]))
                if dest1 == dest2:
                    combined=max(0,min(32512,base+sum(deltas)))
                    sequential=max(0,min(32512,max(0,min(32512,base+deltas[0]))+deltas[1]))
                    clipping_difference |= combined != sequential
                # Partir de la valeur de base,
                # ajouter les deux deltas signés, saturer une seule fois.
                merged = {d:max(0,min(32512,base+sum(delta for delta,target in
                          zip(deltas,(dest1,dest2)) if target==d))) for d in (11,14)}
                for dest,value in merged.items():
                    struct.pack_into('>H',expected,track*66+14+dest*2,value)
                seen.add(tuple(merged.values()))
            assert bytes(rig.uc.mem_read(outptr,len(expected)))==bytes(expected)
            # Même base et même états : aucun cumul d'un appel au suivant.
            rig.call(mix,outptr,baseptr,len(expected)//2,LFO_PHASE,SECOND)
            assert bytes(rig.uc.mem_read(outptr,len(expected)))==bytes(expected)
        assert len(seen)>1,(base,dest1,dest2)
    assert clipping_difference, 'cas de clipping des deux contributions non couvert'
    print('ok : sorties natives et deltas signés, cibles identiques/distinctes, bases 0/64/max ; mélange ColdFire sans accumulation')


def edit_settings(rig):
    ctx=0x93030000
    fn=rig.lf2_symbols['lf2_edit']
    rig.uc.mem_write(ctx,b'\xa5'*1240)
    maximum=(32767,23,32767,32,6,32767,4,32767)
    enums=(1,3,4,6)
    for track in range(6):
      for field,limit in enumerate(maximum):
        for value in (0,limit//2,limit):
            before=bytearray(rig.uc.mem_read(ctx,1240))
            rig.call(fn,ctx,track,field,value)
            assert rig.uc.reg_read(mk.UC_M68K_REG_D0)==1
            struct.pack_into('>H',before,192+16*track+2*field,value<<8 if field in enums else value)
            assert bytes(rig.uc.mem_read(ctx,1240))==bytes(before)
        for value in (limit+1,0xffffffff):
            before=bytes(rig.uc.mem_read(ctx,1240))
            rig.call(fn,ctx,track,field,value)
            assert rig.uc.reg_read(mk.UC_M68K_REG_D0)==0
            assert bytes(rig.uc.mem_read(ctx,1240))==before
    rig.call(fn,ctx,0,3,127)
    assert rig.r16(ctx+192+6)==127<<8
    for track,field in ((6,0),(0,8),(0xffffffff,0),(0,0xffffffff)):
        before=bytes(rig.uc.mem_read(ctx,1240))
        rig.call(fn,ctx,track,field,0)
        assert rig.uc.reg_read(mk.UC_M68K_REG_D0)==0
        assert bytes(rig.uc.mem_read(ctx,1240))==before
    print('ok : setter huit réglages × six LFO, enums natifs et destination OFF ; états/buffers intacts, refus hors domaine')


def initialize(rig):
    ctx=0x93030000
    frame=bytearray(lfo_params([17000+i*100 for i in range(6)],[9]*6)).ljust(476,b'\0')
    rig.uc.mem_write(OBJ,bytes(frame))
    rig.uc.mem_write(ctx-4,b'\x12\x34\x56\x78'+b'\xa5'*1240+b'\x87\x65\x43\x21')
    rig.uc.reg_write(mk.UC_M68K_REG_SR,0x2505)
    rig.call(rig.lf2_symbols['lf2_init'],ctx,OBJ)
    assert rig.uc.reg_read(mk.UC_M68K_REG_SR)==0x2505
    assert rig.uc.reg_read(mk.UC_M68K_REG_D0)==1
    expected=bytearray(1240)
    for track in range(6):
        expected[192+track*16:208+track*16]=frame[track*66+16:track*66+32]
        struct.pack_into('>H',expected,192+track*16+6,127<<8)
        struct.pack_into('>H',expected,192+track*16+14,16384)
    assert bytes(rig.uc.mem_read(ctx,1240))==bytes(expected)
    assert bytes(rig.uc.mem_read(OBJ,476))==bytes(frame)
    assert bytes(rig.uc.mem_read(ctx-4,4))==b'\x12\x34\x56\x78'
    assert bytes(rig.uc.mem_read(ctx+1240,4))==b'\x87\x65\x43\x21'
    for args in ((0,OBJ),(ctx,0)):
        rig.call(rig.lf2_symbols['lf2_init'],*args)
        assert rig.uc.reg_read(mk.UC_M68K_REG_D0)==0
        assert rig.uc.reg_read(mk.UC_M68K_REG_SR)==0x2505
        assert bytes(rig.uc.mem_read(ctx,1240))==bytes(expected)
    rig.uc.reg_write(mk.UC_M68K_REG_SR,0x2700)
    pointer=rig.lf2_symbols['lf2_context']
    native_results=[]
    for track in range(6):
        frame[track*66+22]=11
        struct.pack_into('>H',frame,track*66+30,28000)
        struct.pack_into('>H',frame,track*66+36,16384)
    rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
    for tick in range(8):
        rig.uc.mem_write(OBJ,bytes(frame))
        rig.call(LFO,OBJ,14400,0)
        native_results.append((bytes(rig.uc.mem_read(OBJ,476)),bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))))
    rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
    rig.w32(pointer,ctx)
    for expected_frame,expected_phase in native_results:
        rig.uc.mem_write(OBJ,bytes(frame))
        rig.call(rig.lf2_symbols['lf2_dispatch'],OBJ,14400,0)
        assert bytes(rig.uc.mem_read(OBJ,476))==expected_frame
        assert bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))==expected_phase
    rig.w32(pointer,0)
    print('ok : initialisation LFO 2 depuis six réglages natifs ; phases vides, OFF/profondeur neutre, bornes et source intactes')
    print('ok : publication du contexte initialisé conserve exactement huit blocs du LFO primaire actif')


def dispatch(rig):
    ctx=0x93030000
    pointer=rig.lf2_symbols['lf2_context']
    fn=rig.lf2_symbols['lf2_dispatch']
    first=bytearray(lfo_params([19000]*6,[9]*6)).ljust(476,b'\0')
    second=bytearray(lfo_params([22000]*6,[9]*6)).ljust(476,b'\0')
    for track in range(6):
        for blob,dest in ((first,11),(second,11)):
            blob[track*66+22]=dest
            struct.pack_into('>H',blob,track*66+30,28000)
            struct.pack_into('>H',blob,track*66+36,16384)
    rig.w32(pointer,0)
    rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
    rig.uc.mem_write(OBJ,bytes(first));rig.call(LFO,OBJ,14400,0)
    native_frame=bytes(rig.uc.mem_read(OBJ,476))
    native_states=bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))
    rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
    rig.uc.mem_write(OBJ,bytes(first));rig.call(fn,OBJ,14400,0)
    assert bytes(rig.uc.mem_read(OBJ,476))==native_frame
    assert bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))==native_states
    rig.uc.mem_write(ctx,bytes(1240))
    for track in range(6):rig.uc.mem_write(ctx+192+track*16,bytes(second[track*66+16:track*66+32]))
    rig.w32(pointer,ctx)
    rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
    previous=None
    for tick in range(64):
        rig.uc.mem_write(OBJ,bytes(first))
        rig.call(fn,OBJ,14400,0)
        expected=bytearray(first)
        for track in range(6):
            deltas=[struct.unpack('>i',rig.uc.mem_read(bank+track*32+20,4))[0] for bank in (LFO_PHASE,ctx)]
            value=max(0,min(32512,16384+sum(deltas)))
            struct.pack_into('>H',expected,track*66+36,value)
        assert bytes(rig.uc.mem_read(OBJ,476))==bytes(expected)
        if previous is not None:assert bytes(rig.uc.mem_read(ctx,192))!=previous
        previous=bytes(rig.uc.mem_read(ctx,192))
    assert not rig.bad
    print('ok : dispatcher firmware, contexte nul identique au natif ; 64 blocs deux LFO actifs, base 476 octets et réglages indépendants')


def key_navigation(rig):
    view,event,vt,close,callback=0x93040000,0x93041000,0x93042000,0x93043000,0x93043010
    rig.w32(view,vt)
    rig.w32(vt+124,close)
    seen=[]
    opened=[0]
    def hook(u,addr,size,data):
        sp=u.reg_read(mk.UC_M68K_REG_A7)
        seen.append(addr)
        assert rig.r32(sp+4)==view
        u.reg_write(mk.UC_M68K_REG_D0,opened[0] if addr==callback else 99)
        u.reg_write(mk.UC_M68K_REG_PC,rig.r32(sp))
        u.reg_write(mk.UC_M68K_REG_A7,sp+4)
    handles=[rig.uc.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr)
             for addr in (close,callback,0x40075822)]
    count=0
    try:
      for present,result,ipl in ((0,0,0),(1,0,0),(1,1,0),(1,1,5)):
        opened[0]=result
        rig.w32(rig.lf2_symbols['lf2_open_callback'],callback if present else 0)
        for sub in (0,56):
          for code in range(33):
            for flags in range(64):
              for guard in (0,1):
                seen.clear()
                rig.w32(event+12,code);rig.w32(event+16,flags)
                rig.uc.mem_write(view+604,bytes([guard]))
                rig.uc.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8))
                fn=rig.lf2_symbols['lf2_key_sub' if sub else 'lf2_key']
                actual=rig.call(fn,view+sub,event)[0]
                candidate=code==8 and not(flags&3) and not guard
                attempts=bool(candidate and present and not ipl)
                delegated=code!=8 or flags&2
                expected=([callback] if attempts else [])
                if delegated:expected+=[0x40075822]
                elif candidate and not(attempts and result):expected+=[close]
                assert seen==expected,(sub,code,flags,guard,seen,expected)
                assert actual==(99 if delegated else 1)
                assert rig.uc.mem_read(view+604,1)==bytes([guard if delegated or candidate else 0])
                count+=1
    finally:
        for handle in handles:rig.uc.hook_del(handle)
        rig.uc.reg_write(mk.UC_M68K_REG_SR,0x2700)
    print(f'ok : {count} événements natifs LFO, second appui, FUNC/maintien potard, callback absent/refusé, IPL et sous-objet +56')


def all_shapes_modes(rig):
    ctx=0x93030000;pointer=rig.lf2_symbols['lf2_context']
    count=0
    for wave in range(7):
      for mode in range(5):
        rig.uc.mem_write(ctx,bytes(1240))
        rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
        rig.w32(pointer,ctx)
        base=bytearray(lfo_params([22000]*6,[9]*6)).ljust(476,b'\0')
        for track in range(6):
            primary=(wave+track)%7;secondary=(wave+track+1)%7
            primary_mode=(mode+track)%5;secondary_mode=(mode+track+1)%5
            struct.pack_into('>8H',base,track*66+16,22000,9<<8,16384,
                             ((wave*5+mode+track)%33)<<8,primary<<8,8000,primary_mode<<8,30000)
            secondary_settings=struct.pack('>8H',25000,9<<8,12000,
                             ((wave*5+mode+track+11)%33)<<8,secondary<<8,16000,secondary_mode<<8,28000)
            rig.uc.mem_write(ctx+192+16*track,secondary_settings)
        settings=bytes(rig.uc.mem_read(ctx+192,96))
        for tick in range(32):
            rig.uc.mem_write(OBJ,bytes(base))
            rig.call(rig.lf2_symbols['lf2_dispatch'],OBJ,14400,0x3f if tick%8==0 else 0)
            expected=bytearray(base);sums={}
            for bank in (LFO_PHASE,ctx):
                for track in range(6):
                    target=struct.unpack('>i',rig.uc.mem_read(bank+32*track+16,4))[0]
                    delta=struct.unpack('>i',rig.uc.mem_read(bank+32*track+20,4))[0]
                    if 0<=target<=32:
                        offset=track*66+14+target*2
                        sums[offset]=sums.get(offset,0)+delta
            for offset,delta in sums.items():
                value=struct.unpack_from('>H',base,offset)[0]
                struct.pack_into('>H',expected,offset,max(0,min(32512,value+delta)))
            assert bytes(rig.uc.mem_read(OBJ,476))==bytes(expected),(wave,mode,tick)
            assert bytes(rig.uc.mem_read(ctx+192,96))==settings
            count+=1
    rig.w32(pointer,0)
    assert not rig.bad
    print(f'ok : {count} blocs, sept formes/cinq modes par banque, 33 destinations, retriggers périodiques ; frame entier et réglages indépendants')


def main():
    global PLACED
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    ap.add_argument('--tweak',help='Tester les octets réellement placés dans les masques du firmware')
    args = ap.parse_args()
    PLACED=args.tweak
    image = main_os_from_syx(args.cycles)
    rig = Rig(image)
    mix = install_entry(rig)
    original_call=rig.call
    registers=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
    count=[0];worst={}
    def tick(u,a,s,d):count[0]+=1
    rig.uc.hook_add(UC_HOOK_CODE,tick)
    def checked_call(fn,*args):
        saved={reg:rig.uc.reg_read(reg) for reg in registers}
        count[0]=0
        result=original_call(fn,*args)
        assert rig.uc.reg_read(mk.UC_M68K_REG_A7)==STACK-0x200+4
        assert all(rig.uc.reg_read(reg)==value for reg,value in saved.items())
        worst[fn]=max(worst.get(fn,0),count[0])
        return result
    rig.call=checked_call
    speeds = ([17000, 18000, 19000, 20000, 21000, 22000],
              [23000, 24000, 25000, 26000, 27000, 28000])
    mults = [9] * 6
    for bank, params, values in zip((LFO_PHASE, SECOND), (OBJ, PARAM2), speeds):
        rig.uc.mem_write(bank, bytes(BANK_SIZE))
        rig.uc.mem_write(params, lfo_params(values, mults))
    model = [[0] * 6 for _ in range(2)]
    rig.emac.macsr = 0x20
    if PLACED:
        initial=bytes(rig.uc.mem_read(OBJ,476))
        rig.uc.mem_write(rig.lf2_symbols['lf2_context'],bytes(4))
        rig.call(LFO,OBJ,14400,0)
        native_frame=bytes(rig.uc.mem_read(OBJ,476))
        native_phase=bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))
        rig.uc.mem_write(OBJ,initial);rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
        rig.snippet(0x400597c6,0x400597cc,{},stack=(OBJ,14400,0))
        assert rig.uc.reg_read(mk.UC_M68K_REG_A7)==STACK-0x400
        assert bytes(rig.uc.mem_read(OBJ,476))==native_frame
        assert bytes(rig.uc.mem_read(LFO_PHASE,BANK_SIZE))==native_phase
        rig.uc.mem_write(OBJ,initial);rig.uc.mem_write(LFO_PHASE,bytes(BANK_SIZE))
        print('ok : vrai callsite audio patché, ABI trois arguments et retour natif, contexte nul identique')
    distinct = False
    for tick in range(128):
        for index, bank, params in ((0, LFO_PHASE, OBJ), (1, SECOND, PARAM2)):
            other = SECOND if index == 0 else LFO_PHASE
            before = bytes(rig.uc.mem_read(other, BANK_SIZE))
            rig.call(ENTRY, params, 14400, 0, bank)
            assert bytes(rig.uc.mem_read(other, BANK_SIZE)) == before
            for track, speed in enumerate(speeds[index]):
                inc = ((speed - 16384) * 2 * 14400) >> 2
                model[index][track] = (model[index][track] + inc) % C
                assert rig.r32(bank + track * 32) == model[index][track]
        distinct |= model[0] != model[1]
    assert distinct
    assert not rig.bad
    print('ok : 128 doubles mises à jour natives, six phases indépendantes par banque ; autre banque inchangée')
    destinations(rig, mix)
    edit_settings(rig)
    initialize(rig)
    dispatch(rig)
    all_shapes_modes(rig)
    key_navigation(rig)
    print("Instructions max, entrée LFO",worst[ENTRY],"; mélange",worst[mix],"; pas une mesure du temps audio")
    print('Instructions max, dispatcher douze LFO et mélange :',worst[rig.lf2_symbols['lf2_dispatch']],'; pas une mesure de durée matérielle')
    print('NOTE : entrée assembleur réelle, banques en fixture ; mélange assembleur exécuté, intégration/UI/sauvegarde/coût audio à prouver')


if __name__ == '__main__':
    main()
