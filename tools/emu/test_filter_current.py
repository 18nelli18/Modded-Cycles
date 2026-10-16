#!/usr/bin/env python3
"""Note 102 : vrai SYX, ladder six pistes, precision, resonance et ABI.
Allocateur/peripheriques simules ; aucune validation materielle inventee.
"""
import argparse,json,pathlib,struct,sys,math
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_INVALID,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP,RAW,EVENT,OBJ,VT,GET,SIGNAL
from test_sdvintage import main_os_from_syx
import build

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',required=True);p.add_argument('--inject',action='store_true');p.add_argument('--precision-data');a=p.parse_args()
    prefix=pathlib.Path(a.case);cat=json.loads(prefix.with_suffix('.json').read_text())['tweaks']
    bank=next((t for t in cat if t['id']=='midi-out-bank'),None);img=main_os_from_syx(str(prefix.with_suffix('.syx')))
    r=Rig(img,{'writes':[]},{'writes':[],'symbols':bank['symbols'] if bank else {}});u=r.u
    for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000),(0x90000000,0x20000)]:u.mem_map(at,size)
    u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
    def fault(u,access,addr,size,value,data):print('FAULT',hex(u.reg_read(mk.UC_M68K_REG_PC)),hex(addr),size,flush=True);return False
    u.hook_add(UC_HOOK_MEM_INVALID,fault)
    def cache(u,pc,size,data):u.reg_write(mk.UC_M68K_REG_PC,pc+4)
    sites=set()
    for at,raw in [(build.BASE,img)]+[(int(p['dest'],16),bytes.fromhex(p['hex'])) for t in cat if t.get('append') for p in t['append']['parts'] if 'hex' in p]:
        sites.update(at+i for i in range(0,len(raw)-3,2) if raw[i:i+2]==b'\x4e\x7b')
    for site in sites:u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
    u.emu_start(0x40000530,0x4000053a,count=200_000_000)
    assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,'boot incomplet'
    print('PASS vrai bootstrap navigateur',flush=True)
    r.call(0x4007929c)
    ws=next(t['symbols'] for t in cat if t['id']=='sample-wizard')
    fs=next(t['symbols'] for t in cat if t['id']=='wizard-continuous-filter')
    addr=lambda n:int(ws[n],16)
    precision=None
    if a.precision_data:
        import emac
        text=pathlib.Path(a.precision_data).read_text();precision=json.loads(text[text.index('=')+1:].strip().rstrip(';'))
        patch=bytes.fromhex(precision['hex'])
        if a.inject:u.mem_write(precision['at'],patch)
        else:assert bytes(u.mem_read(precision['at'],len(patch)))==patch,'filtre navigateur absent/alteré au boot/cache'
        codefile=pathlib.Path('build/filter-precision-code.bin');codefile.write_bytes(patch)
        r.emac=emac.EMAC(u);r.emac.install(emac.disasm(str(codefile),precision['at'],precision['at'],precision['at']+precision['code_size']))
    frame,buf=0x93070000,0x93071000
    def coef(lane,cut,res):
        u.mem_write(frame,bytes(80));u.mem_write(frame+48,struct.pack('>hh',cut*256,res*256))
        u.reg_write(mk.UC_M68K_REG_D1,15);u.reg_write(mk.UC_M68K_REG_D2,lane);u.reg_write(mk.UC_M68K_REG_A2,frame)
        r.call(addr('gflt_coef'))
    quality=[]
    for cut in (127,126,96,64,32,0):
        for level in (1<<29,1<<20,1<<15):
            outputs=[]
            for lane in range(6):
                for state in ('gflt_y1','gflt_y2','gflt_y3','gflt_y4'):r.w32(addr(state)+4*lane,0)
                coef(lane,cut,0);out=[]
                for block in range(20):
                    values=[int(level*math.sin(2*math.pi*220*(block*32+i)/48000)) for i in range(32)]
                    u.mem_write(buf,struct.pack('>32i',*values))
                    try:r.call(int(fs['avfc_run'],16),buf,lane)
                    except Exception:
                        pc=u.reg_read(mk.UC_M68K_REG_PC);print('PC',hex(pc),bytes(u.mem_read(pc,16)).hex(),'cut',cut,'f',r.r32(addr('gflt_f')+4*lane),flush=True);raise
                    out+=struct.unpack('>32i',bytes(u.mem_read(buf,128)))
                outputs.append(out)
            assert all(x==outputs[0] for x in outputs),'difference track 6 '+str((cut,level))
            if cut==127:assert outputs[0]==[int(level*math.sin(2*math.pi*220*i/48000)) for i in range(640)],'bypass non exact'
            if cut==96 and level in (1<<20,1<<15):
                f=r.r32(addr('gflt_f'))/4096;state=[0.0]*4;ref=[]
                for j in range(640):
                    v=int(level*math.sin(2*math.pi*220*j/48000))
                    for pole in range(4):state[pole]+=f*(v-state[pole]);v=state[pole]
                    ref.append(v)
                power=sum(v*v for v in ref[128:]);error=sum((v-w)**2 for v,w in zip(ref[128:],outputs[-1][128:]));snr=10*math.log10(power/max(error,1e-20));quality.append(snr)
                print('MESURE SNR',level,round(snr,2),'dB',flush=True)
                if precision:assert snr>(45 if level==1<<20 else 30),('precision insuffisante',snr)
            print('PASS ladder six pistes identiques',cut,level,'peak',max(abs(x) for x in outputs[-1]),flush=True)
    if precision:
        # Balayage resonance et toutes les voies, y compris l'indice 5 signale.
        regs=[getattr(mk,'UC_M68K_REG_D'+str(i)) for i in range(2,8)]+[getattr(mk,'UC_M68K_REG_A'+str(i)) for i in range(2,7)]
        for cut in (0,32,64,96,126):
            for res in (32,96,127):
                for lane in range(6):
                    for name in ('gflt_y1','gflt_y2','gflt_y3','gflt_y4'):r.w32(addr(name)+4*lane,0)
                    coef(lane,cut,res)
                    for reg in regs:u.reg_write(reg,0x12345678)
                    r.emac.macsr=0x20;r.emac.acc[:]=[0,111,222,333]
                    for block in range(8):
                        u.mem_write(buf,struct.pack('>32i',*([0x70000000 if i&1 else -0x70000000 for i in range(32)])))
                        r.call(addr('gflt_run'),buf,lane)
                        assert all(u.reg_read(reg)==0x12345678 for reg in regs),'ABI'
                        assert r.emac.macsr==0x20 and r.emac.acc==[0,111,222,333],'EMAC ABI'
                        assert all(abs(v)<0x80000000 for v in struct.unpack('>32i',bytes(u.mem_read(buf,128))))
        for lane in range(6):
            coef(lane,64,0)
            for name in ('gflt_y1','gflt_y2','gflt_y3','gflt_y4'):r.w32(addr(name)+4*lane,256)
            u.mem_write(buf,bytes(128));r.call(addr('gflt_run'),buf,lane)
            assert bytes(u.mem_read(buf,128))==bytes(128)
            assert all(r.r32(addr(name)+4*lane)==0 for name in ('gflt_y1','gflt_y2','gflt_y3','gflt_y4'))
        print('PASS silence : retour exact au zero, voie inactive sans ladder',flush=True)
        print('PASS resonance/cutoff : six pistes, registres, MACSR, accumulateurs et bornes',flush=True)
    retro=next((t for t in cat if 'retrosyn_update' in t.get('symbols',{})),None)
    if retro:
        import mcengine as E
        from test_model_tg import engine
        source=bank or retro;pay=int(source['append']['dest'],16)
        image=bytes(u.mem_read(build.BASE,len(img)));runtime=bytes(u.mem_read(pay,source['append']['size']))
        e=engine(image,end=build.BASE+len(image),payload=(pay,runtime))
        e.uc.mem_write(0x80000000,bytes(u.mem_read(0x80000000,0x20000)))
        for lane in range(6):
            e.set(lane,machine=16 if 'all-machines' in retro['id'] else 7,note=60,color=64,shape=0,sweep=64,contour=0,decay=90)
            e.uc.mem_write(E.PARAMS+14+66*lane+46,struct.pack('>3h',0,96*256,0))
        for block in range(20):
            dry=e.block(63 if block==0 else 0)
            coefs=[int.from_bytes(e.uc.mem_read(addr('gflt_f')+4*i,4),'big') for i in range(6)]
            filtered=[]
            for lane in range(6):
                e.call(int(fs['avfc_run'],16),E.TRACK_BASE+128*lane,lane)
                filtered.append(struct.unpack('>32i',bytes(e.uc.mem_read(E.TRACK_BASE+128*lane,128))))
            assert all(coef==coefs[0] for coef in coefs),('coefs',coefs)
            assert all(row==filtered[0] for row in filtered),('voix piste 6',block,[max(abs(v) for v in row) for row in filtered])
        print('PASS vraies six voix RETROSYN : memes coefficients et son filtre identique',flush=True)
    if precision:
        print('PASS precision faible niveau : SNR',quality,flush=True)
    print('LIMITES : peripheriques simules ; comportement physique piste 6 a confirmer')
if __name__=='__main__':main()
