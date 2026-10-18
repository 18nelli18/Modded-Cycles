// Profil909 : activer la preecoute Wizard existante, sans modifier les voix909.
(()=>{
 const a=window.MCFlasherApp,d=window.MC909CurrentData;
 if(!d.features.includes('sample-preview'))d.features.push('sample-preview');
 window.MC909SamplePreviewReady=Promise.all([window.MC909CurrentReady,window.MC909CrossoverReady,window.MCLfoDestinationsReady]).then(()=>{
  const box=document.getElementById('feat-sample-preview');if(!box)throw Error('909 Sample Preview: missing feature');
  if(!box.checked){box.checked=true;box.dispatchEvent(new Event('change',{bubbles:true}));}
  if(!window.MC909CurrentLabels.includes('Sample Preview'))window.MC909CurrentLabels.push('Sample Preview');
  const previous=window.MCMidiBankCompose;
  window.MCMidiBankCompose=(...args)=>{
   const r=previous(...args),preview=r.tweaks.find(t=>t.id==='wizard-sample-preview');
   if(!preview)throw Error('909 Sample Preview: missing composed preview');
   return {...r,tweaks:r.tweaks.map(t=>t===preview?{...t,status:'experimental',hardwareTestedByOwner:false}:t)};
  };
 });
})();
