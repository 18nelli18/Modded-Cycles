#!/usr/bin/env python3
"""Page isolée : suppression des locks A/B et copies LFO2 allégées (note76).

Les recettes et les hashes de mods sont reconstruits depuis les sources ;
aucune sauvegarde MIDI réintroduite, aucun geste ChordKeys modifié.
"""
import argparse,copy,hashlib,json,pathlib,shutil,tempfile
import build,ref_mainos
from chord_keys_pr87 import load_stock
STAMP='2026-10-13-control-all-copy-test'
def generate(base,lfo,alt,step,control,stock,catalog,out,references=None):
 shutil.copytree(base,out,dirs_exist_ok=True)
 refs={control['id']:dict(w=hashlib.sha256(ref_mainos.writes_bytes(control)).hexdigest())}
 for key,t in ((lfo['id'],lfo),(lfo['id']+'-without-bank',alt)):refs[key]=dict(w=hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest())
 banks=[]
 for name in ('integration-midi-bank.json','integration-midi-bank-chord.json'):
  t=json.loads((out/'source'/name).read_text());t['writes']+=copy.deepcopy(step['writes']);t['symbols'].update(step['symbols']);t['fresh_step_reset']=dict(audio=True,midi=True,hardware_tested=False);banks.append(t)
  (out/'source'/name).write_text(json.dumps(t,ensure_ascii=False,indent=1)+'\n')
 assert banks[0]['writes']==banks[1]['writes']
 build.apply_writes(stock,[lfo if t['id']==lfo['id'] else banks[1] if t['id']==banks[1]['id'] else t for t in catalog]+[control])
 refs[banks[0]['id']]=dict(w=hashlib.sha256(ref_mainos.writes_bytes(banks[0])).hexdigest())
 (out/'source/controls-lfo-copy.json').write_text(json.dumps(lfo,ensure_ascii=False,indent=1)+'\n')
 (out/'source/controls-lfo-copy-without-bank.json').write_text(json.dumps(alt,ensure_ascii=False,indent=1)+'\n')
 (out/'source/controls-step-reset.json').write_text(json.dumps(step,ensure_ascii=False,indent=1)+'\n')
 (out/'source/controls-control-all.json').write_text(json.dumps(control,ensure_ascii=False,indent=1)+'\n')
 shutil.copyfile(pathlib.Path(__file__).parent/'machines/control_all_config/LICENSE',out/'LICENSE-Control-All-Config.txt')
 texts={'en':{'label':'Control All Config','short':'Choose which audio tracks follow TRACK + knob Control All.','desc':'Hold TRACK and tap TRIG 1–6 to exclude or include the corresponding A-side track. Lit trigs follow Control All; the active track always follows. Choices reset after power-off. Experimental integration by durchgemacht.','shortcuts':['TRACK + TRIG 1–6: exclude/include a track.','TRACK + knob: Control All on included tracks. The active track always follows.']},'fr':{'label':'Control All Config','short':'Choisir les pistes audio concernées par TRACK + potentiomètre.','desc':'Tenir TRACK et appuyer sur TRIG 1–6 pour exclure ou inclure la piste A correspondante. Trigs allumés : pistes incluses ; la piste active suit toujours. Choix réinitialisés au redémarrage. Intégration expérimentale de durchgemacht.','shortcuts':['TRACK + TRIG 1–6 : exclure/inclure une piste.','TRACK + potentiomètre : Control All sur les pistes incluses. La piste active suit toujours.']}}
 app=(out/'app.js').read_text();at=app.index('window.MCFlasherApp =');app=app[:at]+'for(const L of ["en","fr"])FEAT[L]["control-all-config"]='+json.dumps(texts,ensure_ascii=False)+'[L];\n'+app[at:];(out/'app.js').write_text(app)
 tail='\n// Contrôles expérimentaux : source note76 ; ChordKeys inchangé.\n(()=>{const lfo='+json.dumps(lfo,ensure_ascii=False)+';const alt='+json.dumps(alt,ensure_ascii=False)+';const writes='+json.dumps(banks[0]['writes'])+';const stepSymbols='+json.dumps(step['symbols'])+';const refs='+json.dumps(refs)+';const control='+json.dumps(control,ensure_ascii=False)+';\n'
 tail+='''window.MC_TWEAKS.tweaks.push(control);window.MCFlasherApp.REF_MODS[control.id]=refs[control.id];
window.MC_TWEAKS.features.push({id:control.id,label:'Control All Config',desc:'Choose tracks for Control All.',cat:'live',status:'experimental',variants:[{id:control.id,label:null}],credit:{kind:'by',who:'durchgemacht',repo:'durchgemacht/cycles-control-all-config'},license:'LICENSE-Control-All-Config.txt'});
const enabled=()=>!!document.getElementById('feat-midi-bank-bundle')?.checked;
const index=window.MC_TWEAKS.tweaks.findIndex(t=>t.id===lfo.id), fresh={...lfo};
Object.defineProperty(fresh,'writes',{get:()=>enabled()?lfo.writes:alt.writes});Object.defineProperty(fresh,'symbols',{get:()=>enabled()?lfo.symbols:alt.symbols});window.MC_TWEAKS.tweaks[index]=fresh;
const b=window.MC_TWEAKS.tweaks.find(t=>t.id==='midi-bank-bundle');b.writes=writes;Object.assign(b.symbols,stepSymbols);
window.MCFlasherApp.REF_MODS[lfo.id]={};Object.defineProperty(window.MCFlasherApp.REF_MODS[lfo.id],'w',{get:()=>refs[lfo.id+(enabled()?'':'-without-bank')].w});
window.MCFlasherApp.REF_MODS[b.id].w=refs[b.id].w;
for(const key of Object.keys(window.MCFlasherApp.REF_MAINOS))if(key.split('+').some(id=>id===lfo.id||id===b.id))delete window.MCFlasherApp.REF_MAINOS[key];
for(const id of ['lfo-secondary','midi-bank-bundle']){const f=window.MC_TWEAKS.features.find(x=>x.id===id);if(f)f.status='experimental';}
window.MCFlasherApp.applyLang(document.documentElement.lang||'en');
})();\n'''
 (out/'bundle.js').write_text((out/'bundle.js').read_text()+tail)
 if references:
  (out/'source/controls-reference-check.json').write_text(json.dumps(references,ensure_ascii=False,indent=1)+'\n')
  with (out/'bundle.js').open('a') as f:f.write('\nObject.assign(window.MCFlasherApp.REF_MAINOS,'+json.dumps(references['refs'])+');\n')
 for f in out.iterdir():
  if f.is_file() and f.suffix in ('.js','.html','.md'):f.write_text(f.read_text().replace('2026-10-13-chordkeys-rotero-main',STAMP))
 path=out/'index.html';html=path.read_text().replace('ChordKeys + roterodamus Model-TG integration. New integrations remain experimental. MIDI Bank data is held in RAM.','Experimental controls test: Control All Config, fresh step deletion on A/B and lighter LFO 2 frame copies. ChordKeys pad behavior unchanged. MIDI Bank data is held in RAM.').replace('Intégration ChordKeys + Model-TG roterodamus. Nouveautés encore expérimentales. Données Banque MIDI en RAM.','Test expérimental : Control All Config, suppression complète des locks A/B et copies LFO2 allégées. Pads ChordKeys inchangés. Données Banque MIDI en RAM.');path.write_text(html)
 (out/'ABOUT.md').write_text('''# Supermodel controls test — 13 October 2026

Includes the published ChordKeys/roterodamus integration, with its original pad
behavior, all existing choices and MIDI protocols. New experimental changes:

- Control All Config: TRACK + TRIG 1–6 excludes/includes audio tracks; lit trigs follow. The selected track always follows. TRACK + knob applies Control All; choices reset at startup.\n- MIDI Bank selected: removing an A-side grid trig clears all native locks and
  SCRAMBLE/slide markers. B-side deletion verified to clear all twelve CC locks,
  chance/retrig/arp/nudge and slide data; fresh note C5, velocity 100, length1.
- Second LFO: equivalent frame-copy code uses 476 fewer executed instructions
  per audio block. CPU percentage and complete overload recovery are not claimed.
- MIDI Bank remains RAM-only. Track clear + LFO Undo is still in development.

Test on hardware: delete/recreate locked trigs on A/B; play the same Syntakt/ACID
pattern used to reproduce timing trouble. Check notes, MIDI and active LFOs.

Inclut ChordKeys/roterodamus publié, avec ses gestes de pads d’origine, tous les
choix et protocoles MIDI. Nouveautés expérimentales :

- Control All Config : TRACK + TRIG 1–6 exclut/inclut les pistes audio ; trigs allumés = incluses. Piste active toujours incluse. TRACK + potentiomètre applique Control All ; choix réinitialisés au démarrage.\n- Banque MIDI cochée : effacer un trig grille A supprime ses locks natifs et
  marques SCRAMBLE/slide. En B, suppression des 12 locks CC, chance/retrig/arp/nudge
  et slide vérifiée ; nouveau pas C5, vélocité100, longueur1.
- Second LFO : copies identiques avec 476 instructions exécutées en moins par
  bloc audio. Aucun pourcentage CPU ni correction complète de surcharge annoncé.
- Banque MIDI en RAM. Clear piste + Undo LFO encore en développement.
''')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-dir',required=True);p.add_argument('--lfo-json',required=True);p.add_argument('--lfo-alt-json',required=True);p.add_argument('--step-json',required=True);p.add_argument('--control-all-json',required=True);p.add_argument('--catalog',required=True);p.add_argument('--references');p.add_argument('--cycles',required=True);p.add_argument('--output',required=True);p.add_argument('--check',action='store_true');a=p.parse_args();base=pathlib.Path(a.base_dir);target=pathlib.Path(a.output);lfo=json.loads(pathlib.Path(a.lfo_json).read_text());alt=json.loads(pathlib.Path(a.lfo_alt_json).read_text());step=json.loads(pathlib.Path(a.step_json).read_text());control=json.loads(pathlib.Path(a.control_all_json).read_text());stock=load_stock(a.cycles);catalog=json.loads(pathlib.Path(a.catalog).read_text())['tweaks'];references=json.loads(pathlib.Path(a.references).read_text()) if a.references else None
 with tempfile.TemporaryDirectory() as d:
  out=pathlib.Path(d)/'page' if a.check else target;generate(base,lfo,alt,step,control,stock,catalog,out,references)
  if a.check:
   for f in out.rglob('*'):
    if f.is_file():assert f.read_bytes()==(target/f.relative_to(out)).read_bytes(),str(f)
 print('ok : page de contrôle '+('reproductible' if a.check else 'générée'))
if __name__=='__main__':main()
