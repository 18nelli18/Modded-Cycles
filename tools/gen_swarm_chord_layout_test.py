"""Note123 : copie test ciblee, source ChordKeys apres recompression Swarm."""
import argparse,json,pathlib,re,shutil,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-swarm-chord-layout-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();target=ROOT/'docs/flasher-swarm-chord-layout-test'
 temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else target;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher').iterdir():
  if f.is_file() and f.suffix!='.wav':shutil.copyfile(f,out/f.name)
 for name in ['beat-diagnostic-data.js','beat-diagnostic.js']:shutil.copyfile(ROOT/'docs/flasher-invert-track-test'/name,out/name)
 shutil.copyfile(ROOT/'tools/web/swarm-chord-layout.js',out/'swarm-chord-layout.js')
 s=(out/'swarm-lite.js').read_text(encoding='utf-8');old='return previous(changed,cycles,syntakt);';assert s.count(old)==1
 s=s.replace(old,'return previous(window.MCSwarmChordLayout(changed,input,b,a,syntakt,stock,saved),cycles,syntakt);');(out/'swarm-lite.js').write_text(s,encoding='utf-8')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<script src="swarm-lite.js?',f'<script src="swarm-chord-layout.js?v={STAMP}"></script><script src="swarm-lite.js?')
 s=s.replace('../assets/release.js?','test-release.js?').replace('</body>',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script></body>')
 notice='<p><strong data-l="en">Swarm / ChordKeys layout test.</strong><strong data-l="fr">Test placement Swarm / ChordKeys.</strong> <span data-l="en">Repairs firmware preparation for the reported ACID + all Syntakt engines + WAVE + Sample Wizard + ChordKeys selection. Corrects a stale loader address after Swarm LITE compression; no new voice code. Main remains unchanged. Optional CPU/CUT diagnostic needs Beat Repeat and a SY engine; release TRACK + RETRIG to read it. Hardware verification pending.</span><span data-l="fr">Corrige la preparation ACID + tous les moteurs Syntakt + WAVE + Sample Wizard + ChordKeys. Adresse de chargement perimee apres compression Swarm LITE ; voix conservees. Principal inchange. Diagnostic CPU/CUT facultatif avec Beat Repeat et moteur SY ; relacher TRACK + RETRIG. Verification machine attendue.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+notice);(out/'index.html').write_text(s,encoding='utf-8')
 (out/'test-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='Swarm-Chord-test.1',date='2026-10-18',changes=[dict(en='Targeted repair for stale ChordKeys payload source after Swarm LITE recompression. Main unchanged.',fr='Correction ciblee de source ChordKeys apres recompression Swarm LITE. Principal inchange.')])])+';\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',base='main1.91',hardware_verified=False,diagnostics=True,repair='ChordKeys source relocation only'),indent=2)+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS reproducible targeted Swarm/Chord test; main unchanged')
if __name__=='__main__':main()
