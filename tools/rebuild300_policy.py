"""Contrat des sections retirees et des donnees de transit du chargeur remplace.

Ne change ni adresses natives ni machines partagees. Les anciens points ABI
MIDI gardent leurs JMP vers les versions sans ChordKeys ; leurs corps morts
ne font plus partie du payload. Deux petits adaptateurs communs sont assembles
depuis leurs sources, pas copies comme une pretendue feature desactivee.
"""
from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta,areas,proof,output):
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ.get('PATH','')
    edits=[]
    def region(at,size):
        for base,raw in areas:
            if base<=at and at+size<=base+len(raw):return raw,at-base
        raise ValueError(('outside captured region',hex(at),size))
    def get(at,size):
        raw,offset=region(at,size);return bytes(raw[offset:offset+size])
    def change(at,data,owner,kind):
        raw,offset=region(at,len(data));old=bytes(raw[offset:offset+len(data)])
        if old==data:return
        raw[offset:offset+len(data)]=data
        edits.append(dict(address=at,bytes=len(data),owner=owner,kind=kind,
                          old_sha256=hashlib.sha256(old).hexdigest(),new_sha256=hashlib.sha256(data).hexdigest()))
    def erase(at,size,owner):change(at,bytes(size),owner,'remove')
    # Le layout Syntakt declare ces deux banques comme zone de transit, non
    # comme adresse d'execution. Le vrai code reste dans le snapshot SRAM.
    for copy in proof.get('runtime_to_final_copies',[]):
        if copy['source'] in (0x46700000,0x46705858,0x4672e900,0x46794700):
            lo,hi=copy['source'],copy['source']+copy['bytes']
            # La banque de transit CK reutilise aussi la fenetre de donnees
            # Syntakt apres copie. Garder son etat initial tant que les champs
            # effectivement lus n'ont pas une initialisation source verifiee.
            for begin,end in ((lo,min(hi,0x46730000)),(max(lo,0x46731000),hi)):
                if begin<end:erase(begin,end-begin,'boot-only staging copied to '+hex(copy['destination']))
    # Chargeurs remplaces. Les bornes viennent de leurs recettes/sections,
    # jamais du prochain bloc de RAM arbitraire.
    for at,size,prefix in [(0x4016cae8,192,'4fefffe848d7047c'),
                           (0x401907a4,54,'41f9'),
                           (0x46741b00,86,'41f980001c5c'),
                           (0x467ab320,52,'4feffff448d70301')]:
        if get(at,len(bytes.fromhex(prefix)))==bytes.fromhex(prefix):
            erase(at,size,'superseded boot loader')
    if meta.get('vinyl_removed'):
        sy=meta['fx_menu']['symbols'];lo=sy['fx_vinyl'];hi=sy['fx_reverb']
        expected=b'\x4e\xf9'+struct.pack('>I',meta['per_track_fx']['symbols']['nv_bypass'])
        assert get(lo,6)==expected
        erase(lo+6,hi-lo-6,'retired Vinyl algorithm')
        ps=meta['per_track_fx']['symbols'];at=ps['mf_old_vinyl_bypass']
        following=min(v for v in ps.values() if isinstance(v,int) and at<v<at+128)
        erase(at,following-at,'retired Vinyl trampoline')
    if meta.get('chordkeys_removed'):
        recipe=json.loads((ROOT/'docs/flasher-own-support-test/source/integration-chord-keys.json').read_text())
        # Reassembler les ABI effectivement utilisees par les controles et
        # le codec actuels, sous des noms qui decrivent leur seule fonction.
        obj=output/'shared.o';elf=output/'shared.elf'
        subprocess.run([CROSS+'gcc.exe','-mcpu=54418','-c',str(ROOT/'tools/machines/clean_build/shared_compat.S'),'-o',str(obj)],check=True)
        midi=meta['midi_input_symbols'];ps=meta['per_track_fx']['symbols']
        codec=int(recipe['symbols']['ck_plock_decode_hook'],16)
        banner=int(recipe['symbols']['visible_chord'],16)
        (output/'shared.ld').write_text(f'SECTIONS {{ .midi_return {midi["mi_pad_hook"]:#x} : {{ *(.midi_return) }} .parameter_codec {codec:#x} : {{ *(.parameter_codec) }} .banner_off {banner:#x} : {{ *(.banner_off) }} }}\n')
        subprocess.run([CROSS+'ld.exe','-T',str(output/'shared.ld'),'-o',str(elf),str(obj)],check=True)
        compiled={}
        for section in ('midi_return','parameter_codec','banner_off'):
            target=output/(section+'.bin')
            subprocess.run([CROSS+'objcopy.exe','-O','binary','-j','.'+section,str(elf),str(target)],check=True)
            compiled[section]=target.read_bytes()
        assert compiled['parameter_codec']==get(codec,len(compiled['parameter_codec']))
        # Les anciens handlers sont deja detournes vers nc_* dans le profil
        # courant. Ne conserver que cette delegation, pas l'ancien corps.
        names=('on','off','on_received','off_received','receive_on','receive_off','encoder_block','pad','reset','visible_chord','step_on')
        all_symbols=sorted(set(v for v in midi.values() if isinstance(v,int)))
        for suffix in names:
            at=midi['mi_'+suffix]
            assert get(at,6)==b'\x4e\xf9'+struct.pack('>I',ps['nc_'+suffix]),suffix
            end=min(v for v in all_symbols if v>at)
            erase(at+6,end-at-6,'retired ChordKeys MIDI '+suffix)
        enabled=midi['enabled'];assert midi['mi_encoder_block']>enabled
        erase(enabled,midi['mi_encoder_block']-enabled,'retired ChordKeys enabled predicate')
        # Le corps de PR87 n'a plus aucun proprietaire selectionne dans Main.
        # Le decodeur commun est remis ci-dessous, compile depuis shared_compat.S.
        for unit in recipe['relocation_audit']['placements']:
            erase(int(unit['new'],16),unit['size'],'retired ChordKeys PR87 unit')
        for at,section in [(codec,'parameter_codec'),(banner,'banner_off'),(midi['mi_pad_hook'],'midi_return')]:
            change(at,compiled[section],'shared '+section,'assemble')
        # Ancien pont de pad : retirer aussi ses instructions orphelines,
        # l'epilogue partage est maintenant autonome, sans appel CK.
        end=midi['mi_reset_hook'];start=midi['mi_pad_hook']+len(compiled['midi_return'])
        erase(start,end-start,'retired ChordKeys pad bridge body')
        # Les deux adaptateurs propres ne sont pas des routines Elektron.
        # Main revient au dispatch natif ; ces adaptateurs ne sont plus listes.
        # Le second adaptateur a une limite de section explicite dans sa
        # recette ; ne pas estimer son entree ou couper son prologue.
        private=json.loads((ROOT/'docs/flasher-chord-independent-test/source/chord-independent-tg.json').read_text())
        pad=int(private['symbols']['mpu_pad'],16)
        for part in private['append']['parts']:
            if 'hex' not in part:continue
            lo=int(part['dest'],16);raw=bytes.fromhex(part['hex'])
            if lo<=pad<lo+len(raw):
                expected=raw[pad-lo:]
                assert get(pad,len(expected))==expected
                erase(pad,len(expected),'retired ChordKeys private pad adapter')
                break
        else:raise ValueError('missing private pad ownership')
        # Ce fork de pad ne sert que pad_live PR87. Les anciennes branches
        # vers pad_live/ck_gesture sont verifiees avant de retirer le fork.
        at=0x401beac2;body=get(at,52)
        assert body.startswith(bytes.fromhex('7010b088'))
        assert b'\x4e\xb9'+struct.pack('>I',int(recipe['symbols']['ck_plock_gesture'],16)) in body
        erase(at,52,'retired ChordKeys pad fork')
    # Les installateurs modernes n'ont plus de role : les bindings finaux
    # sont poses par le seul chargeur. Garder les trampolines audio/UI et les
    # helpers de reset, qui ont une duree de vie differente.
    boot_removed=[];boot_unresolved=[]
    for name,item in meta.items():
        if not isinstance(item,dict) or not isinstance(item.get('code_bytes'),int) or not isinstance(item.get('code'),int):continue
        symbols=item.get('symbols',{});roots=[]
        if isinstance(item.get('boot_target'),int):roots.append(item['boot_target'])
        if name=='activity_masks' and 'am_boot_finish' in symbols:roots.append(symbols['am_boot_finish'])
        lo,hi=item['code'],item['code']+item['code_bytes']
        for at in roots:
            if not lo<=at<hi:continue
            end=min([v for v in symbols.values() if isinstance(v,int) and at<v<=hi]+[hi])
            first=get(at,min(8,end-at))
            if first[:2] not in (b'\x4f\xef',b'\x4e\xf9',b'\x4e\x56',b'\x41\xf9'):
                boot_unresolved.append(dict(module=name,address=at,bytes=end-at));continue
            erase(at,end-at,'superseded installer '+name)
            boot_removed.append(dict(module=name,address=at,bytes=end-at))
        for key,start in symbols.items():
            if key.endswith('_guard') and isinstance(start,int) and key+'_end' in symbols:
                end=symbols[key+'_end']
                if lo<=start<end<=hi:erase(start,end-start,'boot-only guard template '+name+'.'+key)
    return dict(edits=edits,changed_bytes=sum(e['bytes'] for e in edits),
                source_assembled_helpers=bool(meta.get('chordkeys_removed')),
                installers_removed=boot_removed,installers_unresolved=boot_unresolved,
                statement='Explicit component policy; behavioral validation required')
