#!/usr/bin/env python3
"""RETROSYN/ChordKeys : vrai bootstrap, clear BSS, cache et copie partagee.

Lit la selection et le SYX reel produits par le test navigateur. MOVEC est
observe, sans modele physique du cache ; aucun resultat materiel revendique.
"""
import argparse,json,pathlib,struct,sys
from unicorn import UC_HOOK_CODE,m68k_const as mk
HERE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from test_seq_gen_menu import Rig,STACK,STOP
from test_sdvintage import main_os_from_syx
import build

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--case',required=True);a=p.parse_args()
    prefix=pathlib.Path(a.case)
    chosen=json.loads(prefix.with_suffix('.json').read_text())['tweaks']
    img=main_os_from_syx(str(prefix.with_suffix('.syx')))
    ck=next(t for t in chosen if t['id']=='chord-keys-supermodel' or 'chord_keys_build' in t.get('symbols',{}))
    engine=next(t for t in chosen if t['id'].startswith('retrosyn'))
    r=Rig(img,{'writes':[]},{'writes':[],'symbols':ck['symbols']});u=r.u
    for at,size in [(0x43000000,0x800000),(0x46700000,0x400000),(0x80000000,0x200000)]:u.mem_map(at,size)
    u.mem_write(STACK,struct.pack('>I',STOP));u.reg_write(mk.UC_M68K_REG_A7,STACK)
    events=[]
    def cache(u,pc,size,data):
        events.append(pc);u.reg_write(mk.UC_M68K_REG_PC,pc+4)
    for t in chosen:
        for w in t['writes']:
            raw=bytes.fromhex(w['new'])
            for i in range(0,len(raw)-3,2):
                if raw[i:i+2]==b'\x4e\x7b':
                    site=build.BASE+w['off']+i;u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
        for part in t.get('append',{}).get('parts',[]):
            raw=bytes.fromhex(part.get('hex',''))
            for i in range(0,len(raw)-3,2):
                if raw[i:i+2]==b'\x4e\x7b':
                    site=int(part['dest'],16)+i;u.hook_add(UC_HOOK_CODE,cache,begin=site,end=site)
    try:u.emu_start(0x40000530,0x4000053a,count=200_000_000)
    except Exception:
        print('PC',hex(u.reg_read(mk.UC_M68K_REG_PC)), 'A0',hex(u.reg_read(mk.UC_M68K_REG_A0)),flush=True);raise
    assert u.reg_read(mk.UC_M68K_REG_PC)==0x4000053a,hex(u.reg_read(mk.UC_M68K_REG_PC))
    if ck['id']=='chord-keys-supermodel':
        raw=bytes.fromhex(engine['append']['parts'][-1]['hex']) if engine.get('chord_source') else bytes.fromhex(ck['append']['parts'][0]['hex'])
        address=0x401c383c
    else:
        address=int(ck['symbols']['chord_keys_build'],16)
        part=next(p for p in ck['append']['parts'] if int(p['dest'],16)<=address<int(p['dest'],16)+len(p.get('hex',''))//2)
        offset=address-int(part['dest'],16);raw=bytes.fromhex(part['hex'])[offset:offset+64]
    assert bytes(u.mem_read(address,len(raw)))==raw,'ChordKeys ecrase au boot'
    for name in ['retrosyn_update','retrosyn_render']:
        address_r=int(engine['symbols'][name],16)
        part=next(p for p in engine['append']['parts'] if int(p['dest'],16)<=address_r<int(p['dest'],16)+len(p.get('hex',''))//2)
        offset=address_r-int(part['dest'],16);expected=bytes.fromhex(part['hex'])[offset:offset+32]
        assert bytes(u.mem_read(address_r,len(expected)))==expected,'RETROSYN absent au boot'
    assert u.reg_read(mk.UC_M68K_REG_A7)==STACK-4,'contrat de pile boot'
    r.call(0x4007929c)
    assert bytes(u.mem_read(address,len(raw)))==raw,'ChordKeys ecrase par le cache disque'
    assert events,'invalidation cache absente'

    print('ok boot RETROSYN + ChordKeys, clear BSS et cache disque natifs, code ChordKeys exact',flush=True)

if __name__=='__main__':main()




