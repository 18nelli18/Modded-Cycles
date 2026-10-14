#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tempo stock au-dessus de B RAM : --base recette --cycles OS1.13 --output JSON.

Ne réactive aucune sauvegarde. Réutilise uniquement le corps propre devenu
inerte de save_notice, conserve tous les symboles musicaux et vérifie les octets.
"""
import argparse, copy, hashlib, json, pathlib, shutil, struct, subprocess, tempfile
import aplib_dense, build
from gen_seq_gen import main_os_from_syx, STOCK, symbols
ROOT=pathlib.Path(__file__).resolve().parents[1]

def generate(base, stock, cross=None):
    assert hashlib.sha256(stock).hexdigest()==STOCK
    t=copy.deepcopy(base);assert t['ram_only_rollback'] and t['id']=='midi-bank-bundle'
    s={k:int(v,16) for k,v in t['symbols'].items()}
    assert all(build.BASE+w['off'] not in (0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6) for w in t['writes'])
    part=t['append']['parts'][0];assert len(t['append']['parts'])==1
    dest=int(part['dest'],16);raw=bytearray.fromhex(part['hex'])
    for k in ('ml_store_service','ml_store_bootstrap','ml_store_save_notice'):
        assert raw[s[k]-dest:s[k]-dest+2]==b'\x4e\x75'
    # Deux branches propres contiguës REC/SETTINGS vers le même handler global.
    lo=s['mlp_menu_key']-dest
    at=raw.find(bytes.fromhex('0c82000000096700'),lo,lo+0x200);assert at>=lo
    assert raw[at+10:at+18]==bytes.fromhex('0c820000000d6700')
    global_pc=dest+at+8+struct.unpack('>h',raw[at+8:at+10])[0]
    assert global_pc==dest+at+18+struct.unpack('>h',raw[at+18:at+20])[0]
    start=s['ml_store_save_notice']+2;end=s['ml_store_save_hook']
    assert end-start==362
    assert not [k for k,v in s.items() if start<=v<end], 'symbole vivant dans la réserve'
    cross=cross or next((c for c in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(c+'as')), 'm68k-linux-gnu-')
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)
        subprocess.run([cross+'as','-march=cfv4e','-o',str(p/'t.o'),str(ROOT/'tools/machines/midi_lanes/tempo.s')],check=True)
        defs={'mlp_obj':s['mlp_obj'],'ml_settings_native':s['ml_settings_native'],'ml_settings_toggle':s['ml_settings_toggle'],'ml_tempo_global':global_pc,'ml_tempo_bank_continue':s['ml_toggle']+6}
        (p/'link.ld').write_text('\n'.join(k+' = '+hex(v)+';' for k,v in defs.items())+'\nSECTIONS { .dispatch '+hex(dest+at)+' : { *(.text.tempo_dispatch) } .text '+hex(start)+' : { *(.text) } }')
        subprocess.run([cross+'ld','-T',str(p/'link.ld'),'-e','ml_tempo_present','-o',str(p/'t.elf'),str(p/'t.o')],check=True)
        new=symbols(cross,p/'t.elf')
        for section in ('dispatch','text'):
            subprocess.run([cross+'objcopy','-O','binary','--only-section=.'+section,str(p/'t.elf'),str(p/(section+'.bin'))],check=True)
        dispatch=(p/'dispatch.bin').read_bytes();code=(p/'text.bin').read_bytes()
    assert len(dispatch)==20 and len(code)<=end-start
    raw[at:at+20]=dispatch
    raw[start-dest:end-dest]=code+bytes(end-start-len(code))
    for old,new_name,expected in [('ml_settings_present','ml_tempo_present',b'\x4a\xb9'+struct.pack('>I',s['mlp_obj'])),('ml_toggle','ml_tempo_bank_guard',b'\x20\x79'+struct.pack('>I',s['mlp_obj']))]:
        i=s[old]-dest;assert raw[i:i+6]==expected
        raw[i:i+6]=b'\x4e\xf9'+struct.pack('>I',new[new_name])
    addr=0x4001c23a;off=addr-build.BASE;assert stock[off:off+6].hex()=='4eb940077da8'
    assert not any(w['off']<=off<w['off']+len(bytes.fromhex(w['new'])) for w in t['writes'])
    t['writes'].append(dict(off=off,old=stock[off:off+6].hex(),new=(b'\x4e\xb9'+struct.pack('>I',new['ml_tempo_toggle'])).hex()))
    part['hex']=raw.hex();packed=min((aplib_dense.pack(bytes(raw),depth=d) for d in (32,128,512)),key=len)
    t['append']['compressed_hex']=packed.hex()
    for k,v in new.items():
        if k.startswith('ml_tempo_'):t['symbols'][k]=hex(v)
    t['status']='experimental';t['midi_tempo_native']=True
    t['description']=['Six pistes MIDI parallèles en RAM, avec potards CC, locks, slides et live-rec.','TEMPO ouvre le menu global natif sans quitter B ; fermer revient à B. Sortie B uniquement depuis son accueil.','Données B perdues à extinction ; Save Project sauvegarde uniquement A.']
    # Les anciens hooks attendent le bundle TG ; le seul nouveau hook attend l’OS.
    build.apply_writes(stock,[dict(id='midi-tempo-native',writes=[t['writes'][-1]])])
    return t

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True);p.add_argument('--cycles',required=True);p.add_argument('--output',required=True);p.add_argument('--cross');p.add_argument('--check',action='store_true');a=p.parse_args()
    t=generate(json.loads(pathlib.Path(a.base).read_text()),main_os_from_syx(a.cycles),a.cross)
    text=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
    if a.check:assert out.read_text()==text
    else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text)
    print('ok : TEMPO natif en B, réserves propres, aucun hook disque ; '+str(len(bytes.fromhex(t['append']['compressed_hex'])))+' octets compressés')
if __name__=='__main__':main()
