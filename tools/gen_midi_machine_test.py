"""Note126 : test isole stock+MIDI live, sans modifier le flasheur principal."""
import argparse,json,pathlib,re,tempfile,hashlib
import build,gen_sdvintage_7th as g7
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-midi-machine-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 target=ROOT/'docs/flasher-midi-machine-test';tmp=tempfile.TemporaryDirectory(dir=ROOT/'build') if a.check else None
 out=pathlib.Path(tmp.name) if tmp else target;out.mkdir(exist_ok=True)
 src=ROOT/'docs/flasher'
 for name in ('builder.js','flasher.js','app.js','style.css'):(out/name).write_bytes((src/name).read_bytes().rstrip(b'\r\n')+b'\n')
 data=json.JSONDecoder().raw_decode((src/'tweaks.js').read_text(encoding='utf-8').split('window.MC_TWEAKS =',1)[1].lstrip())[0]
 t=json.loads((ROOT/'build/midi-machine/core.json').read_text());t['description']=['Prototype MIDI live uniquement. Les CC ne sont pas raccordes.']
 payload=build.build_payload([t],g7.cycles_main(str(ROOT/'firmware/model-cycles_OS1.13.syx')),None)[0]
 payload_hash=hashlib.sha256(payload).hexdigest()
 feature=dict(id=t['id'],label='MIDI Out machine — live prototype',cat='sound',status='experimental',variants=[dict(id=t['id'])],excludes=[])
 (out/'tweaks.js').write_text('window.MC_TWEAKS='+json.dumps(dict(device=data['device'],features=[feature],tweaks=[t]),separators=(',',':'))+';\n',encoding='utf-8')
 script="""// Prototype isole : aucune combinaison ou banque B n'est ajoutee.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,t=window.MC_TWEAKS.tweaks[0];
const hash=x=>b.hex(b.sha256(x));a.REF_MODS[t.id]={w:hash(b.writesBytes(t)),p:'PAYLOAD_HASH'};
a.registerFeatureTexts(t.id,{en:{label:'MIDI Out machine — live prototype',short:'Six stock machines plus a silent MIDI Out machine. Live-note test only.',desc:'Choose MIDI Out in MACHINES on any track. Set that track MIDI channel and enable MIDI output ports in the normal settings. Play its pad or keyboard. The normal A-side grid remains available. This first isolated prototype has no B-side bank and no other mods. CC knobs are placeholders and do not transmit. CC editing, locks, saving, full sequencer/arp behavior and Stop cleanup are unfinished. Release held notes before changing machines or projects. Hardware verification pending. CPU/CUT diagnostics are unavailable in this stock-only profile because it has no SY load counters.'},fr:{label:'Machine MIDI Out — prototype live',short:'Six machines stock et une machine MIDI silencieuse. Test des notes live seulement.',desc:'Choisir MIDI Out dans MACHINES sur une piste. Regler son canal et activer les ports MIDI dans les reglages habituels. Jouer son pad ou clavier. La grille A reste disponible. Prototype isole sans banque B ni autres mods. Les potards CC ne transmettent pas encore. Edition CC, locks, sauvegarde, sequence/arpege complets et nettoyage STOP non termines. Relacher les notes avant de changer de machine ou projet. Verification materielle attendue. Diagnostic CPU/CUT indisponible dans ce profil stock sans compteurs SY.'}});
})();
"""
 (out/'midi-machine.js').write_text(script.replace('PAYLOAD_HASH',payload_hash),encoding='utf-8')
 html=(src/'index.html').read_text(encoding='utf-8')
 # Conserver uniquement le moteur de flash habituel et les assets communs.
 html=re.sub(r'<script src="[^\"]+"></script>','',html)
 html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=html.replace('<title>A.V.\'s Supermodel Edition.</title>','<title>MIDI Out machine — live prototype</title>')
 notice='<p role="note"><strong data-l="en">MIDI Out machine: early live-note prototype.</strong><strong data-l="fr">Machine MIDI Out : premier prototype live.</strong> <span data-l="en">Stock machines + MIDI Out only. CC controls, saving and full sequence behavior are unfinished. Select the single test option below. CPU/CUT unavailable without SY counters. Main flasher unchanged.</span><span data-l="fr">Machines stock + MIDI Out seulement. CC, sauvegarde et sequence complete non termines. Cocher la seule option de test ci-dessous. CPU/CUT indisponible sans compteurs SY. Flasheur principal inchange.</span></p>'
 html=html.replace('<main class="wrap fl">','<main class="wrap fl">'+notice)
 scripts=['../assets/site.js','builder.js','tweaks.js','flasher.js','app.js','midi-machine.js']
 html=html.replace('</body>',''.join(f'<script src="{f}?v={STAMP}"></script>' for f in scripts)+'</body>')
 (out/'index.html').write_text(html,encoding='utf-8')
 (out/'BUILD.json').write_text(json.dumps(dict(stamp=STAMP,scope='test-only',profile='six stock machines + MIDI live',diagnostics='unavailable: no SY counters',hardware_verified=False,main_unchanged=True),indent=2)+'\n')
 if a.check:
  for f in out.iterdir():assert f.read_bytes().replace(b'\r\n',b'\n')==(target/f.name).read_bytes().replace(b'\r\n',b'\n'),f.name
 print('PASS page isolee MIDI live ; principal inchange')
if __name__=='__main__':main()
