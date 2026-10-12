#!/usr/bin/env python3
"""Sauvegarde projet native : slot et succès après conversion, sans disque.

Exécute 0x4000f762, simule cache/conversion/backend ; ne prouve ni Save As
complet ni durabilité. Un futur hook annexe doit attendre les deux succès.
"""
import argparse,pathlib,subprocess,tempfile,struct
from unicorn import UC_HOOK_CODE
from test_seq_gen_menu import Rig, OBJ, RAW
from test_sdvintage import main_os_from_syx

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--working',action='store_true')
    args=ap.parse_args();r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    root=pathlib.Path(__file__).resolve().parents[2];cross=str(root.parent/'toolchain/bin/m68k-elf-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_WORKING=1'] if args.working else []),'-o',str(p/'h.o'),str(root/'tools/machines/midi_lanes/storage_save_hook.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0x93050000','--defsym=ml_store_save_notice=0x93060000','-e','ml_store_save_hook','-o',str(p/'h.elf'),str(p/'h.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'h.elf'),str(p/'h.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'h.bin').read_bytes())
    assert bytes(r.u.mem_read(0x4000f850,8)).hex()=='4cd77c1c4fef0034'
    r.u.mem_write(0x4000f850,b'\x4e\xf9'+struct.pack('>I',0x93050000)+b'\x4e\x71')
    notices=[]
    r.stubs[0x93060000]=lambda args:notices.append(args[:2]) or 0xdeadbeef
    r.u.hook_add(UC_HOOK_CODE,r.stub,begin=0x93060000,end=0x93060000)
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
            state.update(slot=slot,available=available,convert=converted,save=saved);calls.clear();notices.clear()
            result=r.call(0x4000f762,OBJ,slot,callback)&255
            assert result==int(available and converted and saved),(state,result,calls)
            expected=['retrieve']
            if available:
                expected+=['convert']
                if converted:expected+=['save']
            assert calls==expected,(calls,expected)
            assert notices==([(OBJ,slot)] if available and converted and saved and (slot<96 or args.working) else []),notices
            assert r.r32(RAW+8)==0x12345678
    print('ok : hook compilé sur épilogue natif, notice après succès seulement, slot0..95 ; résultat natif préservé')
    print('ok : identité inchangée par cette routine avec dépendances simulées')
    print('Limite : Save As complet, slot96, backend disque et raccordement annexe non prouvés')
if __name__=='__main__':main()
