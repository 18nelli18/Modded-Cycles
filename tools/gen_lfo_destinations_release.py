"""Note121 : publier les octets du test8 confirme par AveyCole, sans diagnostic.

python3 tools/gen_lfo_destinations_release.py [--check]
Le helper compile reste identique au test valide ; seul son mode de composition change.
"""
import argparse,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-lfo-main-190'
CONFIRMED='0e44b0b9dac586656b0f0e604846ba67ebde8b0badae83fd6a25a44de77bb4be'

CONFIRMED_METADATA='583546546cb158a93577f19568213eb634ac441aee7aa4613e8cef4ba48a10e8'

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 data=json.loads((ROOT/'docs/flasher-lfo-destinations-test/lfo-destinations-data.js').read_text(encoding='utf-8').split('=',1)[1].strip().rstrip(';'))
 assert hashlib.sha256(bytes.fromhex(data['hex'])).hexdigest()==CONFIRMED,'Test8 confirme requis'
 assert hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()==CONFIRMED_METADATA,'Symboles et relocations du test8 requis'
 data['release']=True
 for folder in ('flasher','flasher-supermodel-909'):
  out=ROOT/'docs'/folder
  html=(out/'index.html').read_text(encoding='utf-8')
  # Conserver le cache courant et l'ordre des modules publies apres cette release.
  stamp=re.search(r"window.MC_BUILD='([^']+)'",html).group(1)
  if 'lfo-destinations.js?' not in html:
   html=html.replace('</body>',f'<script src="lfo-destinations-data.js?v={stamp}"></script><script src="lfo-destinations.js?v={stamp}"></script></body>')
  assert 'beat-diagnostic.js' not in html and 'audio-load.js?' not in html
  files={'index.html':html,'lfo-destinations.js':(ROOT/'tools/web/lfo-destinations.js').read_text(encoding='utf-8'),'lfo-destinations-data.js':'window.MCLfoDestinations='+json.dumps(data,separators=(',',':'))+';\n'}
  for name,text in files.items():
   if a.check:assert (out/name).read_text(encoding='utf-8')==text,str(out/name)
   else:(out/name).write_text(text,encoding='utf-8')
 print('PASS confirmed test8 helper in both released flashers; no diagnostic scripts')
if __name__=='__main__':main()
