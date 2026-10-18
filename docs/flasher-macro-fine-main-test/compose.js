// Composition des options Wizard ; utilisée identiquement par l'UI et les preuves.
function composeWizard(c,state,basic,engineSizes){
 const v=c.variants[state.mask];if(!v)throw Error('Sample Wizard: unavailable machine combination '+state.mask);
 const clone=x=>JSON.parse(JSON.stringify(x)),w=clone(v.wizard),cat=[w];
 w.prototype_only=false;w.flashable=true;w.status='experimental';
 const ap=w.append,part=ap.parts[0],base=parseInt(ap.dest,16),writeLong=(name,value)=>{const off=(parseInt(w.symbols[name],16)-base)*2;part.hex=part.hex.slice(0,off)+value.toString(16).padStart(8,'0')+part.hex.slice(off+8);};
 writeLong('av_perf_on',Number(state.perf));writeLong('av_ui_mods',Number(state.perf||state.genie||state.scramble));
 if(state.perf)w.writes.push(...clone(c.perf));if(state.lfo)w.writes.push(...clone(c.clear));
 if(state.chord){for(const x of w.writes){if(x.off+0x40000400===0x400792f2)x.new='401eb7dc';if(x.off+0x40000400===0x400792bc)x.new='401eb800';}w.cache_blocks=7;}
 if(v.engine)cat.push(clone(v.engine));if(state.preview)cat.push(clone(c.preview));
 if(state.genie)cat.push(clone(c.sg));if(state.scramble)cat.push(clone(state.genie?c.scg:c.sc));
 if(state.chord){const ck=clone(c.ck),source=base+ap.size+(engineSizes[state.mask]||0),loader=ck.writes.find(x=>x.off+0x40000400===parseInt(ck.symbols.chord_boot,16));
  if(!loader.new.startsWith('41f9'))throw Error('Wizard: unexpected ChordKeys bootstrap');
  if(!v.engine){const route=ck.writes.find(x=>x.new==='4ef9401907a4');if(!route)throw Error('Wizard: missing ChordKeys route');route.off=0x130;route.old='4eb9'+parseInt(w.symbols.boot_extra_hook,16).toString(16);route.new='4eb9401907a4';}
  loader.new='41f9'+source.toString(16).padStart(8,'0')+loader.new.slice(12);ck.append.at='0x'+source.toString(16);cat.push(ck);
 }
 const reserved=t=>t.id.startsWith('model-tg')||t.id.startsWith('scale-gen')||t.id.startsWith('scramble')||t.id==='chord-keys-supermodel'||t.id==='supermodel-performance'||t.id==='supermodel-support-independent'||t.id==='supermodel-wave-support'||t.id==='sample-wizard'||t.id.startsWith('sample-preview')||t.id==='wave-supermodel'||!!t.append;
 cat.push(...basic.filter(t=>!reserved(t)));return cat.sort((a,b)=>a.order-b.order);
}
if(typeof module!=='undefined')module.exports=composeWizard;
