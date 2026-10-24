"""Guide canonique principal2.38 : contenu EN/FR commun a HTML, Markdown et PDF."""
import argparse,html,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CSS='''*{box-sizing:border-box}html{color-scheme:light}body{margin:0;background:#f4f2eb;color:#20241f;font:16px/1.55 system-ui,sans-serif}header,main,footer{width:min(100% - 36px,1000px);margin:auto}header{padding:24px 0;border-bottom:3px solid #36563e}nav{display:flex;gap:14px;flex-wrap:wrap;align-items:center}a{color:#36563e}button{padding:8px 12px;border:1px solid #c9cec3;background:white;border-radius:5px;cursor:pointer}h1{font-size:clamp(2rem,5vw,3.4rem);line-height:1.1}h2{margin-top:35px;border-bottom:1px solid #c9cec3;padding-bottom:7px}.sub,.note{color:#5c625b}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.card{background:white;border:1px solid #c9cec3;border-radius:8px;padding:15px}table{width:100%;border-collapse:collapse;margin:14px 0 26px;background:white}th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #c9cec3}th{background:#e5eadf}td:first-child{font-weight:650;width:23%}td:nth-child(2){width:29%;font-weight:600}footer{padding:25px 0}html[lang=en] [data-l=fr],html[lang=fr] [data-l=en]{display:none}@media(max-width:650px){.grid{grid-template-columns:1fr}table,tbody,tr,td{display:block}thead{display:none}td:first-child,td:nth-child(2){width:auto}td:first-child{padding-bottom:2px}td:nth-child(2){padding-top:2px;color:#36563e}}@media print{body{background:white;font-size:10pt}header,main,footer{width:100%}nav{display:none}h2{break-after:avoid}tr,.card{break-inside:avoid}a{color:inherit}}'''
INTRO={'en':'Main 2.38. Hold the first button while pressing the next button or turning the named knob. TRIG means a step key; pad means a track key; DATA means LEVEL/DATA. All listed features are included.','fr':'Principal2.38. Maintenez le premier bouton pendant le second geste. TRIG : touche de pas ; pad : touche de piste ; DATA : LEVEL/DATA. Toutes les fonctions ci-dessous sont incluses.'}
SETUP={'en':'Hold SETTINGS + TRACK until Mod Setup opens, then release both buttons. A short tap runs SCRAMBLE on release. DATA selects a row; click to edit, turn, click again to return. Stk = Stock; SIL = Silent; LTC = Latch.','fr':'Maintenez SETTINGS + TRACK pour ouvrir Mod Setup puis relÃ¢chez. Un appui bref lance SCRAMBLE au relÃ¢chement. DATA choisit une ligne ; clic pour Ã©diter, tourner, puis clic pour revenir. Stk = Stock ; SIL = Silent ; LTC = Latch.'}
SAVE={'en': "These are global preferences. BACK closes Mod Setup and saves its global preferences; each track's Scramble checklist saves when you return from its submenu. If playback is running, the save waits until it stops. Stop playback and allow saving to finish before powering off. Saved choices return after reboot. FX types and added settings are separate: each pattern remembers them, and Save Project preserves them after reloading.", 'fr': 'Préférences globales. BACK ferme Mod Setup et sauvegarde ses préférences ; la liste Scramble de chaque piste se sauvegarde au retour du sous-menu. En lecture, la sauvegarde attend son arrêt. Arrêtez et attendez la fin avant extinction. Les types FX et réglages ajoutés sont séparés : chaque pattern les garde et Save Project les conserve au chargement.'}
DEFAULTS={'en': 'Startup defaults: stock pads and mute behavior; USB 2ch; Num Off; DX Off. Blank patterns use standard Reverb and Delay with default added FX settings. Six-channel USB excludes the stereo effect returns.', 'fr': 'Défauts : pads et mute stock ; USB 2ch ; Num Off ; DX Off. Les patterns vierges utilisent Reverb et Delay standard et les réglages ajoutés par défaut. USB six canaux sans retours stéréo des effets.'}
def e(s):return html.escape(s)
def article(data,lang):
 out=['<article data-l="'+lang+'"><p>'+e(INTRO[lang])+'</p><h2>'+('Included features' if lang=='en' else 'Fonctions incluses')+'</h2><div class="grid">']
 for c in data['cards']:a,b=c[lang];out.append('<div class="card"><b>'+e(a)+'</b><br>'+e(b)+'</div>')
 out.append('</div>')
 for section in data['sections']:
  title=section['title'][lang];out.append('<h2>'+e(title)+'</h2>')
  if section['title']['en']=='Mod Setup':out.append('<p class="mod-setup-intro">'+e(SETUP[lang])+'</p>')
  headers=['Feature','Controls','Behavior'] if lang=='en' else ['Fonction','Commandes','Comportement']
  if section['title']['en']=='LEGACY voice library':headers=['Slot','Voice','Source'] if lang=='en' else ['Slot','Voix','Source']
  out.append('<table><thead><tr>'+''.join('<th>'+e(t)+'</th>' for t in headers)+'</tr></thead><tbody>')
  for row in section['rows']:out.append('<tr>'+''.join('<td>'+e(t)+'</td>' for t in row[lang])+'</tr>')
  out.append('</tbody></table>')
  if section['title']['en']=='Mod Setup':out.append('<p class="mod-setup-save">'+e(SAVE[lang])+'</p>')
 out.append('<h2>'+('SPEAK word library' if lang=='en' else 'Lexique SPEAK')+'</h2><table><thead><tr>'+''.join('<th>Index</th><th>Word</th>' for _ in range(4))+'</tr></thead><tbody>')
 for i in range(32):out.append('<tr>'+''.join('<td>'+str(i+32*j)+'</td><td>'+e(data['speak_words'][i+32*j])+'</td>' for j in range(4))+'</tr>')
 out.append('</tbody></table>')
 out.append('<p class="note">'+e(DEFAULTS[lang])+'</p></article>');return '\n'.join(out)
def markdown(data,lang):
 out=['# '+('Feature and shortcut guide' if lang=='en' else 'Guide des fonctions et raccourcis'),'','Supermodel 2.38 - 24 October 2026' if lang=='en' else 'Supermodel2.38 - 24 octobre2026','',INTRO[lang],'','## '+('Included features' if lang=='en' else 'Fonctions incluses')]
 for card in data['cards']:a,b=card[lang];out+=['',f'**{a}:** {b}']
 for sec in data['sections']:
  out+=['','## '+sec['title'][lang],'']
  if sec['title']['en']=='Mod Setup':out +=[SETUP[lang],'']
  out+=['| '+' | '.join(['Feature','Controls','Behavior'] if lang=='en' else ['Fonction','Commandes','Comportement'])+' |','|---|---|---|']
  for row in sec['rows']:out+=['| '+' | '.join(t.replace('|','/') for t in row[lang])+' |']
  if sec['title']['en']=='Mod Setup':out+=['',SAVE[lang]]
 out+=['','## '+('SPEAK word library' if lang=='en' else 'Lexique SPEAK'),'','| Index | Word | Index | Word | Index | Word | Index | Word |','|---:|---|---:|---|---:|---|---:|---|']
 for i in range(32):out.append('| '+' | '.join(str(i+32*j)+' | '+data['speak_words'][i+32*j] for j in range(4))+' |')
 out+=['',DEFAULTS[lang],''];return '\n'.join(out)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args();data=json.loads((ROOT/'tools/shortcut_guide_content.json').read_text(encoding='utf-8'));stamp=data['stamp'];dest=ROOT/'docs/flasher'
 nav='<header><nav><a href="./">Flasher</a><a href="shortcut-guide.pdf?v='+stamp+'">PDF</a><div class="lang"><button data-lang="en">EN</button><button data-lang="fr">FR</button></div><button onclick="window.print()"><span data-l="en">Print</span><span data-l="fr">Imprimer</span></button></nav><h1>Supermodel 2.38</h1><div class="sub"><span data-l="en">Features and shortcut guide</span><span data-l="fr">Guide des fonctions et raccourcis</span></div></header>'
 page='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Supermodel 2.38 - Features and Shortcuts</title><style>'+CSS+'</style></head><body>'+nav+'<main>'+article(data,'en')+article(data,'fr')+'</main><footer>Supermodel 2.38 Â· Model:Cycles Â· 24 October 2026</footer><script src="../assets/site.js?v='+stamp+'"></script></body></html>\n'
 for name,text in {'shortcut-guide.html':page,'quick-reference.md':markdown(data,'en'),'quick-reference-fr.md':markdown(data,'fr')}.items():
  if a.check:assert (dest/name).read_text(encoding='utf-8')==text,name
  else:(dest/name).write_text(text,encoding='utf-8')
 print('PASS guide principal2.38 : HTML/Markdown EN/FR, source commune')
if __name__=='__main__':main()
