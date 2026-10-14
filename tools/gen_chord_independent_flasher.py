#!/usr/bin/env python3
"""Page test : Chord autonome, TG facultatif, Banque existante compatible.

Chaque reprise moteur est vérifiée depuis sa recette propre et référencée
en Python. Le flasher principal et la page source ne sont jamais modifiés.
"""
import argparse,copy,hashlib,json,pathlib,shutil,tempfile
import build,ref_mainos
from chord_keys_pr87 import load_stock
STAMP='2026-10-13-chord-independent-startup'
BASE=build.BASE

def digest(t):return hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest()

def generate(base,out,low,high,catalog,stock,references=None):
 shutil.copytree(base,out,dirs_exist_ok=True)
 original=json.loads((base/'source/integration-chord-keys.json').read_text())
 tg=json.loads((base/'source/integration-model-tg-st.json').read_text())
 bankmeta={};prototypes={}
 for name,t in [('low',low),('tg',high)]:
  p=copy.deepcopy(t);p['id']=original['id'];p['requires']=[];p['flashable']=True;p['pending']=['hardware_verification','remaining_nonmachine_compatibility']
  prototypes[name]=p
  bankmeta[name]={'w':digest(p),'p':hashlib.sha256(bytes.fromhex(p['append']['compressed_hex'])).hexdigest()}
 engines={}
 for e in catalog:
  if not e.get('append') or not e['id'].startswith(('syntakt-','macro','acid')):continue
  is_tg='-tg' in e['id'];p=copy.deepcopy(prototypes['tg' if is_tg else 'low'])
  expected=bytes.fromhex('4ef9'+tg['symbols']['boot_extra_hook'][2:]) if is_tg else bytes.fromhex('4feffff048d700f04ef9400004ba')
  sites=[]
  for w in e['writes']:
   code=bytes.fromhex(w['new'])
   for off in range(0,len(code)-len(expected)+1,2):
    if code[off:off+len(expected)]==expected:sites.append(w['off']+off)
  assert len(sites)==1,(e['id'],sites)
  hook={'off':sites[0],'old':expected.hex(),'new':'4ef9401907a4'+'4e71'*((len(expected)-6)//2)}
  direct=0x40000532-BASE if is_tg else 0x40000530-BASE
  p['writes']=[w for w in p['writes'] if w['off']!=direct]+[hook]
  p['requires']=([tg['id']] if is_tg else [])+[e['id']]
  # Vérifie aussi les masques communs : aucun conflit effacé en silence.
  build.apply_writes(stock,([tg] if is_tg else [])+[e,p])
  engines[e['id']]={'tg':is_tg,'hook':hook,'w':digest(p)}
 bundle=(out/'bundle.js').read_text()
 old="document.addEventListener('change',event=>{if(event.target.id==='feat-chord-keys'&&event.target.checked)document.getElementById('select-all').click();},true);"
 assert bundle.count(old)==1;bundle=bundle.replace(old,'// Chord autonome : aucun Select All implicite.')
 old="if(['feat-syntakt','feat-macro','feat-acid'].includes(event.target.id)&&!event.target.checked){const c=document.getElementById('feat-chord-keys');if(c.checked){c.checked=false;c.dispatchEvent(new Event('change',{bubbles:true}));}}"
 assert bundle.count(old)==1;bundle=bundle.replace(old,'')
 tail='\n// Chord autonome : recettes Python contrôlées, aucune sauvegarde MIDI.\n(()=>{const prototypes='+json.dumps(prototypes,separators=(',',':'))+';const engines='+json.dumps(engines,separators=(',',':'))+';const refs='+json.dumps(bankmeta)+';\n'
 tail+='''const app=window.MCFlasherApp,tw=window.MC_TWEAKS,c=tw.tweaks.find(t=>t.id==='chord-keys-supermodel');
const original={...c,writes:c.writes,requires:c.requires};
const on=id=>!!document.getElementById('feat-'+id)?.checked;
function context(){const bank=on('midi-bank-bundle');if(bank)return {bank};
 const tg=on('model-tg'),engine=app.chosenTweaks().find(t=>t.id!==c.id&&Object.hasOwn(engines,t.id));
 if(engine&&engines[engine.id].tg!==tg)throw Error('Chord machine bootstrap mismatch');
 return {bank:false,tg,engine,key:tg?'tg':'low',p:prototypes[tg?'tg':'low']};}
function writes(){const x=context();if(x.bank)return original.writes;
 if(!x.engine)return x.p.writes;
 const direct=x.tg?306:304;return x.p.writes.filter(w=>w.off!==direct).concat([engines[x.engine.id].hook]);}
for(const field of ['writes','append','symbols','requires'])Object.defineProperty(c,field,{configurable:true,enumerable:true,get:()=>{const x=context();
 if(x.bank)return field==='append'?undefined:original[field];
 if(field==='writes')return writes();
 if(field==='requires')return (x.tg?['model-tg-st']:[]).concat(x.engine?[x.engine.id]:[]);
 return x.p[field];}});
app.REF_MODS[c.id]={};Object.defineProperty(app.REF_MODS[c.id],'w',{get:()=>{const x=context();return x.bank?''+originalRef.w:x.engine?engines[x.engine.id].w:refs[x.key].w;}});
Object.defineProperty(app.REF_MODS[c.id],'p',{get:()=>{const x=context();return x.bank?undefined:refs[x.key].p;}});
const f=tw.features.find(f=>f.id==='chord-keys');f.requires=null;f.with={};f.variants=[{id:c.id,label:null}];f.status='experimental';
tw.features.find(f=>f.id==='model-tg').with={...tw.features.find(f=>f.id==='model-tg').with,'chord-keys':'model-tg-st'};
tw.features.find(f=>f.id==='control-all-config').status='tested';
for(const key of Object.keys(app.REF_MAINOS))if(key.includes(c.id))delete app.REF_MAINOS[key];
app.applyLang(document.documentElement.lang||'en');
})();\n'''
 # Référence originale capturée avant remplacement de REF_MODS.
 tail=tail.replace('const original={','const originalRef=app.REF_MODS[c.id];\nconst original={')
 (out/'bundle.js').write_text(bundle+tail)
 if references:
  verified={row['key']:row['sha'] for row in references['cases']}
  with (out/'bundle.js').open('a') as f:f.write('\nObject.assign(window.MCFlasherApp.REF_MAINOS,'+json.dumps(verified,separators=(',',':'))+');\n')
  (out/'source/chord-independent-reference-check.json').write_text(json.dumps(references,indent=1)+'\n')
 p=out/'builder.js';s=p.read_text();old="if(t.id==='midi-bank-bundle'&&ap.zero_pad_from==='0x401bf8c0'&&end>=0x401bf8c0&&end<target&&target<=END_LIMIT)"
 new="if(((t.id==='midi-bank-bundle'&&ap.zero_pad_from==='0x401bf8c0'&&end>=0x401bf8c0)||(t.id==='chord-keys-supermodel'&&ap.zero_pad_from==='0x401aa140'&&ap.at==='0x401f8f76'&&end>=0x401aa140))&&end<target&&target<=END_LIMIT)"
 assert s.count(old)==1;p.write_text(s.replace(old,new))
 texts={'en':{'label':'ChordKeys — independent test','short':'Diatonic ChordKeys; Model-TG, MIDI Bank and extra machines are optional.','desc':'Experimental independent loader. ChordKeys can be selected alone, with Model-TG, or with MIDI Bank. No extra synth machines are selected automatically. Without MIDI Bank, hold a physical TRIG for Harmony pad modifiers; otherwise pads select tracks. The existing MIDI Bank integration is retained. Hardware verification required.','note':'Independent selections are experimental. MIDI Bank data remains RAM-only.'},'fr':{'label':'ChordKeys — test indépendant','short':'ChordKeys diatonique ; TG, Banque MIDI et machines facultatifs.','desc':'Chargeur indépendant expérimental. ChordKeys seul, avec TG ou Banque MIDI. Aucune machine supplémentaire cochée automatiquement. Sans Banque, tenir un TRIG physique pour HARMONY ; sinon les pads sélectionnent les pistes. Intégration Banque existante conservée. Vérification matérielle requise.','note':'Sélections indépendantes expérimentales. Banque MIDI en RAM uniquement.'}}
 p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');p.write_text(s[:at]+'for(const L of ["en","fr"])Object.assign(FEAT[L]["chord-keys"],'+json.dumps(texts,ensure_ascii=False)+'[L]);\n'+s[at:])
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-13-midi-bank-optional-machines',STAMP))
 p=out/'index.html';s=p.read_text();s=s.replace('Experimental controls test: Control All Config, fresh step deletion on A/B and previous LFO 2 processing restored. ChordKeys pad behavior unchanged. MIDI Bank data is held in RAM.','Experimental independent ChordKeys selections. Model-TG, MIDI Bank and extra machines are optional for ChordKeys. Main unchanged. MIDI Bank remains RAM-only.').replace('Test expérimental : Control All Config, suppression complète des locks A/B et traitement LFO2 précédent restauré. Pads ChordKeys inchangés. Données Banque MIDI en RAM.','Test ChordKeys indépendant : Model-TG, Banque MIDI et machines facultatifs pour ChordKeys. Flasher principal inchangé. Banque MIDI en RAM.');p.write_text(s)
 for name,t in [('low',prototypes['low']),('tg',prototypes['tg']),('engine-hooks',engines)]:
  (out/'source'/('chord-independent-'+name+'.json')).write_text(json.dumps(t,ensure_ascii=False,indent=1)+'\n')
 (out/'ABOUT.md').write_text('# Independent ChordKeys test\n\nExperimental standalone and Model-TG loaders. MIDI Bank still uses its existing compatible runtime and remains RAM-only. Main unchanged. Hardware verification required.\n\nChargeurs Chord seul et TG expérimentaux. Banque MIDI garde son runtime compatible, en RAM. Flasher principal inchangé. Test matériel requis.\n')
 print('ok : candidat indépendant,',len(engines),'reprises moteur vérifiées ; non publié')

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-dir',required=True);p.add_argument('--output',required=True);p.add_argument('--low',required=True);p.add_argument('--tg',required=True);p.add_argument('--catalog',required=True);p.add_argument('--cycles',required=True);p.add_argument('--references');p.add_argument('--check',action='store_true');a=p.parse_args();read=lambda f:json.loads(pathlib.Path(f).read_text())
 with tempfile.TemporaryDirectory() as d:
  target=pathlib.Path(a.output);out=pathlib.Path(d)/'page' if a.check else target
  generate(pathlib.Path(a.base_dir),out,read(a.low),read(a.tg),read(a.catalog),load_stock(a.cycles),read(a.references) if a.references else None)
  if a.check:
   for f in out.rglob('*'):
    if f.is_file():assert f.read_bytes()==(target/f.relative_to(out)).read_bytes(),str(f)
if __name__=='__main__':main()
