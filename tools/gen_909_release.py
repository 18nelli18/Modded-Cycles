"""Note 108 : promouvoir le profil 909 verifie, page sobre et controles actuels."""
import argparse,json,pathlib,re,shutil,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-16-909-current-release'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 target=ROOT/'docs/flasher-supermodel-909';source=ROOT/'docs/flasher-supermodel-909-current-test'
 tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(tmp.name) if tmp else target
 out.mkdir(exist_ok=True)
 names={p.name for p in source.iterdir() if p.is_file()}-{'TEST-NOTES.md'}
 for name in names:shutil.copyfile(source/name,out/name)
 html=(out/'index.html').read_text(encoding='utf-8')
 html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=re.sub(r'<title>.*?</title>','<title>Supermodel 909 — A.V.’s Edition</title>',html,count=1)
 html=re.sub(r'<h1>.*?</h1>','<h1>Supermodel 909<br><span>A.V.’s Edition</span></h1><p class="release-status"><span data-l="en">Hardware tested</span><span data-l="fr">Teste sur machine</span></p>',html,count=1,flags=re.S)
 head,tail=html.split('<section',1)
 head=re.sub(r'<p class="alert">.*?</p>','',head,flags=re.S)
 head+='<p><span data-l="en">Six 909 voices with Sample Wizard, ACID, per-track filter, slide trigs, Sequence Genie, SCRAMBLE, Second LFO, MIDI Bank and Control All Beat Repeat. Choose four WAVs and official Cycles OS 1.13.</span><span data-l="fr">Six voix 909, Sample Wizard, ACID, filtre par piste, slides, Sequence Genie, SCRAMBLE, Second LFO, banque MIDI et beat repeat Control All. Quatre WAV et OS Cycles 1.13 officiel requis.</span></p><details><summary><span data-l="en">MIDI saving</span><span data-l="fr">Sauvegarde MIDI</span></summary><p><span data-l="en">Saved MIDI loads only when entering B-side while playback is stopped.</span><span data-l="fr">Le MIDI sauvegarde charge uniquement en entrant cote B, lecture arretee.</span></p></details>'
 html=head+'<section'+tail
 html=html.replace('<script src="909-current.js', '<script>window.MC909Released=true;</script><script src="909-current.js')
 (out/'index.html').write_text(html,encoding='utf-8')
 (out/'909-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='909.2',date='2026-10-16',changes=[dict(en='Current shared modules, Sample Wizard, per-track filter and Control All Beat Repeat; owner approved for release after test 2.',fr='Modules partages actuels, Sample Wizard, filtre par piste et beat repeat Control All ; publication validee apres test 2.')])])+';\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(status='released',hardware_tested=True,hardware_tested_by='AveyCole',hardware_tested_date='2026-10-16',samples_hosted=False,sample_capacity_bytes=180000,sample_rate=32000),indent=2)+'\n',encoding='utf-8')
 (out/'ABOUT.md').write_text('Supermodel 909 909.2: current shared modules with Sample Wizard, filter, slides, Genie, SCRAMBLE, MIDI saving and held Control All Beat Repeat. Hardware verified and release approved by AveyCole after current test 2. Four local WAVs and official Cycles 1.13 required. No audio or firmware hosted.\n',encoding='utf-8')
 if a.check:
  for p in out.iterdir():assert p.read_bytes().replace(b'\r\n',b'\n')==(target/p.name).read_bytes().replace(b'\r\n',b'\n'),p.name
 else:
  keep={p.name for p in out.iterdir()} if tmp else names|{'BUILD.json','ABOUT.md'}
  for p in target.iterdir():
   if p.is_file() and p.name not in keep:p.unlink()
 print('PASS edition 909 publiee, statut verifie et en-tete sobre')
if __name__=='__main__':main()
