// RETROSYN experimental : seule, ou avec la banque complete, Wizard facultatif.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,data=window.MCRetrosyn;
 const clone=x=>JSON.parse(JSON.stringify(x)),previous=window.MCMainClearResolve;
 tw.features.push({id:'retrosyn',label:'RETROSYN',cat:'sound',status:'experimental',
  desc:'Six retro oscillator types. Preview supports RETROSYN alone or the full added machine set, with or without independent Sample Wizard. Hardware testing pending.',
  excludes:[],variants:[{id:'retrosyn'}],credit:{kind:'by',who:'AveyCole, supplied RETROSYN core'}});
 tw.tweaks.push(clone(data.recipes.s));Object.assign(a.REF_MODS,data.refs);
 window.MCMainClearResolve=out=>{
  out=previous?previous(out):out;if(!a.isSelected('retrosyn'))return out;
  const other=[a.chosenEngines().filter(e=>['sd','cp','toy','bits','swarm'].includes(e.code)).length,...['macro','acid','wave-supermodel','tiny'].map(id=>Number(a.isSelected(id)))];
  const any=other.some(Boolean),full=other[0]===5&&other.slice(1).every(Boolean),wizard=a.isSelected('sample-wizard');
  if(any&&!full)throw Error('RETROSYN preview: choose all five Syntakt engines, MACRO, ACID, WAVE and TINY together, or turn the other added machines off. / Apercu RETROSYN : choisissez toutes les machines ajoutees ensemble, ou desactivez-les.');
  const chord=a.isSelected('chord-keys'),key=(full?'a':'s')+(wizard?'w':'')+(full&&chord?'c':''),e=clone(data.recipes[key]);
  a.REF_MODS[e.id]=clone(data.chord_refs[key]||data.refs[e.id]);
  const oldEngine=out.find(t=>t.append&&t.id!=='sample-wizard'&&t.id!=='chord-keys-supermodel'&&!['supermodel-support-independent','supermodel-wave-support'].includes(t.id));
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
  for(const support of result.filter(t=>['supermodel-support-independent','supermodel-wave-support'].includes(t.id))){
   const tail='4feffff048d700f04ef9400004ba';let row=support.writes.find(w=>w.old===tail);
   if(!row){const root=support.writes.find(w=>w.off===0x130);if(root){support.writes=support.writes.filter(w=>w!==root);row={off:0,old:tail,new:root.new.slice(0,12)+'4e714e714e714e71'};support.writes.push(row);}}
   if(row){const stub=e.writes.find(w=>w.new.includes(tail));if(!stub)throw Error('RETROSYN: support startup tail missing');row.off=stub.off+stub.new.indexOf(tail)/2;}
   const leds=new Set([0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18]);
   e.writes=e.writes.filter(w=>{const other=support.writes.find(v=>v.off===w.off&&v.new!==w.new);if(!other||!leds.has(w.off+0x40000400))return true;if(w.old!==other.old)throw Error('RETROSYN: support LED guard');return false;});
   a.REF_MODS[support.id]={w:b.hex(b.sha256(b.writesBytes(support))),p:b.hex(b.sha256(b.buildPayload(support.append,null,null)))};
   a.REF_MODS[e.id]={...a.REF_MODS[e.id],w:b.hex(b.sha256(b.writesBytes(e)))};
  }
  const ck=result.find(t=>t.id==='chord-keys-supermodel');
  if(ck&&!full){
   const route=ck.writes.find(w=>w.off===0x130);
   if(route){const original=window.MCWizardCatalogue.ck.writes.find(w=>w.new==='4ef9401907a4');if(!original)throw Error('RETROSYN: ChordKeys return guard');Object.assign(route,clone(original));const stub=e.writes.find(w=>w.new.includes(route.old));if(!stub)throw Error('RETROSYN: ChordKeys engine return missing');route.off=stub.off+stub.new.indexOf(route.old)/2;}
   const source=0x401f8f76;ck.append.zero_pad_from='0x401aa140';
   const loader=ck.writes.find(w=>w.off+0x40000400===parseInt(ck.symbols.chord_boot,16));
   loader.new='41f9'+source.toString(16).padStart(8,'0')+loader.new.slice(12);ck.append.at='0x'+source.toString(16);
   a.REF_MODS[ck.id]={w:b.hex(b.sha256(b.writesBytes(ck))),p:b.hex(b.sha256(b.buildPayload(ck.append,null,null)))};
  }
  if(ck&&full){
   const loader=ck.writes.find(w=>w.off+0x40000400===parseInt(ck.symbols.chord_boot,16));
   if(!loader?.new.startsWith('41f9'))throw Error('RETROSYN: ChordKeys bootstrap guard');
   const raw=ck.append.parts[0].hex,tail=loader.new.slice(loader.new.indexOf('203c000cc100'));
   if(raw!==e.append.parts.find(p=>p.dest===e.chord_source)?.hex||raw.length%8||tail.length!==36)throw Error('RETROSYN: ChordKeys shared payload guard');
   // Copier depuis la SDRAM deja decompressee, puis invalider le cache natif.
   let copy='41f9'+parseInt(e.chord_source,16).toString(16).padStart(8,'0')+'43f9'+parseInt(ck.append.dest,16).toString(16).padStart(8,'0')+'203c'+(raw.length/8).toString(16).padStart(8,'0')+'22d8538066fa';
   while(copy.length+tail.length<loader.new.length)copy+='4e71';
   if(copy.length+tail.length!==loader.new.length)throw Error('RETROSYN: ChordKeys copy length guard');
   loader.new=copy+tail;delete ck.append;
   a.REF_MODS[ck.id]={w:b.hex(b.sha256(b.writesBytes(ck)))};
  }
  result.push(e);return result.sort((x,y)=>x.order-y.order);
 };
 const text={en:{label:'RETROSYN',short:'Six retro oscillator types; experimental.',desc:'Pulse, stepped triangle, wave tables, two noise types and an SNES-style loop voice. COLOR changes duty/table/noise rate, SWEEP bends pitch and CONTOUR chooses an arpeggio. PUNCH reduces to four bits. This preview supports RETROSYN alone or the complete added machine set including WAVE and TINY, with Sample Wizard optional. ChordKeys is compatible. Second LFO and either startup animation are compatible. Partial engine combinations are not yet supported. Hardware testing pending.'},fr:{label:'RETROSYN',short:'Six oscillateurs retro ; experimental.',desc:'Impulsion, triangle en escalier, tables d’ondes, deux bruits et boucle de style SNES. COLOR choisit rapport/table/cadence, SWEEP balaie la hauteur, CONTOUR choisit un arpege. PUNCH reduit a quatre bits. Cet apercu propose RETROSYN seule ou toutes les machines ajoutees dont WAVE et TINY, avec Sample Wizard facultatif. ChordKeys compatible. Second LFO et une animation de demarrage au choix sont compatibles. Combinaisons partielles pas encore prises en charge. Test materiel attendu.'}};
 a.registerFeatureTexts('retrosyn',text);
 a.applyLang(document.documentElement.lang||'en');
})();
