"""Note129 : copie du principal fixe avec accord MACRO inclus et diagnostic."""
import argparse,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
STAMP='2026-10-18-macro-fine-main-test-1'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 out=ROOT/'docs/flasher-macro-fine-main-test';out.mkdir(exist_ok=True)
 files={f.name:f.read_bytes() for f in (ROOT/'docs/flasher').iterdir() if f.is_file()}
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):
  files[name]=(ROOT/'docs/flasher-machine-combinations-test'/name).read_bytes()
 files['macro-fine-data.js']=(ROOT/'docs/flasher-macro-fine-test/macro-fine-data.js').read_bytes()
 fine=(ROOT/'tools/web/macro-fine.js').read_text(encoding='utf-8')
 fine=fine.replace('Promise.all([window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady])','Promise.all([window.MCMidiMachineAllReady,window.MCBeatDiagnosticReady])')
 fine=fine[:fine.index(" const e=document.getElementById('feat-audio-load-diagnostic');")]+"});})();\n"
 files['macro-fine-main.js']=fine.encode()
 preset=files['midi-machine-main.js'].decode().replace('pageReady,window.MCLfoDestinationsReady','pageReady,window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady')
 preset=preset.replace("'startup-animation','boot-anim','audio-load-diagnostic'","'startup-animation','boot-anim'").replace("select('audio-load-diagnostic',false)","select('audio-load-diagnostic',true)")
 files['midi-machine-main.js']=preset.encode()
 html=files['index.html'].decode();html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=re.sub(r'<title>.*?</title>','<title>Supermodel — MACRO fine-tune main test</title>',html,count=1)
 html=html.replace('<script src="midi-machine-main.js?',f'<script src="beat-diagnostic-data.js?v={STAMP}"></script><script src="beat-diagnostic.js?v={STAMP}"></script><script src="midi-machine-main.js?')
 html=html.replace('</body>',f'<script src="macro-fine-data.js?v={STAMP}"></script><script src="macro-fine-main.js?v={STAMP}"></script></body>')
 notice='<p role="note"><strong data-l="en">Current main + MACRO fine tune, included by default.</strong><strong data-l="fr">Principal actuel + accordage fin MACRO inclus.</strong> <span data-l="en">SETTINGS + PITCH fine-tunes MACRO; FUNC + PITCH retains Lo-Fi. CPU/CUT diagnostics included for this test. Only six-track USB audio is optional. Main and 909 are unchanged.</span><span data-l="fr">SETTINGS + PITCH accorde MACRO ; FUNC + PITCH conserve le Lo-Fi. Diagnostic CPU/CUT inclus dans ce test. Seul choix : audio USB six pistes. Principal et909 inchanges.</span></p>'
 html=html.replace('<main class="wrap fl">','<main class="wrap fl">'+notice)
 html=html.replace('<ul><li><span data-l="en">Machines:', '<ul><li><span data-l="en">MACRO fine tune: SETTINGS + PITCH, saved with the sound. FUNC + PITCH still controls Lo-Fi.</span><span data-l="fr">Accord MACRO : SETTINGS + PITCH, sauvegarde avec le son. FUNC + PITCH conserve le Lo-Fi.</span></li><li><span data-l="en">Machines:')
 files['index.html']=html.encode()
 files['midi-machine-release.js']=('window.MC_RELEASES='+json.dumps([dict(version='MACRO-fine-main-test.1',date='2026-10-18',changes=[dict(en='Current fixed main with MACRO fine tune included by default, USB audio on/off and test-only CPU/CUT diagnostics. SETTINGS + PITCH fine-tunes; FUNC + PITCH stays Lo-Fi. Hardware verification pending.',fr='Principal fixe actuel avec accord MACRO inclus, choix audio USB et diagnostic CPU/CUT de test. SETTINGS + PITCH accorde ; FUNC + PITCH conserve le Lo-Fi. Verification materielle attendue.')])])+';\n').encode()
 files['BUILD.json']=(json.dumps(dict(stamp=STAMP,scope='test-only',base='2026-10-18-fixed-main-194-init',diagnostics=True,hardware_verified=False,fine_default=True,usb_audio_optional=True,midi_machine=True,midi_bank=False),indent=2)+'\n').encode()
 for name,raw in files.items():
  istext=pathlib.Path(name).suffix in ('.js','.html','.css','.json','.md','.txt')
  if istext:raw=raw.replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
  if a.check:assert ((out/name).read_bytes().replace(b'\r\n',b'\n') if istext else (out/name).read_bytes())==raw,name
  else:(out/name).write_bytes(raw)
 print('PASS copie principale MACRO fine incluse, USB seul choix, diagnostic test, principal/909 inchanges')
if __name__=='__main__':main()
