"""Copie de test séparée : filtre à historique continu, lampe corrigée conservée."""
import pathlib,shutil,json,hashlib
P=pathlib.Path('work/wizard-filter-continuous');out=P/'page';shutil.copytree('work/genie-attack-test/page',out,dirs_exist_ok=True);data=json.load(open(P/'data.json'))
(out/'continuous-filter.js').write_text('window.MCContinuousFilter='+json.dumps(data,separators=(',',':'))+';\n'+'''(()=>{
 const af=window.MC_TWEAKS.features.find(f=>f.id==='synth-attack');if(af){af.status='tested';af.hardwareTestedByOwner=true;}
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,c=window.MCContinuousFilter,prev=window.MCMainClearResolve,hash=t=>b.hex(b.sha256(b.writesBytes(t)));
 for(const id of ['sample-wizard','lfo-secondary']){const q=tw.features.find(f=>f.id===id);if(q)q.excludes=(q.excludes||[]).filter(x=>x!=='track-filter');}
 tw.features.push({id:'track-filter',status:'experimental',cat:'sound',requires:'synth-attack',variants:[{id:'track-filter'}]});tw.tweaks.push({id:'track-filter',order:63,writes:[],requires:['sample-wizard']});
 window.MCMainClearResolve=out=>{
  out=prev(out);if(!a.isSelected('track-filter'))return out;
  const result=out.filter(t=>t.id!=='track-filter').map(t=>{
   if(!['sample-wizard','supermodel-genie-attack'].includes(t.id))return t;
   const ref=a.REF_MODS[t.id];if(hash(t)!==ref.w)throw Error('Continuous filter: trusted reference mismatch');const n=JSON.parse(JSON.stringify(t));
   if(n.id==='sample-wizard'){
    if(b.hex(b.sha256(b.buildPayload(n.append,null,null)))!==ref.p)throw Error('Continuous filter: trusted payload mismatch');const p=n.append.parts[0];
    for(const ch of c.payload){const i=ch.off*2;if(p.hex.slice(i,i+ch.old.length)!==ch.old)throw Error('Continuous filter payload guard');p.hex=p.hex.slice(0,i)+ch.new+p.hex.slice(i+ch.old.length);}
   }else for(const ch of c.changes){const off=ch.at-0x40000400,w=n.writes.find(w=>w.off<=off&&off+ch.old.length/2<=w.off+w.new.length/2);if(!w)throw Error('Continuous filter hook missing');const i=(off-w.off)*2;if(w.new.slice(i,i+ch.old.length)!==ch.old)throw Error('Continuous filter hook guard');w.new=w.new.slice(0,i)+ch.new+w.new.slice(i+ch.old.length);}
   a.REF_MODS[n.id]={w:hash(n),...(n.append?{p:b.hex(b.sha256(b.buildPayload(n.append,null,null)))}:{})};return n;
  });a.REF_MODS[c.recipe.id]={w:hash(c.recipe)};return result.concat(c.recipe).sort((x,y)=>x.order-y.order);
 };a.applyLang(document.documentElement.lang||'en');
})();''')
p=out/'app.js';s=p.read_text();needle="GUIDE_OF['sample-wizard']='sample-wizard';";s=s.replace(needle,needle+'''
FEAT.en['track-filter']={label:'Per-track filter — continuous',short:'Low-pass cutoff/resonance with continuous filter history.',desc:'Hold MACHINES and turn SWEEP for cutoff or CONTOUR for resonance. Requires Synth Attack and Wizard shared support in this test. The ladder no longer clears its history on the voice-trigger flag, removing a reproduced block-edge discontinuity. Wizard keeps its own filter. Cutoff fully open and zero resonance bypasses the ladder. Hardware verification of the click correction is pending.',shortcuts:['MACHINES + SWEEP: cutoff.','MACHINES + CONTOUR: resonance.','Hold a TRIG for parameter locks; CC74 cutoff / CC71 resonance.']};
FEAT.fr['track-filter']={label:'Filtre par piste — continu',short:'Passe-bas coupure/résonance, historique du filtre continu.',desc:'MACHINES + SWEEP : coupure ; MACHINES + CONTOUR : résonance. Requiert Attack synth et support Wizard dans ce test. Le ladder ne remet plus son historique à zéro au flag de trig : une discontinuité de blocs reproduite est supprimée. Wizard conserve son filtre. Coupure maximale et résonance nulle : bypass. Correction à vérifier sur machine.',shortcuts:['MACHINES + SWEEP : coupure.','MACHINES + CONTOUR : résonance.','Tenir un TRIG pour un lock ; CC74 coupure / CC71 résonance.']};
''');s=s.replace('if (need && !isOn(need.id)) turnOn(need);', '''if (need && !isOn(need.id)) { const chain=[]; for(let h=need;h;h=h.requires&&featById(h.requires)){if(chain.includes(h))throw new Error("Cyclic feature dependency");chain.unshift(h);}for(const h of chain)if(!isOn(h.id))turnOn(h); }''');p.write_text(s)
p=out/'index.html';s=p.read_text().replace('2026-10-15-genie-lamp-allocation-fix','2026-10-15-filter-continuous-history').replace('2026-10-15-tested-status','2026-10-15-filter-continuous-history');a=s.index('<p class="alert">');z=s.index('</p>',a)+4;s=s[:a]+'''<p class="alert"><span data-l="en"><strong>Continuous filter history — hardware test.</strong> Includes the Genie allocation correction, restored lamp/mute lights and Synth Attack. The shared filter keeps its history across note triggers instead of restarting each audio block. Select All includes the filter. Main and 909 remain unchanged.</span><span data-l="fr"><strong>Historique du filtre continu — test matériel.</strong> Inclut la correction d’allocation Genie, lampe/mutes et Attack synth. Le filtre partagé conserve son historique entre les trigs, sans redémarrage par bloc audio. Tout sélectionner inclut le filtre. Main et 909 inchangés.</span></p>'''+s[z:];s=s.replace('</body>','<script src="continuous-filter.js?v=2026-10-15-filter-continuous-history"></script></body>');p.write_text(s)
source=out/'source/continuous-filter';source.mkdir(parents=True,exist_ok=True)
for name in ['generate.py','page.py','probe.py','filter.s']:shutil.copy(P/name,source/name)
files=[]
for e in json.load(open('work/genie-attack-test/publish-files.json')):
 p=out/pathlib.Path(e['local']).relative_to('work/genie-attack-test/page');b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-filter-continuous-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
for p in [out/'continuous-filter.js',*source.iterdir()]:
 b=p.read_bytes();files.append(dict(local=str(p),path='docs/flasher-filter-continuous-test/'+str(p.relative_to(out)),size=len(b),sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
(P/'publish-files.json').write_text(json.dumps(files));print('Prepared',len(files),'separate filter test files')
