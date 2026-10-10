#!/usr/bin/env python3
"""Preuve ciblée du prototype PAN/niveau (notes/50).

Exécute le calcul de delta d'origine et le nouveau crochet, les glyphes et les
délais dans Unicorn. Les services de projet et l'invalidation sont simulés.
Ne prouve pas le démarrage complet ni le dispatch complet : pas de flasher.
Usage : python3 tools/emu/test_pan_level.py --cycles model-cycles_OS1.13.syx
"""
import argparse
import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as m
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
import gen_pan_level as G

STOP, STACK, EVENT, BITMAP, PIXELS = 0x90000000,0x90010000,0x90020000,0x90030000,0x90040000

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True)
    a=ap.parse_args()
    stock=G.main_os(a.cycles)
    t=G.build_tweak(stock)
    patched,_=build.apply_writes(stock,[t])
    tail=build.payload_runtime(t,stock,None)
    syms={k:int(v,16) for k,v in t['symbols'].items()}
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(m.UC_CPU_M68K_CFV4E)
    uc.mem_map(0x40000000,0x02400000)
    uc.mem_map(0x90000000,0x00100000)
    uc.mem_write(G.BASE,patched+tail)
    uc.reg_write(m.UC_M68K_REG_SR,0x2700)
    # La charge utile est normalement copiée par le crochet de démarrage.
    n=(syms['level_valid']+6-G.RUNTIME+3)&~3
    uc.mem_write(G.RUNTIME,tail[-n:])
    def w32(addr,v): uc.mem_write(addr,struct.pack('>I',v&0xffffffff))
    def r32(addr): return struct.unpack('>I',uc.mem_read(addr,4))[0]
    def call(entry,*args):
        uc.mem_write(STACK,struct.pack('>'+'I'*(len(args)+1),STOP,*[x&0xffffffff for x in args]))
        uc.reg_write(m.UC_M68K_REG_A7,STACK)
        uc.emu_start(entry,STOP,count=100000)
        assert uc.reg_read(m.UC_M68K_REG_PC)==STOP
        assert uc.reg_read(m.UC_M68K_REG_A7)==STACK+4
        return uc.reg_read(m.UC_M68K_REG_D0)
    for held in (0,1):
        uc.mem_write(EVENT+20,bytes([held]))
        for delta in (-1,1):
            w32(EVENT+16,delta)
            original=call(0x4006f73a,EVENT,2,16)
            new=call(syms['level_pan_delta'],EVENT,2,16)
            assert original==(delta*(16 if held else 2))&0xffffffff
            assert new==(delta*(16 if held else 1))&0xffffffff
    print('ok : vrai delta OS, pas normal 2 -> 1 ; pas maintenu 16 inchangé')
    w32(BITMAP+12,2);w32(BITMAP+16,PIXELS)
    font=bytes(uc.mem_read(syms['pan_font'],77))
    for glyph in range(11):
        for fn,y in (('level_glyph',9),('pan_glyph',22)):
            uc.mem_write(PIXELS,bytes(128*8))
            uc.reg_write(m.UC_M68K_REG_D0,glyph)
            uc.reg_write(m.UC_M68K_REG_D2,66)
            uc.reg_write(m.UC_M68K_REG_A2,BITMAP)
            call(syms[fn])
            actual=bytes(uc.mem_read(PIXELS,128*8))
            expected=bytearray(128*8)
            for row,bits in enumerate(font[glyph*7:glyph*7+7][::-1]):
                for x in range(3):
                    if bits&(1<<(2-x)):
                        at=(66+x)*8
                        word=struct.unpack_from('>I',expected,at)[0]|(1<<(31-y-row))
                        struct.pack_into('>I',expected,at,word)
            assert actual==expected
            assert uc.reg_read(m.UC_M68K_REG_D2)==70
    print('ok : 22 glyphes exécutés, pixels et avance de colonne exacts')
    active=[0]
    def ret(value):
        sp=uc.reg_read(m.UC_M68K_REG_A7)
        uc.reg_write(m.UC_M68K_REG_D0,value)
        uc.reg_write(m.UC_M68K_REG_PC,r32(sp))
        uc.reg_write(m.UC_M68K_REG_A7,sp+4)
    def hook(u,addr,size,data):
        if addr==0x40012412: ret(active[0])
        else: ret(0)
    for addr in (0x400cf866,0x4000eb90,0x40012412,0x40076082,0x40090f48):
        uc.hook_add(UC_HOOK_CODE,hook,begin=addr,end=addr)
    for track in range(6):
        active[0]=track
        for arm,array,valid in (('pan_arm','pan_deadlines','pan_valid'),('level_arm','level_deadlines','level_valid')):
            for now in (0,12345,0xfffffff0):
                w32(syms['pan_clock'],now)
                call(syms[arm])
                assert r32(syms[array]+track*4)==(now+90)&0xffffffff
                assert bytes(uc.mem_read(syms[valid]+track,1))==b'\x01'
    w32(syms['pan_clock'],0xffffffff)
    call(syms['pan_ui_tick'])
    assert r32(syms['pan_clock'])==0
    print('ok : armement PAN/niveau, six pistes, redémarrage et wrap de l’horloge')
    lo=0x4001c0d2-G.BASE;hi=0x4001cce0-G.BASE
    assert patched[lo:hi]==stock[lo:hi]
    print('ok : gestionnaire clavier inchangé ; aucun déclenchement au clic')
    print('À FAIRE : démarrage et dispatch complets, rendu principal, coexistence et matériel')

if __name__=='__main__': main()
