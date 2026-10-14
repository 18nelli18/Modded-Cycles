#!/usr/bin/env python3
"""Copie main : support local Genie/SCRAMBLE/Chord, Model-TG facultatif.

Main/909 inchangés. Les profils sont prouvés séparément avant publication.
"""
import argparse,copy,json,pathlib,shutil,hashlib
import build,ref_mainos
from test_sdvintage import main_os_from_syx
STAMP='2026-10-14-supermodel-own-support'
p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--output',required=True);p.add_argument('--profiles',required=True);p.add_argument('--cycles',required=True);a=p.parse_args();base=pathlib.Path(a.base);out=pathlib.Path(a.output);shutil.copytree(base,out,dirs_exist_ok=True)
profiles=json.load(open(a.profiles));stock=main_os_from_syx(a.cycles)
for t in profiles.values():t.update(flashable=True,pending=['hardware_verification']);t.pop('prototype_only',None)
refs={k:{'w':hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest(),'p':hashlib.sha256(bytes.fromhex(t['append']['compressed_hex'])).hexdigest()} for k,t in profiles.items()}
# Le catalogue privé sélectionné contient la vraie reprise moteur de chaque recette.
# Les empreintes supplémentaires sont générées depuis les recettes du navigateur.
engine_hooks={};engine_refs={}
catalog=json.load(open('work/supermodel-support/frontend-catalog.json'))
for e in catalog:
 if not e.get('append') or '-tg' in e['id'] or not e['id'].startswith(('syntakt-','macro','acid')):continue
 expected=bytes.fromhex('4feffff048d700f04ef9400004ba');hits=[]
 for w in e['writes']:
  code=bytes.fromhex(w['new'])
  hits += [w['off']+i for i in range(0,len(code)-len(expected)+1,2) if code[i:i+len(expected)]==expected]
 assert len(hits)==1,(e['id'],hits)
 hook={'off':hits[0],'old':expected.hex(),'new':'4ef9401907a4'+'4e71'*4};engine_hooks[e['id']]=hook
 for key,t in profiles.items():
  n=copy.deepcopy(t);n['writes']=[w for w in n['writes'] if w['off']!=0x40000530-build.BASE]+[hook];n['requires']=[e['id']]
  build.apply_writes(stock,[e,n]);engine_refs[key+':'+e['id']]=hashlib.sha256(ref_mainos.writes_bytes(n)).hexdigest()
tail='\n// Support propre optionnel : aucun code sampler lorsque Model-TG est décoché.\n(()=>{const profiles='+json.dumps(profiles,separators=(',',':'))+';const refs='+json.dumps(refs)+';const hooks='+json.dumps(engine_hooks)+';const engineRefs='+json.dumps(engine_refs)+';\n'+'''
const a=window.MCFlasherApp,tw=window.MC_TWEAKS,on=a.isSelected,previous=window.MCMainClearResolve;let current=null;
tw.tweaks.push({id:'supermodel-performance',order:30,writes:[]});a.REF_MODS['supermodel-performance']={w:'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'};
tw.features.push({id:'supermodel-performance',cat:'live',label:'Slide trigs + Scale Lock',status:'experimental',variants:[{id:'supermodel-performance',label:null}],credit:{kind:'based',who:'TinyGregAudio · A.V. support layer',repo:'TinyGregAudio/Model-TG'},license:'LICENSE-Model-TG.txt',desc:'Standalone slide and scale-lock support, without the Model-TG sampler.'});
for(const id of ['chord-keys','scale-gen','scramble']){const f=tw.features.find(x=>x.id===id);if(f)Object.defineProperty(f,'requires',{configurable:true,get:()=>null});}
window.MCMainClearResolve=out=>{
 current=null;out=out.filter(t=>t.id!=='supermodel-performance');
 if(on('model-tg'))return previous(out);
 const needed=on('supermodel-performance')||on('scale-gen')||on('scramble')||on('chord-keys');
 if(!needed)return previous(out);
 const key=Number(on('scale-gen'))+''+Number(on('scramble'))+Number(on('chord-keys'));
 out=out.filter(t=>!t.id.startsWith('scale-gen')&&!t.id.startsWith('scramble')&&t.id!=='chord-keys-supermodel');
 const engine=out.find(t=>Object.hasOwn(hooks,t.id)),n=JSON.parse(JSON.stringify(profiles[key]));
 current={...refs[key]};if(engine){n.writes=n.writes.filter(w=>w.off!==304).concat([hooks[engine.id]]);n.requires=[engine.id];current.w=engineRefs[key+':'+engine.id];}
 return out.concat([n]).sort((x,y)=>x.order-y.order);
};
const ref={};for(const k of ['w','p'])Object.defineProperty(ref,k,{get:()=>current?.[k]});a.REF_MODS['supermodel-support-independent']=ref;
for(const k of Object.keys(a.REF_MAINOS))if(k.includes('scale-gen')||k.includes('scramble')||k.includes('chord-keys'))delete a.REF_MAINOS[k];
const texts={en:{label:'Slide trigs + Scale Lock',desc:'Standalone slide trigs and scale lock using the local Supermodel support layer. No sampler is included.'},fr:{label:'Slides + Scale Lock',desc:'Slides et Scale Lock via le support local Supermodel. Aucun sampler inclus.'}};
const own=tw.features.find(f=>f.id==='supermodel-performance');for(const k of ['label','desc'])Object.defineProperty(own,k,{configurable:true,get:()=>(texts[document.documentElement.lang]||texts.en)[k]});
const ck=tw.features.find(f=>f.id==='chord-keys'),oldDesc=Object.getOwnPropertyDescriptor(ck,'desc');Object.defineProperty(ck,'label',{configurable:true,get:()=> 'ChordKeys'});Object.defineProperty(ck,'desc',{configurable:true,get:()=>oldDesc.get.call(ck).replace('ChordKeys requires Model-TG, but does not require MIDI Bank or Syntakt, MACRO or ACID machines.','ChordKeys works with or without Model-TG in this test.').replace('ChordKeys nécessite Model-TG, sans imposer Banque MIDI ni machines Syntakt, MACRO ou ACID.','ChordKeys fonctionne avec ou sans Model-TG dans ce test.')});
a.applyLang(document.documentElement.lang||'en');
})();
'''
f=out/'bundle.js';f.write_text(f.read_text()+tail)
f=out/'builder.js';s=f.read_text();needle='    if (BASE + full.length !== parseInt(ap.at, 16))';s=s.replace(needle,"    if(t.id==='supermodel-support-independent'&&ap.zero_pad_from==='0x401aa140'&&ap.at==='0x401f8f76'&&BASE+full.length>=0x401aa140&&BASE+full.length<0x401f8f76){const pad=new Uint8Array(0x401f8f76-BASE-full.length);full=concat(full,pad);fullDirty=concat(fullDirty,pad);}\n"+needle,1);f.write_text(s)
f=out/'app.js';s=f.read_text().replace('const preferred = ["model-tg",','const preferred = ["supermodel-performance",');start=s.index('function selectAllCompatible()');end=s.index('function ',start+10);part=s[start:end].replace('for (const f of features()) {','for (const f of features()) {\n    if (f.id === "model-tg" || f.requires === "model-tg") continue;',1);s=s[:start]+part+s[end:];f.write_text(s)
f=out/'index.html';s=f.read_text().replace('2026-10-14-main-bank-909-exclusive',STAMP);s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en">Independent support test. Select All leaves Model-TG off. Genie, SCRAMBLE, ChordKeys, slides and Scale Lock use A.V.’s support layer. Experimental: startup and physical I/O need hardware testing. Main and 909 are unchanged.</span><span data-l="fr">Test du support autonome. Tout sélectionner laisse Model-TG décoché. Genie, SCRAMBLE, ChordKeys, slides et Scale Lock utilisent le support A.V. Expérimental : démarrage et I/O physiques à vérifier. Main et 909 inchangés.</span></p>',1);f.write_text(s)
print('Independent main copy',out,'profiles',len(profiles),'engine routes',len(engine_hooks))
