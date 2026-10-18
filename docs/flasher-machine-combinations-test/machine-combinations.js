// Choix independants des machines : corps natifs partages, interfaces propres au choix.
(()=>{
 'use strict';const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMachineCombinationData;
 const clone=x=>JSON.parse(JSON.stringify(x)),hash=x=>b.hex(b.sha256(x)),whash=x=>hash(b.writesBytes(x));
 Object.assign(window.MCWizardCatalogue.variants,d.wizard);
 Object.assign(window.MCTinyCatalogue.normal,d.normal);
 const mask=()=>a.chosenEngines().reduce((m,e)=>m|({sd:1,cp:2,toy:4,bits:8,swarm:16}[e.code]||0),0)|
  (a.isSelected('macro')?32:0)|(a.isSelected('acid')?64:0)|(a.isSelected('wave-supermodel')?128:0)|(a.isSelected('tiny')?256:0)|(a.isSelected('retrosyn')?512:0);
 function trust(e,entry){const raw=Uint8Array.from(unescape(encodeURIComponent(JSON.stringify(e))),c=>c.charCodeAt(0));if(!entry||hash(raw)!==entry.engine_sha256)throw Error('Machine selection: catalogue integrity mismatch');}
 function normalRef(e){trust(e,d.normal[e.machine_selection]);return {w:whash(e),size:0};}
 function wizard(c,state,out){
  trust(c.variants[state.mask].engine,d.wizard[state.mask]);
  Object.assign(a.REF_MODS,window.MCWizardReferences.refs.mods);
  const result=composeWizard(c,state,out,{}),engine=result.find(t=>t.machine_selection!==undefined),ck=result.find(t=>t.id==='chord-keys-supermodel');
  if(ck){
   const raw=ck.append.parts[0].hex,source=parseInt(engine.append.dest,16)+0x2e900,loader=ck.writes.find(w=>w.off+0x40000400===parseInt(ck.symbols.chord_boot,16));
   for(const part of engine.append.parts){const lo=parseInt(part.dest,16),n=part.hex?part.hex.length/2:parseInt((part.cycles||part.syntakt)[1],16)-parseInt((part.cycles||part.syntakt)[0],16);if(source<lo+n&&lo<source+raw.length/2)throw Error('Machine selection: ChordKeys reservation occupied');}
   const tail=loader.new.slice(loader.new.indexOf('203c000cc100'));
   if(tail.length!==36||raw.length%8)throw Error('Machine selection: ChordKeys copy guard');
   let copy='41f9'+source.toString(16).padStart(8,'0')+'43f9'+parseInt(ck.append.dest,16).toString(16).padStart(8,'0')+'203c'+(raw.length/8).toString(16).padStart(8,'0')+'22d8538066fa';
   while(copy.length+tail.length<loader.new.length)copy+='4e71';
   if(copy.length+tail.length!==loader.new.length)throw Error('Machine selection: ChordKeys loader size');
   loader.new=copy+tail;engine.chord_source='0x'+source.toString(16);engine.append.parts.push({dest:'0x'+source.toString(16),hex:raw});delete ck.append;
  }
  for(const t of result){if(t===engine||t===ck||t.id==='sample-wizard')a.REF_MODS[t.id]={w:whash(t),...(t.append&&t!==engine?{p:hash(b.buildPayload(t.append,null,null))}:{})};}
  return result;
 }
 function normal(out){const key=mask(),data={normal:d.normal,refs:{n:{}}};return composeTinyNormal(data,key,out,b,a.REF_MODS).filter(t=>t.id!=='retrosyn');}
 window.MCMachineCombinations={wizard,normal,normalRef};
})();
