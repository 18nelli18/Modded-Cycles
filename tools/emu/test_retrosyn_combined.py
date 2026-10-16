#!/usr/bin/env python3
"""Preuve des 16 machines : boot reel, interface, callbacks TINY/WAVE conserves.

python3 tools/emu/test_retrosyn_combined.py --cycles firmware/model-cycles_OS1.13.syx --syntakt firmware/Syntakt_OS1.42.syx --catalog firmware/tiny-catalogue.json
"""
import argparse,ctypes,json,pathlib,struct,sys,tempfile,os,shutil
from types import SimpleNamespace
import numpy as np
from unicorn import Uc,UC_ARCH_M68K,UC_MODE_BIG_ENDIAN,UC_HOOK_CODE
from unicorn import m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
import gen_retrosyn as R,gen_syntakt_engines as gs,build,syntakt,mcengine as E
import test_macro_syntakt as MS
import test_syntakt_machines as UI
import test_sdvintage_7th as T
import test_model_tg as SamplerHarness

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('cycles','syntakt','catalog'):ap.add_argument('--'+k,required=True)
    ap.add_argument('--wizard',action='store_true')
    a=ap.parse_args();alias=tempfile.TemporaryDirectory();os.symlink(shutil.which('m68k-linux-gnu-objdump'),pathlib.Path(alias.name)/'m68k-elf-objdump');os.environ['PATH']=alias.name+os.pathsep+os.environ['PATH']
    stock=R.g7.cycles_main(a.cycles);st=syntakt.dsp_image(a.syntakt)
    cat=json.loads(pathlib.Path(a.catalog).read_text())
    variant=cat['variants']['511'] if a.wizard else cat['normal']['255']
    base=variant['engine']
    t=json.loads((R.DEV/('29-retrosyn-all-machines-wizard.json' if a.wizard else '28-retrosyn-all-machines.json')).read_text());pay=int(t['append']['dest'],16)
    gs.set_base(pay);lay=gs.analyse(st,gs.generation(['sd','cp','toy','bits','swarm']))['lay']
    chord=MS.chord_tables(stock)
    def image(tw):
        ts=([tw.get('sampler_recipe',variant['wizard'])] if a.wizard else [])+[tw]
        p,_=build.apply_writes(stock,ts);pl,_=build.build_payload(ts,stock,a.syntakt)
        rt=bytearray(build.payload_runtime(tw,stock,st));o=lay['chord_at']-pay;rt[o:o+len(chord)]=chord
        return bytes(p)+pl,bytes(rt)
    img,rt=image(t);oldimg,oldrt=image(base)
    # Le vrai crochet aPLib et son deuxieme etage, depuis une SDRAM sale.
    uc=Uc(UC_ARCH_M68K,UC_MODE_BIG_ENDIAN);uc.ctl_set_cpu_model(mk.UC_CPU_M68K_ANY)
    for addr,size in [(0x40000000,0x2400000),(pay,0x100000),(0x80000000,0x10000),(0x90000000,0x20000)]:uc.mem_map(addr,size)
    uc.mem_write(E.BASE,img);uc.mem_write(pay,b'\xa5'*0x100000)
    for lo,hi,dst in gs.CY_SRAM_INIT:uc.mem_write(dst,img[lo-E.BASE:hi-E.BASE])
    uc.mem_write(E.STOP,b'\x4e\x71');uc.reg_write(mk.UC_M68K_REG_SR,0x2700)
    uc.reg_write(mk.UC_M68K_REG_A7,E.STACK);uc.mem_write(E.STACK,struct.pack('>I',E.STOP))
    stale=MS.icache_watch(uc,SimpleNamespace(img=img),pay)
    target=int(t['sampler_recipe']['symbols']['boot_extra_hook'],16) if a.wizard else E.STOP
    uc.emu_start(gs.BOOT_CALL if a.wizard else 0x400004b2,target,count=200_000_000)
    assert uc.reg_read(mk.UC_M68K_REG_PC)==target
    assert bytes(uc.mem_read(pay,len(rt)))==rt
    assert stale[1] and not stale[0]
    print('ok boot aPLib, BSS, tables CHORD, cache instructions')
    if a.wizard:
        # Le constructeur OS construit 17 rangees et le dernier descripteur est RETROSYN.
        class WizardUI(T.UI):
            def __init__(self,img,payload=b''):
                super().__init__(img,payload)
                self.uc.mem_write(E.BASE,img)
                self.uc.mem_map(pay,0x100000);self.uc.mem_write(pay,payload)
        u=WizardUI(img,rt);u.call(0x4005a274)
        assert u.u32(T.ROW_COUNT)==17
        assert u.call(0x4005a692,12,16)==122
        assert not u.bad
        print('ok Sample Wizard independant : 17 machines, RETROSYN apres TINY')
        def eng(im,runtime):return SamplerHarness.engine(im,end=int(t['sampler_recipe']['append']['at'],16)+t['sampler_recipe']['append']['size'],payload=(pay,runtime))
        for machine in range(17):
            oldmachine=machine if machine<16 else None
            ea=eng(oldimg,oldrt) if oldmachine is not None else None
            eb=eng(img,rt)
            for e in ([ea,eb] if ea else [eb]):
                for tr in range(6):e.set(tr,machine=machine,note=48+tr*3,color=64,shape=0,sweep=64,contour=0,decay=90)
            audible=False
            for b in range(8):
                y=eb.block(63 if b==0 else 0);audible|=bool(np.any(y))
                if ea:assert np.array_equal(ea.block(63 if b==0 else 0),y),(machine,b)
            assert not eb.unmapped
            if machine==16:assert audible
            print('ok Wizard audio',t['machine_names'][machine])
        return
    # Donnees decodees du resultat, verifiees par les vraies fonctions UI OS.
    def u32(addr):return struct.unpack_from('>I',rt,addr-pay)[0]
    def text(addr):return rt[addr-pay:rt.index(b'\0',addr-pay)].decode('ascii')
    desc=pay+0x33c00;data=pay+0x33800
    added=[]
    for j in range(10):
        knobs=[];d=desc+(76+5*j)*56
        for k in range(4):
            at=d+56*k;knobs.append((text(u32(at+44)),text(u32(at+52)),u32(at+16)>>8,u32(at+8)>>8,u32(at+12)>>8))
        image=gs.CATALOG[['sd','cp','toy','bits','swarm'][j]]['image'] if j<5 else 4
        added.append(dict(name=t['machine_names'][6+j],label=t['machine_names'][6+j],image=image,
                          index=6+j,knobs=knobs,decay=u32(d+4*56+16)>>8))
    UI.SAFE=True;UI.ADDED=added;UI.N=10;UI.NM=16;UI.TOP=15;UI.NAMES=t['machine_names']
    UI.FIRST={6+i:76+5*i for i in range(10)};UI.REC={6+i:pay+0x84800+96*i for i in range(10)}
    UI.ROWS=pay+0x84000;UI.CCROWS=pay+0x84400
    gs.MARKS_ROW=9;gs.MARKS['x']=68
    OriginalUI=UI.UI
    class RelocatedUI(OriginalUI):
        def __init__(self,img,payload=b''):
            super().__init__(img,payload)
            self.uc.mem_map(pay,0x100000)
            self.uc.mem_write(pay,payload)
    UI.UI=RelocatedUI
    T.UI=RelocatedUI
    aa,bb=UI.tables(stock,img,rt);UI.lookups(aa,bb);UI.accessors(aa,bb,stock,img)
    UI.screens(stock,img,rt);UI.setter_and_wheel(stock,img,rt);UI.records_and_change(stock,img,rt)
    UI.out_of_range(stock,img,rt);UI.small_icon(stock,img,rt)
    assert not T.FAIL,T.FAIL
    # Chaque ancienne machine conserve son son sur les six pistes.
    for machine in range(15):
        engines=[E.Engine(oldimg,payload=(pay,oldrt)),E.Engine(img,payload=(pay,rt))]
        for e in engines:
            for tr in range(6):e.set(tr,machine=machine,note=48+tr*3,color=64,shape=0,sweep=64,contour=0,decay=90)
        for b in range(10):
            x,y=[e.block(63 if b==0 else 0) for e in engines]
            assert np.array_equal(x,y),(machine,b,np.max(np.abs(x-y)))
        print('ok audio conserve',t['machine_names'][machine])
    e=E.Engine(img,payload=(pay,rt))
    for tr in range(6):e.set(tr,machine=15,note=48+tr*3,sweep=64,decay=90)
    e.block(63);out=e.block(0);assert np.any(out)
    assert not e.unmapped
    print('ok RETROSYN audible apres TINY, 16 machines, aucune lecture hors memoire')

if __name__=='__main__':main()
