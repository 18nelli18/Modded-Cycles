// Note 99 : builds de la carte autonome et des combinaisons du principal.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const main=process.argv.includes('--main')||process.argv.includes('--feedback-main'),feedback=process.argv.includes('--feedback'),feedbackMain=process.argv.includes('--feedback-main');
process.env.RETROSYN_PAGE=feedback?'docs/flasher-performance-feedback-test':main?'docs/flasher':'docs/flasher-beat-repeat-test';
const reference=main?JSON.parse(fs.readFileSync(path.resolve(__dirname,feedbackMain?'../build/performance-feedback/cases.json':'../build/beat-repeat/cases.json'))):null;
const {open,change}=require('./test_retrosyn_flasher');
const dir=path.resolve(__dirname,feedback?'../build/performance-feedback':feedbackMain?'../build/performance-feedback-main':main?'../build/beat-repeat-main':'../build/beat-repeat');fs.mkdirSync(dir,{recursive:true});
const read=name=>Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/'+name)));
const cycles=read('model-cycles_OS1.13.syx'),syntakt=read('Syntakt_OS1.42.syx');
const profiles=[{name:'alone'},{name:'supports',features:['control-all-config','lfo-secondary','scale-gen','scramble']},{name:'wizard-chord',features:['sample-wizard','chord-keys']},{name:'midi',features:['midi-out-bank']},{name:'retrosyn',features:['retrosyn']},{name:'tiny',features:['tiny']},{name:'all',all:true},{name:'all-native',all:true,native:true},{name:'all-boot',all:true,animation:true}];
if(feedback||feedbackMain)profiles.push({name:'midi-alone',midiOnly:true,features:['midi-out-bank']},{name:'midi-supports',midiOnly:true,features:['midi-out-bank','scale-gen','lfo-secondary','scramble']});
(async()=>{const rows=[];for(const p of profiles){const {w,errors}=open();await new Promise(r=>setTimeout(r,40));try{
 const id='control-all-beat-repeat',f=w.MC_TWEAKS.features.find(f=>f.id===id);assert.equal(f.status,main?'tested':'experimental');assert.equal(!!f.hardwareTestedByOwner,main);if(!p.midiOnly)change(w,id,true);
 if(p.all)w.document.getElementById('select-all').click();for(const id of p.features||[])change(w,id,true);if(p.native)change(w,'sample-wizard',false);if(p.animation)change(w,'boot-anim',true);
 if(p.name==='alone')assert.deepEqual(Array.from(w.MC_TWEAKS.features.filter(f=>w.MCFlasherApp.isSelected(f.id)).map(f=>f.id)),[id]);
 if(!p.midiOnly)for(const lang of ['en','fr']){w.MCFlasherApp.applyLang(lang);assert(w.document.getElementById('det-'+id).textContent.includes('TRACK + RETRIG'));}
 const prepared=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),cycles,syntakt),t=prepared.tweaks.find(t=>t.id===id);if(!p.midiOnly){assert.equal(t.status,main?'tested':'experimental');assert(!t.requires.length);}
 if(!p.midiOnly){
 const config=prepared.tweaks.find(t=>t.symbols?.cac_mask),module=w.MCBuilder.fromHex(t.append.parts[0].hex),origin=parseInt(t.append.dest,16);
 assert.equal(new DataView(module.buffer).getUint32(parseInt(t.symbols.br_mask_address,16)-origin,false),config?parseInt(config.symbols.cac_mask,16):0,'Control All mask binding');
 for(const at of [0x40100ee8,0x40100f98])assert(t.writes.some(w=>w.off+0x40000400===at),'priority TRACK view hook');}

 if(feedback){const mf=w.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank');assert.equal(mf.status,'experimental');assert(!mf.hardwareTestedByOwner);const bank=prepared.tweaks.find(t=>t.id==='midi-out-bank');if(bank){assert.equal(bank.status,'experimental');assert(!bank.hardwareTestedByOwner);assert(bank.symbols.ml_feedback_pad);assert.equal(bank.persistence,'MPI1');}if(p.midiOnly)assert(!t,'MIDI seul ne force pas beat repeat');}
 const built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,prepared.tweaks,{syntakt,refMods:prepared.refMods});if(main)assert.equal(built.mainOsSha,reference.find(x=>x.name===p.name).sha,'exact tested firmware');assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 assert(!w.document.getElementById('feat-model-tg'));assert(!w.document.getElementById('feat-lfo-plus'));assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(dir,p.name+'.syx'),built.raw);fs.writeFileSync(path.join(dir,p.name+'.json'),JSON.stringify({tweaks:prepared.tweaks,mainOsSha:built.mainOsSha}));rows.push({name:p.name,sha:built.mainOsSha});console.log('PASS beat repeat browser',p.name,built.mainOsSha);
 }finally{w.close();}}fs.writeFileSync(path.join(dir,'cases.json'),JSON.stringify(rows,null,1));})().catch(e=>{console.error(e.stack);process.exitCode=1});
