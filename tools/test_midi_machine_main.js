// Preset MIDI complet : vrai flasheur, signature et sauvegarde du cas pour boot natif.
const fs=require('fs'),assert=require('node:assert/strict');process.env.RETROSYN_PAGE='docs/flasher';const{open}=require('./test_retrosyn_flasher');
(async()=>{for(const usb of [true,false]){const{w,errors}=open();try{
 await w.MCMidiMachineAllReady;const a=w.MCFlasherApp;const toggle=w.document.getElementById('fixed-six-usb');toggle.checked=usb;toggle.dispatchEvent(new w.Event('change',{bubbles:true}));assert.equal(a.isSelected('usb6'),usb);assert(a.isSelected('supermodel-startup'));assert(!a.isSelected('boot-anim'));assert(!a.isSelected('midi-out-bank'));
 assert.equal(a.chosenEngines().filter(e=>['sd','cp','toy','bits','swarm'].includes(e.code)).length,5);assert.equal(w.document.getElementById('drop3-wrap').hidden,false);assert.equal(w.document.getElementById('file3').type,'file');const tweaks=a.chosenTweaks();assert(!a.state.selectionError,a.state.selectionError);assert(tweaks.some(t=>t.machine_selection===1023),JSON.stringify({errors,labels:a.chosenLabels(),machines:tweaks.filter(t=>t.machine_selection!==undefined).map(t=>t.machine_selection)}));
 const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
 const p=w.MCMidiBankCompose(tweaks,os,st);assert(!p.tweaks.some(t=>t.id==='midi-out-bank'));assert(p.tweaks.some(t=>t.id==='midi-out-machine'));assert(!p.tweaks.some(t=>t.symbols?.br_load_address));assert(!p.tweaks.some(t=>t.id==='audio-load-diagnostic'));assert(!p.tweaks.some(t=>t.id==='macro-fine-test'));assert(!w.MCMacroFineReady);assert(p.tweaks.some(t=>t.id==='supermodel-startup'));assert.equal(p.tweaks.some(t=>t.id==='6ch-usbup'),usb);
 const built=w.MCBuilder.build(os,w.MC_TWEAKS.device,p.tweaks,{syntakt:st,refMods:p.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 fs.mkdirSync('build/midi-machine/all',{recursive:true});fs.writeFileSync('build/midi-machine/all/main-'+(usb?'usb':'standard')+'.json',JSON.stringify({tweaks:p.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync('build/midi-machine/all/main-'+(usb?'usb':'standard')+'.syx',built.raw);
 assert(a.chosenLabels().includes('MIDI Out machine'));assert(!w.document.getElementById('feat-midi-out-bank'));
 a.loadOs(os,'model-cycles_OS1.13.syx');assert.equal(a.state.fwError,'needs_syntakt');assert(!a.state.fw);a.loadSyntakt(st,'Syntakt_OS1.42.syx');
 for(let tries=0;(!a.state.fw||a.state.building)&&tries<300;tries++)await new Promise(r=>setTimeout(r,100));
 assert(a.state.fw,a.state.fwError);assert.equal(a.state.fw.sha,built.mainOsSha);assert(w.document.getElementById('flash').disabled);
 assert(w.document.getElementById('feat-midi-out-machine').disabled);assert(w.document.getElementById('select-all').disabled);
 console.log('PASS upload OS+Syntakt dans vraie UI, meme firmware, preset verrouille, aucun transfert automatique');
 assert.equal(errors.length,0,errors.join('\n'));console.log('PASS principal fixe sans banque B ni diagnostic, Supermodel, USB '+usb+', signature',built.mainOsSha,p.tweaks.map(t=>t.id).join(','));
}finally{w.close();}}})().catch(e=>{console.error(e.stack);process.exitCode=1;});
