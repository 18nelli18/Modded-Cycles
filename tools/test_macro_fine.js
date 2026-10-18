// Deux profils complets avant/apres, avec et sans banque B.
const fs=require('fs'),assert=require('node:assert/strict');process.env.RETROSYN_PAGE='docs/flasher-macro-fine-test';const{open,change}=require('./test_retrosyn_flasher');
(async()=>{fs.mkdirSync('build/macro-fine',{recursive:true});const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
for(const bank of [false,true]){const{w,errors}=open();try{await w.MCMacroFineReady;
 w.document.getElementById('select-all').click();
 change(w,'midi-out-bank',bank);change(w,'audio-load-diagnostic',true);
 const a=w.MCFlasherApp,chosen=a.chosenTweaks();assert(!a.state.selectionError,a.state.selectionError);
 for(const[mode,compose]of[['before',w.MCMacroFineBaseCompose],['after',w.MCMidiBankCompose]]){
  const p=compose(chosen,os,st);assert.equal(p.tweaks.some(t=>t.id==='macro-fine-test'),mode==='after');
  const built=w.MCBuilder.build(os,w.MC_TWEAKS.device,p.tweaks,{syntakt:st,refMods:p.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
  const prefix='build/macro-fine/'+(bank?'bank':'all')+'-'+mode;fs.writeFileSync(prefix+'.json',JSON.stringify({tweaks:p.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(prefix+'.syx',built.raw);console.log('PASS signe',bank?'bank':'all',mode,built.mainOsSha);
 }
 assert(!errors.length,errors.join('\n'));
}finally{w.close();}}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
