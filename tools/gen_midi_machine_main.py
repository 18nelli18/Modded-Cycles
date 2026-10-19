"""Note126 : principal fixe, seul choix USB six pistes, sans diagnostic."""
import argparse,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-pad-mode-main-197'
FEATURES=[
 ('Machines: six stock engines, Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, TINY, ChpHzrd / Retrosyn and MIDI Out.', 'Machines : six moteurs stock, Sample Wizard, SD Vintage, Clap Vintage, SY Toy, SY Bits, Swarm LITE, MACRO, ACID, WAVE, TINY, ChpHzrd / Retrosyn et MIDI Out.'),
 ('MIDI Out: silent A-side tracks with notes, 12 assignable CCs, locks, channel/port routing and two MIDI LFOs. No MIDI B-side bank.', 'MIDI Out : pistes A silencieuses avec notes,12CC assignables, locks, canal/port et deux LFO MIDI. Sans banque B.'),
 ('Track Setup follows track selection while open, switching between MIDI Out settings and stock audio settings.', 'Track Setup suit la selection de piste, entre reglages MIDI Out et menu audio stock.'),
 ('Sound shaping: synth attack, per-track filter and envelope, filter/resonance/attack LFO destinations and quick assignment.', 'Sculpture sonore : attaque, filtre et enveloppe par piste, destinations LFO filtre/resonance/attaque et assignation rapide.'),
 ('Second audio LFO; arpeggiator with Octave 0 for held notes only; ChordKeys for in-scale chords.', 'Second LFO audio ; arpege avec octave0 pour les notes tenues seules ; ChordKeys pour les accords en gamme.'),
 ('Sequence Genie, SCRAMBLE, slide trigs, Control All configuration, audio beat repeat and latching mutes.', 'Sequence Genie, SCRAMBLE, slides, configuration Control All, beat repeat audio et mutes verrouillables.'),
 ('Pad selection: SETTINGS + TRACK opens Pad Setup. Press DATA, then choose Silent or Stock; BACK exits. Silent is restored after reboot. Trig preview, easier trig removal and dimmed trigless steps.', 'Selection des pads : SETTINGS + TRACK ouvre Pad Setup. Presser DATA puis choisir Silent ou Stock ; BACK ferme. Retour Silent apres redemarrage. Preecoute des trigs, suppression simplifiee et pas trigless attenues.'),
 ('Sample Wizard preview and slicing, scrolling long names and a multiline browser.', 'Sample Wizard : preecoute et decoupe, noms longs defilants et navigateur multiligne.'),
 ('MACRO fine tune: SETTINGS + PITCH; plain PITCH keeps stock behavior and FUNC + PITCH remains Lo-Fi.', 'Accord fin MACRO : SETTINGS + PITCH ; PITCH seul conserve le comportement stock, FUNC + PITCH reste Lo-Fi.'),
 ('Permanent quick save, updated MACRO Lo-Fi/rendering and audio/filter fixes.', 'Sauvegarde rapide permanente, MACRO Lo-Fi/rendu actualises et corrections audio/filtre.'),
 ('Tempo up to 546 BPM, scale lock, numeric volume/pan and live MIDI OUT/THRU toggle.', 'Tempo jusqu’a546BPM, scale lock, volume/pan numeriques et bascule MIDI OUT/THRU live.'),
 ('Supermodel startup. Optional six-track USB audio; standard USB audio when unchecked.', 'Demarrage Supermodel. Audio USB six pistes en option ; audio USB standard sinon.')]
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 source=ROOT/'docs/flasher-midi-machine-all-test';out=ROOT/'docs/flasher'
 names=['index.html','midi-machine-all-data.js','midi-machine-all-catalogue.js','midi-machine-guide.html','lfo-destinations.js']
 files={n:(source/n).read_text(encoding='utf-8') for n in names}
 files['midi-machine-all-data.js']=(ROOT/'docs/flasher-macro-fine-main-test/midi-machine-all-data.js').read_text(encoding='utf-8')
 html=files['index.html'];html=re.sub(r'<p role="note"><strong data-l="en">MIDI Out machine.*?</p>','',html)
 html=re.sub(r'<script src="beat-diagnostic[^\"]+"></script>','',html)
 html=html.replace('midi-machine-all.js?', 'midi-machine-main.js?')
 html=re.sub(r'<title>.*?</title>','<title>Supermodel — Model:Cycles firmware</title>',html,count=1)
 html=html.replace('MIDI Out machine controls and test guide','MIDI Out machine controls').replace('Commandes et guide de test MIDI Out','Commandes MIDI Out')
 html=html.replace('Choose mods','Features').replace('Choisir les mods','Fonctions')
 html=html.replace('<head>','<head><style>.super-search,.super-toolbar,.super-columns,#select-all-note,.mods-lede,#mach-q,.seg.sub,#tab-samples{display:none!important}.fixed-features{max-width:850px}.fixed-features li{margin:.8em 0}.fixed-usb{display:flex;gap:12px;align-items:center;padding:18px;border:2px solid currentColor;margin:20px 0}.fixed-usb input{width:22px;height:22px}</style>',1)
 listing='<div class="fixed-features"><h3><span data-l="en">Included features</span><span data-l="fr">Fonctions incluses</span></h3><p><span data-l="en">One complete firmware. All features below are included; only six-track USB audio is optional.</span><span data-l="fr">Un firmware complet. Toutes les fonctions ci-dessous sont incluses ; seul l’audio USB six pistes est optionnel.</span></p><label class="fixed-usb"><input type="checkbox" id="fixed-six-usb" checked><span data-l="en">Enable six-track USB audio</span><span data-l="fr">Activer l’audio USB six pistes</span></label><ul>'
 listing+=''.join('<li><span data-l="en">'+en+'</span><span data-l="fr">'+fr+'</span></li>' for en,fr in FEATURES)
 listing+='</ul><a href="#step-file"><span data-l="en">Continue: load OS files</span><span data-l="fr">Continuer : charger les OS</span></a></div>'
 html=html.replace('<div class="super-toolbar">',listing+'<div class="super-toolbar">',1)
 html=html.replace('<h2 id="h1s" data-i18n="s1">What do you want to install?</h2>', '<h2 id="h1s"><span data-l="en">Your firmware</span><span data-l="fr">Votre firmware</span></h2>')
 html=html.replace('</body>',f'<script src="macro-fine-data.js?v={STAMP}"></script><script src="macro-fine-release.js?v={STAMP}"></script><script src="pad-mode-data.js?v={STAMP}"></script><script src="pad-mode.js?v={STAMP}"></script></body>')
 files['index.html']=html
 files['pad-mode-data.js']=(out/'pad-mode-data.js').read_text(encoding='utf-8')
 files['pad-mode.js']=(ROOT/'tools/web/pad-mode.js').read_text(encoding='utf-8')
 files['macro-fine-data.js']=(ROOT/'docs/flasher-macro-fine-main-test/macro-fine-data.js').read_text(encoding='utf-8')
 fine=(ROOT/'docs/flasher-macro-fine-main-test/macro-fine-main.js').read_text(encoding='utf-8').replace('window.MCMidiMachineAllReady,window.MCBeatDiagnosticReady','window.MCMidiMachineAllReady').replace("id:'macro-fine-test',status:'experimental'","id:'macro-fine',status:'tested'").replace('Test adds fine pitch','Fine pitch').replace('Test : SETTINGS','SETTINGS').replace(' CPU/CUT diagnostic available. Hardware verification pending.','').replace(' Diagnostic CPU/CUT disponible. Verification materielle attendue.','')
 assert 'MCBeatDiagnosticReady' not in fine
 files['macro-fine-release.js']=fine
 files['midi-machine-main.js']=(ROOT/'tools/web/midi-machine-main.js').read_text(encoding='utf-8')
 guide=files['midi-machine-guide.html'].replace('Select All test','firmware').replace('fixed test preset','firmware').replace('CPU/CUT diagnostics and ','').replace('Hardware verification is pending.','').replace('Preset fixe avec les fonctions actuelles du principal, diagnostic CPU/CUT et','Firmware complet avec les fonctions du principal et').replace('Verification materielle attendue.','')
 guide=re.sub(r'<li><b>(Load diagnostic|Diagnostic).*?</li>','',guide);files['midi-machine-guide.html']=guide
 files['BUILD.json']=json.dumps(dict(stamp=STAMP,scope='main',profile='All features, MIDI machine, no B-side; USB six-track on/off',diagnostics=False,startup='Supermodel',track_setup_follows_selection=True,macro_fine=True,hardware_verified=True,pad_selection_menu=True,pad_mode_persistent=False,sample_lock_filter=False),indent=2)
 files['midi-machine-release.js']='window.MC_RELEASES='+json.dumps([dict(version='1.97',date='2026-10-18',changes=[dict(en='Pad Setup is now included: SETTINGS + TRACK, press DATA and choose Silent or Stock; BACK exits. Choice resets to Silent after reboot. The sample-lock filter experiment is excluded; main audio/filter behavior is preserved. No diagnostics.',fr='Pad Setup inclus : SETTINGS + TRACK, presser DATA et choisir Silent ou Stock ; BACK ferme. Retour Silent apres redemarrage. Le test filtre sample locks est exclu ; audio/filtre principal conserves. Aucun diagnostic.')])])+';'
 for name,text in files.items():
  text=re.sub(r'2026-10-18-(?:midi-machine-all-test-\d+|macro-fine-main-test-\d+)',STAMP,text).replace('\r\n','\n').rstrip()+'\n'
  if a.check:assert (out/name).read_text(encoding='utf-8')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 assert 'beat-diagnostic' not in files['index.html']
 print('PASS principal fixe genere, deux variantes USB, Supermodel, aucun diagnostic')
if __name__=='__main__':main()
