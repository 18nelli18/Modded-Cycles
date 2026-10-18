"""Copie test des combinaisons machines, principal publie inchange."""
import argparse,json,pathlib,re,shutil,tempfile
from gen_beat_repeat import generate
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-17-machine-combinations-test-1'

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');a=parser.parse_args()
 target=ROOT/'docs/flasher-machine-combinations-test'
 temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None
 out=pathlib.Path(temp.name) if temp else target;out.mkdir(exist_ok=True)
 for source in (ROOT/'docs/flasher').iterdir():
  if source.is_file() and source.suffix!='.wav':shutil.copyfile(source,out/source.name)
 data=generate([],ROOT/'tools/machines/beat_diagnostic')
 normal=json.loads((ROOT/'docs/flasher/beat-repeat-data.js').read_text(encoding='utf-8').split('window.MCBeatRepeat=',1)[1].strip().rstrip(';'))
 data['boot']=normal['boot'];data['redirect']=normal['redirect']
 (out/'beat-diagnostic-data.js').write_text('window.MCBeatDiagnostic='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 diagnostic=(ROOT/'tools/web/beat-diagnostic.js').read_text(encoding='utf-8').replace('p:hash(raw)', 'p:hash(b.buildPayload(beat.append,syntakt,null))')
 (out/'beat-diagnostic.js').write_text(diagnostic,encoding='utf-8')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=re.sub(r'<title>.*?</title>','<title>Modded Cycles — machine combinations test</title>',s,count=1)
 notice='<p><span data-l="en"><strong>Machine combinations test.</strong> TINY and RETROSYN with any selection of the other added machines, including partial SY sets; Sample Wizard optional. Recheck your usual selection and the reported checklist. Voice code is unchanged; the expanded menus and boot paths are verified in emulation. Hardware verification pending. CPU/CUT diagnostic: select Audio load diagnostic, Control All Beat Repeat and at least one SY engine; hold TRACK + RETRIG, then release either button. Record CPU average/peak and CUT. The diagnostic is optional; without SY load counters those readings are unavailable. Main flasher unchanged.</span><span data-l="fr"><strong>Test combinaisons machines.</strong> TINY et RETROSYN avec les autres machines au choix, dont les sous-ensembles SY ; Sample Wizard facultatif. Verifier votre selection habituelle et la liste signalee. Code des voix conserve ; menus et demarrage verifies en emulation. Validation materielle attendue. Diagnostic CPU/CUT : cocher Diagnostic charge audio, Beat Repeat collectif et au moins une voix SY ; maintenir TRACK + RETRIG puis relacher un bouton. Noter moyenne/pic CPU et CUT. Diagnostic facultatif ; releves indisponibles sans compteurs SY. Flasheur principal inchange.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+notice).replace('../assets/release.js?','test-release.js?').replace('</body>',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script></body>')
 (out/'index.html').write_text(s,encoding='utf-8')
 (out/'test-release.js').write_text('window.MC_RELEASES=[{version:"Machine-combinations-test.1",date:"2026-10-17",changes:[{en:"Independent TINY/RETROSYN selections, with optional Sample Wizard. CPU/CUT diagnostic retained. Test only; main unchanged.",fr:"Selections TINY/RETROSYN independantes, Sample Wizard facultatif. Diagnostic CPU/CUT conserve. Test seulement ; principal inchange."}]}];\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',source_fix='0c93eb314490572d7c1f4e52814584e507fbc1c5',main_unchanged=True,hardware_verified=False,diagnostic='optional CPU average/peak and CUT with beat repeat and SY counters'),indent=2)+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS separate machine-combinations test copy with CPU/CUT diagnostic')
if __name__=='__main__':main()
