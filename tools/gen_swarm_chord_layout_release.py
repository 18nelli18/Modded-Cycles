"""Note123 : publier exactement le placement confirme sans diagnostic."""
import argparse,hashlib,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-swarm-chord-main-192'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=ROOT/'docs/flasher';test=ROOT/'docs/flasher-swarm-chord-layout-test'
 helper=(test/'swarm-chord-layout.js').read_text(encoding='utf-8');swarm=(test/'swarm-lite.js').read_text(encoding='utf-8')
 assert hashlib.sha256(helper.encode()).hexdigest()=='0ad0f93f99ea96c4f296aa0553e458fd7baa54fd225a7d679b9fea20822c24c6','Helper confirme requis'
 assert hashlib.sha256(swarm.encode()).hexdigest()=='c890979cda98e735a422dd05cec78b8109c67852e1e931fbf30b99947994f1f4','Integration Swarm confirmee requise'
 assert helper==(ROOT/'tools/web/swarm-chord-layout.js').read_text(encoding='utf-8')
 baseline=(out/'swarm-lite.js').read_text(encoding='utf-8');old='return previous(changed,cycles,syntakt);';new='return previous(window.MCSwarmChordLayout(changed,input,b,a,syntakt,stock,saved),cycles,syntakt);'
 assert baseline==swarm or baseline.replace(old,new)==swarm,'Seul appel de placement confirme autorise'
 html=(out/'index.html').read_text(encoding='utf-8');html=re.sub(r'<script src="swarm-chord-layout\.js\?v=[^"]+"></script>','',html)
 html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=html.replace('<script src="swarm-lite.js?',f'<script src="swarm-chord-layout.js?v={STAMP}"></script><script src="swarm-lite.js?')
 assert html.count('src="swarm-chord-layout.js?')==1 and 'beat-diagnostic' not in html and 'audio-load.js?' not in html
 for name,text in {'swarm-chord-layout.js':helper,'swarm-lite.js':swarm,'index.html':html}.items():
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS main1.92: placement du test confirme, voix identiques, aucun diagnostic')
if __name__=='__main__':main()
