// Note 102 : builds signes, filtre precision seul et combinaisons actuelles.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE='docs/flasher-filter-precision-test';const {open,change}=require('./test_retrosyn_flasher');
const dir=path.resolve(__dirname,'../build/filter-precision');fs.mkdirSync(dir,{recursive:true});
const read=n=>Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/'+n))),cycles=read('model-cycles_OS1.13.syx'),syntakt=read('Syntakt_OS1.42.syx');
const profiles=[{name:'alone'},{name:'supports',features:['scale-gen','lfo-secondary','scramble']},{name:'chord',features:['chord-keys']},{name:'midi',features:['midi-out-bank']},{name:'retrosyn',features:['retrosyn']},{name:'all',all:true},{name:'all-boot',all:true,animation:true},{name:'all-no-midi',all:true,noMidi:true,noRepeat:true},{name:'all-no-repeat',all:true,noRepeat:true}];
(async()=>{const rows=[];for(const p of profiles){const {w,errors}=open();await new Promise(r=>setTimeout(r,50));try{
 change(w,'track-filter',true);if(p.all)w.document.getElementById('select-all').click();for(const id of p.features||[])change(w,id,true);if(p.noMidi)change(w,'midi-out-bank',false);if(p.noRepeat)change(w,'control-all-beat-repeat',false);if(p.animation)change(w,'boot-anim',true);
 assert(w.MCFlasherApp.isSelected('track-filter'));assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='track-filter').status,'experimental');
 const prepared=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),cycles,syntakt);const built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,prepared.tweaks,{syntakt,refMods:prepared.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));assert(!w.document.getElementById('feat-model-tg'));
 fs.writeFileSync(path.join(dir,p.name+'.syx'),built.raw);fs.writeFileSync(path.join(dir,p.name+'.json'),JSON.stringify({tweaks:prepared.tweaks,mainOsSha:built.mainOsSha}));rows.push({name:p.name,sha:built.mainOsSha});console.log('PASS precision browser',p.name,built.mainOsSha);
 }finally{w.close();}}fs.writeFileSync(path.join(dir,'cases.json'),JSON.stringify(rows,null,1));})().catch(e=>{console.error(e.stack);process.exitCode=1;});
