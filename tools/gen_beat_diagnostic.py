"""Note 111 : diagnostic CPU/CUT seul sur une copie du principal courant."""
import argparse,json,pathlib,re,shutil,tempfile
from gen_beat_repeat import generate
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-17-beat-diagnostic-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 data=generate([],ROOT/'tools/machines/beat_diagnostic')
 original=json.loads((ROOT/'docs/flasher/beat-repeat-data.js').read_text(encoding='utf-8').split('window.MCBeatRepeat=',1)[1].strip().rstrip(';'))
 data['boot']=original['boot'];data['redirect']=original['redirect']
 target=ROOT/'docs/flasher-beat-diagnostic-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher').iterdir():
  if f.is_file() and f.suffix!='.wav':shutil.copyfile(f,out/f.name)
 (out/'beat-diagnostic-data.js').write_text('window.MCBeatDiagnostic='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 shutil.copyfile(ROOT/'tools/web/beat-diagnostic.js',out/'beat-diagnostic.js')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=re.sub(r'<title>.*?</title>','<title>Main flasher — beat repeat diagnostic test</title>',s,count=1)
 notice='<p><span data-l="en"><strong>Beat repeat load diagnostic test.</strong> Current main checklist with the CPU average/peak and CUT diagnostic. Select Audio load diagnostic, Control All Beat Repeat, and at least one SY engine. Hold TRACK + RETRIG while reproducing the problem, then release either button to see CPU average / peak and CUT track count. You can hold the combo without a division pad. Record the numbers and selected machines. This measures load; it is not a click repair. No MIDI beat repeat or MIDI filter experiment. Released main unchanged.</span><span data-l="fr"><strong>Test diagnostic charge beat repeat.</strong> Checklist principale avec CPU moyenne/pic et compteur CUT. Cocher Diagnostic charge audio, Control All Beat Repeat et au moins un moteur SY. Maintenir TRACK + RETRIG pendant le probleme puis relacher un bouton : CPU moyenne/pic et nombre de pistes CUT. Le combo seul suffit, sans pad division. Noter les valeurs et machines. Mesure, pas correction des clicks. Sans repeat MIDI ni filtre MIDI experimental. Principal publie inchange.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+notice).replace('../assets/release.js?','diagnostic-release.js?').replace('</body>',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script></body>')
 (out/'index.html').write_text(s,encoding='utf-8')
 (out/'diagnostic-release.js').write_text('window.MC_RELEASES=[{version:"Beat-diagnostic-test.1",date:"2026-10-17",changes:[{en:"CPU average/peak and CUT counter on the current main checklist. Experimental diagnostic only.",fr:"CPU moyenne/pic et compteur CUT sur checklist principale. Diagnostic experimental uniquement."}]}];\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 build=ROOT/'build/beat-diagnostic';build.mkdir(exist_ok=True);(build/'data.json').write_text(json.dumps(data),encoding='utf-8')
 print('PASS copie principale avec diagnostic CPU/CUT uniquement')
if __name__=='__main__':main()
