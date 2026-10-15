"""Test partagé avec le sampler et toutes les options compatibles."""
import json,pathlib,shutil,hashlib
P=pathlib.Path('work/wizard-filter-integration');out=P/'page';shutil.copytree('work/genie-queue-choice/page',out,dirs_exist_ok=True);data=json.load(open(P/'recipe.json'))
(out/'shared-filter.js').write_text('window.MCSharedWizardFilter='+json.dumps(data,separators=(',',':'))+';\n'+'''(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,c=window.MCSharedWizardFilter,prev=window.MCMainClearResolve,prior=a.REF_MODS['sample-wizard'],priorChord=a.REF_MODS['chord-keys-supermodel'],cache=new Map();
 const f=tw.features.find(f=>f.id==='track-filter');f.requires='sample-wizard';f.with={};f.excludes=(f.excludes||[]).filter(id=>!['sample-wizard','lfo-secondary'].includes(id));f.status='experimental';f.credit={kind:'by',who:'TinyGregAudio; roterodamus; A.V.',repo:'TinyGregAudio/Model-TG'};f.license='LICENSE-Sample-Wizard.txt';
 for(const id of ['sample-wizard','lfo-secondary']){const q=tw.features.find(f=>f.id===id);if(q)q.excludes=(q.excludes||[]).filter(x=>x!=='track-filter');}
 window.MCMainClearResolve=out=>{
  a.REF_MODS['sample-wizard']=prior;a.REF_MODS['chord-keys-supermodel']=priorChord;out=prev(out);if(!a.isSelected('track-filter'))return out;
  const w=out.find(t=>t.id==='sample-wizard');if(!w)throw Error('Shared filter requires Sample Wizard support');
  const ref={w:prior.w,p:prior.p},key=ref.p;let n=cache.get(key);
  if(!n){if(b.hex(b.sha256(b.buildPayload(w.append,null,null)))!==ref.p)throw Error('Shared filter: original payload reference mismatch');
   const ap=JSON.parse(JSON.stringify(w.append)),part=ap.parts[0];for(const ch of c.changes){const i=ch.off*2;if(part.hex.slice(i,i+ch.old.length)!==ch.old)throw Error('Shared filter: codec guard mismatch');part.hex=part.hex.slice(0,i)+ch.new+part.hex.slice(i+ch.old.length);}
   n={append:ap,p:b.hex(b.sha256(b.buildPayload(ap,null,null)))};cache.set(key,n);
  }
  a.REF_MODS['sample-wizard']={w:ref.w,p:n.p};a.REF_MODS[c.recipe.id]=c.ref;
  return out.filter(t=>t.id!=='track-filter').map(t=>{
   if(t===w)return {...t,append:n.append};if(t.id!=='chord-keys-supermodel')return t;
   const ref=a.REF_MODS[t.id];if(b.hex(b.sha256(b.writesBytes(t)))!==ref.w)throw Error('Shared filter: ChordKeys reference mismatch');
   const q={...t,writes:t.writes.filter(x=>![0x5b5c6,0x5b6d2].includes(x.off))};
   a.REF_MODS[t.id]={w:b.hex(b.sha256(b.writesBytes(q))),p:ref.p};return q;
  }).concat(c.recipe).sort((x,y)=>x.order-y.order);
 };
 a.applyLang(document.documentElement.lang||'en');
})();''')
p=out/'app.js';s=p.read_text();needle="GUIDE_OF['sample-wizard']='sample-wizard';";extra='''
FEAT.en['track-filter']={label:'Per-track filter (Wizard)',short:'Shared four-pole low-pass cutoff and resonance for synth/drum tracks.',desc:'Hold MACHINES and turn SWEEP for cutoff or CONTOUR for resonance. Available with Sample Wizard and Second LFO in Select All. Synth/drum tracks use Wizard’s ladder filter; Wizard tracks retain their own filter. Cutoff fully open with resonance zero bypasses processing. Supports native LFO/CC control, parameter locks and sound saves. This shared version replaces the older LP/OFF/HP filter: it has no high-pass or separate filter-envelope controls.',shortcuts:['MACHINES + SWEEP: cutoff (0–127; 127 = fully open).','MACHINES + CONTOUR: resonance (0–127).','Hold a TRIG while adjusting to parameter-lock the filter. CC74: cutoff; CC71: resonance.']};
FEAT.fr['track-filter']={label:'Filtre par piste (Wizard)',short:'Passe-bas ladder quatre pôles : coupure et résonance des pistes synth/drum.',desc:'Tenir MACHINES et tourner SWEEP pour la coupure ou CONTOUR pour la résonance. Compatible Wizard et Second LFO dans Tout sélectionner. Les pistes Wizard conservent leur filtre. Coupure maximale et résonance nulle : bypass. Contrôle LFO/CC, locks et sauvegarde du son natifs. Cette variante remplace LP/OFF/HP ; pas de passe-haut ni enveloppe de filtre séparée.',shortcuts:['MACHINES + SWEEP : coupure (0–127 ; 127 = ouvert).','MACHINES + CONTOUR : résonance (0–127).','Tenir un TRIG pour verrouiller le filtre. CC74 : coupure ; CC71 : résonance.']};
''';s=s.replace(needle,needle+extra);p.write_text(s)
p=out/'guide.html';text=p.read_text().replace('</main>','<section id="track-filter" lang="en"><h2>Shared per-track filter</h2><p>Hold MACHINES and turn SWEEP for low-pass cutoff or CONTOUR for resonance. Select All includes this shared version with Sample Wizard and Second LFO. Wizard keeps its own filter; synth/drum tracks receive the same ladder algorithm. Cutoff 127 and resonance 0 bypass processing. Hold a TRIG to lock a value; CC74 controls cutoff and CC71 resonance. Settings save with the sound. This is a low-pass filter, without the previous high-pass or filter-envelope controls. Experimental, pending hardware verification.</p></section><section lang="fr"><h2>Filtre partagé</h2><p>MACHINES + SWEEP : coupure passe-bas ; MACHINES + CONTOUR : résonance. Compatible Wizard et Second LFO dans Tout sélectionner. Wizard conserve son propre filtre. Coupure 127 et résonance 0 : bypass. Tenir un TRIG pour un lock ; CC74 coupure, CC71 résonance. Réglages sauvegardés avec le son. Pas de passe-haut ni enveloppe séparée. Test matériel en attente.</p></section></main>');p.write_text(text)
p=out/'index.html';s=p.read_text().replace('2026-10-15-genie-queue-page-loop','2026-10-15-wizard-shared-filter');start=s.index('<p class="alert">');end=s.index('</p>',start)+4;s=s[:start]+'''<p class="alert"><span data-l="en"><strong>Shared Wizard filter — experimental hardware test.</strong> Select all now includes Per-track Filter alongside Sample Wizard, Second LFO, Genie and the other compatible options. MACHINES + SWEEP: cutoff; MACHINES + CONTOUR: resonance. Synth/drum tracks gain Wizard’s low-pass filter; Wizard retains its own. Main and previous tests remain unchanged.</span><span data-l="fr"><strong>Filtre Wizard partagé — test matériel expérimental.</strong> Tout sélectionner inclut le filtre avec Wizard, Second LFO, Genie et les options compatibles. MACHINES + SWEEP : coupure ; MACHINES + CONTOUR : résonance. Passe-bas sur les pistes synth/drum ; filtre Wizard conservé. Main et anciens tests inchangés.</span></p>'''+s[end:];s=s.replace('</body>','<script src="shared-filter.js?v=2026-10-15-wizard-shared-filter"></script></body>');p.write_text(s)
source=out/'source/shared-filter';source.mkdir(parents=True,exist_ok=True)
for name in ['shared.s','generate.py','page.py','test-native.py','test-boot.py','test-page.js']:shutil.copy(P/name,source/name)
(source/'README.md').write_text('Experimental shared Wizard four-pole low-pass filter. MACHINES+SWEEP cutoff, MACHINES+CONTOUR resonance. Synth/drum tracks use k24/25; Wizard keeps its own filter. Native LFO2 k28..32 and packed record+88 are preserved. Open cutoff / zero resonance bypasses processing. Includes extended pattern-lock mapping with ChordKeys HARMONY id33 preserved. CPU cost is only paid by the ladder on actively filtered tracks; no new startup payload. Main and previous tests are unchanged. Hardware verification pending.\n')
files=[]
for e in json.load(open('work/genie-queue-choice/publish-files.json')):
 p=out/pathlib.Path(e['local']).relative_to('work/genie-queue-choice/page');buf=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-wizard-filter-test/'+str(p.relative_to(out)),size=len(buf),sha=hashlib.sha1(b'blob '+str(len(buf)).encode()+b'\0'+buf).hexdigest()))
for p in [out/'shared-filter.js',*source.iterdir()]:
 buf=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-wizard-filter-test/'+str(p.relative_to(out)),size=len(buf),sha=hashlib.sha1(b'blob '+str(len(buf)).encode()+b'\0'+buf).hexdigest()))
(P/'publish-files.json').write_text(json.dumps(files));print('Prepared',len(files),'test-only files')
