#!/usr/bin/env python3
"""Catalogue statique compact, sans toucher les octets du firmware.

Partage objets/chaînes et différences alignées de chaînes hexadécimales.
Le décodeur doit restaurer exactement les recettes avant tout build.
"""
import json,re

def compact(value):
 strings=[];full=[];seen_strings={};lengths={};objects=[];seen_objects={}
 def encode(v):
  if isinstance(v,str) and len(v)>=256 and re.fullmatch('[0-9a-f]+',v):
   if v in seen_strings:return {'$s':seen_strings[v]}
   entry=v;best=len(v)
   for base in lengths.get(len(v),[]):
    previous=full[base];patch=[];i=0
    while i<len(v):
     if v[i]==previous[i]:i+=1;continue
     start=i
     while i<len(v) and v[i]!=previous[i]:i+=1
     patch.append([start,v[start:i]])
    candidate={'base':base,'patch':patch};size=len(json.dumps(candidate,separators=(',',':')))
    if size<best*.8:entry=candidate;best=size
   index=len(strings);strings.append(entry);full.append(v);seen_strings[v]=index;lengths.setdefault(len(v),[]).append(index)
   return {'$s':index}
  if isinstance(v,list):encoded=[encode(x) for x in v]
  elif isinstance(v,dict):encoded={k:encode(x) for k,x in v.items()}
  else:return v
  key=json.dumps(encoded,separators=(',',':'),ensure_ascii=False)
  if len(key)<64:return encoded
  if key in seen_objects:return {'$o':seen_objects[key]}
  index=len(objects);objects.append(encoded);seen_objects[key]=index;return {'$o':index}
 root=encode(value);return dict(strings=strings,objects=objects,root=root)

def restore(data):
 strings=[]
 for entry in data['strings']:
  if isinstance(entry,str):strings.append(entry);continue
  value=strings[entry['base']]
  for off,text in entry['patch']:value=value[:off]+text+value[off+len(text):]
  strings.append(value)
 cache={}
 def decode(v):
  if isinstance(v,dict):
   if len(v)==1 and '$s' in v:return strings[v['$s']]
   if len(v)==1 and '$o' in v:
    key=v['$o']
    if key not in cache:cache[key]=decode(data['objects'][key])
    return cache[key]
   return {k:decode(x) for k,x in v.items()}
  if isinstance(v,list):return [decode(x) for x in v]
  return v
 return decode(data['root'])

JS_DECODER='''function unpackCatalogue(data){
 const strings=[];for(const entry of data.strings){if(typeof entry==='string'){strings.push(entry);continue;}
 let value=strings[entry.base];for(const [off,text] of entry.patch)value=value.slice(0,off)+text+value.slice(off+text.length);strings.push(value);}
 const cache=new Map();function decode(v){if(Array.isArray(v))return v.map(decode);
 if(v&&typeof v==='object'){if(Object.keys(v).length===1&&Object.hasOwn(v,'$s'))return strings[v.$s];
 if(Object.keys(v).length===1&&Object.hasOwn(v,'$o')){if(!cache.has(v.$o))cache.set(v.$o,decode(data.objects[v.$o]));return cache.get(v.$o);}
 return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,decode(x)]));}return v;}
 return decode(data.root);}
'''
