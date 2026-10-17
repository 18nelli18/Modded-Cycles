"""Note114 : test entree B en lecture, branchements natifs gardes, diagnostics conserves."""
import argparse,json,pathlib,re,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];STAMP='2026-10-17-midi-entry-test-4'
JS='''// Note114 : un contexte cree pendant Play peut demarrer au tick audio suivant.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCMidiEntryReady=window.MCQuickSaveLatchReady.then(()=>{const previous=window.MCMidiBankCompose;window.MCMidiBankCompose=(...args)=>{const prior=previous(...args),old=prior.tweaks.find(t=>t.id==='midi-out-bank');if(!old)return prior;const r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},bank=r.tweaks.find(t=>t.id===old.id),at=n(bank.symbols.ml_native_tick),p=bank.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+152<=n(p.dest)+p.hex.length/2);if(!p)throw Error('MIDI entry: native tick missing');const i=2*(at-n(p.dest)),body=p.hex.slice(i,i+304);if(body.slice(84,100)!=='4ab9'+h(n(bank.symbols.ml_start_serial))+'6700'||body.slice(104,120)!=='b5f9'+h(n(bank.symbols.ml_start_context))+'6600'||body.slice(260,280)!=='2f032f024eb9'+h(n(bank.symbols.ml_audio_tick)))throw Error('MIDI entry: transport layout guard');for(const [off,old,nw] of [[0x32,'005c','0050'],[0x3c,'0052','0046']]){const pos=i+2*off;if(p.hex.slice(pos,pos+4)!==old)throw Error('MIDI entry: transport branch guard');p.hex=p.hex.slice(0,pos)+nw+p.hex.slice(pos+4);}delete bank.append.compressed_hex;delete bank.append.stored;
const c=b.parseContainer(b.unwrap(args[1]).stream),section=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(section.off,section.off+section.size)).data;r.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(b.buildPayload(bank.append,args[2],stock))};const repeat=r.tweaks.find(t=>t.id==='control-all-beat-repeat');if(repeat){const source=n(bank.append.at)+b.buildPayload(bank.append,args[2],stock).length;repeat.append.at='0x'+h(source);const loader=repeat.writes.find(w=>0x40000400+w.off===window.MCBeatRepeat.boot.at);if(!loader)throw Error('MIDI entry: repeat loader missing');const boot=b.fromHex(loader.new);new DataView(boot.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,source,false);loader.new=b.hex(boot);r.refMods[repeat.id]={w:hash(b.writesBytes(repeat)),p:hash(b.buildPayload(repeat.append,args[2],stock))};}return r;};});})();
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();src=ROOT/'docs/flasher-quick-save-test';out=ROOT/'docs/flasher-midi-entry-test'
 if not a.check and not out.exists():
  out.mkdir(exist_ok=True)
  for f in src.iterdir():
   if f.is_file():shutil.copyfile(f,out/f.name)
 s=((out/'index.html') if (out/'index.html').exists() else (src/'index.html')).read_text(encoding='utf-8');s=re.sub(r'(?<=\?v=)[\w.-]+',STAMP,s);s=re.sub(r"window.MC_BUILD='[^']+'",f"window.MC_BUILD='{STAMP}'",s)
 intro='<p><strong data-l="en">MIDI first-entry playback test:</strong><strong data-l="fr">Test premiere ouverture MIDI en lecture :</strong> <span data-l="en">Recording cursor test: only the B-side playback head should appear while recording. Open B-side while playback is running. Its RAM sequence should join the native track phase without exiting and reopening. Each B lane retains its own loop length and speed. Existing A-side playback stays running. Saved MIDI still loads only when entering B-side with playback stopped. Includes the confirmed quick-save repair and diagnostics. Keep Control All Beat Repeat selected for this test. Main unchanged.</span><span data-l="fr">Test curseur REC : seul le curseur B doit apparaitre pendant enregistrement. Ouvrir B pendant la lecture : sa sequence RAM rejoint la phase native sans fermer et rouvrir. Chaque voie B conserve longueur et vitesse. La lecture A continue. MIDI sauvegarde toujours charge uniquement en entrant B lecture arretee. Inclut correction sauvegarde confirmee et diagnostics. Garder Control All Beat Repeat selectionne. Principal inchange.</span></p>'
 s=re.sub(r'(<main class="wrap fl">)<p>.*?</p>',lambda m:m.group(1)+intro,s,count=1,flags=re.S).replace('stock quick-save test','MIDI first-entry test')
 if 'src="midi-entry.js?' not in s:s=s.replace('</body>',f'<script src="midi-entry.js?v={STAMP}"></script></body>')
 if 'src="midi-cursor.js?' not in s:s=s.replace('</body>',f'<script src="midi-cursor-data.js?v={STAMP}"></script><script src="midi-cursor.js?v={STAMP}"></script></body>')
 s=re.sub(r'<script src="quick-save-latch(?:-data)?\.js\?[^"]+"></script>', '', s)
 if 'src="quick-save-exit.js?' not in s:s=s.replace('<script src="midi-entry.js?',f'<script src="quick-save-exit-data.js?v={STAMP}"></script><script src="quick-save-exit.js?v={STAMP}"></script><script src="midi-entry.js?')
 release='window.MC_RELEASES='+json.dumps([dict(version='MIDI-entry-test.4',date='2026-10-17',changes=[dict(en='MIDI access now times out after 20 seconds with a retry path instead of waiting indefinitely. Tests suppression of the extra stock recording cursor while B-side is open. Allow the MIDI bank to start when first opened during playback. Saved MIDI loading still requires stopped playback. Diagnostics and confirmed quick-save repair retained; main unchanged.',fr='Acces MIDI : delai de20secondes et nouvelle tentative au lieu d attente infinie. Teste la suppression du curseur REC stock supplementaire pendant B. Permet le demarrage de la Banque MIDI lors de sa premiere ouverture en lecture. Chargement MIDI sauvegarde toujours lecture arretee. Diagnostics et correction sauvegarde confirmee conserves ; principal inchange.')])],ensure_ascii=False)+';\n'
 app=(ROOT/'docs/flasher/app.js').read_text(encoding='utf-8')
 helper="""function midiAccessWithTimeout() {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      const error = new Error('Browser MIDI initialization did not finish. Close other flashers or MIDI apps, retry, or reopen this page in Chrome or Edge.');
      error.name = 'TimeoutError'; reject(error);
    }, 20000);
    try {
      Promise.resolve(navigator.requestMIDIAccess({ sysex: true })).then(
        access => { clearTimeout(timeout); resolve(access); },
        error => { clearTimeout(timeout); reject(error); }
      );
    } catch (error) { clearTimeout(timeout); reject(error); }
  });
}

"""
 assert app.count('async function initMidi(silent) {')==1
 app=app.replace('async function initMidi(silent) {',helper+'async function initMidi(silent) {')
 app=app.replace('await navigator.requestMIDIAccess({ sysex: true });','await midiAccessWithTimeout();')
 app=app.replace('st.midiState = "denied";', 'st.midiState = e && e.name === "TimeoutError" ? "stalled" : "denied";')
 app=app.replace('  if (st.midiState === "denied") rows.push', '  if (st.midiState === "stalled") rows.push(["is-bad", esc(t("midi_stalled"))]);\n  if (st.midiState === "denied") rows.push')
 app=app.replace('    midi_denied: "MIDI access was refused.', '    midi_stalled: "The browser has not finished MIDI permission or device initialization. If you already allowed it, close other flashers and MIDI apps, then click Allow MIDI access to retry. If it still stalls, reopen this page in Chrome or Edge. This page cannot override browser permission or a stalled MIDI driver.",\n    midi_denied: "MIDI access was refused.')
 app=app.replace('    midi_denied: "Accès MIDI refusé.', '    midi_stalled: "Le navigateur n a pas termine l autorisation ou l initialisation MIDI. Si vous avez deja autorise, fermez les autres flasheurs et applications MIDI, puis cliquez Autoriser pour reessayer. Sinon, rouvrez cette page dans Chrome ou Edge. La page ne peut pas forcer une permission ou un pilote MIDI bloque.",\n    midi_denied: "Accès MIDI refusé.')
 app=app.replace('Waiting for your permission: Chrome shows a prompt near the address bar. Click “Allow”. If you blocked it before, click the icon left of the address and allow MIDI.', 'Waiting for browser MIDI permission or device initialization. Allow the browser prompt if shown. If already allowed, the MIDI device service may still be initializing; a retry message appears after 20 seconds.')
 app=app.replace('En attente de votre autorisation : Chrome affiche une demande près de la barre d’adresse. Cliquez sur « Autoriser ». Si vous l’avez bloquée, cliquez sur l’icône à gauche de l’adresse et autorisez le MIDI.', 'Attente de l autorisation ou de l initialisation MIDI du navigateur. Autorisez la demande si affichee. Un message de nouvelle tentative apparait apres 20 secondes.')
 exit_js=(ROOT/'docs/flasher/quick-save-exit.js').read_text(encoding='utf-8');exit_js=exit_js.replace('(()=>{','window.MCQuickSaveLatchReady=window.MCQuickSaveReady.then(()=>{',1).replace('})();','});');exit_data=(ROOT/'docs/flasher/quick-save-exit-data.js').read_text(encoding='utf-8')
 for name,text in {'quick-save-exit.js':exit_js,'quick-save-exit-data.js':exit_data,'index.html':s,'midi-entry.js':JS,'diagnostic-release.js':release,'app.js':app}.items():
  if a.check:assert (out/name).read_text(encoding='utf-8').replace('\r\n','\n')==text,name
  else:(out/name).write_text(text,encoding='utf-8')
 print('PASS test entree MIDI : deux deplacements de branche gardes, principal inchange')
if __name__=='__main__':main()
