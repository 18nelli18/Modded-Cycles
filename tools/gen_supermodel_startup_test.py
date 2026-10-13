#!/usr/bin/env python3
"""Ajouter l'animation originale à une page test, jamais à main implicitement."""
import argparse,hashlib,html,json,pathlib,re,shutil,subprocess
import build,ref_mainos,gen_boot_supermodel
from test_sdvintage import main_os_from_syx
STAMP='2026-10-13-supermodel-startup-save-test'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for x in ('base-page','output-dir','cycles','syntakt'):p.add_argument('--'+x,required=True)
 p.add_argument('--node',default='node');a=p.parse_args();base=pathlib.Path(a.base_page);out=pathlib.Path(a.output_dir)
 assert base.resolve()!=out.resolve()
 shutil.copytree(base,out,dirs_exist_ok=True)
 stock=main_os_from_syx(a.cycles);tw=gen_boot_supermodel.generate(stock)
 (out/'source/supermodel-startup.json').write_text(json.dumps(tw,ensure_ascii=False,indent=1)+'\n')
 bank=json.loads((out/'source/midi-storage.json').read_text());bank['requires']=[x for x in bank['requires'] if x!='boot-anim']
 # L'animation ne fournit aucun hook à la banque : seule dépendance de sélection.
 (out/'source/midi-storage.json').write_text(json.dumps(bank,ensure_ascii=False,indent=1)+'\n')
 texts={'en':{'label':'SUPERMODEL startup','short':'SUPERMODEL with a smaller by A.V. signature. Preferred by Select All.','desc':'Original startup animation: SUPERMODEL appears letter by letter, followed by an underline and a smaller by A.V. signature on the right. Keeps the normal startup duration. Choose either this or the Modded Cycles animation. Verified in emulation; hardware testing pending.'},'fr':{'label':'Démarrage SUPERMODEL','short':'SUPERMODEL et petite signature by A.V. Prioritaire dans Tout sélectionner.','desc':'Animation originale : SUPERMODEL apparaît lettre par lettre, puis un trait et la petite signature by A.V. à droite. Durée de démarrage normale conservée. Choisissez cette animation ou Modded Cycles. Vérifiée en émulation, matériel à tester.'}}
 feature=dict(id=tw['id'],cat='screen',status='experimental',variants=[dict(id=tw['id'],label=None)],excludes=['boot-anim'])
 extra='\n// Animation seule : choix exclusif, aucune modification du service de sauvegarde.\n(()=>{\nconst tw='+json.dumps(tw,ensure_ascii=False)+';\nconst texts='+json.dumps(texts,ensure_ascii=False)+';\nconst f='+json.dumps(feature)+';\nfor(const key of ["label","short","desc"])Object.defineProperty(f,key,{get:()=>(texts[document.documentElement.lang]||texts.en)[key]});\nconst old=window.MC_TWEAKS.features.find(f=>f.id==="boot-anim");if(!old)throw Error("Missing boot animation card");old.excludes=[...new Set([...(old.excludes||[]),tw.id])];\nwindow.MC_TWEAKS.features.splice(window.MC_TWEAKS.features.indexOf(old),0,f);window.MC_TWEAKS.tweaks.push(tw);\nconst bank=window.MC_TWEAKS.tweaks.find(t=>t.id==="midi-bank-bundle");bank.requires=bank.requires.filter(id=>id!=="boot-anim");\nwindow.MC_BUNDLE_IDS=window.MC_BUNDLE_IDS.map(id=>id==="boot-anim"?tw.id:id);\nwindow.MCFlasherApp.REF_MODS[tw.id]={w:'+json.dumps(hashlib.sha256(ref_mainos.writes_bytes(tw)).hexdigest())+'};\nwindow.MCFlasherApp.applyLang(document.documentElement.lang||"en");\n})();\n'
 (out/'bundle.js').write_text((out/'bundle.js').read_text()+extra)
 app=(out/'app.js').read_text();needle='const preferred = ["model-tg", "midi-live-both", "scale-gen", "lfo-secondary"]';assert needle in app
 (out/'app.js').write_text(app.replace(needle,needle[:-1]+', "supermodel-startup"]'))
 for path in out.iterdir():
  if path.is_file() and path.suffix in ('.html','.js','.md'):
   s=path.read_text().replace('2026-10-13-midi-cc-save-load-recovery',STAMP);path.write_text(s)
 (out/'ABOUT.md').write_text((out/'ABOUT.md').read_text()+'\n\n'+texts['en']['desc']+'\n\n'+texts['fr']['desc']+'\n')
 guide=out/'guide.html';guide.write_text(guide.read_text().replace('</main>','<section id="supermodel-startup"><h2>SUPERMODEL by A.V.</h2><p data-l="en">'+html.escape(texts['en']['desc'])+'</p><p data-l="fr">'+html.escape(texts['fr']['desc'])+'</p></section></main>'))
 # Exporter les vrais choix du navigateur, y compris getters de compression/LFO.
 catalog=out/'source/startup-test-catalog.json'
 subprocess.run([a.node,'tools/export_supermodel_test_catalog.js',str(out),str(catalog)],check=True)
 c=json.loads(catalog.read_text());chosen=c['tweaks'];build.check_conflicts(chosen)
 patched,_=build.apply_writes(stock,chosen);payload,_=build.build_payload(chosen,stock,a.syntakt);image=patched+payload
 refs={'+'.join(t['id'] for t in chosen):hashlib.sha256(image).hexdigest()}
 without=[t for t in chosen if t['id']!='6ch-usbup'];alternate,_=build.apply_writes(stock,without);alternate+=payload
 refs['+'.join(t['id'] for t in without)]=hashlib.sha256(alternate).hexdigest()
 assert len(image)+build.BASE<=build.END_LIMIT
 (out/'bundle.js').write_text((out/'bundle.js').read_text()+'\nObject.assign(window.MCFlasherApp.REF_MAINOS,'+json.dumps(refs)+');\n')
 print('ok : animation prioritaire, banque indépendante du logo, marge',build.END_LIMIT-build.BASE-len(image));print(refs)
if __name__=='__main__':main()
