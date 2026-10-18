"""Port cible de Sample Preview dans909.6 ; voix, WAV et principal conserves."""
import argparse,json,pathlib,re,subprocess
from gen_909_crossover import render
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE='f7298611cea3f48db0d6a02bf047412022fb96e2';STAMP='2026-10-18-909-sample-preview'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'docs/flasher-supermodel-909'
 def original(name):return subprocess.check_output(['git','show',BASE+':docs/flasher-supermodel-909/'+name],cwd=ROOT).decode('utf-8')
 files={'909-sample-preview.js':(ROOT/'tools/web/model909/sample-preview.js').read_text(encoding='utf-8')}
 s=original('index.html');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 files['index.html']=s.replace('</body>',f'<script src="909-sample-preview.js?v={STAMP}"></script></body>')
 meta=json.loads(original('BUILD.json'));meta.update(sample_preview=True,sample_preview_validation='emulation; main feature hardware-confirmed, 909 combination pending',sample_preview_updated='2026-10-18');files['BUILD.json']=json.dumps(meta,indent=2)+'\n'
 release=json.loads(original('909-release.js').split('=',1)[1].strip().rstrip(';'));release.insert(0,dict(version='909.7',date='2026-10-18',changes=[dict(en='Adds Sample Preview from main: FUNC + MACHINES opens the Sample Wizard browser; highlight a sample and play a pad or keyboard to audition before loading. Six 909 voices and four local WAV inputs are unchanged. 909 integration checked in emulation; hardware verification pending.',fr='Ajoute la preecoute du principal : FUNC + MACHINES ouvre le navigateur Sample Wizard ; choisir un sample et jouer un pad ou clavier pour ecouter avant chargement. Six voix909 et quatre WAV locaux conserves. Integration909 verifiee en emulation ; verification materielle attendue.')]))
 files['909-release.js']='window.MC_RELEASES='+json.dumps(release,ensure_ascii=False)+';\n'
 for name,heading,row in [('quick-reference.md','## Performance and sound','| Sample Preview | FUNC + MACHINES, highlight a sample, then play a pad or keyboard | Audition in the Sample Wizard browser before loading. |'),('quick-reference-fr.md','## Performance et son','| Preecoute samples | FUNC + MACHINES, choisir un sample puis jouer un pad ou clavier | Ecouter dans le navigateur Sample Wizard avant chargement. |')]:
  text=original(name).replace('909.5 ·','909.7 ·');separator='|---|---|---|\n';assert separator in text
  text=text.replace(separator,separator+row+'\n',1);files[name]=text
 prefix=original('shortcut-guide.html').split('<main>',1)[0]
 files['shortcut-guide.html']=prefix+'<main>'+''.join('<article data-l="'+lang+'">'+render(files[name])+'</article>' for lang,name in [('en','quick-reference.md'),('fr','quick-reference-fr.md')])+'</main></html>\n'
 files['guide.html']=files['shortcut-guide.html']
 for name,text in files.items():
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS port909 Sample Preview cible ; principal et voix conserves')
if __name__=='__main__':main()
