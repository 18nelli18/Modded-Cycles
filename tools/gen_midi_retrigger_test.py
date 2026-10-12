#!/usr/bin/env python3
"""Test3 retrigger/arp B à partir d'une copie épinglée de la page publiée.

--base-page DIR --output-dir DIR --cycles SYX --syntakt SYX --model-tg DIR
[--cross PREFIX] [--check]. Aucun firmware distribué, uniquement recette propre.
La page de base est celle du commit7abbe84a9fae9c57a44128e4ed4dcbb0a48f0aa4.
"""
import argparse,hashlib,json,pathlib,re,html as html_lib
import build,gen_midi_bank_bundle as bank,ref_mainos
STAMP='2026-10-12-test-3-retrigger-locks'
EN=('FUNC + RETRIG opens B-side Retrig Setup. Turn DATA to select a row, click to edit, '
    'then turn to change it. A.On enables sequenced repeats; Rte selects their rate and Len '
    'their duration (127 = INF). Arp selects UP, DOWN, UPDN, RAND, PLAY or OFF; Oct selects '
    '1–4 octaves. With REC enabled, hold a step before pressing FUNC + RETRIG to lock it; release the trig '
    'after editing to retain it. Copy/paste carries these settings and locks; clear removes '
    'step locks while retaining lane defaults, and repeating clear/paste restores Undo. '
    'Deleting a step removes its locks. BACK retains the B-side and the keyboard stays active '
    'behind the menu. This candidate tests sequenced retrigger/arp only: live keyboard retrigger '
    'is unfinished, and V.Crv displays --- because velocity curves are not implemented yet. '
    'Retrigger settings reset on project load and are not saved. Sequences and MIDI LFO '
    'settings remain RAM only; restart before changing projects. Existing B-side controls, '
    'Sequence Genie and LFO-to-CC remain included. 6-channel USB audio is optional. '
    'New retrigger/arp behavior is experimental and needs hardware testing.')
FR=('FUNC + RETRIG ouvre Retrig Setup côté B. Tournez DATA pour choisir une ligne, cliquez '
    'pour éditer puis tournez pour changer la valeur. A.On active les répétitions séquencées ; '
    'Rte règle leur vitesse et Len leur durée (127 = INF). Arp choisit UP, DOWN, UPDN, RAND, '
    'PLAY ou OFF ; Oct règle 1–4 octaves. REC actif : maintenez un pas puis ouvrez FUNC + RETRIG pour le verrouiller, '
    'puis relâchez-le après édition pour le conserver. Copier/coller transporte ces réglages '
    'et locks ; clear retire les locks de pas en conservant les défauts de voie. Répéter '
    'clear/paste restaure Undo. Supprimer un pas retire ses locks. BACK conserve B et le '
    'clavier reste actif derrière le menu. Ce candidat teste le retrigger/arp séquencé seulement : '
    'le retrigger live reste inachevé et V.Crv affiche --- car la courbe de vélocité reste '
    'à raccorder. Les réglages retrigger sont réinitialisés au chargement du projet et ne sont '
    'pas sauvegardés. Séquences et réglages LFO MIDI restent en RAM ; redémarrez avant de '
    'changer de projet. Commandes B, Sequence Genie et LFO vers CC restent inclus. Audio USB '
    '6 canaux facultatif. Nouveau retrigger/arp expérimental, à tester sur matériel.')

def replace_json(text,prefix,value):
 start=text.index(prefix)+len(prefix)
 _,length=json.JSONDecoder().raw_decode(text[start:])
 return text[:start]+json.dumps(value,ensure_ascii=False,indent=1)+text[start+length:]

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 for name in ('base-page','output-dir','cycles','syntakt','model-tg'):ap.add_argument('--'+name,required=True)
 ap.add_argument('--cross',default='m68k-elf-');ap.add_argument('--check',action='store_true');a=ap.parse_args()
 base=pathlib.Path(a.base_page);out=pathlib.Path(a.output_dir)
 stock=bank.main_os_from_syx(a.cycles)
 tweak,chosen,image=bank.generate(stock,a.syntakt,a.model_tg,a.cross,True,True,True,7,True,False,True)
 tweak['requires']=[x for x in tweak['requires'] if x!='6ch-usbup']
 tweak['description']=['Retrigger/arp séquencé B, réglages et locks privés par pattern ; RAM seulement.',
                       'Candidat Test3 ; live retrigger, courbe de vélocité et sauvegarde inachevés.']
 without=[t for t in chosen if t['id']!='6ch-usbup']
 alternate,_=build.apply_writes(stock,without+[tweak])
 # USB6 n'ajoute aucune charge ; les mêmes parties append restent identiques.
 assert [t['id'] for t in without if t.get('append')]==[t['id'] for t in chosen if t.get('append')]
 alternate+=image[len(stock):]
 refs={'+'.join([name for name in bank.IDS if name in {t['id'] for t in ts}]+[tweak['id']]):hashlib.sha256(img).hexdigest()
       for ts,img in ((chosen,image),(without,alternate))}
 mod={'w':hashlib.sha256(ref_mainos.writes_bytes(tweak)).hexdigest(),
      'p':hashlib.sha256(image[int(tweak['append']['at'],16)-build.BASE:]).hexdigest()}
 bundle=(base/'bundle.js').read_text()
 bundle=replace_json(bundle,'window.MC_TWEAKS.tweaks.push(',tweak)
 texts={'en':{'label':'MIDI OUT Bank — retrigger test','short':'Sequenced retrigger/arp locks, copy/clear/undo. Experimental; RAM only.','desc':EN},
        'fr':{'label':'Banque MIDI OUT — test retrigger','short':'Locks retrigger/arp séquencés, copie/clear/undo. Expérimental ; RAM seulement.','desc':FR}}
 bundle=replace_json(bundle,'const bankTexts = ',texts)
 bundle=replace_json(bundle,'Object.assign(window.MCFlasherApp.REF_MODS, ',{tweak['id']:mod})
 bundle=replace_json(bundle,'Object.assign(window.MCFlasherApp.REF_MAINOS, ',refs)
 html=(base/'index.html').read_text()
 html=re.sub(r'window.MC_BUILD\s*=\s*[^;]+;', 'window.MC_BUILD = '+json.dumps(STAMP)+';', html)
 html=re.sub(r'(bundle\.js|builder\.js)\?v=[^"\s<]+',lambda m:m.group(1)+'?v='+STAMP,html)
 builder=(base/'builder.js').read_text()
 old='    return aplibPack(out);'
 replacement='''    if (ap.compressed_hex !== undefined) {
      const packed = fromHex(ap.compressed_hex);
      const restored = aplibDepack(concat(new Uint8Array(8), packed)).data;
      if (!eq(restored, out)) throw new Error("charge precompressee differente");
      return packed;
    }
    return aplibPack(out);'''
 if 'ap.compressed_hex' not in builder:
  assert builder.count(old)==1;builder=builder.replace(old,replacement)
 guide=(base/'guide.html').read_text()
 section='<section id="midi-retrigger-test"><h2>Test3 — MIDI retrigger / arp</h2><p data-l="en">'+html_lib.escape(EN)+'</p><p data-l="fr">'+html_lib.escape(FR)+'</p></section>\n'
 assert '</main>' in guide;guide=guide.replace('</main>',section+'</main>')
 about=(base/'ABOUT.md').read_text()+'\n## '+STAMP+'\n\n'+EN+'\n\n'+FR+'\n'
 files={'bundle.js':bundle,'index.html':html,'builder.js':builder,'ABOUT.md':about,'guide.html':guide,
        'source/midi-retrigger.json':json.dumps(tweak,indent=1,ensure_ascii=False)+'\n'}
 for name,body in files.items():
  dest=out/name
  if a.check:assert dest.read_text()==body,dest
  else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
 print('ok : Test3 retrigger/arp, références avec/sans USB6, marge image',build.END_LIMIT-build.BASE-len(image),'octets')
 print('SHA MAIN OS :',refs)
if __name__=='__main__':main()
