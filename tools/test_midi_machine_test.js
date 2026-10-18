// Note126 : vraie page et construction signee du prototype isole.
const fs=require('fs'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE='docs/flasher-midi-machine-test';
const {open,change}=require('./test_retrosyn_flasher');
(async()=>{const {w,errors}=open();try{
 await new Promise(r=>setTimeout(r,100));
 assert.equal(w.MC_TWEAKS.features.length,1);assert(!w.document.querySelector('script[src*="midi-bank"]'));
 change(w,'midi-machine-core',true);const a=w.MCFlasherApp,chosen=a.chosenTweaks();assert.equal(chosen.length,1);
 const raw=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx'));
 const built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,chosen,{refMods:a.REF_MODS});
 assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 a.loadOs(raw,'model-cycles_OS1.13.syx');await new Promise(r=>setTimeout(r,100));
 assert(!a.state.fwError,a.state.fwError);assert(a.state.fw,'page did not prepare firmware');
 assert.deepEqual(Buffer.from(a.state.fw.raw),Buffer.from(built.raw));
 fs.writeFileSync('build/midi-machine/live-test.syx',built.raw);
 fs.writeFileSync('build/midi-machine/live-test-browser.json',JSON.stringify({mainOsSha:built.mainOsSha,tweaks:chosen}));
 assert(!errors.length,errors.join('\n'));console.log('PASS isolated browser page and signed build',built.mainOsSha);
 }finally{w.close();}})().catch(e=>{console.error(e.stack);process.exitCode=1});
