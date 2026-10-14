#!/usr/bin/env python3
"""Page SCRAMBLE autonome ; reprise commune Chord et Banque facultative.

Les pages source et principale restent inchangées. Aucune publication auto.
"""
import argparse,copy,hashlib,json,pathlib,shutil,struct
import build,ref_mainos
from chord_keys_pr87 import load_stock
STAMP='2026-10-14-scramble-independent'
def digest(t):return hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()

def generate(base,out,plain,chord,catalog,stock):
 shutil.copytree(base,out,dirs_exist_ok=True);variants={};engines={}
 for key,recipe in [('plain',plain),('chord',chord)]:
  t=copy.deepcopy(recipe);t.update(id='scramble-independent',flashable=True,pending=['hardware_verification']);t.pop('prototype_only',None)
  variants[key]={'recipe':t,'refs':{'w':digest(t),'p':hashlib.sha256(bytes.fromhex(t['append']['compressed_hex'])).hexdigest()},'engine_refs':{}}
 for e in catalog:
  if not e.get('append') or not e['id'].startswith(('syntakt-','macro','acid')) or '-tg' in e['id']:continue
  expected=bytes.fromhex('4feffff048d700f04ef9400004ba');hits=[]
  for w in e['writes']:
   body=bytes.fromhex(w['new'])
   hits.extend(w['off']+i for i in range(0,len(body)-len(expected)+1,2) if body[i:i+len(expected)]==expected)
  assert len(hits)==1,(e['id'],hits)
  hook={'off':hits[0],'old':expected.hex(),'new':'4ef9401907a4'+'4e71'*4};engines[e['id']]=hook
  for v in variants.values():
   t=copy.deepcopy(v['recipe']);t['writes']=[w for w in t['writes'] if w['off']!=0x40000530-build.BASE]+[hook];t['requires']=[e['id']]
   build.apply_writes(stock,[e,t]);v['engine_refs'][e['id']]=digest(t)
 tail='\n// SCRAMBLE autonome : recettes propres vérifiées et références strictes.\n(()=>{const variants='+json.dumps(variants,separators=(',',':'))+';const engines='+json.dumps(engines,separators=(',',':'))+';\n'
 tail+='''const app=window.MCFlasherApp,tw=window.MC_TWEAKS,on=id=>app.isSelected(id);
const previous=window.MCMidiIndependentResolve,cache=new Map();let active=null;
window.MCMidiIndependentResolve=out=>{
 if(on('midi-bank-bundle')||!on('scramble')){active=null;return previous(out);}
 if(on('model-tg')){active=null;const st=out.some(t=>t.id==='model-tg-st'),sg=out.find(t=>t.id.startsWith('scale-gen'));
  return previous(out.map(t=>{
   if(t.id.startsWith('scale-gen')){const id='scale-gen'+(st?'-st':'')+(t.id.endsWith('-queued')?'-queued':'');return tw.tweaks.find(x=>x.id===id);}
   if(t.id.startsWith('scramble')){const id='scramble'+(st?'-st':'')+(sg?'-gen':'')+(sg?.id.endsWith('-queued')?'-queued':'');return tw.tweaks.find(x=>x.id===id);}
   return t;}));}
 const key=on('chord-keys')?'chord':'plain',engine=out.find(t=>Object.hasOwn(engines,t.id)),id=key+':'+(engine?.id||'');
 let v=cache.get(id);if(!v){v=JSON.parse(JSON.stringify(variants[key]));if(engine){v.recipe.writes=v.recipe.writes.filter(w=>w.off!==304).concat([engines[engine.id]]);v.recipe.requires=[engine.id];v.refs.w=v.engine_refs[engine.id];}cache.set(id,v);}active=v;
 return out.filter(t=>!t.id.startsWith('scramble')&&t.id!=='chord-keys-supermodel').concat([v.recipe]).sort((a,b)=>a.order-b.order);
};
const ref={};for(const field of ['w','p'])Object.defineProperty(ref,field,{enumerable:true,get:()=>active?.refs[field]});app.REF_MODS['scramble-independent']=ref;
const f=tw.features.find(f=>f.id==='scramble');Object.defineProperty(f,'requires',{configurable:true,get:()=>null});f.status='experimental';
for(const k of Object.keys(app.REF_MAINOS))if(k.includes('scramble'))delete app.REF_MAINOS[k];
app.applyLang(document.documentElement.lang||'en');
})();
'''
 p=out/'bundle.js';p.write_text(p.read_text()+tail)
 p=out/'builder.js';s=p.read_text();old="(t.id==='midi-bank-bundle'&&ap.at==='0x401f8f76'";new="(['midi-bank-bundle','scramble-independent'].includes(t.id)&&ap.at==='0x401f8f76'";assert s.count(old)==1;p.write_text(s.replace(old,new))
 text={'en':{'label':'SCRAMBLE — independent test','short':'Randomize four machine controls; Model-TG and MIDI Bank are optional.','desc':'SETTINGS + TRACK scrambles the selected A-side machine. Hold TRIG(s), then SETTINGS + TRACK to toggle fresh randomization on each pass. With MIDI Bank selected, B-side SCRAMBLE randomizes assigned CCs. Standalone support and ChordKeys combinations are experimental; hardware verification required.','note':'No Model-TG, MIDI Bank, Sequence Genie or extra machines are selected automatically.'},'fr':{'label':'SCRAMBLE — test indépendant','short':'Quatre contrôles machine aléatoires ; TG et Banque MIDI facultatifs.','desc':'SETTINGS + TRACK mélange les quatre contrôles de la machine A sélectionnée. Tenir des TRIG puis SETTINGS + TRACK active/retire un tirage frais à chaque passage. Avec Banque MIDI, SCRAMBLE B mélange les CC assignés. Support autonome et combinaisons ChordKeys expérimentaux ; test matériel requis.','note':'TG, Banque MIDI, Genie et machines supplémentaires ne sont pas cochés automatiquement.'}}
 p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');p.write_text(s[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["scramble"],'+json.dumps(text,ensure_ascii=False)+'[L]);\n'+s[at:])
 for p in out.iterdir():
  if p.is_file() and p.suffix in ('.js','.html','.md'):p.write_text(p.read_text().replace('2026-10-13-midi-bank-independent',STAMP))
 p=out/'index.html';s=p.read_text().replace('Experimental independent MIDI Bank selections. Model-TG, Sequence Genie, Second LFO, SCRAMBLE and machines are optional. Main unchanged. MIDI Bank remains RAM-only.','Experimental standalone SCRAMBLE and independent MIDI Bank. Model-TG and extra machines are optional. Main unchanged. MIDI Bank remains RAM-only.').replace('Test Banque MIDI indépendante : TG, Genie, LFO2, SCRAMBLE et machines facultatifs. Flasher principal inchangé. Banque MIDI en RAM.','Test SCRAMBLE autonome et Banque MIDI indépendante. TG et machines facultatifs. Flasher principal inchangé. Banque MIDI en RAM.');p.write_text(s)
 (out/'source/scramble-independent.json').write_text(json.dumps(variants,ensure_ascii=False,indent=1)+'\n')
 (out/'ABOUT.md').write_text('# Independent SCRAMBLE test\n\nSCRAMBLE alone or with ChordKeys, optional machines, Model-TG or MIDI Bank. Experimental standalone support. Main unchanged. MIDI Bank remains RAM-only.\n\nSCRAMBLE autonome ou avec ChordKeys, machines, TG ou Banque facultatifs. Support autonome expérimental. Flasher principal inchangé. Banque en RAM.\n')
 print('ok : page autonome, deux backends et',len(engines),'reprises moteurs contrôlées')

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('base-dir','output','plain','chord','catalog','cycles'):p.add_argument('--'+name,required=True)
 a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text())
 generate(pathlib.Path(a.base_dir),pathlib.Path(a.output),read(a.plain),read(a.chord),read(a.catalog),load_stock(a.cycles))
if __name__=='__main__':main()
