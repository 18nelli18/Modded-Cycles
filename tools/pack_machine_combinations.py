#!/usr/bin/env python3
"""Factorise les recettes et leurs differences hexadecimales ; aucun OS exporte."""
import json,pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from midi_catalog_compact import JS_DECODER,restore
ROOT=pathlib.Path(__file__).resolve().parent.parent
strings=[];full=[];seen={};lengths={};objects=[];seenobjects={}
def enc(v):
 if isinstance(v,str) and len(v)>=128:
  if v in seen:return {'$s':seen[v]}
  value=v;previous=lengths.get(len(v))
  if previous is not None:
   old=full[previous];patch=[];i=0
   while i<len(v):
    if v[i]==old[i]:i+=1;continue
    start=i
    while i<len(v) and v[i]!=old[i]:i+=1
    patch.append([start,v[start:i]])
   candidate={'base':previous,'patch':patch}
   if len(json.dumps(candidate,separators=(',',':')))<len(v)*.8:value=candidate
  index=len(strings);strings.append(value);full.append(v);seen[v]=index;lengths[len(v)]=index
  return {'$s':index}
 if isinstance(v,list):out=[enc(x) for x in v]
 elif isinstance(v,dict):out={k:enc(x) for k,x in v.items()}
 else:return v
 key=json.dumps(out,separators=(',',':'),ensure_ascii=False)
 if len(key)<64:return out
 if key in seenobjects:return {'$o':seenobjects[key]}
 index=len(objects);objects.append(out);seenobjects[key]=index;return {'$o':index}
def main():
 data={'wizard':{},'normal':{}}
 paths=sorted((ROOT/'build/machine-combinations').glob('[0-9]*-[wn].json'))
 for p in paths:
  mask,mode=p.stem.split('-');data['wizard' if mode=='w' else 'normal'][mask]=enc(json.loads(p.read_text(encoding='utf-8')))
 packed=dict(strings=strings,objects=objects,root=data)
 text='// Genere par tools/pack_machine_combinations.py.\n(()=>{'+JS_DECODER+'window.MCMachineCombinationData=unpackCatalogue('+json.dumps(packed,separators=(',',':'),ensure_ascii=False)+');})();\n'
 target=ROOT/'docs/flasher/machine-combinations-data.js';
 if '--check' in sys.argv:assert target.read_text(encoding='utf-8')==text
 else:target.write_text(text,encoding='utf-8')
 print('ok',len(paths),'recettes',len(text),'octets',flush=True)
 restored=restore(packed)
 for p in paths:
  mask,mode=p.stem.split('-');actual=restored['wizard' if mode=='w' else 'normal'][mask]
  assert actual==json.loads(p.read_text(encoding='utf-8'))
 print('ok restauration exacte',flush=True)
if __name__=='__main__':main()
