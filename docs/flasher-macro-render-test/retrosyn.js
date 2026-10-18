// RETROSYN : choix independant, Sample Wizard facultatif.
(()=>{
 const a=window.MCFlasherApp,tw=window.MC_TWEAKS,data=window.MCRetrosyn;
 tw.features=tw.features.filter(f=>f.id!=='lfo-plus');tw.tweaks=tw.tweaks.filter(t=>t.id!=='lfo-plus');
 const clone=x=>JSON.parse(JSON.stringify(x)),previous=window.MCMainClearResolve;
 tw.features.push({id:'retrosyn',label:'RETROSYN',cat:'sound',status:'tested',hardwareTestedByOwner:true,
  desc:'Six retro oscillator types. Combine freely with the other added machines, with or without Sample Wizard.',
  excludes:[],variants:[{id:'retrosyn'}],credit:{kind:'by',who:'AveyCole, supplied RETROSYN core'}});
 tw.tweaks.push(clone(data.recipes.s));Object.assign(a.REF_MODS,data.refs);
 window.MCMainClearResolve=out=>{
  out=previous?previous(out):out;
  if(out.some(t=>t.machine_selection!==undefined))return out.filter(t=>t.id!=='retrosyn');
  if(!a.isSelected('retrosyn'))return out;
  return window.MCMachineCombinations.normal(out);
 };
 a.registerFeatureTexts('retrosyn',{
  en:{label:'RETROSYN',short:'Six retro oscillator types; hardware tested.',desc:'Pulse, stepped triangle, wave tables, two noise types and an SNES-style loop voice. COLOR changes duty/table/noise rate, SWEEP bends pitch and CONTOUR chooses an arpeggio. PUNCH reduces to four bits. Combine freely with any selection of the added machines. Sample Wizard is optional; ChordKeys, Second LFO and either startup animation are compatible. The voice was hardware tested by AveyCole on 16 October 2026; the expanded selection catalogue is verified in emulation.'},
  fr:{label:'RETROSYN',short:'Six oscillateurs retro ; testes sur machine.',desc:'Impulsion, triangle en escalier, tables d’ondes, deux bruits et boucle de style SNES. COLOR choisit rapport/table/cadence, SWEEP balaie la hauteur, CONTOUR choisit un arpege. PUNCH reduit a quatre bits. Combinez librement les machines ajoutees. Sample Wizard reste facultatif ; ChordKeys, Second LFO et une animation de demarrage au choix sont compatibles. Voix testee par AveyCole le 16/10/2026 ; catalogue etendu verifie en emulation.'}
 });a.applyLang(document.documentElement.lang||'en');
})();
