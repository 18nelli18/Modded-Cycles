#!/usr/bin/env python3
"""Publier seulement Control All Config testé, sans copies LFO expérimentales."""
import argparse,ast,copy,hashlib,json,pathlib,shutil
import ref_mainos
STAMP='2026-10-14-main-control-all'
def generate(base,out,recipe):
 shutil.copytree(base,out,dirs_exist_ok=True);t=copy.deepcopy(recipe);assert t['active_track_excludable'];t['status']='tested'
 tree=ast.parse(pathlib.Path('tools/gen_controls_test_flasher.py').read_text());texts=next(ast.literal_eval(n.value) for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='texts' for v in n.targets))
 texts['en']['desc']=texts['en']['desc'].replace('Experimental integration','Hardware-tested integration');texts['fr']['desc']=texts['fr']['desc'].replace('Intégration expérimentale','Intégration vérifiée sur matériel')
 p=out/'app.js';s=p.read_text();at=s.index('window.MCFlasherApp =');p.write_text(s[:at]+'for(const L of ["en","fr"])FEAT[L]["control-all-config"]='+json.dumps(texts,ensure_ascii=False)+'[L];\n'+s[at:])
 tail='\n// Control All Config seul ; traitement audio LFO2 existant conservé.\n(()=>{const t='+json.dumps(t,separators=(',',':'))+';window.MC_TWEAKS.tweaks.push(t);window.MCFlasherApp.REF_MODS[t.id]={w:'+json.dumps(hashlib.sha256(ref_mainos.writes_bytes(t)).hexdigest())+'};\n'
 tail+='''window.MC_TWEAKS.features.push({id:t.id,label:'Control All Config',desc:'Choose tracks for Control All.',cat:'live',status:'tested',variants:[{id:t.id,label:null}],credit:{kind:'by',who:'durchgemacht',repo:'durchgemacht/cycles-control-all-config'},license:'LICENSE-Control-All-Config.txt'});
window.MCFlasherApp.applyLang(document.documentElement.lang||'en');})();
'''
 p=out/'bundle.js';p.write_text(p.read_text()+tail)
 for p in out.iterdir():
  if p.is_file() and p.suffix in ['.js','.html','.md']:p.write_text(p.read_text().replace('2026-10-14-main-chord-optional-machines',STAMP))
 (out/'source/control-all-config.json').write_text(json.dumps(t,ensure_ascii=False,indent=1)+'\n');shutil.copyfile('tools/machines/control_all_config/LICENSE',out/'LICENSE-Control-All-Config.txt')
 for n,x in [('quick-reference.md','Control All Config: hold TRACK + TRIG1–6 to include/exclude each audio track, including the selected track. TRACK + knob changes included tracks. Choices reset on power-off.'),('quick-reference-fr.md','Control All Config : TRACK + TRIG1–6 inclut/exclut chaque piste audio, y compris la piste active. TRACK + potentiomètre agit sur les pistes incluses. Choix réinitialisés au redémarrage.')]:
  p=out/n;p.write_text(p.read_text()+'\n'+x+'\n')
 print('ok : Control All Config testé ; aucun code copy-fast ou noyau indépendant ajouté')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['base-dir','output','recipe']:p.add_argument('--'+n,required=True)
 a=p.parse_args();generate(pathlib.Path(a.base_dir),pathlib.Path(a.output),json.loads(pathlib.Path(a.recipe).read_text()))
if __name__=='__main__':main()
