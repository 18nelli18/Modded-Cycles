// Note124 : builds signes, noyau unique et absence d'effet sans MACRO.
process.env.RETROSYN_PAGE='docs/flasher-macro-render-test';
const fs=require('fs'),assert=require('node:assert/strict'),{open,change}=require('./test_retrosyn_flasher');
const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),out='build/macro-render-test';fs.mkdirSync(out,{recursive:true});
(async()=>{for(const name of ['all','no-midi','wizard','minimal','partial','no-macro','diagnostic'].filter(x=>!process.env.MACRO_CASE||x===process.env.MACRO_CASE)){const{w,errors}=open();try{
 await Promise.all([w.MCInvertTrackReady,w.MCBeatDiagnosticReady]);const a=w.MCFlasherApp,b=w.MCBuilder;w.document.getElementById('super-clear').click();
 if(['all','no-midi','no-macro','diagnostic'].includes(name)){w.document.getElementById('select-all').click();if(name==='no-midi')change(w,'midi-out-bank',false);if(name==='no-macro')change(w,'macro',false);}
 else{for(const id of ['macro','latching-mute'])change(w,id,true);if(name!=='minimal')for(const id of ['sample-wizard','lfo-secondary','arp'])change(w,id,true);if(name==='partial')for(const id of ['syntakt','acid','wave-supermodel','chord-keys','synth-attack','track-filter','control-all-beat-repeat'])change(w,id,true);}
 change(w,'audio-load-diagnostic',name==='diagnostic');const optimize=w.MCMacroRenderOptimize;w.MCMacroRenderOptimize=input=>input;const before=w.MCMidiBankCompose(a.chosenTweaks(),os,st);w.MCMacroRenderOptimize=optimize;const after=w.MCMidiBankCompose(a.chosenTweaks(),os,st),d=w.MCMacroHalfband;
 let hits=0;for(const t of after.tweaks)for(const p of t.append?.parts||[])if(p.hex)hits+=p.hex.split(d.hex).length-1;assert.equal(hits,name==='no-macro'?0:1);
 if(name==='no-macro'){assert.deepEqual(JSON.parse(JSON.stringify(after.tweaks)),JSON.parse(JSON.stringify(before.tweaks)));assert.deepEqual(JSON.parse(JSON.stringify(after.refMods)),JSON.parse(JSON.stringify(before.refMods)));}
 for(const [suffix,r]of [['before',before],['after',after]]){const built=b.build(os,w.MC_TWEAKS.device,r.tweaks,{syntakt:st,refMods:r.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);fs.writeFileSync(out+'/'+name+'-'+suffix+'.json',JSON.stringify({tweaks:r.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(out+'/'+name+'-'+suffix+'.syx',built.raw);console.log('PASS signed',name,suffix,built.mainOsSha);}
 if(name==='no-macro')assert.deepEqual(fs.readFileSync(out+'/'+name+'-before.syx'),fs.readFileSync(out+'/'+name+'-after.syx'));
 assert(!errors.length,errors.join('\n'));console.log('PASS MACRO renderer count, selection and references',name);
 }finally{w.close()}}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
