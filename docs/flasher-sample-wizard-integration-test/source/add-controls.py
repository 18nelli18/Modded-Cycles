"""Candidat d'intégration des contrôles Supermodel, sans fournisseur Model-TG."""
import json,pathlib,struct,copy
import build
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/sample-wizard-main');stock=load_stock('firmware/model-cycles_OS1.13.syx');w,e=json.load(open(P/'combined.json'));s={k:int(v,16) for k,v in w['symbols'].items()};mapping={int(k,16):int(v,16) for k,v in json.load(open(P/'relocation-map.json')).items()};main=json.load(open('work/lfo-clear-test3/chosen-tg-select-all.json'))
def relocate(h):
 b=bytearray.fromhex(h)
 for off in range(0,len(b)-3,2):
  v=int.from_bytes(b[off:off+4],'big')
  if v in mapping:b[off:off+4]=struct.pack('>I',mapping[v])
 return b.hex()
raw=bytearray.fromhex(w['append']['parts'][0]['hex']);base=int(w['append']['dest'],16)
for symbol in ['av_perf_on','av_ui_mods']:struct.pack_into('>I',raw,s[symbol]-base,1)
w['append']['parts'][0]['hex']=raw.hex()
# Le noyau sampler contient les fonctions MIT partagées ; seuls les quatre
# hooks non déjà possédés sont activés, sans DSP/FX/profilage Model-TG.
def hook(at,name,call=False,nops=0):
 new=(b'\x4e\xb9' if call else b'\x4e\xf9')+struct.pack('>I',s[name])+b'\x4e\x71'*nops
 return dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+len(new)].hex(),new=new.hex())
w['writes'] += [hook(0x400169f0,'sld_reset',nops=1),hook(0x40021f56,'sld_led',True,1),hook(0x4002f7d8,'install_scale_menu_item'),hook(0x40081474,'note_off_hook')]+w['clear_writes']
extra=json.load(open(P/'main-select-all-no-tg.json'));main += [t for t in extra if t['id'] in ['latching-mute','trig-preview','browser-scroll']]
cat=[w,e];excluded={'model-tg-st','chord-keys-supermodel','syntakt-tg-sd-cp-toy-bits-swarm-macro-acid'}
for old in main:
 if old['id'] in excluded:continue
 t=copy.deepcopy(old)
 if t['id'].startswith(('scale-gen','scramble')):
  for x in t['writes']:
   x['old']=relocate(x['old']);x['new']=relocate(x['new'])
  t['requires']=[x for x in t.get('requires',[]) if not x.startswith('model-tg')]+['sample-wizard']
 cat.append(t)
# Les écritures indépendantes gardent leur vraie garde de provenance. Aucune
# divergence n'est remplacée par les octets courants pour faire passer le test.
image,_=build.apply_writes(stock,sorted(cat,key=lambda t:t['order']))
(P/'controls.json').write_text(json.dumps(cat));print('PASS contrôles natifs + Second LFO + Genie + SCRAMBLE + Control All : gardes exactes, aucun fournisseur Model-TG ; ChordKeys à intégrer séparément.')
