"""Note126 : preset de test Select All avec machine MIDI, sans banque B."""
import argparse,json,pathlib,re
import gen_midi_machine_core as core
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-18-midi-machine-all-test-2'
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 out=ROOT/'docs/flasher-midi-machine-all-test';out.mkdir(exist_ok=True)
 files={f.name:f.read_bytes() for f in (ROOT/'docs/flasher').iterdir() if f.is_file()}
 entry=json.loads((ROOT/'build/midi-machine/catalogue-1023-1-controls.json').read_text())
 hooks=list(core.CONTROL_HOOKS)+list(core.LIVE_HOOKS)
 entry['engine']['writes']=[w for w in entry['engine']['writes'] if w['off']+0x40000400 not in {site for site,_,_ in hooks}]
 data=dict(entry=entry,hooks=hooks,stamp=STAMP)
 files['midi-machine-all-data.js']=('window.MCMidiMachineAll='+json.dumps(data,separators=(',',':'))+';\n').encode()
 files['midi-machine-all.js']=(ROOT/'tools/web/midi-machine-all.js').read_bytes()
 for name in ('beat-diagnostic-data.js','beat-diagnostic.js'):files[name]=(ROOT/'docs/flasher-machine-combinations-test'/name).read_bytes()
 html=files['index.html'].decode('utf-8');html=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,html);html=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",html)
 html=html.replace('<script src="machine-combinations.js?',f'<script src="midi-machine-all-data.js?v={STAMP}"></script><script src="midi-machine-all-catalogue.js?v={STAMP}"></script><script src="machine-combinations.js?')
 html=html.replace('</body>',''.join(f'<script src="{name}?v={STAMP}"></script>' for name in ('beat-diagnostic-data.js','beat-diagnostic.js','midi-machine-all.js'))+'</body>')
 notice='<p role="note"><strong data-l="en">MIDI Out machine — Select All test preset.</strong><strong data-l="fr">Machine MIDI Out — preset de test Select All.</strong> <span data-l="en">All current main features, a silent MIDI Out machine, and CPU/CUT diagnostics. No MIDI B-side bank. This test uses a fixed full-feature preset. Hardware verification pending.</span><span data-l="fr">Fonctions actuelles du principal, machine MIDI Out silencieuse et diagnostic CPU/CUT. Sans banque MIDI B. Preset complet fixe pour ce test. Verification materielle attendue.</span></p>'
 html=html.replace('<main class="wrap fl">','<main class="wrap fl">'+notice);files['index.html']=html.encode()
 html=html.replace(notice,notice+'<p><a href="midi-machine-guide.html"><strong data-l="en">MIDI Out machine controls and test guide</strong><strong data-l="fr">Commandes et guide de test MIDI Out</strong></a></p>')
 html=html.replace('../assets/release.js?', 'midi-machine-release.js?');html=re.sub(r'<title>.*?</title>','<title>MIDI Out machine — Select All test</title>',html,count=1);files['index.html']=html.encode()
 files['midi-machine-release.js']=('window.MC_RELEASES='+json.dumps([dict(version='MIDI-machine-all-test.2',date='2026-10-18',changes=[dict(en='Select All preset with a silent A-side MIDI Out machine, assignable CCs/locks, two MIDI LFOs, saved channel/output routing and CPU/CUT diagnostics. No B-side bank. Experimental; hardware verification pending.',fr='Preset complet avec machine MIDI Out silencieuse sur A, CC/locks assignables, deux LFO MIDI, canal/port sauvegardes et diagnostic CPU/CUT. Sans banque B. Experimental ; verification materielle attendue.')])])+';\n').encode()
 files['midi-machine-guide.html']=(ROOT/'tools/web/midi-machine-guide.html').read_bytes()
 files['midi-machine-all-catalogue.js']=b'''// Catalogue du preset MIDI seulement ; les pages publiees restent inchangees.
(()=>{const d=window.MCMachineCombinationData,b=window.MCBuilder,x=window.MCMidiMachineAll.entry,old=d.wizard[1023];x.engine.id=old.engine.id;x.engine_sha256=b.hex(b.sha256(Uint8Array.from(unescape(encodeURIComponent(JSON.stringify(x.engine))),c=>c.charCodeAt(0))));d.wizard[1023]=x;})();
'''
 # Les bornes passent de MOVEQ a un detour 32bits pour131descripteurs.
 text=files['lfo-destinations.js'].decode()
 text=text.replace('if(!/^72[0-7][0-9a-f]202f0004$/.test(mapOld))','const wide=r.tweaks.find(t=>t.wide_descriptor_bounds)?.wide_descriptor_bounds;const descriptorCount=wide?.count||patched[0x4005a4e9-BASE];if(!/^72[0-7][0-9a-f]202f0004$/.test(mapOld)&&!(wide&&mapOld.startsWith("4ef9")))')
 text=text.replace('view.setUint32(d.symbols.ld_api+12,patched[0x4005a4e9-BASE],false)','view.setUint32(d.symbols.ld_api+12,descriptorCount,false)')
 text=text.replace("if(!/^72[0-7][0-9a-f]202f0008$/.test(old))",'if(!/^72[0-7][0-9a-f]202f0008$/.test(old)&&!(wide&&old.startsWith("4ef9")&&wide.sites.includes("0x"+at.toString(16))))')
 text=text.replace('count=patched[0x4005a4e9-BASE],start=table+56*(count-5)','count=descriptorCount-5,start=table+56*(count-5)')
 files['lfo-destinations.js']=text.encode()
 files['BUILD.json']=(json.dumps(dict(stamp=STAMP,scope='test-only',profile='Select All except MIDI B-side; silent MIDI Out machine',diagnostics=True,hardware_verified=False,released_flashers_unchanged=True),indent=2)+'\n').encode()
 for name,raw in files.items():
  textfile=pathlib.Path(name).suffix in ('.js','.html','.css','.json','.md','.txt')
  if textfile:raw=raw.replace(b'\r\n',b'\n').rstrip(b'\n')+b'\n'
  if a.check:assert ((out/name).read_bytes().replace(b'\r\n',b'\n') if textfile else (out/name).read_bytes())==raw,name
  else:(out/name).write_bytes(raw)
 print('PASS page preset MIDI generee ; principale et909 conservees')
if __name__=='__main__':main()
