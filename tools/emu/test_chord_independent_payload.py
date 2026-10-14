#!/usr/bin/env python3
"""ChordKeys seul : vrais hooks/clavier et compaction, sans Banque/TG/moteurs.

Installation directe du runtime pour isoler son contrat fonctionnel. Cette
preuve n'exécute pas un bootstrap indépendant et ne rend pas le mod flashable.
"""
import argparse,json,pathlib,sys,importlib.util,struct
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'chord_keys_compat'))
from test_step_delete_reset import image
from test_sdvintage import main_os_from_syx
from mtlib import aplib
spec=importlib.util.spec_from_file_location('independent_chord_ui',HERE/'chord_keys_compat/chord_ui_checks.py')
ck=importlib.util.module_from_spec(spec);spec.loader.exec_module(ck)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--payload',required=True);p.add_argument('--audio',action='store_true');p.add_argument('--boot-tweak',action='store_true');a=p.parse_args()
 t=json.loads(pathlib.Path(a.payload).read_text());assert t['requires']==[] and not t['flashable']
 if a.boot_tweak:t=dict(t,parts=t['append']['parts'],compressed_hex=t['append']['compressed_hex'])
 raw=bytes.fromhex(t['parts'][0]['hex']);packed=bytes.fromhex(t['compressed_hex'])
 unpacked,_=aplib.depack(struct.pack('>II',len(packed),sum(packed)&0xffffffff)+packed);assert unpacked==raw
 stock=main_os_from_syx(a.cycles);recipe={'writes':t['writes'],'append':{'parts':t['parts']}}
 blob=image(stock,[recipe]);symbols={k:int(v,16) for k,v in t['symbols'].items()}
 for lane in range(6):
  r,config,selected,*_=ck._ui_rig(blob,symbols);selected[0]=lane
  for key in range(1,17):
   ck._key(r,key,True)
   ons=[args for name,args in r.calls if name=='on'];assert len(ons)==1 and ons[0][0]==lane,(lane,key,r.calls)
   note=ons[0][1];ck._key(r,key,False)
   assert r.calls==[('off',(lane,note,64))],(lane,key,r.calls)
  for track in range(6):assert r.call(symbols['ck_ui_config_get'],track)==config[track]
 if not a.boot_tweak:assert t['audit']['bank_hooks']==0 and t['audit']['tg_hooks']==0
 else:
  for secondary in (False,True):
   for pad in range(1,7):
    r,*_=ck._ui_rig(blob,symbols);ck._pad(r,pad,True,secondary=secondary)
    assert ('select',(pad-1,)) in r.calls,(pad,secondary,r.calls)
    ck._pad(r,pad,False,secondary=secondary);assert any(name=='off' for name,args in r.calls)
   r,*_=ck._ui_rig(blob,symbols);ck._key(r,1,True);ck._pad(r,2,True,secondary=secondary)
   assert not any(name=='select' for name,args in r.calls)
   ck._key(r,1,False);ck._pad(r,2,False,secondary=secondary)
   assert bytes(r.uc.mem_read(symbols['held_pads'],6))==bytes(6)
  print('ok : nouveaux pads dans le runtime autonome, deux interfaces ; TRIG physique conserve HARMONY et releases')
 print('ok : Chord seul, 6 pistes x16 touches, note-on/off natifs et configuration ; aucun runtime Banque/TG/moteurs installé')
 if a.audio:
  spec=importlib.util.spec_from_file_location('independent_audio',HERE/'chord_keys_compat/chord_audio_checks.py')
  audio=importlib.util.module_from_spec(spec);spec.loader.exec_module(audio)
  ranges=[(0x40000400+w['off'],len(bytes.fromhex(w['new']))) for w in t['writes'] if len(w['new'])>64]
  ranges.extend((int(part['dest'],16),len(bytes.fromhex(part['hex']))) for part in t['parts'])
  assert audio.run_audio_storage_checks(stock,blob,ranges,setup=lambda e:e.uc.mem_write(0x40000400,blob))==0
 print('ok : aPLib exact ; bootstrap/chainage de tous les mods encore non prouvés, prototype non flashable')
if __name__=='__main__':main()
