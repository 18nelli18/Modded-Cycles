"""Note 105 : candidat charge filtre, principal conserve en 1.77."""
import argparse,pathlib,re,shutil,tempfile,json
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-filter-load-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();expected=ROOT/'docs/flasher-filter-load-test';temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else expected;out.mkdir(exist_ok=True)
 for src in (ROOT/'docs/flasher').iterdir():
  if src.is_file() and src.suffix!='.wav':shutil.copyfile(src,out/src.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Busy-playback filter test.</strong> Less repeated processing work with identical filter arithmetic. Compare your busy pattern and cutoff movements with MIDI OUT Bank on and off. Check distortion and ticks. Main unchanged; hardware verification pending.</span><span data-l="fr"><strong>Test filtre en lecture chargee.</strong> Moins de calcul repete avec memes resultats filtre. Comparer votre pattern charge et mouvements de coupure avec Banque MIDI active/inactive. Verifier distorsion et ticks. Principal inchange ; test materiel attendu.</span></p>')
 s=s.replace('../assets/release.js?','load-release.js?').replace('</body>',f'<script src="filter-load-data.js?v={STAMP}"></script><script src="filter-load.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8')
 shutil.copyfile(ROOT/'build/filter-load-data.js',out/'filter-load-data.js');shutil.copyfile(ROOT/'tools/machines/track_filter/load.js',out/'filter-load.js')
 (out/'load-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='1.78-filter-load-preview.1',date='2026-10-16',changes=[dict(en='Experimental filter-workload reduction. Same arithmetic and bit-identical comparison samples; check busy playback, distortion and ticks with MIDI Bank on/off. Includes optional-bank build support. Main unchanged.',fr='Test reduction du travail filtre. Memes calculs et samples compares identiques ; verifier lecture chargee, distorsion et ticks avec/sans Banque MIDI. Build sans Banque pris en charge. Principal inchange.')])])+';\n')
 for name in ('ABOUT.md','TEST-NOTES.md'):(out/name).write_text('Experimental filter workload test. Use the same busy pattern and compare MIDI OUT Bank selected and unselected. Lower cutoff and listen for distortion/ticks; verify full-open, zero-resonance bypass and resonance. Existing no-MIDI capacity support and all selected features are retained. Main unchanged.\n\nTest charge filtre. Meme pattern charge avec et sans Banque MIDI. Baisser la coupure et ecouter distorsion/ticks ; verifier bypass ouvert/resonance nulle et resonance. Capacite sans Banque et fonctions choisies conservees. Principal inchange.\n')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():
   if src.suffix in ('.js','.html','.css','.md','.txt'):assert src.read_text(encoding='utf-8')==(expected/src.name).read_text(encoding='utf-8'),src.name
   else:assert src.read_bytes()==(expected/src.name).read_bytes(),src.name
 print('PASS page test charge filtre')
if __name__=='__main__':main()
