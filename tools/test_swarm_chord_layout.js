// Note123 : regression exacte, sources gardees et selections valides identiques.
process.env.RETROSYN_PAGE=process.env.RETROSYN_PAGE||'docs/flasher-swarm-chord-layout-test';
const release=process.env.RETROSYN_PAGE==='docs/flasher';
const fs=require('fs'),assert=require('node:assert/strict'),{open,change}=require('./test_retrosyn_flasher');
const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),out=release?'build/swarm-chord-release':'build/swarm-chord-layout';fs.mkdirSync(out,{recursive:true});
const cases=['reported','expanded','no-swarm','no-chord','select-all','all-no-midi','diagnostic','with-midi','reported-no-invert'];
(async()=>{for(const name of cases.filter(x=>(!release||x!=='diagnostic')&&(!process.env.LAYOUT_CASE||x===process.env.LAYOUT_CASE))){const{w,errors}=open();try{
 await Promise.all([w.MCInvertTrackReady,w.MCBeatDiagnosticReady]);const a=w.MCFlasherApp,b=w.MCBuilder;w.document.getElementById('super-clear').click();
 if(name==='select-all'||name==='all-no-midi'){w.document.getElementById('select-all').click();if(name==='all-no-midi')change(w,'midi-out-bank',false);}
 else{
  for(const id of ['trig-preview','trig-hold','arp','trigless-dim','lfo-secondary','acid','syntakt','wave-supermodel','sample-wizard','synth-attack','track-filter','usb6','sample-preview','browser-scroll','supermodel-startup',...w.MC_TWEAKS.features.filter(f=>f.cat==='live'&&f.id!=='audio-load-diagnostic').map(f=>f.id)])change(w,id,true);
  for(const code of ['sd','cp','toy','bits','swarm']){const e=w.document.getElementById('eng-'+code);e.checked=name!=='no-swarm'||code!=='swarm';e.dispatchEvent(new w.Event('change',{bubbles:true}));}
  if(name==='expanded')for(const id of ['scramble','scale-gen'])change(w,id,true);
  if(name==='no-chord')change(w,'chord-keys',false);if(name==='reported-no-invert')change(w,'invert-track',false);
  if(name==='with-midi')change(w,'midi-out-bank',true);
 }
 if(release){assert(!w.document.getElementById('feat-audio-load-diagnostic'));assert(!w.document.querySelector('script[src*="diagnostic"]'));}else change(w,'audio-load-diagnostic',name==='diagnostic');
 const fix=w.MCSwarmChordLayout;w.MCSwarmChordLayout=changed=>changed;
 let before;try{before=w.MCMidiBankCompose(a.chosenTweaks(),os,st);}catch(e){w.MCSwarmChordLayout=fix;if(name!=='with-midi')throw e;assert.equal(e.message,'MIDI Bank: unknown machine startup');assert.throws(()=>w.MCMidiBankCompose(a.chosenTweaks(),os,st),err=>err.message===e.message);console.log('PASS separate pre-existing MIDI startup error unchanged by targeted repair');continue;}
 w.MCSwarmChordLayout=fix;const after=w.MCMidiBankCompose(a.chosenTweaks(),os,st);
 const oldChord=before.tweaks.find(t=>t.id==='chord-keys-supermodel'),newChord=after.tweaks.find(t=>t.id==='chord-keys-supermodel');const affected=!!oldChord?.append&&oldChord.append.at!==newChord.append.at;if(['reported','expanded','diagnostic'].includes(name))assert(affected,name+' expected relocation');
 if(affected){assert.throws(()=>b.build(os,w.MC_TWEAKS.device,before.tweaks,{syntakt:st,refMods:before.refMods}),/image ne finit/);const x=before.tweaks.find(t=>t.id==='chord-keys-supermodel'),y=after.tweaks.find(t=>t.id===x.id);assert.notEqual(x.append.at,y.append.at);assert.equal(JSON.stringify(x.append.parts),JSON.stringify(y.append.parts));for(const t of before.tweaks.filter(t=>t.append)){const other=after.tweaks.find(u=>u.id===t.id);assert.equal(JSON.stringify(t.append.parts),JSON.stringify(other.append.parts),name+' voice/payload bytes '+t.id);}console.log('PASS original error reproduced; payload contents unchanged',name,x.append.at,'->',y.append.at);}
 else{fs.writeFileSync(out+'/'+name+'-compare.json',JSON.stringify({before,after}));assert.deepEqual(JSON.parse(JSON.stringify(after.tweaks)),JSON.parse(JSON.stringify(before.tweaks)),name+' existing composition changed');assert.deepEqual(JSON.parse(JSON.stringify(after.refMods)),JSON.parse(JSON.stringify(before.refMods)),name+' references changed');console.log('PASS existing composition/reference equality',name);}
 const built=b.build(os,w.MC_TWEAKS.device,after.tweaks,{syntakt:st,refMods:after.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 if(name==='select-all'){const original=b.build(os,w.MC_TWEAKS.device,before.tweaks,{syntakt:st,refMods:before.refMods});assert.deepEqual(Buffer.from(built.raw),Buffer.from(original.raw));console.log('PASS SELECT ALL SIGNED FIRMWARE BYTE-FOR-BYTE IDENTICAL');}
 fs.writeFileSync(out+'/'+name+'.json',JSON.stringify({tweaks:after.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(out+'/'+name+'.syx',built.raw);assert(!errors.length,errors.join('\n'));console.log('PASS signed firmware',name,built.mainOsSha);
 }finally{w.close()}}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
