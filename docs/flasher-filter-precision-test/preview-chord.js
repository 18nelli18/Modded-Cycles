// ChordKeys est désormais dans sa charge utile séparée : aucun masque commun avec la préécoute.
(()=>{
 const a=window.MCFlasherApp,tw=window.MC_TWEAKS,c=window.MCWizardCatalogue;
 const p=tw.features.find(f=>f.id==='sample-preview'),k=tw.features.find(f=>f.id==='chord-keys');
 p.excludes=(p.excludes||[]).filter(id=>!['chord-keys','wave-supermodel'].includes(id));
 const wf=tw.features.find(f=>f.id==='wave-supermodel');wf.excludes=(wf.excludes||[]).filter(id=>id!=='sample-preview');
 k.excludes=(k.excludes||[]).filter(id=>id!=='sample-preview');
 c.preview.conflicts=(c.preview.conflicts||[]).filter(id=>id!=='chord-keys-supermodel');
 p.status='experimental';p.hardwareTestedByOwner=false;
 const prev=window.MCMainClearResolve,prior={...a.REF_MODS},b=window.MCBuilder,hash=t=>b.hex(b.sha256(b.writesBytes(t)));
 window.MCMainClearResolve=out=>{
  for(const [id,ref] of Object.entries(prior))a.REF_MODS[id]=ref;
  out=prev(out);if(!a.isSelected('sample-preview')||!a.isSelected('wave-supermodel'))return out;
  const wizard=out.find(t=>t.id==='sample-wizard');if(!wizard)throw Error('Preview: missing Wizard support');
  const route=wizard.writes.find(x=>x.off===0xa6026);if(!route||!route.new.startsWith('4eb9'))throw Error('Preview: WAVE browser guard');
  return out.map(t=>{
   if(t.id!=='wizard-sample-preview')return t;
   if(hash(t)!==a.REF_MODS[t.id].w)throw Error('Preview: trusted reference mismatch');
   const n=JSON.parse(JSON.stringify(t));
   function patch(va,old,bytes){const off=va-0x40000400,w=n.writes.find(x=>x.off<=off&&off+old.length/2<=x.off+x.new.length/2);if(!w)throw Error('Preview: missing hook');const i=(off-w.off)*2;if(w.new.slice(i,i+old.length)!==old)throw Error('Preview: hook bytes changed');w.new=w.new.slice(0,i)+bytes+w.new.slice(i+old.length);}
   patch(0x40185d20,'4eb9400a3052',route.new);
   patch(0x40185a42,'4e56ff98707f4ef940081724','4ef9'+parseInt(wizard.symbols.av_pad_hook,16).toString(16).padStart(8,'0')+'4e714e714e71');
   const browser=n.writes.find(x=>x.off===0xa6026);if(browser.old!=='4eb9400a3052')throw Error('Preview: old browser guard');browser.old=route.new;
   a.REF_MODS[n.id]={w:hash(n)};return n;
  });
 };
 a.applyLang(document.documentElement.lang||'en');
})();
