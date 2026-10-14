#!/usr/bin/env python3
"""Importer le fondu ACID de Kevin sans remplacer les intégrations Supermodel.

Recettes MIT de wave-acid-preview 5b6108ee ; quatre corps compilés et leurs
longueurs PACK, aucun remplacement du démarrage TG ou de la banque MIDI.
"""
import argparse,copy,hashlib,json,pathlib,shutil
import build,ref_mainos
from test_sdvintage import main_os_from_syx
import syntakt
STAMP='2026-10-14-acid-fade-test'
def read(p):return json.loads(pathlib.Path(p).read_text())
def load_pairs(upstream):
 pairs=[]
 for name in ['26-acid.json','35-acid-tg.json','25-macro-acid.json','32-macro-acid-tg.json']:
  old=read(pathlib.Path('tweaks/model-cycles_OS1.13')/name);new=read(upstream/name)
  changes=[(a,b) for a,b in zip(old['append']['parts'],new['append']['parts']) if a!=b];assert len(changes)==1
  pairs.append((old,new,*changes[0]))
 return pairs
def generate(base,out,catalog,upstream,cycles,stpath):
 pairs=[]
 if upstream.is_file():
  m=read(upstream)
  for row in m['pairs']:pairs.append(({'writes':[x[0] for x in row['writes']]},{'writes':[x[1] for x in row['writes']]},row['old_part'],row['new_part']))
 else:
  pairs=load_pairs(upstream)
 stock=main_os_from_syx(cycles);stimg=syntakt.dsp_image(stpath);replacements={};refs={}
 for original in catalog:
  if 'acid' not in original['id']:continue
  t=copy.deepcopy(original);hits=0
  for old,new,a,b in pairs:
   for part in t.get('append',{}).get('parts',[]):
    if part.get('dest')==a['dest'] and part.get('hex')==a['hex']:
     part.update(b);hits+=1
     for row in t['append'].get('pack',[]):
      if row[0]==a['dest']:assert row[1]==len(a['hex'])//2;row[1]=len(b['hex'])//2
     for ow,nw in zip(old['writes'],new['writes']):
      if ow!=nw:
       for w in t['writes']:
        if w==ow:w.update(nw)
  assert hits==1,(t['id'],hits)
  t['append'].pop('compressed_hex',None);t['append'].pop('stored',None)
  payload=build.payload_image(t,build.payload_runtime(t,stock,stimg))
  t['append']['stored']=len(payload);refs[t['id']]={'w':hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest(),'p':hashlib.sha256(payload).hexdigest()};replacements[t['id']]=t
 shutil.copytree(base,out,dirs_exist_ok=True)
 tail='\n// Fondu ACID Kevin : autres charges utiles et chemins TG inchangés.\n(()=>{const recipes='+json.dumps(replacements,separators=(',',':'))+';const refs='+json.dumps(refs,separators=(',',':'))+';const a=window.MCFlasherApp;window.MC_TWEAKS.tweaks=window.MC_TWEAKS.tweaks.map(t=>recipes[t.id]||t);Object.assign(a.REF_MODS,refs);for(const k of Object.keys(a.REF_MAINOS))if(k.includes("acid"))delete a.REF_MAINOS[k];const f=window.MC_TWEAKS.features.find(f=>f.id==="acid");f.status="experimental";a.applyLang(document.documentElement.lang||"en");})();\n'
 p=out/'bundle.js';p.write_text(p.read_text()+tail)
 p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');texts={'en':'ACID bass with Kevin Shallvari’s retrigger click fix. Slides are preserved. New fade-in awaits hardware testing.','fr':'Basse ACID avec le correctif de clic au retrig de Kevin Shallvari. Slides conservés. Nouveau fondu à vérifier sur matériel.'};s=s[:at]+'for(const L of ["en","fr"])FEAT[L].acid.desc='+json.dumps(texts,ensure_ascii=False)+'[L];\n'+s[at:];p.write_text(s)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-14-main-control-all',STAMP))
 (out/'source/acid-fade-recipes.json').write_text(json.dumps({'recipes':replacements,'refs':refs},indent=1)+'\n')
 shutil.copyfile('tools/machines/acid/LICENSE-Kevin-Shallvari.txt',out/'LICENSE-Kevin-Shallvari.txt')
 compact_page(base,out,pairs,refs)
 print('ok :',len(replacements),'recettes ACID ; références strictes recalculées',flush=True)
def compact_page(base,out,pairs,refs):
 moved={}
 variants=read(base/'source/main-clear-led-variants.json')
 chord=read(base/'source/chord-tg-optional-machines.json');prototype=chord['recipe']
 full_prototype=copy.deepcopy(prototype);full_prototype['writes']=[w for w in full_prototype['writes'] if w['off']!=306]+[chord['engine_hooks']['syntakt-tg-sd-cp-toy-bits-swarm-macro-acid']['hook']]
 for key,t in [(k,v['recipe']) for k,v in variants.items()]+[('prototype',prototype),('prototype-full-engine',full_prototype)]:
  t=copy.deepcopy(t);assert t['append']['at']=='0x401f8f76';t['append']['at']='0x401f8f8a';hits=0
  for w in t['writes']:
   if '401f8f76' in w['new']:
    assert w['off']+build.BASE==0x401907a4;w['new']=w['new'].replace('401f8f76','401f8f8a');hits+=1
  assert hits==1;moved[key]={'w':hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()}
 maps={'source':'Kevin-Shallvari/Modded-Cycles','commit':'5b6108ee57cdee4767f91bfb894ccefaadf4210d','license':'MIT','pairs':[{'old_part':a,'new_part':b,'writes':[[ow,nw] for ow,nw in zip(old['writes'],new['writes']) if ow!=nw]} for old,new,a,b in pairs]}
 data={'maps':maps,'refs':refs,'moved_refs':moved}
 (out/'source/acid-fade-map.json').write_text(json.dumps(data,indent=1)+'\n')
 p=out/'bundle.js';s=p.read_text();s=s[:s.index('// Fondu ACID Kevin')];p.write_text(s+pathlib.Path('tools/machines/acid/kevin-browser-tail.js').read_text().replace('DATA',json.dumps(data,separators=(',',':'))))

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['base','output','catalog','upstream','cycles','syntakt']:p.add_argument('--'+n,required=True)
 a=p.parse_args();generate(pathlib.Path(a.base),pathlib.Path(a.output),read(a.catalog),pathlib.Path(a.upstream),a.cycles,a.syntakt)
if __name__=='__main__':main()
