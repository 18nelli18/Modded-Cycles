#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Preuve du maintien des niveaux au rechargement (notes/58), stock contre modifié.
Exécute les vraies fonctions 0x400107d8, 0x400106de et le décodeur 0x4005d080.
Stockage, décodage des sons/FX/séquence et notifications UI sont simulés ; pas de
preuve du temps réel ou du boot complet. Environ 10 s sous Rosetta.
Usage : python3 tools/emu/test_reload_keep_levels.py --cycles model-cycles_OS1.13.syx
        [--with level-pan-values,6ch-usbup,arp,trig-hold --syntakt Syntakt_OS1.42.syx].
"""
import argparse
import json
import random
import struct
import sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
from unicorn import m68k_const as m
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build
import sprites
import gen_reload_keep_levels as G
STACK, FRAME, DEST, PROJECT, VT, HW = 0x90010000,0x90012000,0x90020000,0x90030000,0x90031000,0x90000020
STOP = 0x90000000
SAVED = [m.UC_M68K_REG_D2+i for i in range(6)]+[m.UC_M68K_REG_A2+i for i in range(5)]
class Runner:
    def __init__(self,image):
        self.uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN)
        self.uc.ctl_set_cpu_model(m.UC_CPU_M68K_ANY)
        self.uc.mem_map(0x40000000,0x08000000)
        self.uc.mem_map(0x90000000,0x100000)
        self.uc.mem_map(0x80000000,0x100000)
        self.uc.mem_write(G.BASE,image)
        self.uc.hook_add(UC_HOOK_CODE,self.hook)
    def put(self,a,v):self.uc.mem_write(a,struct.pack('>I',v&0xffffffff))
    def get(self,a):return struct.unpack('>I',self.uc.mem_read(a,4))[0]
    def ret(self,v):
        sp=self.uc.reg_read(m.UC_M68K_REG_A7)
        self.uc.reg_write(m.UC_M68K_REG_D0,v&0xffffffff)
        self.uc.reg_write(m.UC_M68K_REG_PC,self.get(sp))
        self.uc.reg_write(m.UC_M68K_REG_A7,sp+4)
    def hook(self,u,pc,size,_):
        self.steps+=1
        sp=u.reg_read(m.UC_M68K_REG_A7)
        if pc in (0x400d0974,0x400060d8,0x4000ff26):self.ret(1)
        elif pc==0x400d0a10:self.ret(0x90032000)
        elif pc==0x4008c2c2:self.ret(6)
        elif pc==0x4008c324:self.ret(3)
        elif pc==0x4000eae2:self.ret(3)
        elif pc==0x4008c4ce:
            self.reads+=1
            u.mem_write(self.get(sp+8),self.source)
            self.ret(self.io)
        elif pc==HW:self.ret(DEST-2948188-self.index*7094)
        elif pc==0x4008f1f0:
            u.mem_write(self.get(sp+4),bytes(u.mem_read(self.get(sp+8),self.get(sp+12))))
            self.ret(self.get(sp+4))
        elif pc==0x4005cf50:self.ret(1)
        elif pc in (0x4005aecc,0x4005b21a,0x4005b108):
            n={0x4005aecc:100,0x4005b21a:76,0x4005b108:16}[pc]
            self.calls.append((pc,self.get(sp+4),self.get(sp+8)))
            u.mem_write(self.get(sp+4),bytes(u.mem_read(self.get(sp+8),n)))
            self.ret(1)
        elif pc==0x400d1f98:
            self.calls.append((pc,self.get(sp+8),self.get(sp+12)))
            self.ret(0)
        elif pc in (0x400f980c,0x400f7d5c,0x400d3ebe,0x400747c0,0x400d4082,0x4007700e,0x400cf23c):self.ret(0)
        elif pc==0x400802e0:self.ret(0x90033000)
    def execute(self,initial,source,caller,io,index,outer):
        u=self.uc
        self.source=source;self.io=io;self.index=index;self.steps=0;self.reads=0;self.calls=[]
        u.mem_write(STACK-4096,bytes(16384));u.mem_write(DEST,bytes(initial))
        u.mem_write(PROJECT,bytes(256));u.mem_write(VT,bytes(256))
        self.put(PROJECT,VT);self.put(VT+40,HW);self.put(FRAME+4,caller)
        args=(PROJECT,1,index,1,1) if outer else (PROJECT,1,index)
        stop=caller if outer else STOP
        self.put(STACK,stop)
        for i,arg in enumerate(args):self.put(STACK+4+4*i,arg)
        u.reg_write(m.UC_M68K_REG_SR,0x2700);u.reg_write(m.UC_M68K_REG_A7,STACK)
        for i,reg in enumerate(SAVED):u.reg_write(reg,0x11220000+i)
        u.reg_write(m.UC_M68K_REG_A6,FRAME)
        u.emu_start(0x400107d8 if outer else 0x400106de,stop,count=20000)
        assert u.reg_read(m.UC_M68K_REG_PC)==stop,'retour'
        assert u.reg_read(m.UC_M68K_REG_A7)==STACK+4,'pile'
        assert u.reg_read(m.UC_M68K_REG_A6)==FRAME,'cadre'
        for i,reg in enumerate(SAVED):
            if reg!=m.UC_M68K_REG_A6:assert u.reg_read(reg)==0x11220000+i,'ABI'
        version=struct.unpack_from('>I',source)[0]
        assert u.reg_read(m.UC_M68K_REG_D0)&255==(1 if version==4 and io==0 else 0),'résultat'
        assert self.reads==1,'lecture seule'
        return bytes(u.mem_read(DEST,len(initial))),tuple(self.calls)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True);ap.add_argument('--with',dest='others',default='');ap.add_argument('--syntakt')
    a=ap.parse_args();stock=G.main_os(a.cycles);t=G.build_tweak(stock)
    every=[json.loads(f.read_text()) for f in G.OUT.parent.glob('[0-9]*.json')]
    files={x['id']:x for x in every}
    tweaks=[files[x] for x in a.others.split(',') if x]
    build.check_conflicts(tweaks+[t]);payload=build.build_payload(tweaks,stock,a.syntakt)[0]
    base=build.apply_writes(stock,sorted(tweaks,key=lambda x:x['order']))[0]+payload
    patched=build.apply_writes(stock,sorted(tweaks+[t],key=lambda x:x['order']))[0]+payload
    assert patched[0x4000045c-G.BASE:0x40000464-G.BASE]==base[0x4000045c-G.BASE:0x40000464-G.BASE],'boot inchangé'
    size,ptr,_,shared=sprites.MASKS[G.CAVE]
    assert stock[G.CAVE-G.BASE:G.CAVE-G.BASE+size]==stock[shared-G.BASE:shared-G.BASE+size]
    assert [i for i in range(len(stock)-3) if stock[i:i+4]==struct.pack('>I',G.CAVE)]==[ptr-G.BASE]
    print('ok : masque identique, référence unique, recette et boot inchangé')
    before,after=Runner(base),Runner(patched);r=random.Random(113);cases=0;steps=0
    for trial in range(140):
        initial=bytearray(r.randbytes(800));saved=bytearray(r.randbytes(7680))
        for track in range(6):
            live=(trial<<8) if trial<128 else r.randrange(0x7f01)
            struct.pack_into('>H',initial,16+2*track,live)
            struct.pack_into('>H',saved,20+2*track,r.randrange(128)<<8)
        for caller in (0x4001c1a2,0x4001b88a,0x4002cad6):
            for failure in range(3):
                version=3 if failure==1 else 4;io=1 if failure==2 else 0
                struct.pack_into('>I',saved,0,version)
                x,c1=before.execute(initial,bytes(saved),caller,io,(0,1,95)[trial%3],trial>=128)
                y,c2=after.execute(initial,bytes(saved),caller,io,(0,1,95)[trial%3],trial>=128)
                assert c1==c2,'appels natifs identiques'
                expected=bytearray(x)
                if caller==0x4001c1a2 and failure==0:
                    assert y[16:28]==initial[16:28],'six niveaux maintenus'
                    expected[16:28]=initial[16:28]
                assert y==expected,'seuls les niveaux changent'
                cases+=1;steps+=before.steps+after.steps
    print(f'ok : {cases} comparaisons, {steps} instructions ; six niveaux, fractions, trois routes, erreurs, cadre et ABI')
    print('ok : combinaison '+','.join(x['id'] for x in tweaks+[t]))
    print('À vérifier par le mainteneur : playback, MIDI, raccourci et menu sur la machine')
if __name__=='__main__':main()
