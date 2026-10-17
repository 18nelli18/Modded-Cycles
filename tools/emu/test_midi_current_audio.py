#!/usr/bin/env python3
"""Comparer les 17 moteurs du main avec/sans Banque, apres leurs vrais boots.

Les SYX restent locaux. MOVEC observe sans simulation du cache physique.
"""
import argparse,json,pathlib,struct,sys,tempfile,os,shutil
from types import SimpleNamespace
import numpy as np
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build,mcengine as E,test_model_tg as Harness

def boot(prefix,with_sram=False):
    prefix=pathlib.Path(prefix);ts=json.loads(prefix.with_suffix('.json').read_text())['tweaks']
    img=main_os_from_syx(str(prefix.with_suffix('.syx')))
    r=Rig(img,{'writes':[]},{'writes':[],'symbols':{}});u=r.u
    for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,size)
    sites=set()
    for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in ts for p in t.get('append',{}).get('parts',[]) if 'hex' in p]:
        sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
    def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
    for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
    u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
    u.emu_start(0x40000530,0x4000053a,count=200_000_000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a
    ap=next(t['append'] for t in ts if t.get('append',{}).get('dest')=='0x46700000')
    if with_sram:r.call(0x4007929c)
    result=bytes(u.mem_read(build.BASE,0x40200000-build.BASE)),bytes(u.mem_read(0x46700000,ap['size'])),ts
    return result+(bytes(u.mem_read(0x80000000,0x10000)),) if with_sram else result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True);p.add_argument('--baseline',required=True);p.add_argument('--blocks',type=int,default=8);a=p.parse_args()
    alias=tempfile.TemporaryDirectory();os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
    baseline=boot(a.baseline);candidate=boot(a.case)
    names=next(t['machine_names'] for t in candidate[2] if t.get('machine_names'))
    for machine,name in enumerate(names):
        engines=[Harness.engine(img,payload=(0x46700000,rt)) for img,rt,ts in (baseline,candidate)]
        for e in engines:
            for track in range(6):e.set(track,machine=machine,note=48+track*3,color=64,shape=0,sweep=64,contour=0,decay=90)
        for block in range(a.blocks):
            x,y=[e.block(63 if block==0 else 0) for e in engines]
            assert np.array_equal(x,y),(name,block,int(np.max(np.abs(x-y))))
        assert not any(e.unmapped for e in engines)
        print('PASS audio identique six pistes : '+name,flush=True)
    print('ok',len(names),'moteurs,',a.blocks,'blocs chacun, Banque inactive ; pas de mesure CPU materielle')
if __name__=='__main__':main()
