"""Note 104 : page de test du stockage commun sans Banque MIDI."""
import argparse,pathlib,re,shutil,tempfile,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-16-no-midi-capacity-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();expected=ROOT/'docs/flasher-no-midi-capacity-test';temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else expected;out.mkdir(exist_ok=True)
 # Conserver le candidat historique apres sa promotion au principal.
 baseline='7704ae05bb7002f00114bb0f5590794070bf5f64'
 for name in subprocess.check_output(['git','ls-tree','--name-only',baseline+':docs/flasher'],cwd=ROOT,text=True).splitlines():
  if '.' in name and not name.endswith('.wav') and subprocess.check_output(['git','cat-file','-t',baseline+':docs/flasher/'+name],cwd=ROOT,text=True).strip()=='blob':(out/name).write_bytes(subprocess.check_output(['git','show',baseline+':docs/flasher/'+name],cwd=ROOT))
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>No-MIDI build capacity test.</strong> Select All, then untick MIDI OUT Bank. Keeps all machines, Sample Wizard and beat repeat through joint compression. Main is unchanged. The reported filter issue under heavy activity is still under investigation.</span><span data-l="fr"><strong>Test capacite sans Banque MIDI.</strong> Tout choisir puis decocher MIDI OUT Bank. Toutes machines, Sample Wizard et beat repeat conserves par compression commune. Principal inchange. Probleme filtre en forte activite encore en cours d analyse.</span></p>')
 s=s.replace('../assets/release.js?','capacity-release.js?').replace('<script src="beat-repeat.js',f'<script src="no-midi-capacity-data.js?v={STAMP}"></script><script src="no-midi-capacity.js?v={STAMP}"></script><script src="beat-repeat.js');(out/'index.html').write_text(s,encoding='utf-8')
 shutil.copyfile(ROOT/'build/no-midi-capacity-data.js',out/'no-midi-capacity-data.js');shutil.copyfile(ROOT/'tools/machines/beat_repeat/capacity.js',out/'no-midi-capacity.js')
 (out/'capacity-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='1.77-capacity-preview.1',date='2026-10-16',changes=[dict(en='Experimental joint compression for full builds without MIDI OUT Bank, retaining Sample Wizard, machines and beat repeat. Main unchanged; filter issue under heavy activity remains open.',fr='Compression commune experimentale sans Banque MIDI, avec Wizard, machines et beat repeat conserves. Principal inchange ; probleme filtre en forte activite encore ouvert.')])])+';\n')
 for name in ('ABOUT.md','TEST-NOTES.md'):(out/name).write_text('Experimental no-MIDI capacity repair. Select All, then disable MIDI OUT Bank; keep beat repeat and Sample Wizard. Test power-on, all machines including TINY and RETROSYN, a Wizard sample, Control All beat repeat and ordinary playback. No filter DSP changes; heavy-activity filter issue remains open. Main unchanged.\n\nTest capacite sans Banque MIDI. Tout choisir puis decocher Banque MIDI ; garder beat repeat et Wizard. Verifier boot, machines dont TINY/RETROSYN, sample Wizard, beat repeat collectif et lecture normale. DSP filtre inchange ; probleme en forte activite ouvert. Principal inchange.\n')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():
   if src.suffix in ('.js','.html','.css','.md','.txt'):assert src.read_text(encoding='utf-8')==(expected/src.name).read_text(encoding='utf-8'),src.name
   else:assert src.read_bytes()==(expected/src.name).read_bytes(),src.name
 print('PASS page capacite test uniquement')
if __name__=='__main__':main()
