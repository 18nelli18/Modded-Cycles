"""Test séparé : préécoute Wizard et ChordKeys relogé, sans changer leurs octets."""
import pathlib, shutil, re, json, hashlib
P=pathlib.Path('work/preview-chord-test'); out=P/'page'
shutil.copytree('work/wizard-filter-continuous/main',out,dirs_exist_ok=True)
stamp='2026-10-15-preview-chordkeys'
script='''// ChordKeys est désormais dans sa charge utile séparée : aucun masque commun avec la préécoute.
(()=>{
 const a=window.MCFlasherApp,tw=window.MC_TWEAKS,c=window.MCWizardCatalogue;
 const p=tw.features.find(f=>f.id==='sample-preview'),k=tw.features.find(f=>f.id==='chord-keys');
 p.excludes=(p.excludes||[]).filter(id=>!['chord-keys','wave-supermodel'].includes(id));
 const wf=tw.features.find(f=>f.id==='wave-supermodel');wf.excludes=(wf.excludes||[]).filter(id=>id!=='sample-preview');
 k.excludes=(k.excludes||[]).filter(id=>id!=='sample-preview');
 c.preview.conflicts=(c.preview.conflicts||[]).filter(id=>id!=='chord-keys-supermodel');
 p.status='experimental';p.hardwareTestedByOwner=false;
 const prev=window.MCMainClearResolve,prior={...a.REF_MODS},b=window.MCBuilder,hash=t=>b.hex(b.sha256(b.writesBytes(t)));
 window.MCMainClearResolve=out=>{
  for(const [id,ref] of Object.entries(prior))a.REF_MODS[id]=ref;
  out=prev(out);if(!a.isSelected('sample-preview')||!a.isSelected('wave-supermodel'))return out;
  const wizard=out.find(t=>t.id==='sample-wizard');if(!wizard)throw Error('Preview: missing Wizard support');
  const route=wizard.writes.find(x=>x.off===0xa6026);if(!route||!route.new.startsWith('4eb9'))throw Error('Preview: WAVE browser guard');
  return out.map(t=>{
   if(t.id!=='wizard-sample-preview')return t;
   if(hash(t)!==a.REF_MODS[t.id].w)throw Error('Preview: trusted reference mismatch');
   const n=JSON.parse(JSON.stringify(t));
   function patch(va,old,bytes){const off=va-0x40000400,w=n.writes.find(x=>x.off<=off&&off+old.length/2<=x.off+x.new.length/2);if(!w)throw Error('Preview: missing hook');const i=(off-w.off)*2;if(w.new.slice(i,i+old.length)!==old)throw Error('Preview: hook bytes changed');w.new=w.new.slice(0,i)+bytes+w.new.slice(i+old.length);}
   patch(0x40185d20,'4eb9400a3052',route.new);
   patch(0x40185a42,'4e56ff98707f4ef940081724','4ef9'+parseInt(wizard.symbols.av_pad_hook,16).toString(16).padStart(8,'0')+'4e714e714e71');
   const browser=n.writes.find(x=>x.off===0xa6026);if(browser.old!=='4eb9400a3052')throw Error('Preview: old browser guard');browser.old=route.new;
   a.REF_MODS[n.id]={w:hash(n)};return n;
  });
 };
 a.applyLang(document.documentElement.lang||'en');
})();
'''
(out/'preview-chord.js').write_text(script)
p=out/'app.js'; s=p.read_text().replace('function statusOf(f) {',"function statusOf(f) { if(f.id==='sample-preview')return 'experimental';")
s=s.replace('Preview samples in the Sample Wizard browser. Requires Sample Wizard; uses browser hooks that cannot be combined with WAVE or ChordKeys in this test.','Preview samples in the Sample Wizard browser while ChordKeys is selected. Requires Sample Wizard; compatible with WAVE and ChordKeys. Select a sample in the browser, then play its track pad or keyboard to audition it.')
s=s.replace('Préécoute dans le navigateur Sample Wizard. Exige Wizard ; ses hooks navigateur ne se combinent pas à WAVE ou ChordKeys dans ce test.','Préécoute dans le navigateur Sample Wizard avec ChordKeys sélectionné. Exige Wizard ; compatible avec WAVE et ChordKeys. Choisir un sample puis jouer le pad ou le clavier de sa piste pour l’écouter.')
s=s.replace("window.MCFlasherApp = {","FEAT.en['sample-preview'].label='Sample Preview'; FEAT.fr['sample-preview'].label='Préécoute des samples';\nwindow.MCFlasherApp = {");p.write_text(s)
p=out/'index.html';s=p.read_text();s=re.sub(r'(?<=[?&])v=[^"\'&<> ]+','v='+stamp,s);s=re.sub(r'window.MC_BUILD\s*=\s*["\'][^"\']+["\']',"window.MC_BUILD='"+stamp+"'",s)
a=s.index('<p class="alert">');z=s.index('</p>',a)+4
s=s[:a]+'''<p class="alert"><span data-l="en"><strong>Sample Preview + ChordKeys + WAVE — hardware test.</strong> The obsolete conflict is removed for the relocated ChordKeys implementation. Choose Sample Preview and ChordKeys; Sample Wizard is enabled automatically. WAVE is compatible as well. Main and the filter test remain unchanged by this preview test.</span><span data-l="fr"><strong>Préécoute + ChordKeys + WAVE — test matériel.</strong> Conflit ancien retiré pour ChordKeys relogé. Choisir Préécoute et ChordKeys ; Wizard s’active automatiquement. WAVE est également compatible. Main et le test filtre restent inchangés par ce test de préécoute.</span></p>'''+s[z:]
s=s.replace('</body>','<script src="preview-chord.js?v='+stamp+'"></script></body>');p.write_text(s)
source=out/'source/preview-chord';source.mkdir(parents=True,exist_ok=True)
for name in ['page.py','probe.js','test-native.py','test-wave-native.py','test-boot.py','test-html.js'] :shutil.copyfile(P/name,source/name)
(out/'TEST-NOTES.md').write_text('''# Sample Preview + ChordKeys\n\nSeparate hardware test based on the current main flasher. Removes the obsolete mutual exclusion for the relocated ChordKeys implementation; the non-WAVE pair keeps its firmware bytes unchanged. With WAVE, guarded browser and pad continuations preserve wavetable selection/loading as well as Wizard preview. WAVE is compatible as well.\n\nSelect Sample Preview and ChordKeys; Wizard is enabled automatically. On a Wizard track open FUNC + MACHINES, highlight a sample and play its pad/keyboard to audition it.\n\nValidated: signed browser builds for the pair, Genie, Attack, all compatible features with and without WAVE, and no extra machines. Native startup preserves ChordKeys, Wizard and stock CHORD tables. Real native browser and note paths include resident/missing samples, failed/busy loads, ordinary presets, non-Wizard tracks and register preservation. Filesystem and sample loader are simulated. The WAVE-native test exercises its real browser and pad routes; filesystem/sample loading are simulated. Physical hardware remains to be checked. Main and the separate filter test remain unchanged.\n''')
files=[]
for p in out.rglob('*'):
 if not p.is_file():continue
 b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-preview-chord-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
(P/'publish-files.json').write_text(json.dumps(files));print(len(files),'fichiers du test séparé')
