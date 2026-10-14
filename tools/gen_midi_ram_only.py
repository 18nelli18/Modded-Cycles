#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Désactiver le raccordement disque d'une recette MIDI propre, garder les CC RAM.

Le corps musical reste identique ; enlever hooks Save/disque et service restore.
--input JSON --output JSON [--check]. Aucun OS ni routine extraite embarqués.
"""
import argparse,copy,json,pathlib,struct
import aplib_dense
NATIVE_SAVE=(0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6)
def generate(base):
 t=copy.deepcopy(base);assert t['id']=='midi-bank-bundle';s={k:int(v,16) for k,v in t['symbols'].items()}
 assert 'mlkc_slide_tick' in s and 'mlkc_enc' in s and 'mlkcs_save_project' not in s
 found={0x40000400+w['off'] for w in t['writes']}
 assert all(x in found for x in NATIVE_SAVE)
 t['writes']=[w for w in t['writes'] if 0x40000400+w['off'] not in NATIVE_SAVE]
 load=next(w for w in t['writes'] if 0x40000400+w['off']==0x4006a660)
 assert load['new']==('4ef9'+struct.pack('>I',s['ml_store_load_hook']).hex()+'4e71')
 # Notification RAM existante : annule retrigger/arp, aucune E/S ni remplacement de table.
 load['new']='4ef9'+struct.pack('>I',s['ml_repeat_project_hook']).hex()+'4e71'
 ap=t['append'];assert len(ap['parts'])==1
 part=ap['parts'][0];raw=bytearray.fromhex(part['hex']);dest=int(part['dest'],16)
 for name in ('ml_store_service','ml_store_bootstrap','ml_store_save_notice'):
  i=s[name]-dest;assert 0<=i<len(raw)-8 and raw[i:i+2]!=b'\x4e\x75'
  raw[i:i+2]=b'\x4e\x75' # RTS : conserver toutes les autres adresses publiées.
 i=s['ml_store_load_ready']-dest;assert raw[i:i+4]==b'\0\0\0\1'
 part['hex']=raw.hex();ap['compressed_hex']=min((aplib_dense.pack(bytes(raw),depth=d) for d in (32,128,512)),key=len).hex()
 t['status']='experimental';t['name']='Banque MIDI OUT — RAM avec contrôles CC';t['description']=['Banque MIDI en RAM : potards CC, locks, slides, SCRAMBLE et live-rec conservés.','Save/Load MIDI et hooks disque retirés. Séquences et CC perdus à extinction, aucun fichier existant supprimé.','Retrait généré depuis une recette propre : tools/gen_midi_ram_only.py ; test matériel du rollback attendu.']
 t['ram_only_rollback']=True
 return t

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();t=generate(json.loads(pathlib.Path(a.input).read_text()));s=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
 if a.check:assert out.read_text()==s
 else:out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s)
 print('ok : hooks Save/disque retirés, Load RAM, service/boot/save inertes ; tous contrôles CC conservés')
if __name__=='__main__':main()
