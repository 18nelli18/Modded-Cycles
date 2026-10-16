// Note 105 : garde stricte du noyau 1.77, moins de travail sans changer les calculs.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCFilterLoad,previous=window.MCMainClearResolve,num=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 const f=window.MC_TWEAKS.features.find(f=>f.id==='track-filter');f.status='experimental';f.hardwareTestedByOwner=false;
 a.registerFeatureTexts('track-filter',{
  en:{label:'Per-track filter — busy playback test',short:'Reduced processing work; same filter sound. Test busy patterns and ticks.',desc:'Experimental test for distortion and ticks when lowering cutoff during busy playback. Retains the same four-pole filter arithmetic, cutoff, resonance and neutral bypass while reducing repeated processing checks. Compare with and without MIDI OUT Bank. No new filter controls. Hardware verification pending.'},
  fr:{label:'Filtre par piste — test lecture chargee',short:'Calcul allege, meme son. Verifier patterns charges et ticks.',desc:'Test experimental des distorsions et ticks en baissant la coupure pendant une lecture chargee. Memes calculs quatre poles, coupure, resonance et bypass ; moins de verifications repetees. Comparer avec et sans Banque MIDI. Aucune nouvelle commande. Verification materielle attendue.'}
 });
 window.MCMainClearResolve=input=>previous(input).map(t=>{
  if(!a.isSelected('track-filter'))return t;
  if(t.id==='wizard-continuous-filter')return {...t,status:'experimental',hardwareTestedByOwner:false};
  if(t.id!=='sample-wizard')return t;
  const n=JSON.parse(JSON.stringify(t)),p=n.append.parts.find(p=>p.hex&&num(p.dest)<=d.at&&d.at+d.size<=num(p.dest)+p.hex.length/2);if(!p)throw Error('Filter load: body missing');const i=(d.at-num(p.dest))*2;
  if(hash(b.fromHex(p.hex.slice(i,i+2*d.size)))!==d.old_sha256)throw Error('Filter load: main precision guard');p.hex=p.hex.slice(0,i)+d.hex+p.hex.slice(i+2*d.size);delete n.append.compressed_hex;
  a.REF_MODS[n.id]={w:hash(b.writesBytes(n)),p:hash(b.buildPayload(n.append,null,null))};return n;
 });a.applyLang(document.documentElement.lang||'en');
})();
