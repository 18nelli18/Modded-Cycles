#!/usr/bin/env python3
"""Sauvegarde projet native : slot et succès après conversion, sans disque.

Exécute 0x4000f762, simule cache/conversion/backend ; ne prouve ni Save As
complet ni durabilité. Un futur hook annexe doit attendre les deux succès.
"""
import argparse
from unicorn import m68k_const as mk
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig, OBJ, RAW
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    args=ap.parse_args();r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    cache,serialized,callback=0x93010000,0x41400000,0x93012000
    r.u.mem_write(callback,bytes(16));calls=[]
    state={'available':1,'convert':1,'save':1,'slot':0}
    def retrieve(a):
        assert a[:2]==(cache,state['slot']);calls.append('retrieve')
        return serialized if state['available'] else 0
    def convert(a):
        assert a[:4]==(serialized,RAW,0,0xffffffff),a[:4]
        assert r.r32(RAW+8)==0x12345678
        calls.append('convert');return state['convert']
    def save(a):
        assert a[:2]==(cache,state['slot']);calls.append('save');return state['save']
    for addr,fn in ((0x400cfdaa,lambda a:cache),(0x4006a216,retrieve),
                    (0x4005d18a,convert),(0x4006a4d6,save),
                    (0x400d0aae,lambda a:0),(0x400cf044,lambda a:0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    r.w32(RAW+8,0x12345678)
    for slot in (0,1,95,96):
        for available,converted,saved in ((1,1,1),(0,1,1),(1,0,1),(1,1,0)):
            state.update(slot=slot,available=available,convert=converted,save=saved);calls.clear()
            result=r.call(0x4000f762,OBJ,slot,callback)&255
            assert result==int(available and converted and saved),(state,result,calls)
            expected=['retrieve']
            if available:
                expected+=['convert']
                if converted:expected+=['save']
            assert calls==expected,(calls,expected)
            assert r.r32(RAW+8)==0x12345678
    # Le callback stock est une double indirection vers self, pas self direct.
    holder,wrapped=0x93014000,0x93014010
    r.w32(holder,wrapped);r.w32(wrapped,OBJ)
    for available,converted,saved in ((1,1,1),(0,1,1),(1,0,1),(1,1,0)):
        state.update(slot=96,available=available,convert=converted,save=saved);calls.clear()
        r.u.reg_write(mk.UC_M68K_REG_D2,0x12345678)
        r.u.reg_write(mk.UC_M68K_REG_D3,0x76543210)
        result=r.call(0x4000fa26,holder)&255
        assert result==int(available and converted and saved),(state,result,calls)
        assert calls[0]=='retrieve'
        assert r.u.reg_read(mk.UC_M68K_REG_D2)==0x12345678
        assert r.u.reg_read(mk.UC_M68K_REG_D3)==0x76543210
    print('ok : callback natif working96, indirection self et ABI ; succès/échecs propagés')
    print('ok : sauvegarde projet native, slot transmis ; refus cache/conversion/save propagés')
    print('ok : identité inchangée par cette routine avec dépendances simulées')
    print('Limite : cadence autosave, Save As complet, backend disque et raccordement annexe non prouvés')
if __name__=='__main__':main()
