// Empreintes figees des recettes et invalidation d'une ancienne selection erronee.
const fs=require('fs'),vm=require('vm'),crypto=require('crypto'),assert=require('node:assert/strict');
const ctx={window:{}};vm.runInNewContext(fs.readFileSync('docs/flasher/machine-combinations-data.js','utf8'),ctx);
for(const [mode,entries] of Object.entries(ctx.window.MCMachineCombinationData)){
 assert.equal(Object.keys(entries).length,768);
 for(let mask=256;mask<1024;mask++){const v=entries[mask];assert(v);assert.equal(crypto.createHash('sha256').update(JSON.stringify(v.engine)).digest('hex'),v.engine_sha256);assert.equal(v.engine.machine_selection,mask);assert.equal(v.engine.machine_tables,'0x46789000');}
 console.log('PASS 768 pinned recipes',mode);
}
const {open,change}=require('./test_retrosyn_flasher');
(async()=>{const {w,errors}=open();try{await w.MCPerformanceReleaseReady;await new Promise(r=>setTimeout(r,100));change(w,'sample-wizard',true);change(w,'tiny',true);change(w,'acid',true);const a=w.MCFlasherApp;assert(a.chosenTweaks().length);const entry=w.MCMachineCombinationData.wizard[320],saved=entry.engine.id;entry.engine.id+='-corrupt';a.state.fw={stale:true};a.state.buildKey='stale';assert.equal(a.chosenTweaks().length,0);assert.match(a.state.selectionError,/catalogue integrity/);assert.equal(a.state.fw,null);assert.equal(a.state.buildKey,null);entry.engine.id=saved;assert(a.chosenTweaks().length);assert.equal(a.state.selectionError,null);assert.equal(errors.length,0);console.log('PASS invalid recipe caught; stale firmware cleared; valid selection recovers');}finally{w.close()}})().catch(e=>{console.error(e.stack);process.exitCode=1});
