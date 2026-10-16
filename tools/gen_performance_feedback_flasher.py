"""Note 100 : page de test popup repeat et LEDs mute B, principal inchange."""
import argparse,json,pathlib,re,shutil,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-16-performance-feedback-test-1'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--beat-data',required=True);p.add_argument('--midi-data',required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 expected=ROOT/'docs/flasher-performance-feedback-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None
 out=pathlib.Path(tmp.name) if tmp else expected;out.mkdir(exist_ok=True)
 for src in (ROOT/'docs/flasher').iterdir():
  if not src.is_file() or src.suffix=='.wav':continue
  shutil.copyfile(src,out/src.name)
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 s=re.sub(r'<p class="alert" id="beat-repeat-status">.*?</p>','',s)
 s=s.replace('<main class="wrap fl">','<main class="wrap fl"><p class="alert"><span data-l="en"><strong>Experimental performance feedback.</strong> Beat repeat briefly shows its selected division. MIDI B-side with FUNC: unmuted pads stay lit, muted pads stay dark except B-note pulses; no selected-track highlight until FUNC is released. Both changes await hardware verification. <a href="../flasher/">Hardware-tested main</a>.</span><span data-l="fr"><strong>Feedback performance experimental.</strong> Beat repeat affiche brievement sa division. Cote B avec FUNC : pads actifs allumes, coupes eteints sauf pulses des notes B ; aucun surlignage de selection avant de relacher FUNC. Deux changements en attente de verification materielle. <a href="../flasher/">Principal teste</a>.</span></p>')
 s=s.replace('href="convert.html"','href="../flasher/convert.html"').replace('../assets/release.js?','feedback-release.js?')
 s=s.replace('</body>',f'<script src="feedback-status.js?v={STAMP}"></script></body>');(out/'index.html').write_text(s,encoding='utf-8')
 data=json.loads(pathlib.Path(a.beat_data).read_text());(out/'beat-repeat-data.js').write_text('// Code propre ; note 100.\nwindow.MCBeatRepeat='+json.dumps(data,separators=(',',':'))+';\n',encoding='utf-8')
 shutil.copyfile(a.midi_data,out/'midi-bank-data.js')
 for name in ('beat-repeat.js','midi-persistence.js','midi-bank.js'):
  p=out/name;s=p.read_text(encoding='utf-8').replace("status:'tested',hardwareTestedByOwner:true","status:'experimental'").replace("status:'tested'","status:'experimental'").replace(".status='tested';", ".status='experimental';").replace('.hardwareTestedByOwner=true;', '.hardwareTestedByOwner=false;').replace('Hardware tested by AveyCole.','Experimental UI feedback; hardware verification pending.').replace('Teste sur machine par AveyCole.','Feedback UI experimental ; test materiel attendu.')
  if name=='beat-repeat.js':s=s.replace('Experimental UI feedback; hardware verification pending.','Selected divisions appear briefly in a popup. Hardware verification pending.').replace('Feedback UI experimental ; test materiel attendu.','Popup bref de la division choisie. Test materiel attendu.')
  if name=='midi-persistence.js':s=s.replace('Experimental UI feedback; hardware verification pending.','Experimental mute LEDs: while FUNC is held, unmuted pads stay steadily lit; muted pads stay dark except B-side note pulses. Selection highlight returns on FUNC release. Hardware verification pending.').replace('Feedback UI experimental ; test materiel attendu.','LEDs mute experimentales : pendant FUNC, pistes actives allumees, coupees eteintes sauf pulses B. Selection visible au relachement FUNC. Test materiel attendu.')
  p.write_text(s,encoding='utf-8')
 (out/'feedback-status.js').write_text("// Note 100 : statut experimental pour ces deux changements seulement.\n(()=>{for(const id of ['control-all-beat-repeat','midi-out-bank']){const f=window.MC_TWEAKS.features.find(f=>f.id===id);f.status='experimental';delete f.hardwareTestedByOwner;}})();\n",encoding='utf-8')
 (out/'feedback-release.js').write_text('window.MC_RELEASES='+json.dumps([{'version':'1.74-feedback-preview.1','date':'2026-10-16','changes':[{'en':'Test only: brief beat-repeat division popup. MIDI B mute lighting follows stock while FUNC is held: unmuted pads steadily lit; muted pads dark except B-note pulses. Selected-track highlight returns after FUNC release. Main remains unchanged.','fr':'Test : popup bref de division beat repeat. LEDs mute B selon le natif pendant FUNC : pistes actives allumees, coupees eteintes sauf pulses B. Selection visible apres relachement FUNC. Principal inchange.'}]}],ensure_ascii=False)+';\n',encoding='utf-8')
 for name in ('quick-reference.md','quick-reference-fr.md'):
  p=out/name;p.write_text(p.read_text(encoding='utf-8')+'\n'+('Experimental feedback: beat-repeat divisions appear briefly in a popup. During FUNC in B-side, unmuted pads stay lit and muted pads stay dark except B-note pulses. Selected-track highlight returns on FUNC release. Hardware verification pending.' if name=='quick-reference.md' else 'Feedback experimental : popup bref des divisions beat repeat. Pendant FUNC cote B, pistes actives allumees, coupees eteintes sauf pulses B. Selection visible au relachement FUNC. Test materiel attendu.')+'\n',encoding='utf-8')
 (out/'ABOUT.md').write_text('Experimental performance feedback: brief beat-repeat division popup and stock-style MIDI B mute LEDs during FUNC. No selected-track highlight while FUNC is held. Hardware verification pending; main unchanged.\n\nFeedback performance experimental : popup bref de division beat repeat et LEDs mute B selon le natif pendant FUNC. Aucun surlignage de selection pendant FUNC. Test materiel attendu ; principal inchange.\n',encoding='utf-8')
 for src in out.iterdir():
  if src.suffix in ('.js','.html','.css','.md','.txt'):src.write_text('\n'.join(line.rstrip() for line in src.read_text(encoding='utf-8').splitlines()).rstrip()+'\n',encoding='utf-8')
 if a.check:
  for src in out.iterdir():assert (expected/src.name).read_bytes()==src.read_bytes(),src.name
 print('ok page test feedback ; ressources principales inchangees')
if __name__=='__main__':main()
