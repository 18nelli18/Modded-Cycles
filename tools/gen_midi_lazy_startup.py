#!/usr/bin/env python3
"""Banque sans TG : différer l’allocation UI jusqu’à la première ouverture B.

Les recettes source sont validées séparément. Aucune écriture disque ajoutée.
Le flux prend64 octets de son padding antérieur, dans la même limite flash.
"""
import json,struct,pathlib,argparse,hashlib
from mtlib import aplib
import build
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--matrix',required=True);p.add_argument('--output',required=True);a=p.parse_args();root=pathlib.Path(a.matrix);out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
for row in json.load(open(root/'matrix.json')):
 key=row['key'];data=json.load(open(root/(key+'.json')));b=data['bank'];s={k:int(v,16) for k,v in b['symbols'].items()};part=b['append']['parts'][0];raw=bytearray.fromhex(part['hex']);start=int(part['dest'],16)
 if not row['tg']:
  target=b'\x4e\xb9'+struct.pack('>I',s['ml_prepare']);lo=s['ml_ui_drain']-start;found=[i for i in range(lo,lo+400,2) if raw[i:i+6]==target];assert len(found)==1,(key,found)
  at=found[0];raw[at:at+6]=bytes.fromhex('4e714e714e71');dirty=bytearray(len(raw));dirty[at:at+6]=b'\x01'*6
  before=bytes.fromhex(b['append']['compressed_hex']);decoded,ops=aplib.depack(bytes(8)+before);assert decoded==bytes.fromhex(part['hex']);packed=aplib.repack(raw,ops,dirty)[8:];assert aplib.depack(bytes(8)+packed)[0]==raw
  oldsource=int(b['append']['at'],16);newsource=oldsource-64
  for w in b['writes']:
   code=bytes.fromhex(w['new']);sig=b'\x41\xf9'+struct.pack('>I',oldsource)
   if sig in code:w['new']=code.replace(sig,b'\x41\xf9'+struct.pack('>I',newsource)).hex()
  b['append']['at']=hex(newsource);b['symbols']['ML_PAYLOAD_SRC']=hex(newsource)
  margin=build.END_LIMIT-int(b['append']['at'],16)-len(packed);print(key,'lazy UI',hex(start+at),'packed',len(packed),'margin',margin,flush=True)
  part['hex']=raw.hex();b['append']['compressed_hex']=packed.hex();b['midi_payload_rebase']=dict(raw_sha256=hashlib.sha256(raw).hexdigest(),packed_sha256=hashlib.sha256(packed).hexdigest());b['lazy_startup']={'ui_init_on_first_bside_entry':True,'at':hex(start+at),'old':target.hex(),'new':'4e714e714e71'}
  assert margin>=0,(key,margin)
 (out/(key+'.json')).write_text(json.dumps(data))
(out/'matrix.json').write_text((root/'matrix.json').read_text())
