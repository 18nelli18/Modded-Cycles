"""Note124 : promotion du convertisseur MACRO confirme, sans diagnostic."""
import argparse,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-macro-render-main-193'

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 out=ROOT/'docs/flasher';test=ROOT/'docs/flasher-macro-render-test'
 content={n:(test/n).read_text(encoding='utf-8') for n in ['macro-halfband-data.js','macro-render-optimization.js','swarm-lite.js']}
 old='window.MCSwarmChordLayout(changed,input,b,a,syntakt,stock,saved)'
 new='window.MCSwarmChordLayout(window.MCMacroRenderOptimize(changed,b,a,syntakt,stock,saved),input,b,a,syntakt,stock,saved)'
 baseline=(out/'swarm-lite.js').read_text(encoding='utf-8')
 assert baseline==content['swarm-lite.js'] or baseline.replace(old,new)==content['swarm-lite.js'],'Seule integration MACRO confirmee autorisee'
 html=(out/'index.html').read_text(encoding='utf-8')
 html=re.sub(r'<script src="macro-(?:halfband-data|render-optimization)\.js\?v=[^"]+"></script>','',html)
 html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html)
 html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=html.replace('<script src="swarm-lite.js?',f'<script src="macro-halfband-data.js?v={STAMP}"></script><script src="macro-render-optimization.js?v={STAMP}"></script><script src="swarm-lite.js?')
 assert html.count('src="macro-render-optimization.js?')==1
 assert 'beat-diagnostic' not in html and 'audio-load.js?' not in html
 content['index.html']=html
 for name,text in content.items():
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS main1.93 : convertisseur MACRO confirme, aucun diagnostic')
if __name__=='__main__':main()
