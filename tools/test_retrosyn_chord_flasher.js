// RETROSYN/ChordKeys : cases reelles, deux animations, LFO restant et Select All.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const {open,change}=require('./test_retrosyn_flasher');
(async()=>{
 const cases=[[false,false,false],[false,true,false],[true,false,false],[true,true,false],[true,true,true,'boot-anim'],[true,true,true,'supermodel-startup']];
 for(const [full,wizard,all,animation='boot-anim'] of cases){
  const {w,errors}=open();await new Promise(r=>setTimeout(r,50));
  try{
   if(w.MCRetrosynTestProfile){w.MCRetrosynTestProfile('solo');change(w,'retrosyn',false);}
   assert(!w.document.getElementById('feat-lfo-plus'));
   if(full){change(w,'syntakt',true);for(const code of ['sd','cp','toy','bits','swarm']){const box=w.document.getElementById('eng-'+code);box.checked=true;box.dispatchEvent(new w.Event('change',{bubbles:true}));}for(const id of ['macro','acid','wave-supermodel','tiny'])change(w,id,true);}
   if(wizard)change(w,'sample-wizard',true);
   if(all)w.document.getElementById('select-all').click();
   change(w,'retrosyn',true);change(w,'chord-keys',true);change(w,'lfo-secondary',true);change(w,animation,true);
   const a=w.MCFlasherApp,t=a.chosenTweaks();
   assert(a.isSelected('retrosyn')&&a.isSelected('chord-keys')&&a.isSelected('lfo-secondary'));
   assert.equal(a.isSelected('sample-wizard'),wizard);
   assert(!a.isSelected(animation==='boot-anim'?'supermodel-startup':'boot-anim'));
   assert(t.some(t=>(t.id==='chord-keys-supermodel'||t.symbols?.chord_keys_build)),JSON.stringify(t.map(t=>t.id)));assert(!t.some(t=>t.id==='lfo-plus'));
   if(all)for(const f of w.MC_TWEAKS.features)if(!['boot-anim','supermodel-startup'].includes(f.id))assert(a.isSelected(f.id),'Select All lost '+f.id);
   const name='retrosyn-chord-'+(full?'full':'solo')+(wizard?'-wizard':'')+(all?'-all-'+animation:'');
   const raw=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));
   const built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,t,{syntakt:st,refMods:a.REF_MODS});
   assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));
   fs.writeFileSync(path.resolve(__dirname,'../build/'+name+'.syx'),built.raw);
   fs.writeFileSync(path.resolve(__dirname,'../build/'+name+'.json'),JSON.stringify({tweaks:t,mainOsSha:built.mainOsSha}));
   console.log('ok',name,built.mainOsSha);
  }finally{w.close();}
 }
})().catch(e=>{console.error(e.stack);process.exitCode=1;});


