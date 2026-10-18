// Note124 : parite signee test confirme/principal, diagnostic absent.
const fs=require('fs'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE='docs/flasher';
const {open,change}=require('./test_retrosyn_flasher');
const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
(async()=>{for(const name of ['all','no-midi','wizard','minimal','partial','no-macro']){const {w,errors}=open();try{
 await w.MCInvertTrackReady;
 assert(!w.MC_TWEAKS.features.some(f=>f.id==='audio-load-diagnostic'));
 assert(!w.document.querySelector('script[src*="diagnostic"]'));
 const a=w.MCFlasherApp;w.document.getElementById('super-clear').click();
 if(['all','no-midi','no-macro'].includes(name)){w.document.getElementById('select-all').click();if(name==='no-midi')change(w,'midi-out-bank',false);if(name==='no-macro')change(w,'macro',false);}
 else{for(const id of ['macro','latching-mute'])change(w,id,true);if(name!=='minimal')for(const id of ['sample-wizard','lfo-secondary','arp'])change(w,id,true);if(name==='partial')for(const id of ['syntakt','acid','wave-supermodel','chord-keys','synth-attack','track-filter','control-all-beat-repeat'])change(w,id,true);}
 const r=w.MCMidiBankCompose(a.chosenTweaks(),os,st),built=w.MCBuilder.build(os,w.MC_TWEAKS.device,r.tweaks,{syntakt:st,refMods:r.refMods});
 assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 assert.deepEqual(Buffer.from(built.raw),fs.readFileSync('build/macro-render-test/'+name+'-after.syx'),name+' differe du test confirme');
 assert(!r.tweaks.some(t=>t.symbols?.br_load_address),'diagnostic firmware absent');
 assert(!errors.length,errors.join('\n'));console.log('PASS signed main equals confirmed test; no diagnostics',name,built.mainOsSha);
 }finally{w.close();}}})().catch(e=>{console.error(e.stack);process.exitCode=1});
