"""Catalogue des choix indépendants ; contrôles communs non forcés."""
import json,pathlib,copy,struct
import build
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/sample-wizard-options');M=pathlib.Path('work/sample-wizard-main');stock=load_stock('firmware/model-cycles_OS1.13.syx');base=json.load(open(M/'installer.json'));s={k:int(v,16) for k,v in base['symbols'].items()};cat=json.load(open(M/'controls.json'));mapping={int(k,16):int(v,16) for k,v in json.load(open(M/'relocation-map.json')).items()}
sc=json.load(open(P/'scramble-no-genie.json'))
for w in sc['writes']:
 for field in ['old','new']:
  b=bytearray.fromhex(w[field])
  for at in range(0,len(b)-3,2):
   v=int.from_bytes(b[at:at+4],'big')
   if v in mapping:b[at:at+4]=struct.pack('>I',mapping[v])
  w[field]=b.hex()
sc['requires']=['sample-wizard']
def hook(at,name,call=False,nops=0):
 b=(b'\x4e\xb9' if call else b'\x4e\xf9')+struct.pack('>I',s[name])+b'\x4e\x71'*nops
 return dict(off=at-build.BASE,old=stock[at-build.BASE:at-build.BASE+len(b)].hex(),new=b.hex())
perf=[hook(0x400169f0,'sld_reset',nops=1),hook(0x40021f56,'sld_led',True,8),hook(0x4002f7d8,'install_scale_menu_item'),hook(0x40081474,'note_off_hook')]
ck=next(t for t in json.load(open(M/'select-all.json')) if t['id']=='chord-keys-supermodel');sg=next(t for t in cat if t['id'].startswith('scale-gen'));scg=next(t for t in cat if t['id'].startswith('scramble'))
for t in [base,ck,sg,sc,scg]:t.update(prototype_only=False,flashable=True,status='experimental')
preview=json.load(open('tweaks/model-cycles_OS1.13/33-sample-preview-st.json'))
for w in preview['writes']:
 for field in ['old','new']:
  b=bytearray.fromhex(w[field])
  for off in range(0,len(b)-3,2):
   value=int.from_bytes(b[off:off+4],'big')
   if value in mapping:b[off:off+4]=struct.pack('>I',mapping[value])
  w[field]=b.hex()
 if w['off']+build.BASE==0x4008171e:w['old']=(b'\x4e\xf9'+struct.pack('>I',s['av_pad_hook'])).hex()
preview.update(id='wizard-sample-preview',requires=['sample-wizard'],conflicts=['chord-keys-supermodel'],status='experimental',prototype_only=False,flashable=True)
build.apply_writes(stock,[base,preview])
data=dict(variants=json.load(open(P/'variants.json')),perf=perf,clear=base['clear_writes'],sg=sg,sc=sc,scg=scg,ck=ck,preview=preview)
(P/'data.json').write_text(json.dumps(data));print('PASS données des 256 variantes et contrôles indépendants préparées.')
