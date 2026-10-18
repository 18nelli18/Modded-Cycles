"""Note124 : test MACRO uniquement, principal1.92 epingle et diagnostic disponible."""
import argparse,json,pathlib,re,shutil,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-18-macro-render-test-1';BASELINE='f3e5ed2cfadef8e69140717bc509febb5368a859'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();target=ROOT/'docs/flasher-macro-render-test'
 temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else target;out.mkdir(exist_ok=True)
 for row in subprocess.check_output(['git','ls-tree',BASELINE+':docs/flasher'],cwd=ROOT,text=True).splitlines():
  meta,name=row.split('\t',1)
  if ' blob ' in meta and pathlib.Path(name).suffix!='.wav':(out/name).write_bytes(subprocess.check_output(['git','show',BASELINE+':docs/flasher/'+name],cwd=ROOT))
 for name in ['beat-diagnostic-data.js','beat-diagnostic.js']:shutil.copyfile(ROOT/'docs/flasher-invert-track-test'/name,out/name)
 shutil.copyfile(ROOT/'build/macro-optimization/macro-halfband-data.js',out/'macro-halfband-data.js');shutil.copyfile(ROOT/'tools/web/macro-render-optimization.js',out/'macro-render-optimization.js')
 s=(out/'swarm-lite.js').read_text(encoding='utf-8');old='window.MCSwarmChordLayout(changed,input,b,a,syntakt,stock,saved)';new='window.MCSwarmChordLayout(window.MCMacroRenderOptimize(changed,b,a,syntakt,stock,saved),input,b,a,syntakt,stock,saved)';assert s.count(old)==1;s=s.replace(old,new);(out/'swarm-lite.js').write_text(s,encoding='utf-8')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<script src="swarm-lite.js?',f'<script src="macro-halfband-data.js?v={STAMP}"></script><script src="macro-render-optimization.js?v={STAMP}"></script><script src="swarm-lite.js?')
 s=s.replace('../assets/release.js?','test-release.js?').replace('</body>',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script></body>')
 notice='<p><strong data-l="en">MACRO render optimization test.</strong><strong data-l="fr">Test optimisation rendu MACRO.</strong> <span data-l="en">Keeps all47 models. Replaces only the 96-to-48 kHz converter with a sample-exact integer EMAC loop; the existing lower-rate models are unchanged. Lower instruction count is an emulator result, not a measured hardware CPU percentage. Check Model 3 in the reported Kick / SD VINTAGE / MACRO / ACID / Metal sequence with the filter inactive and a repeat division held; note CPU/peak/CUT. Optional diagnostic needs Beat Repeat and a SY engine installed: release TRACK + RETRIG to read it. Main unchanged; hardware verification pending.</span><span data-l="fr">Les47 modeles sont conserves. Seule la conversion96vers48kHz utilise une boucle EMAC entiere de sortie identique ; modeles deja alleges conserves. Gain d instructions mesure en emulation, pas un pourcentage CPU materiel. Verifier le modele3 dans Kick / SD VINTAGE / MACRO / ACID / Metal, filtre inactif et division repeat tenue ; noter CPU/pic/CUT. Diagnostic facultatif avec Beat Repeat et moteur SY : relacher TRACK + RETRIG. Principal inchange ; validation machine attendue.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+notice);(out/'index.html').write_text(s,encoding='utf-8')
 (out/'test-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='Macro-render-test.1',date='2026-10-18',changes=[dict(en='Sample-exact, same-size MACRO converter optimization. All47 models retained; main unchanged.',fr='Conversion MACRO optimisee a taille et sortie identiques. Les47 modeles restent ; principal inchange.')])])+';\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',base='main1.92',diagnostics=True,hardware_verified=False,models=47,changed_code_bytes=162),indent=2)+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS copie MACRO1.92, optimisation seule et diagnostic facultatif')
if __name__=='__main__':main()
