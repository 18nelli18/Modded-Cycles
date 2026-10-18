"""Note122 : promotion du test confirme, module facultatif sans diagnostic."""
import argparse,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-invert-track-main-191'

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 out=ROOT/'docs/flasher'
 script=(ROOT/'docs/flasher-invert-track-test/invert-track.js').read_text(encoding='utf-8')
 script=script.replace("status:'experimental'","status:'tested'").replace('"status":"experimental"','"status":"tested"').replace('hardwareTestedByOwner:false','hardwareTestedByOwner:true')
 script=script.replace('window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady','window.MCLfoDestinationsReady')
 script=script.replace('Test build; hardware verification pending.','Hardware tested by AveyCole on 18 October 2026. Optional and unchecked by default.')
 script=script.replace('Test experimental a verifier sur machine.','Teste sur machine par AveyCole le18/10/2026. Facultatif, non coche par defaut.')
 html=(out/'index.html').read_text(encoding='utf-8')
 stamp=re.search(r"window.MC_BUILD='([^']+)'",html).group(1)
 html=re.sub(r'<script src="invert-track\.js\?v=[^"]+"></script>','',html)
 html=re.sub(r'(?<=\?v=)[\w.-]+',stamp,html)
 html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{stamp}'",html)
 html=html.replace('</body>',f'<script src="invert-track.js?v={stamp}"></script></body>')
 assert 'beat-diagnostic' not in html and 'audio-load.js?' not in html and 'Diagnostic' not in script
 assert html.index('lfo-destinations.js?')<html.index('invert-track.js?')
 for name,text in {'index.html':html,'invert-track.js':script}.items():
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS main1.91: optional hardware-tested silent selection, no diagnostics')
if __name__=='__main__':main()
