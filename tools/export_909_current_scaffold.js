// Note 108 : profil 909 depuis les supports actuellement servis par main.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{open,change}=require('./test_retrosyn_flasher');
const features=['sample-wizard','supermodel-performance','track-filter','acid','scale-gen','lfo-secondary','scramble','midi-out-bank','control-all-config','control-all-beat-repeat','midi-live-both','latching-mute'];
(async()=>{const {w,errors}=open();await new Promise(r=>setTimeout(r,60));try{
 w.document.getElementById('select-all').click();w.document.getElementById('super-clear').click();for(const id of features)change(w,id,true);
 const tweaks=w.MCFlasherApp.chosenTweaks();assert(tweaks.some(t=>t.id==='sample-wizard'));assert(!tweaks.some(t=>t.id.startsWith('model-tg')));assert.equal(errors.length,0);
 const refs=Object.fromEntries(tweaks.map(t=>[t.id,{w:w.MCFlasherApp.REF_MODS[t.id]?.w,p:w.MCFlasherApp.REF_MODS[t.id]?.p}]));
 const other=open();await new Promise(r=>setTimeout(r,60));other.w.document.getElementById('select-all').click();other.w.document.getElementById('super-clear').click();for(const id of features.filter(id=>id!=='acid'))change(other.w,id,true);const plainWizard=other.w.MCFlasherApp.chosenTweaks().find(t=>t.id==='sample-wizard');assert(plainWizard);other.w.close();
 fs.mkdirSync('build/909-current',{recursive:true});fs.writeFileSync('build/909-current/scaffold.json',JSON.stringify({tweaks,refs,features,plainWizard}));console.log('PASS supports main',tweaks.map(t=>t.id).join(', '));
}finally{w.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1;});
