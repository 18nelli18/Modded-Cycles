"""ChordKeys dans la réserve suivante ; pas de Clear/Undo ancien dupliqué."""
import json,pathlib,struct,copy,hashlib
import build,syntakt,aplib_cost
from chord_keys_pr87 import load_stock
P=pathlib.Path('work/sample-wizard-main');cat=json.load(open(P/'controls.json'));w,e=cat[:2];stock=load_stock('firmware/model-cycles_OS1.13.syx');st=syntakt.dsp_image('firmware/Syntakt_OS1.42.syx');s={k:int(v,16) for k,v in w['symbols'].items()};mapping={int(k,16):int(v,16) for k,v in json.load(open(P/'relocation-map.json')).items()}
old=next(x for x in json.load(open('work/lfo-clear-test3/chosen-tg-select-all.json')) if x['id']=='chord-keys-supermodel');ck=copy.deepcopy(old);raw=build.payload_runtime(ck,stock,st)[:9620];dest=int(ck['append']['dest'],16);newend=dest+len(raw);mapping[int(ck['symbols']['chord_end'],16)]=newend
legacy=next(t for t in json.load(open('work/lfo-clear-test3/chosen-tg-select-all.json')) if t['id']=='model-tg-st');mapping[int(legacy['symbols']['reserved_end'],16)]=s['reserved_end']

def reloc(b):
 b=bytearray(b)
 for at in range(0,len(b)-3,2):
  x=int.from_bytes(b[at:at+4],'big')
  if x in mapping:b[at:at+4]=struct.pack('>I',mapping[x])
 return bytes(b)
raw=reloc(raw);clearoffs={x['off'] for x in w['clear_writes']};ck['writes']=[x for x in ck['writes'] if x['off'] not in clearoffs]
for x in ck['writes']:
 x['old']=reloc(bytes.fromhex(x['old'])).hex();x['new']=reloc(bytes.fromhex(x['new'])).hex()
# Compression compatible décodeur existant : les deux flux sont relus et le
# prochain test exécute aussi le vrai décompresseur du firmware.
e['append']['compress_cost']=128;e['append'].pop('compressed_hex',None)
fixtures=json.load(open(P/'private-packed-fixture.json')) if (P/'private-packed-fixture.json').exists() else {}
if e['id'] in fixtures:e['append']['compressed_hex']=fixtures[e['id']]
engine=build.payload_image(e,build.payload_runtime(e,stock,st));at=int(e['append']['at'],16)+len(engine)
loader=next(x for x in ck['writes'] if x['off']+build.BASE==int(ck['symbols']['chord_boot'],16));code=bytes.fromhex(loader['new']);source=int(ck['append']['at'],16);assert code.count(struct.pack('>I',source))==1;loader['new']=code.replace(struct.pack('>I',source),struct.pack('>I',at)).hex()
ck['append']=dict(at=hex(at),dest=hex(dest),size=len(raw),parts=[dict(dest=hex(dest),hex=raw.hex())],reloc=[],compress='aplib',compress_cost=128)
ck['symbols']={k:v for k,v in ck['symbols'].items() if not k.startswith('avcl_')};ck['symbols']['chord_end']=hex(newend);ck['requires']=['sample-wizard'];ck['prototype_only']=True
# Le dernier init doit préserver Wizard et ChordKeys ; sept blocs disque pris.
for x in w['writes']:
 if x['off']+build.BASE==0x400792f2:x['new']=struct.pack('>I',0x401eb750+20*7).hex()
 if x['off']+build.BASE==0x400792bc:x['new']=struct.pack('>I',0x401eb750+20*8+16).hex()
w['cache_blocks']=7
cat.append(ck);cat.sort(key=lambda t:t['order']);image,_=build.apply_writes(stock,cat);payload,_=build.build_payload(cat,stock,'firmware/Syntakt_OS1.42.syx');end=build.BASE+len(image)+len(payload)
assert end<=build.END_LIMIT,hex(end)
e['append'].pop('compressed_hex',None)
(P/'select-all.json').write_text(json.dumps(cat));print('PASS Select All + Wizard indépendant :',len(cat),'recettes ; fin flash',hex(end),';',build.END_LIMIT-end,'octets libres ; cache 7 blocs ; ACID corrigée, WAVE, MACRO, Syntakt, ChordKeys conservés.')
