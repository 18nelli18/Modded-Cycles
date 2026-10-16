// TINY utilise les tables combinées ; aucune machine et aucun mod n’est imposé.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,c=window.MCTinyCatalogue,prev=window.MCMainClearResolve,prior={...a.REF_MODS};
 Object.assign(window.MCWizardCatalogue.variants,c.variants);Object.assign(window.MCWizardReferences.sizes,c.sizes);
 for(const name of ['w','wp','ck','engines'])Object.assign(window.MCWizardReferences.refs[name],c.wizardRefs[name]);
 for(const [key,ref] of Object.entries(c.wizardRefs.engines))a.REF_MODS[c.variants[key].engine.id]=ref;
 tw.features.push({id:'tiny',label:'TINY',status:'experimental',cat:'sound',excludes:[],variants:[{id:'tiny'}],credit:{kind:'by',who:'@Glycinate'},license:'TINY-CREDITS.txt'});
 tw.tweaks.push({id:'tiny',order:24,writes:[],requires:[],conflicts:[]});
 window.MCMainClearResolve=out=>{
  for(const [id,ref] of Object.entries(prior))a.REF_MODS[id]=ref;
  out=prev(out);if(!a.isSelected('tiny'))return out;
  if(a.isSelected('sample-wizard'))return out.filter(t=>t.id!=='tiny');
  const codes=a.chosenEngines().map(e=>e.code),all=['sd','cp','toy','bits','swarm'];let mask=all.reduce((n,c,i)=>n+(codes.includes(c)?1<<i:0),0);
  if(a.isSelected('macro'))mask|=32;if(a.isSelected('acid'))mask|=64;if(a.isSelected('wave-supermodel'))mask|=128;
  return composeTinyNormal(c,mask,out,b,a.REF_MODS);
 };
 a.applyLang(document.documentElement.lang||'en');
})();
