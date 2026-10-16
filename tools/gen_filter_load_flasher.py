"""Note 105 : candidat charge filtre, principal conserve en 1.77."""
import argparse,pathlib,re,shutil,tempfile,json
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-filter-load-test-3'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();expected=ROOT/'docs/flasher-filter-load-test';temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else expected;out.mkdir(exist_ok=True)
 for src in (ROOT/'docs/flasher').iterdir():
  if src.is_file() and src.suffix!='.wav':shutil.copyfile(src,out/src.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Busy-playback filter test 3.</strong> Reduced filter work plus lighter repeat-history recording while TRACK + RETRIG is held without a division pad. Compare your busy pattern and cutoff movements with MIDI OUT Bank on and off. Check distortion and ticks. Main unchanged; hardware verification pending.</span><span data-l="fr"><strong>Test filtre en lecture chargee 3.</strong> Filtre allege et enregistrement historique allege pendant TRACK + RETRIG sans pad de division. Comparer votre pattern charge et mouvements de coupure avec Banque MIDI active/inactive. Verifier distorsion et ticks. Principal inchange ; test materiel attendu.</span></p>')
 s=s.replace('../assets/release.js?','load-release.js?').replace('</body>',f'<script src="filter-load-data.js?v={STAMP}"></script><script src="filter-load.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8')
 shutil.copyfile(ROOT/'build/filter-load-data.js',out/'filter-load-data.js');shutil.copyfile(ROOT/'tools/machines/track_filter/load.js',out/'filter-load.js')
 (out/'load-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='1.78-filter-load-preview.3',date='2026-10-16',changes=[dict(en='Test 3: lighter repeat-history recording while holding TRACK + RETRIG without a division pad. Filter test 2 arithmetic retained. Test six active machines and beat repeat with five or more. Check ticks at a fixed lower cutoff. MIDI Bank remains optional and experimental. Main unchanged.',fr='Test 3 : historique beat repeat allege avec TRACK + RETRIG sans pad. Calculs filtre test 2 conserves. Tester six machines actives et beat repeat avec cinq ou plus. Verifier ticks a coupure basse fixe. Banque MIDI facultative et experimentale. Principal inchange.')])])+';\n')
 data=json.loads((ROOT/'build/beat-idle-data.json').read_text());(out/'beat-repeat-data.js').write_text('// Code propre ; note 105.\nwindow.MCBeatRepeat='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 p=out/'beat-repeat.js';p.write_text(p.read_text(encoding='utf-8').replace("status:'tested',hardwareTestedByOwner:true","status:'experimental',hardwareTestedByOwner:false"),encoding='utf-8')
 for name in ('ABOUT.md','TEST-NOTES.md'):(out/name).write_text('Experimental filter workload test. Use the same busy pattern and compare MIDI OUT Bank selected and unselected. Lower cutoff and listen for distortion/ticks; verify full-open, zero-resonance bypass and resonance. Existing no-MIDI capacity support and all selected features are retained. Main unchanged.\n\nTest charge filtre. Meme pattern charge avec et sans Banque MIDI. Baisser la coupure et ecouter distorsion/ticks ; verifier bypass ouvert/resonance nulle et resonance. Capacite sans Banque et fonctions choisies conservees. Principal inchange.\n')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():
   if src.suffix in ('.js','.html','.css','.md','.txt'):assert src.read_text(encoding='utf-8')==(expected/src.name).read_text(encoding='utf-8'),src.name
   else:assert src.read_bytes()==(expected/src.name).read_bytes(),src.name
 print('PASS page test charge filtre')
if __name__=='__main__':main()
