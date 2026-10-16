"""Note 103 : page test uniquement, principal 1.75 sans modification."""
import argparse,pathlib,re,shutil,tempfile,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-genie-timing-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();expected=ROOT/'docs/flasher-genie-timing-test'
 temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else expected;out.mkdir(exist_ok=True)
 # Garder le candidat reproductible apres sa promotion au principal.
 baseline='faf2520a1317ebe53bb2d09893869988e42085eb'
 for name in subprocess.check_output(['git','ls-tree','--name-only',baseline+':docs/flasher'],cwd=ROOT,text=True).splitlines():
  if '.' in name and not name.endswith('.wav') and subprocess.check_output(['git','cat-file','-t',baseline+':docs/flasher/'+name],cwd=ROOT,text=True).strip()=='blob':(out/name).write_bytes(subprocess.check_output(['git','show',baseline+':docs/flasher/'+name],cwd=ROOT))
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Sequence Genie timing test.</strong> Queue offers Loop or Page on both sides; MIDI generation follows the selected boundary. Includes the hardware-tested track 6 filter repair. Main remains 1.75.</span><span data-l="fr"><strong>Test timing Sequence Genie.</strong> Queue propose Loop ou Page des deux cotes ; generation MIDI selon la frontiere choisie. Correction filtre piste 6 testee incluse. Principal conserve en 1.75.</span></p>')
 # Recalculer le payload Banque avant que beat repeat fixe son adresse source.
 s=s.replace('../assets/release.js?','timing-release.js?').replace('<script src="beat-repeat-data.js',f'<script src="genie-timing-data.js?v={STAMP}"></script><script src="genie-timing.js?v={STAMP}"></script><script src="beat-repeat-data.js');(out/'index.html').write_text(s,encoding='utf-8')
 shutil.copyfile(ROOT/'build/genie-timing-data.js',out/'genie-timing-data.js');shutil.copyfile(ROOT/'tools/machines/seq_gen/timing.js',out/'genie-timing.js')
 (out/'timing-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='1.76-genie-preview.1',date='2026-10-16',changes=[dict(en='Experimental Sequence Genie timing restoration: Queue Loop/Page on A and B, replacing Sound 0/1. Main unchanged.',fr='Restauration experimentale timing Genie : Queue Loop/Page sur A et B au lieu de Sound 0/1. Principal inchange.')])])+';\n')
 for name in ('ABOUT.md','TEST-NOTES.md'):(out/name).write_text('Experimental Sequence Genie timing restoration. Generate first, Queue second: Loop waits for the selected track loop; Page waits for the next 16-step page. Verify both audio A and MIDI B during playback, Generate/Undo and MIDI saving. Includes the confirmed filter repair. Main unchanged.\n\nTest experimental du timing Genie. Generate premier, Queue deuxieme : Loop attend la boucle de piste ; Page la prochaine page de 16 pas. Verifier A audio et B MIDI en lecture, Generate/Undo et sauvegarde MIDI. Filtre confirme inclus. Principal inchange.\n')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():
   if src.suffix in ('.js','.html','.css','.md','.txt'):assert src.read_text(encoding='utf-8')==(expected/src.name).read_text(encoding='utf-8'),src.name
   else:assert src.read_bytes()==(expected/src.name).read_bytes(),src.name
 print('PASS page timing test uniquement')
if __name__=='__main__':main()
