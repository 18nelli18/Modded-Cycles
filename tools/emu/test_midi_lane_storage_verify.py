#!/usr/bin/env python3
"""Relecture ColdFire : backend simulé, aucune écriture disque ni hook Save."""
import argparse, pathlib, subprocess, tempfile
from unicorn import UC_HOOK_CODE, m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True);ap.add_argument('--extended',action='store_true');ap.add_argument('--audio-lfo',action='store_true')
    args=ap.parse_args();size=5024 if args.audio_lfo else (4928 if args.extended else 1616);root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    r=Rig(main_os_from_syx(args.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e',*(['--defsym','ML_STORAGE3=1'] if args.audio_lfo else (['--defsym','ML_STORAGE2=1'] if args.extended else [])),'-o',str(p/'v.o'),str(root/'tools/machines/midi_lanes/storage_verify.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0x93050000','--defsym=ml_store_write=0x93060000','--defsym=ml_store_read=0x93060004','-e','ml_store_verified','-o',str(p/'v.elf'),str(p/'v.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'v.elf'),str(p/'v.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'v.bin').read_bytes());r.s=symbols(cross,p/'v.elf')
    path,record,scratch=0x93070000,0x93071000,0x93074000
    data=bytes(i%251 for i in range(size));r.u.mem_write(record,data)
    state={'write':1,'read':1,'bad':None};calls=[]
    def write(a):
        assert a[:3]==(path,record,size);calls.append('write');return state['write']
    def read(a):
        assert a[:3]==(path,scratch,size);calls.append('read')
        out=bytearray(data)
        if state['bad'] is not None:out[state['bad']]^=1
        r.u.mem_write(scratch,bytes(out));return state['read']
    for addr,fn in ((0x93060000,write),(0x93060004,read)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    for w,rd,bad in ([(1,1,None),(0,1,None),(1,0,None)]+[(1,1,i) for i in sorted({0,800,1615,size-1,*([1616,4927] if size>1616 else [])})]):
        state.update(write=w,read=rd,bad=bad);calls.clear();r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        assert r.call('ml_store_verified',path,record,scratch,size)==int(w and rd and bad is None)
        assert calls==(['write','read'] if w else ['write'])
        assert bytes(r.u.mem_read(record,size))==data
    for p,b,s,n in ((0,record,scratch,size),(path,0,scratch,size),(path,record,0,size),(path,record,record,size),(path,record,record+size-1,size),(path,scratch+1,scratch,size),(path,record,scratch,size-1)):
        calls.clear();assert r.call('ml_store_verified',p,b,s,n)==0 and not calls
    for ipl in range(1,8):
        calls.clear();r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8))
        assert r.call('ml_store_verified',path,record,scratch,size)==0 and not calls
    print('ok : écriture/relecture ordonnées ; différences début/milieu/fin et erreurs refusées')
    print('ok : source intacte, tampons chevauchants et IPL1..7 refusés ; backend simulé, pas de hook Save')
if __name__=='__main__':main()
