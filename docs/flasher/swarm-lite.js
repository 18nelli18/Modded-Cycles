// Note 107 : Swarm LITE remplace sept oscillateurs par trois, au build seulement.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCSwarmLite,previous=window.MCMidiBankCompose;
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,h=x=>'0x'+x.toString(16),hash=x=>b.hex(b.sha256(x)),saved=new Map(),resolve=window.MCMainClearResolve;
 window.MCMainClearResolve=input=>{for(const [id,ref] of saved)a.REF_MODS[id]={...ref};return resolve(input);};
 const f=window.MC_TWEAKS.features.find(f=>f.id==='syntakt'),engine=f.engines.find(e=>e.code==='swarm');engine.name='Swarm LITE';engine.label='SY SWARM / 3 osc.';
 a.registerFeatureTexts('eng-swarm',{en:{short:'3-oscillator supersaw; lower load',note:'Swarm LITE replaces the original seven oscillators with three: fundamental plus two detuned saws. Lower processing load, with a leaner and potentially quieter sound; gain is not boosted. PUNCH retains the sub-octave control. AveyCole reports significantly reduced load and clicks on hardware; heavy arrangements can still click.'},fr:{short:'supersaw 3 oscillateurs ; charge reduite',note:'Swarm LITE remplace les sept oscillateurs par trois : fondamental et deux dents de scie desaccordees. Charge reduite, son plus fin et parfois moins fort ; gain non augmente. PUNCH conserve la commande de sous-octave. AveyCole signale une nette reduction de charge et des clicks sur machine ; les arrangements lourds peuvent encore cliquer.'}});
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const c=b.parseContainer(b.unwrap(cycles).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;let edits=0;window.MCSwarmLiteMap=[];
  const changed=input.map(t=>{
   if(!t.append?.parts?.some(p=>p.syntakt&&num(p.syntakt[0])<=d.edits[0].source&&d.edits[0].source<num(p.syntakt[1])))return t;
   const ref=a.REF_MODS[t.id],ap=clone(t.append);
   if(!ref||hash(b.writesBytes(t))!==ref.w||hash(b.buildPayload(ap,syntakt,stock))!==ref.p)throw Error('Swarm LITE: trusted recipe guard');
   const raw=b.buildPayload({...ap,compress:null,pack:null},syntakt,stock);
   for(const e of [...d.exact,...d.edits]){
    const i=ap.parts.findIndex(p=>p.syntakt&&num(p.syntakt[0])<=e.source&&e.source+e.size<=num(p.syntakt[1]));if(i<0)throw Error('Swarm LITE: missing source region');
    const p=ap.parts[i],lo=num(p.syntakt[0]),hi=num(p.syntakt[1]),dest=num(p.dest),at=dest+e.source-lo,off=at-num(ap.dest);
    if(hash(raw.slice(off,off+e.size))!==e.old_sha256)throw Error('Swarm LITE: source SHA guard');
    window.MCSwarmLiteMap.push({source:e.source,dest:at});
    const parts=[];if(lo<e.source)parts.push({dest:h(dest),syntakt:[h(lo),h(e.source)]});parts.push({dest:h(at),hex:e.hex});if(e.source+e.size<hi)parts.push({dest:h(at+e.size),syntakt:[h(e.source+e.size),h(hi)]});ap.parts.splice(i,1,...parts);edits++;
   }
   delete ap.compressed_hex;const n={...t,append:ap};saved.set(n.id,{w:ref.w,p:ref.p});a.REF_MODS[n.id]={w:hash(b.writesBytes(n)),p:hash(b.buildPayload(ap,syntakt,stock))};return n;
  });
  if(a.isSelected('syntakt')&&document.getElementById('eng-swarm')?.checked&&edits!==6)throw Error('Swarm LITE: selected engine was not replaced');
  window.MCSwarmLiteApplied=edits;return previous(window.MCSwarmChordLayout(window.MCMacroRenderOptimize(changed,b,a,syntakt,stock,saved),input,b,a,syntakt,stock,saved),cycles,syntakt);
 };
 a.applyLang(document.documentElement.lang||'en');
})();
