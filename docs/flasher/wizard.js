// Test seulement : même checklist et même transport que main, sans Model-TG.
(()=>{
 const a=window.MCFlasherApp,tw=window.MC_TWEAKS,c=window.MCWizardCatalogue,r=window.MCWizardReferences,prev=window.MCMainClearResolve,on=a.isSelected;
 const tg=document.getElementById('feat-model-tg');if(tg?.checked){tg.checked=false;tg.dispatchEvent(new Event('change',{bubbles:true}));}
 tw.features=tw.features.filter(f=>f.id!=='model-tg');
 tw.features.push({id:'sample-wizard',label:'Sample Wizard',desc:'Independent sampler with Slice varispeed.',status:'tested',cat:'sound',excludes:['track-filter'],variants:[{id:'sample-wizard'}],credit:{kind:'by',who:'TinyGregAudio; roterodamus; A.V.',repo:'TinyGregAudio/Model-TG'},license:'LICENSE-Sample-Wizard.txt'});
 tw.tweaks.push(c.variants[0].wizard);
 const preview=tw.features.find(f=>f.id==='sample-preview');if(preview){preview.status='tested';preview.requires='sample-wizard';preview.with={};preview.excludes=['chord-keys','wave-supermodel'];}
 for(const id of ['chord-keys','wave-supermodel']){const f=tw.features.find(f=>f.id===id);if(f)f.excludes=[...new Set([...(f.excludes||[]),'sample-preview'])];}
 const filter=tw.features.find(f=>f.id==='track-filter');if(filter)filter.excludes=[...new Set([...(filter.excludes||[]),'sample-wizard'])];
 let active=null;
 window.MCMainClearResolve=out=>{
  active=null;if(!on('sample-wizard'))return prev(out);
  const codes=a.chosenEngines().map(e=>e.code),all=['sd','cp','toy','bits','swarm'];let mask=all.reduce((n,c,i)=>n+(codes.includes(c)?1<<i:0),0);
  if(on('macro'))mask|=32;if(on('acid'))mask|=64;if(on('wave-supermodel'))mask|=128;
  const state={mask,perf:on('supermodel-performance'),lfo:on('lfo-secondary'),chord:on('chord-keys'),genie:on('scale-gen'),scramble:on('scramble'),preview:on('sample-preview')};
  const bits=Number(state.perf)+2*Number(state.lfo)+4*Number(state.chord),ui=Number(state.perf||state.genie||state.scramble),pk=ui+2*Number(state.perf);
  active={'sample-wizard':{w:r.refs.w[mask+':'+bits],p:r.refs.wp[mask+':'+pk]},...r.refs.mods};
  if(mask)active[c.variants[mask].engine.id]=r.refs.engines[mask];if(state.chord)active['chord-keys-supermodel']=r.refs.ck[mask];
  return composeWizard(c,state,out,r.sizes);
 };
 const ids=['sample-wizard','chord-keys-supermodel',c.sg.id,c.sc.id,c.scg.id,c.preview.id,...Object.values(c.variants).filter(v=>v.engine).map(v=>v.engine.id)];
 for(const id of new Set(ids)){const old=a.REF_MODS[id],ref={};for(const k of ['w','p'])Object.defineProperty(ref,k,{get:()=>active&&active[id]?active[id][k]:old?.[k]});a.REF_MODS[id]=ref;}
 a.applyLang(document.documentElement.lang||'en');
})();
