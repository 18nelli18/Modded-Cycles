// Page de test seulement : profils explicites, aucune modification du main.
(()=>{
 const tw=window.MC_TWEAKS;tw.features=tw.features.filter(f=>f.id!=='lfo-plus');tw.tweaks=tw.tweaks.filter(t=>t.id!=='lfo-plus');
 const change=(id,on)=>{const e=document.getElementById('feat-'+id);if(e){e.checked=on;e.dispatchEvent(new Event('change',{bubbles:true}));}};
 function profile(mode){
  change('retrosyn',false);
  for(const id of ['chord-keys','midi-bank-bundle','scale-gen','scramble'])change(id,false);
  for(const id of ['tiny','wave-supermodel','acid','macro'])change(id,false);
  change('syntakt',mode!=='solo');
  if(mode!=='solo'){
   for(const code of ['sd','cp','toy','bits','swarm']){const e=document.getElementById('eng-'+code);e.checked=true;e.dispatchEvent(new Event('change',{bubbles:true}));}
   for(const id of ['macro','acid','wave-supermodel','tiny'])change(id,true);
  }
  change('sample-wizard',mode==='wizard');change('retrosyn',true);
 }
 window.MCRetrosynTestProfile=profile;
 document.querySelectorAll('[data-retrosyn-profile]').forEach(e=>e.addEventListener('click',()=>profile(e.dataset.retrosynProfile)));
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>profile('full'),{once:true});else profile('full');
})();
