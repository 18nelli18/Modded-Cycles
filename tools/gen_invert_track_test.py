"""Note122 : page de test facultative sur principal1.90, diagnostics conserves."""
import argparse,json,pathlib,re,shutil,tempfile
from gen_invert_track import recipe
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-18-invert-track-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();folder=ROOT/'docs/flasher-invert-track-test'
 temp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None;out=pathlib.Path(temp.name) if temp else folder;out.mkdir(exist_ok=True)
 for f in (ROOT/'docs/flasher').iterdir():
  if f.is_file() and f.suffix!='.wav':shutil.copyfile(f,out/f.name)
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):shutil.copyfile(ROOT/'docs/flasher-lfo-destinations-test'/name,out/name)
 payload=json.dumps(recipe(experimental=True),ensure_ascii=False,separators=(',',':'))
 script="""// Note122 : module facultatif, references gardees ; aucune selection automatique.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,t=RECIPE;
window.MCInvertTrackReady=Promise.all([window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady]).then(()=>{
tw.tweaks.push(t);tw.features.push({id:t.id,label:'Silent track selection',cat:'live',status:'experimental',excludes:[],variants:[{id:t.id}],credit:{kind:'by',who:'Community contribution supplied by AveyCole'}});
a.REF_MODS[t.id]={w:b.hex(b.sha256(b.writesBytes(t)))};
a.registerFeatureTexts(t.id,{en:{label:'Silent track selection',short:'Plain T1–T6 pad selects silently; TRACK + pad plays.',desc:'Optional reversal of stock pad behavior. Plain track-pad presses select without sound. Hold TRACK and press a track pad to select and play through the normal live-record path. Preset-browser preview on a plain pad is preserved. TRACK + pad in that browser selects and plays. Step keys are unchanged. Test build; hardware verification pending.'},fr:{label:'Selection de piste silencieuse',short:'Pad T1–T6 seul : selection silencieuse ; TRACK + pad : jouer.',desc:'Inversion facultative des pads : appui simple selectionne sans son ; TRACK + pad selectionne et joue par le relais live record natif. Apercu du navigateur conserve par pad simple ; TRACK + pad selectionne et joue dans le navigateur. Touches de pas conservees. Test experimental a verifier sur machine.'}});
const previous=window.MCMidiBankCompose;window.MCMidiBankCompose=(input,...args)=>{const r=previous(input.filter(x=>x.id!==t.id),...args);if(!a.isSelected(t.id))return r;return {...r,tweaks:r.tweaks.concat({...t,hardwareTestedByOwner:false}).sort((x,y)=>x.order-y.order),refMods:{...r.refMods,[t.id]:{w:b.hex(b.sha256(b.writesBytes(t)))}}};};a.applyLang(document.documentElement.lang||'en');
});})();
""".replace('RECIPE',payload)
 (out/'invert-track.js').write_text(script,encoding='utf-8')
 s=(out/'index.html').read_text(encoding='utf-8');s=re.sub(r'<script src="invert-track\.js\?v=[^"]+"></script>','',s);s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s);s=s.replace('../assets/release.js?','test-release.js?')
 notice='<p><strong data-l="en">Optional silent track selection test — main1.90.</strong><strong data-l="fr">Test de selection silencieuse facultative — principal1.90.</strong> <span data-l="en">Enable Silent track selection in the checklist to try the supplied one-byte pad inversion. Plain pads select silently; TRACK + pad plays, including live recording. Browser preview is preserved. The module starts unchecked. Main1.90 LFO fixes are included. Diagnostics remain available: select Audio load diagnostic, Beat Repeat and at least one SY engine, then release TRACK + RETRIG to see CPU/CUT. Without those selections there is no CPU/CUT readout. Released flashers are unchanged by this test.</span><span data-l="fr">Cocher Selection de piste silencieuse pour essayer l’inversion des pads fournie. Pad seul : selection sans son ; TRACK + pad : jouer, y compris enregistrement live. Apercu navigateur conserve. Module non coche par defaut. Corrections LFO principal1.90 incluses. Diagnostic disponible avec Diagnostic charge audio, Beat Repeat et un moteur SY : relacher TRACK + RETRIG pour CPU/CUT. Sans ces choix, pas de compteur. Ce test ne modifie pas les versions publiees.</span></p>'
 s=s.replace('<main class="wrap fl">','<main class="wrap fl">'+notice).replace('</body>',''.join(f'<script src="{name}?v={STAMP}"></script>' for name in ('beat-diagnostic-data.js','beat-diagnostic.js','invert-track.js'))+'</body>');(out/'index.html').write_text(s,encoding='utf-8')
 (out/'test-release.js').write_text('window.MC_RELEASES='+json.dumps([dict(version='Invert-track-test.1',date='2026-10-18',changes=[dict(en='Optional silent track selection: enable its checklist entry. Includes main1.90 and test-only CPU/CUT diagnostics.',fr='Selection silencieuse facultative : cocher sa ligne. Principal1.90 et diagnostic CPU/CUT de test inclus.')])])+';\n',encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,base='main1.90',scope='test-only',optional_module='invert-track',default_enabled=False,diagnostics=True),indent=2)+'\n',encoding='utf-8')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(folder/f.name).read_bytes().replace(b'\r\n',b'\n'),str(f)
 print('PASS optional invert-track test page; diagnostics available; release untouched')
if __name__=='__main__':main()
