// RETROSYN experimental : seule, ou avec la banque complete, Wizard facultatif.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,data=window.MCRetrosyn;
 const clone=x=>JSON.parse(JSON.stringify(x)),previous=window.MCMainClearResolve;
 tw.features.push({id:'retrosyn',label:'RETROSYN',cat:'sound',status:'experimental',
  desc:'Six retro oscillator types. Preview supports RETROSYN alone or the full added machine set, with or without independent Sample Wizard. Hardware testing pending.',
  excludes:['chord-keys','midi-bank-bundle'],variants:[{id:'retrosyn'}],credit:{kind:'by',who:'AveyCole, supplied RETROSYN core'}});
 tw.tweaks.push(clone(data.recipes.s));Object.assign(a.REF_MODS,data.refs);
 window.MCMainClearResolve=out=>{
  out=previous?previous(out):out;if(!a.isSelected('retrosyn'))return out;
  const other=[a.chosenEngines().filter(e=>['sd','cp','toy','bits','swarm'].includes(e.code)).length,...['macro','acid','wave-supermodel','tiny'].map(id=>Number(a.isSelected(id)))];
  const any=other.some(Boolean),full=other[0]===5&&other.slice(1).every(Boolean),wizard=a.isSelected('sample-wizard');
  if(any&&!full)throw Error('RETROSYN preview: choose all five Syntakt engines, MACRO, ACID, WAVE and TINY together, or turn the other added machines off. / Apercu RETROSYN : choisissez toutes les machines ajoutees ensemble, ou desactivez-les.');
  const key=(full?'a':'s')+(wizard?'w':''),e=clone(data.recipes[key]);
  const oldEngine=out.find(t=>t.append&&t.id!=='sample-wizard'&&!['supermodel-support-independent','supermodel-wave-support'].includes(t.id));
  let result=out.filter(t=>t.id!=='retrosyn'&&t!==oldEngine&&t.id!=='sample-wizard');
  if(wizard){
   const old=out.find(t=>t.id==='sample-wizard'),w=clone(data.samplers[key]);
   if(!old)throw Error('RETROSYN: independent Sample Wizard missing');
   const original=(full?window.MCTinyCatalogue.variants[511]:window.MCWizardCatalogue.variants[0]).wizard;
   // Conserver les options UI deja composees sans reprendre leurs anciennes tables machines.
   w.append=clone(old.append);
   for(const row of old.writes){const prior=original.writes.find(v=>v.off===row.off);if(!prior||JSON.stringify(prior)!==JSON.stringify(row)){const i=w.writes.findIndex(v=>v.off===row.off);if(i<0)w.writes.push(clone(row));else w.writes[i]=clone(row);}}
   w.requires=[];w.status='experimental';w.prototype_only=false;w.flashable=true;
   a.REF_MODS[w.id]={w:b.hex(b.sha256(b.writesBytes(w))),p:b.hex(b.sha256(b.buildPayload(w.append,null,null)))};
   result.push(w);
  }
  for(const support of result)if(support.requires?.includes(oldEngine?.id))support.requires=support.requires.map(id=>id===oldEngine.id?e.id:id);
  result.push(e);return result.sort((x,y)=>x.order-y.order);
 };
 const text={en:{label:'RETROSYN',short:'Six retro oscillator types; experimental.',desc:'Pulse, stepped triangle, wave tables, two noise types and an SNES-style loop voice. COLOR changes duty/table/noise rate, SWEEP bends pitch and CONTOUR chooses an arpeggio. PUNCH reduces to four bits. This preview supports RETROSYN alone or the complete added machine set including WAVE and TINY, with Sample Wizard optional. Partial engine combinations and ChordKeys are not yet supported. Hardware testing pending.'},fr:{label:'RETROSYN',short:'Six oscillateurs retro ; experimental.',desc:'Impulsion, triangle en escalier, tables d’ondes, deux bruits et boucle de style SNES. COLOR choisit rapport/table/cadence, SWEEP balaie la hauteur, CONTOUR choisit un arpege. PUNCH reduit a quatre bits. Cet apercu propose RETROSYN seule ou toutes les machines ajoutees dont WAVE et TINY, avec Sample Wizard facultatif. Combinaisons partielles et ChordKeys pas encore pris en charge. Test materiel attendu.'}};
 a.registerFeatureTexts('retrosyn',text);
 a.applyLang(document.documentElement.lang||'en');
})();
