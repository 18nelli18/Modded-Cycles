// Note 106 : optimisation exacte partagee et SWARM trois voix facultatif.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCSwarmLite,tw=window.MC_TWEAKS,previous=window.MCMidiBankCompose;
 const saved=new Map(),resolve=window.MCMainClearResolve;window.MCMainClearResolve=input=>{for(const [id,ref] of saved)a.REF_MODS[id]=JSON.parse(JSON.stringify(ref));return resolve(input);};
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,h=x=>'0x'+x.toString(16),hash=x=>b.hex(b.sha256(x));
 for(const [id,label,requires] of [['sy-load-opt','SY processing optimization','control-all-beat-repeat'],['swarm-lite','Lite Syn Swarm — 3 oscillators','syntakt'],['sy-load-meter','Audio load diagnostic','control-all-beat-repeat']]){
  tw.features.push({id,label,cat:'sound',status:'experimental',variants:[{id}],requires,excludes:[]});tw.tweaks.push({id,order:120,writes:[],requires:[],conflicts:[],status:'experimental'});
 }
 a.registerFeatureTexts('sy-load-opt',{en:{label:'Repeat / SY load optimization',short:'Faster repeat for all SY voices; original sound calculations.',desc:'Exact steady-repeat fast path and cheaper history recording for all voice types. Includes a small Swarm helper improvement. Toy/Bits generators remain unchanged; they gain headroom through repeat processing. Original seven-oscillator Swarm is retained unless Lite is separately checked. Hardware verification pending.'},fr:{label:'Optimisation repeat / SY',short:'Repeat allege pour toutes les SY ; calculs sonores conserves.',desc:'Chemin repeat etabli exact et capture allegee pour toutes les voix. Petit gain du helper Swarm inclus. Generateurs Toy/Bits inchanges ; marge gagnee dans le repeat. Swarm sept oscillateurs conserve sauf carte Lite cochee. Verification materielle attendue.'}});
 a.registerFeatureTexts('swarm-lite',{en:{label:'Lite Syn Swarm — 3 oscillators',short:'Optional lighter Swarm. Thinner and potentially quieter sound.',desc:'Experimental three-oscillator SY Swarm instead of seven: fundamental and two detuned oscillators retained. Other Swarm controls remain. Sound changes and may be quieter; gain is not boosted. Affects Swarm only. Untick to retain the original seven oscillators. Hardware verification pending.'},fr:{label:'Syn Swarm leger — 3 oscillateurs',short:'Swarm allege facultatif. Son plus fin et parfois moins fort.',desc:'SY Swarm experimental a trois oscillateurs au lieu de sept : fondamental et deux oscillateurs desaccordes conserves. Autres commandes conservees. Son modifie, parfois plus faible ; gain non augmente. Swarm seulement. Decocher pour les sept oscillateurs originaux. Verification materielle attendue.'}});
 document.addEventListener('change',event=>{
  const el=event.target;
  if(el.id==='feat-swarm-lite'&&el.checked&&a.isSelected('swarm-lite')){
   const box=document.getElementById('eng-swarm');if(box&&!box.checked){box.checked=true;box.dispatchEvent(new Event('change',{bubbles:true}));}
  }else if(el.id==='eng-swarm'&&!el.checked&&a.isSelected('swarm-lite')){
   const box=document.getElementById('feat-swarm-lite');box.checked=false;box.dispatchEvent(new Event('change',{bubbles:true}));
  }
 });
 const repeatFeature=tw.features.find(f=>f.id==='control-all-beat-repeat'),repeatStatus=repeatFeature.status,repeatTested=repeatFeature.hardwareTestedByOwner;
 Object.defineProperty(repeatFeature,'status',{configurable:true,get:()=>a.isSelected('sy-load-opt')||a.isSelected('sy-load-meter')?'experimental':repeatStatus});
 Object.defineProperty(repeatFeature,'hardwareTestedByOwner',{configurable:true,get:()=>a.isSelected('sy-load-opt')||a.isSelected('sy-load-meter')?false:repeatTested});
 const originalBeat=clone(window.MCBeatRepeat);
 a.registerFeatureTexts('sy-load-meter',{en:{label:'Audio load diagnostic',short:'Release TRACK + RETRIG to see average / peak CPU load.',desc:'Experimental diagnostic for builds containing Syntakt engines. Hold TRACK + RETRIG during the problem, then release either modifier: CPU average / peak and CUT count appear briefly. CUT is the number of distinct tracks seen fading or suspended by the load governor during the hold, including already suspended tracks. This is a diagnostic, not a repair. Works with the original SY voices and optional Lite Swarm. Sampling is in audio; popup formatting only in the interface. Hardware verification pending.'},fr:{label:'Diagnostic charge audio',short:'Relacher TRACK + RETRIG : charge CPU moyenne / pic.',desc:'Diagnostic experimental pour builds avec moteurs Syntakt. Maintenir TRACK + RETRIG pendant le probleme puis relacher un modificateur : CPU moyenne / pic et compteur CUT s affichent brievement. CUT compte les pistes distinctes en fondu ou suspendues par le regulateur pendant le combo, y compris deja suspendues. Diagnostic, pas une correction. Voix SY originales ou Swarm leger. Mesure en audio ; texte depuis l interface uniquement. Verification materielle attendue.'}});
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const exact=a.isSelected('sy-load-opt'),lite=a.isSelected('swarm-lite'),meter=a.isSelected('sy-load-meter'),base=input.filter(t=>!['sy-load-opt','swarm-lite','sy-load-meter'].includes(t.id));Object.assign(window.MCBeatRepeat,clone(meter||exact?window.MCSyMeter:originalBeat));if(!exact&&!lite&&!meter)return previous(base,cycles,syntakt);
  const c=b.parseContainer(b.unwrap(cycles).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
  let applied=0,liteApplied=0;
  const changed=base.map(t=>{
   if(!t.append?.parts?.some(p=>p.syntakt))return t;
   const n=clone(t),ap=n.append,packed=b.buildPayload(ap,syntakt,stock),ref=a.REF_MODS[t.id];
   if(!ref||hash(b.writesBytes(t))!==ref.w||hash(packed)!==ref.p)throw Error('SY load: trusted recipe guard');
   const raw=b.buildPayload({...ap,compress:null,pack:null},syntakt,stock);let count=0;
   for(const e of [...(exact?d.exact:[]),...(lite?d.edits:[])]){
    const i=ap.parts.findIndex(p=>p.syntakt&&num(p.syntakt[0])<=e.source&&e.source+e.size<=num(p.syntakt[1]));if(i<0)continue;
    const p=ap.parts[i],lo=num(p.syntakt[0]),hi=num(p.syntakt[1]),dest=num(p.dest),at=dest+e.source-lo,off=at-num(ap.dest);
    if(hash(raw.slice(off,off+e.size))!==e.old_sha256)throw Error('SY load: source SHA guard');
    const parts=[];if(lo<e.source)parts.push({dest:h(dest),syntakt:[h(lo),h(e.source)]});parts.push({dest:h(at),hex:e.hex});if(e.source+e.size<hi)parts.push({dest:h(at+e.size),syntakt:[h(e.source+e.size),h(hi)]});ap.parts.splice(i,1,...parts);count++;if(d.edits.includes(e))liteApplied++;
   }
   if(!count)return t;applied+=count;delete ap.compressed_hex;n.status='experimental';n.hardwareTestedByOwner=false;
   saved.set(n.id,{w:ref.w,p:ref.p});a.REF_MODS[n.id]={w:hash(b.writesBytes(n)),p:hash(b.buildPayload(ap,syntakt,stock))};return n;
  });
  if(lite&&liteApplied!==5)throw Error('Lite Swarm: select SY SWARM in the Syntakt engines / choisir SY SWARM');
  let result=previous(changed,cycles,syntakt);window.MCSyLoadApplied=applied;
  if(meter||exact){
   const gov=base.find(t=>t.gov)?.gov,beat=result.tweaks.find(t=>t.id==='control-all-beat-repeat');
   if(meter&&!gov)throw Error('Audio load diagnostic: select Syntakt engines / choisir les moteurs Syntakt');
   if(beat){
    const n=clone(beat),p=n.append.parts[0],bytes=b.fromHex(p.hex),view=new DataView(bytes.buffer);
    for(const [name,address] of [['br_load_address',meter?gov.gov_load:0],['br_avg_address',meter?gov.gov_avg:0],['br_fading_address',meter?gov.gov_fading:0],['br_stolen_address',meter?gov.gov_stolen:0],['br_fast_enabled',exact?1:0]]){
     const off=num(n.symbols[name])-num(p.dest);if(view.getUint32(off,false)!==0)throw Error('SY meter: initial pointer guard');view.setUint32(off,num(address),false);
    }
    p.hex=b.hex(bytes);n.status='experimental';n.hardwareTestedByOwner=false;
    result={...result,tweaks:result.tweaks.map(t=>t===beat?n:t),refMods:{...result.refMods,[n.id]:{w:hash(b.writesBytes(n)),p:hash(b.buildPayload(n.append,syntakt,stock))}}};
   }
  }
  return {...result,refMods:{...result.refMods},tweaks:result.tweaks.map(t=>applied&&t.append?.parts?.some(p=>p.hex===d.exact[0].hex||p.hex===d.edits.at(-1).hex)?{...t,status:'experimental',hardwareTestedByOwner:false}:t)};
 };
 a.applyLang(document.documentElement.lang||'en');
})();
