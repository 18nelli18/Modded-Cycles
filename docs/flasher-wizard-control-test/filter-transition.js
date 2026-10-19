// Note112 : correction confirmee sur appareil ; aucun diagnostic embarque.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCFilterTransition,previous=window.MCMainClearResolve,n=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 const feature=window.MC_TWEAKS.features.find(f=>f.id==='track-filter');feature.status='tested';feature.hardwareTestedByOwner=true;
 a.registerFeatureTexts('track-filter',{en:{label:'Per-track filter',short:'Hardware tested: clean filtering after leaving Sample Wizard.',desc:'Prevents an obsolete second filter pass on added machines after switching away from Sample Wizard. Retains the efficient four-pole filter, cutoff, resonance and neutral bypass. Confirmed on hardware by AveyCole on 17 October 2026.'},fr:{label:'Filtre par piste',short:'Teste sur machine : filtre propre apres Sample Wizard.',desc:'Supprime un ancien second passage filtre sur les machines ajoutees apres sortie de Sample Wizard. Conserve le filtre quatre poles efficace, la coupure, la resonance et le bypass neutre. Confirme sur machine par AveyCole le 17/10/2026.'}});
 window.MCMainClearResolve=input=>previous(input).map(t=>{
  if(!a.isSelected('track-filter'))return t;
  if(t.id==='wizard-continuous-filter')return {...t,status:'tested',hardwareTestedByOwner:true};
  if(t.id!=='sample-wizard')return t;
  const result=JSON.parse(JSON.stringify(t)),f=d.filter,p=result.append.parts.find(p=>p.hex&&n(p.dest)<=f.at&&f.at+f.size<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Filter transition: body missing');
  const i=2*(f.at-n(p.dest));if(hash(b.fromHex(p.hex.slice(i,i+2*f.size)))!==f.old_sha256)throw Error('Filter transition: body guard');p.hex=p.hex.slice(0,i)+f.hex+p.hex.slice(i+2*f.size);
  const c=d.inner_call,q=result.append.parts.find(p=>p.hex&&n(p.dest)<=c.at&&c.at+4<=n(p.dest)+p.hex.length/2);if(!q)throw Error('Filter transition: call missing');const j=2*(c.at-n(q.dest));if(q.hex.slice(j,j+8)!==c.old)throw Error('Filter transition: call guard');q.hex=q.hex.slice(0,j)+c.new+q.hex.slice(j+8);
  delete result.append.compressed_hex;a.REF_MODS[result.id]={w:hash(b.writesBytes(result)),p:hash(b.buildPayload(result.append,null,null))};result.status='tested';result.hardwareTestedByOwner=true;return result;
 });a.applyLang(document.documentElement.lang||'en');
})();
