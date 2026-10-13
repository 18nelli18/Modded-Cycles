#!/usr/bin/env python3
"""Writer annexe : vrais wrappers fichier ColdFire, backend simulé sans disque.

Écriture complète/partielle, préparation/finalisation refusées, cleanup natif,
handle fermé et IPL1..7. Aucun hook Save livré par cette preuve.
"""
import argparse,pathlib,subprocess,tempfile,math
from unicorn import UC_HOOK_CODE,m68k_const as mk
from test_seq_gen_menu import Rig
from test_sdvintage import main_os_from_syx
from gen_seq_gen import symbols

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cycles',required=True)
    a=ap.parse_args();root=pathlib.Path(__file__).resolve().parents[2]
    cross=str(root.parent/'toolchain/bin/m68k-elf-')
    r=Rig(main_os_from_syx(a.cycles),{'writes':[]},{'writes':[],'symbols':{}})
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'io.o'),str(root/'tools/machines/midi_lanes/storage_io.s')],check=True)
        subprocess.run([cross+'ld','-Ttext=0x93050000','-e','ml_store_write','-o',str(p/'io.elf'),str(p/'io.o')],check=True)
        subprocess.run([cross+'objcopy','-O','binary',str(p/'io.elf'),str(p/'io.bin')],check=True)
        r.u.mem_write(0x93050000,(p/'io.bin').read_bytes());r.s=symbols(cross,p/'io.elf')
    path,record=0x93070000,0x93071000
    r.u.mem_write(path,b'/MidiBanks/test-B\0');data=bytes(i%251 for i in range(1616));r.u.mem_write(record,data)
    calls=[];state={'open':0,'prepare':0,'write':1616,'final':0};handle=[0]
    def opened(args):
        assert args[0]==path and r.string(args[1])=='w'
        assert bytes(r.u.mem_read(args[2],16))==bytes(16)
        calls.append('open');handle[0]=args[2]
        if not state['open']:
            for off,v in enumerate((42,0,1,1)):r.w32(args[2]+4*off,v)
            r.w32(0x40fe8e10+4,1<<10)
        return state['open']
    def prepare(args):
        assert args[:3]==(42,0,1616),args[:3]
        calls.append('prepare');return state['prepare']
    def written(args):
        inode,offset,size,source=args[:4]
        assert inode==42 and source==record+offset and 0<size<=512 and offset+size<=1616,args[:4]
        assert bytes(r.u.mem_read(source,size))==data[offset:offset+size]
        calls.append('write');return min(size,state['write']) if state['write']>0 else state['write']
    def finalized(args):
        assert args[0]==42
        calls.append('final');return state['final']
    for addr,fn in ((0x4007bc5e,opened),(0x4007b742,prepare),(0x4007b972,written),
                    (0x4007e13a,finalized),(0x40001cc4,lambda args:0),(0x40001df6,lambda args:0)):
        r.stubs[addr]=fn;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=addr,end=addr)
    def closing(u,addr,size,ctx):calls.append('close')
    r.u.hook_add(UC_HOOK_CODE,closing,begin=0x4007bc1c,end=0x4007bc1c)
    r.w32(0x40f07cf4,1)
    for opened_status,pre,count,final in ((0,0,1616,0),(1,0,1616,0),(0,1,1616,0),
            (0,-1,1616,0),(0,0,100,0),(0,0,0,0),(0,0,-1,0),
            (0,0,1616,1),(0,0,1616,-1)):
        state.update(open=opened_status,prepare=pre,write=count,final=final);calls.clear()
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
        expected=int(not opened_status and not pre and count>0 and not final)
        assert r.call('ml_store_write',path,record,1616)==expected,(state,calls)
        want=['open']
        if not opened_status:
            want+=['prepare']
            if not pre:
                want+=['write']*(math.ceil(1616/min(count,512)) if count>0 else 1)
                if count>0:want+=['final']
            want+=['close']
            assert r.r32(handle[0]+12)==0 and r.r32(0x40fe8e10+4)==0
        assert calls==want,(state,calls,want)
        assert bytes(r.u.mem_read(record,1616))==data
    for ipl in range(1,8):
        r.u.reg_write(mk.UC_M68K_REG_SR,0x2000|(ipl<<8));calls.clear()
        assert r.call('ml_store_write',path,record,1616)==0 and not calls
    r.u.reg_write(mk.UC_M68K_REG_SR,0x2000)
    for p,b,n in ((0,record,1616),(path,0,1616),(path,record,1615)):
        calls.clear();assert r.call('ml_store_write',p,b,n)==0 and not calls
    print('ok : vrais wrappers preallocate/write/finalize/close ; backends simulés, ordre et retours validés')
    print('ok : échec à chaque étape, écriture partielle positive reprise, zéro/erreur refusés, handle/bitmap libérés ; source inchangée ; aucun disque écrit')
    print('ok : IPL1..7 et arguments invalides refusés ; durabilité physique et hooks Save restent à prouver')
if __name__=='__main__':main()
