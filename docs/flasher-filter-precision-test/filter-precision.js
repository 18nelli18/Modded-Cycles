// Note 102 : garde SHA, remplacement local du seul ladder partage.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCFilterPrecision,prev=window.MCMainClearResolve;
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 const f=window.MC_TWEAKS.features.find(f=>f.id==='track-filter');f.status='experimental';delete f.hardwareTestedByOwner;
 a.registerFeatureTexts('track-filter',{
 en:{label:'Per-track filter — precision test',short:'Higher-precision ladder; checks bit-crushing reported on track 6.',desc:'Experimental repair for coarse, bit-crushed audio when lowering cutoff, especially on quiet signals. Retains the four-pole ladder, cutoff and resonance controls. MACHINES + SWEEP: cutoff; MACHINES + CONTOUR: resonance. Fully open cutoff with zero resonance remains an exact bypass. Wizard keeps its own filter. Test the same sound on tracks 5 and 6. Hardware verification pending.'},
 fr:{label:'Filtre par piste — test precision',short:'Ladder haute precision ; verifier le son ecrase sur la piste 6.',desc:'Correction experimentale du son quantifie quand la coupure baisse, surtout aux niveaux faibles. Ladder quatre poles et controles conserves. MACHINES + SWEEP : coupure ; MACHINES + CONTOUR : resonance. Coupure maximale et resonance nulle : bypass exact. Wizard garde son filtre propre. Comparer le meme son sur pistes 5 et 6. Verification materielle attendue.'}
 });
 window.MCMainClearResolve=input=>{
  const out=prev(input);if(!a.isSelected('track-filter'))return out;
  return out.map(t=>{
   if(t.id==='wizard-continuous-filter')return {...t,status:'experimental',hardwareTestedByOwner:false};
   if(t.id!=='sample-wizard')return t;
   const n=clone(t),p=n.append.parts.find(p=>p.hex&&num(p.dest)<=d.at&&d.at+d.size<=num(p.dest)+p.hex.length/2);
   if(!p)throw Error('Filter precision: runtime range missing');const off=(d.at-num(p.dest))*2;
   if(hash(b.fromHex(p.hex.slice(off,off+2*d.size)))!==d.old_sha256)throw Error('Filter precision: original ladder changed');
   p.hex=p.hex.slice(0,off)+d.hex+p.hex.slice(off+2*d.size);delete n.append.compressed_hex;
   a.REF_MODS[n.id]={w:hash(b.writesBytes(n)),p:hash(b.buildPayload(n.append,null,null))};return n;
  });
 };a.applyLang(document.documentElement.lang||'en');
})();
