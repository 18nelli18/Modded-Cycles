#!/usr/bin/env python3
"""Recherche LFO 2 : deux banques de phase exécutant la vraie routine native.

Entrée assembleur indépendante avec banque fournie en quatrième argument.
Aucun firmware livré ; phases et mélange de destinations éprouvés séparément.
"""
import argparse
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


def install_entry(rig):
    root = pathlib.Path(__file__).resolve().parents[2]
    cross = str(root.parent / 'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p = pathlib.Path(tmp)
        subprocess.run([cross+'as', '-march=cfv4e', '-o', str(p/'entry.o'),
                        str(root/'tools/machines/lfo_secondary/update.s')], check=True)
        subprocess.run([cross+'as','-march=cfv4e',
                        '-o',str(p/'mix.o'),str(root/'tools/machines/lfo_secondary/mix.s')],check=True)
        subprocess.run([cross+'ld', '-Ttext='+hex(ENTRY), '-e', 'lf2_update',
                        '-o', str(p/'entry.elf'), str(p/'entry.o'),str(p/'mix.o')], check=True)
        subprocess.run([cross+'objcopy', '-O', 'binary', '--only-section=.text',
                        str(p/'entry.elf'), str(p/'entry.bin')], check=True)
        rig.uc.mem_write(ENTRY, (p/'entry.bin').read_bytes())
        symbols=subprocess.check_output([cross+'nm',str(p/'entry.elf')],text=True)
        return int(next(line.split()[0] for line in symbols.splitlines() if line.endswith(' lf2_mix')),16)


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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    args = ap.parse_args()
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
    print("Instructions max, entrée LFO",worst[ENTRY],"; mélange",worst[mix],"; pas une mesure du temps audio")
    print('NOTE : entrée assembleur réelle, banques en fixture ; mélange assembleur exécuté, intégration/UI/sauvegarde/coût audio à prouver')


if __name__ == '__main__':
    main()
