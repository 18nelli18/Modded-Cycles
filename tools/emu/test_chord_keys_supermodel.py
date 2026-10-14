#!/usr/bin/env python3
"""ChordKeys PR87 placé avec Supermodel : vrais events, stockage natif et DSP.

--catalog contient la sélection Supermodel sans Chord ; --tg remplace TG par
sa version portant la réserve Chord ; --bank donne les fragments B déplacés.
Les charges décompressées sont installées comme au bootstrap. Le banc amont
instrumente le périphérique/recorder, pas le code de gamme/accord/DSP.
"""
import argparse,importlib.abc,importlib.util,json,pathlib,sys
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent));sys.path.insert(0,str(HERE/'chord_keys_compat'))
class _PinnedChordProofs(importlib.abc.MetaPathFinder):
 # Les anciens bancs changent sys.path lors de leur import. Imposer les helpers
 # PR87 épinglés évite de charger silencieusement l'ancien menu à trois items.
 def find_spec(self,fullname,path=None,target=None):
  file=HERE/'chord_keys_compat'/(fullname+'.py')
  if fullname.startswith('chord_') and file.is_file():return importlib.util.spec_from_file_location(fullname,file)
sys.meta_path.insert(0,_PinnedChordProofs())
import build,chord_keys_pr87,syntakt
sys.modules['gen_chord_keys']=chord_keys_pr87
from test_sdvintage import main_os_from_syx
import chord_ui_checks,chord_routing_checks,chord_tg_scale_checks,chord_compat_audio_checks
import chord_recording_checks,chord_midi_checks,chord_midi_event_checks,chord_display_checks,chord_palette_ui_checks
from chord_boot_fixture import boot_chord_waves
_unbooted_payload=chord_compat_audio_checks.runtime_payload
def _booted_payload(stock,chosen,path):
 address,data=_unbooted_payload(stock,chosen,path)
 return address,boot_chord_waves(stock,address,data) if data else data
chord_compat_audio_checks.runtime_payload=_booted_payload
from probe_chord_storage import run_storage_checks
from chord_plock_checks import run_plock_checks
from chord_lock_audio_checks import run_lock_audio_checks
assert all(pathlib.Path(module.__file__).resolve().parent==HERE/'chord_keys_compat'
           for name,module in sys.modules.items() if name.startswith('chord_') and name not in ('chord_keys_pr87','chord_boot_fixture')), 'banc ChordKeys non épinglé'
_original_ui_init=chord_ui_checks.t7.UI.__init__
def _ui_full_runtime(self,image,payload=b''):
 # L'ancien banc UI ne chargeait que le MAIN officiel (IMAGE_LEN), ignorant
 # les fonctions propres relogées après lui. Installer exactement l'image RAM
 # préparée plus bas, comme les autres fixtures ; aucun stub de code Chord.
 _original_ui_init(self,image,payload)
 assert len(image)<0x02400000-0x400
 self.uc.mem_write(build.BASE,image)
chord_ui_checks.t7.UI.__init__=_ui_full_runtime
_proof_syntakt=None
_original_pad_init=chord_ui_checks.pads.Rig.__init__
def _pad_full_runtime(self,image):
 _original_pad_init(self,image)
 if _proof_syntakt:
  address,data=_proof_syntakt
  self.uc.mem_map(address,(len(data)+0xfffff)&~0xfffff)
  self.uc.mem_write(address,data)
chord_ui_checks.pads.Rig.__init__=_pad_full_runtime

def main():
 global _proof_syntakt
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cycles',required=True);p.add_argument('--syntakt');p.add_argument('--catalog',required=True);p.add_argument('--chord',required=True);p.add_argument('--tg',required=True);p.add_argument('--bank');p.add_argument('--engine-cost',type=int);p.add_argument('--focus',choices=['ui','plock','compatibility','midi','recording'],default='ui');a=p.parse_args()
 stock=main_os_from_syx(a.cycles);cat=json.loads(pathlib.Path(a.catalog).read_text());baseline=cat['tweaks'];chord=json.loads(pathlib.Path(a.chord).read_text());tg=json.loads(pathlib.Path(a.tg).read_text());bank=json.loads(pathlib.Path(a.bank).read_text()) if a.bank else None
 # SLOT est un paramètre du banc, distinct du nombre natif de 33 champs.
 # L'adaptation Supermodel déplace HARMONY seulement ; ne jamais remplacer
 # les constantes 32 servant à la taille des frames/buffers/sauvegardes.
 harmony_slot=chord.get('harmony_slot',32)
 if isinstance(harmony_slot,str):harmony_slot=int(harmony_slot,0)
 for name,module in tuple(sys.modules.items()):
  if name.startswith('chord_') and hasattr(module,'SLOT'):module.SLOT=harmony_slot
 sys.modules['chord_plock_checks'].PlockRig.get.__defaults__=(harmony_slot,)
 print('HARMONY : slot RAM '+str(harmony_slot)+', ID disque33, frame natif33 champs',flush=True)
 chosen=[tg if t['id']==tg['id'] else bank if bank and t['id']==bank['id'] else t for t in baseline]
 if a.engine_cost:
  chosen=[dict(t,append=dict(t['append'],compress_cost=a.engine_cost)) if t.get('append',{}).get('syntakt') else t for t in chosen]
  for t in chosen:
   if t.get('append',{}).get('syntakt'):t['append'].pop('compress_depth',None)
 st_img=syntakt.dsp_image(a.syntakt) if any(t.get('append',{}).get('syntakt') for t in chosen) else None
 st_tweak=next((t for t in chosen if t.get('append',{}).get('syntakt')),None)
 if st_tweak:
  address=int(st_tweak['append']['dest'],16)
  _proof_syntakt=(address,boot_chord_waves(stock,address,build.payload_runtime(st_tweak,stock,st_img)))
 payload_cache={}
 def image(tweaks):
  raw,_=build.apply_writes(stock,tweaks);raw=bytearray(raw)
  # Banc fonctionnel seulement : vérifier chaque recette/runtime/compression
  # sans la limite flash globale. Le parent valide la taille du vrai installateur
  # séparément ; cette image RAM n'est jamais exportée ni présentée flashable.
  for t in sorted((t for t in tweaks if t.get('append')),key=lambda t:t['order']):
   ap=t['append']
   if id(t) not in payload_cache:
    runtime=build.payload_runtime(t,stock,st_img);payload_cache[id(t)]=build.payload_image(t,runtime)
   payload=payload_cache[id(t)]
   assert build.BASE+len(raw)==int(ap['at'],16),(t['id'],hex(build.BASE+len(raw)),ap['at'])
   raw.extend(payload)
  if build.BASE+len(raw)>build.END_LIMIT:
   print('NOTE : image RAM de preuve dépasse END_LIMIT de '+str(build.BASE+len(raw)-build.END_LIMIT)+' octets ; pas encore flashable',flush=True)
  # B s'exécute après décompression, pas à l'adresse de son flux compressé.
  for t in tweaks:
   if t['id']=='midi-bank-bundle':
    off=int(t['append']['dest'],16)-build.BASE;part=bytes.fromhex(t['append']['parts'][0]['hex']);raw[off:off+len(part)]=part
  return bytes(raw)
 reference=image(baseline);patched=image(chosen+[chord]);s={k:int(v,16) for k,v in chord['symbols'].items()}
 extra=[(build.BASE+w['off'],len(bytes.fromhex(w['new']))) for t in chosen+[chord] for w in t['writes'] if len(w['new'])>64]
 extra += [(int(x['at'],16),x['size']) for x in chord['bank_reservations']]
 if bank:extra.append((int(bank['append']['dest'],16),bank['append']['size']))
 # Le même instrumenteur EMAC doit observer les propres routines déjà
 # présentes dans la référence (sprites LF2/SG/banque compris).
 reference_extra=[(build.BASE+w['off'],len(bytes.fromhex(w['new']))) for t in baseline for w in t['writes'] if len(w['new'])>64]
 reference_extra += [(int(t['append']['dest'],16),t['append']['size']) for t in baseline if t['id']=='midi-bank-bundle']
 original_shared=chord_compat_audio_checks.shared_engine
 def shared_with_all_own_code(image,extra_code=(),tg=None,payload=None,image_len=None):
  ranges=reference_extra if image==reference else extra
  return original_shared(image,tuple(set(ranges+list(extra_code))),tg,payload,image_len)
 chord_compat_audio_checks.shared_engine=shared_with_all_own_code
 failures=[]
 def check(ok,msg):
  print(('ok    ' if ok else 'FAIL  ')+msg,flush=True)
  if not ok:failures.append(msg)
 for addr,expected,name,opcode in chord_keys_pr87.HOOKS:
  assert not [w for t in chosen for w in t['writes'] if max(addr,build.BASE+w['off'])<min(addr+len(bytes.fromhex(expected)),build.BASE+w['off']+len(bytes.fromhex(w['new'])))]
 if a.focus=='plock':
  run_storage_checks(reference,patched,s);run_plock_checks(reference,patched,s)
 elif a.focus=='ui':
  run_storage_checks(reference,patched,s);run_plock_checks(reference,patched,s)
  chord_ui_checks.run(reference,patched,s,check);chord_routing_checks.run(reference,patched,s,check);chord_display_checks.run(reference,patched,s,check);chord_palette_ui_checks.run(reference,patched,s,check)
 elif a.focus=='compatibility':
  run_storage_checks(reference,patched,s);run_plock_checks(reference,patched,s)
  chord_ui_checks.run_pad_release(reference,patched,s,check);chord_routing_checks.run(reference,patched,s,check);chord_tg_scale_checks.run(reference,patched,s,check)
  chord_compat_audio_checks.run(stock,reference,patched,s,chosen,a.syntakt,extra,check)
 elif a.focus=='midi':
  chord_midi_checks.run(reference,patched,s,check);chord_midi_event_checks.run(reference,patched,s,extra,check)
 else:
  chord_recording_checks.run(reference,patched,s,extra,check);run_lock_audio_checks(reference,patched,s,extra,check)
 assert not failures,failures
 print('ok : '+a.focus+' placé Supermodel ; essai matériel requis',flush=True)
if __name__=='__main__':main()
