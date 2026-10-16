// Note 99 : builds de la carte autonome et des combinaisons du principal.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE='docs/flasher-beat-repeat-test';
const {open,change}=require('./test_retrosyn_flasher');
const dir=path.resolve(__dirname,'../build/beat-repeat');fs.mkdirSync(dir,{recursive:true});
const read=name=>Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/'+name)));
const cycles=read('model-cycles_OS1.13.syx'),syntakt=read('Syntakt_OS1.42.syx');
const profiles=[{name:'alone'},{name:'supports',features:['control-all-config','lfo-secondary','scale-gen','scramble']},{name:'wizard-chord',features:['sample-wizard','chord-keys']},{name:'midi',features:['midi-out-bank']},{name:'retrosyn',features:['retrosyn']},{name:'tiny',features:['tiny']},{name:'all',all:true},{name:'all-native',all:true,native:true},{name:'all-boot',all:true,animation:true}];
(async()=>{const rows=[];for(const p of profiles){const {w,errors}=open();await new Promise(r=>setTimeout(r,40));try{
 const id='control-all-beat-repeat',f=w.MC_TWEAKS.features.find(f=>f.id===id);assert.equal(f.status,'experimental');assert(!f.hardwareTestedByOwner);change(w,id,true);
 if(p.all)w.document.getElementById('select-all').click();for(const id of p.features||[])change(w,id,true);if(p.native)change(w,'sample-wizard',false);if(p.animation)change(w,'boot-anim',true);
 if(p.name==='alone')assert.deepEqual(Array.from(w.MC_TWEAKS.features.filter(f=>w.MCFlasherApp.isSelected(f.id)).map(f=>f.id)),[id]);
 for(const lang of ['en','fr']){w.MCFlasherApp.applyLang(lang);assert(w.document.getElementById('det-'+id).textContent.includes('TRACK + RETRIG'));}
 const prepared=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),cycles,syntakt),t=prepared.tweaks.find(t=>t.id===id);assert.equal(t.status,'experimental');assert(!t.requires.length);
 const config=prepared.tweaks.find(t=>t.symbols?.cac_mask),module=w.MCBuilder.fromHex(t.append.parts[0].hex),origin=parseInt(t.append.dest,16);
 assert.equal(new DataView(module.buffer).getUint32(parseInt(t.symbols.br_mask_address,16)-origin,false),config?parseInt(config.symbols.cac_mask,16):0,'Control All mask binding');
 for(const at of [0x40100ee8,0x40100f98])assert(t.writes.some(w=>w.off+0x40000400===at),'priority TRACK view hook');
 const built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,prepared.tweaks,{syntakt,refMods:prepared.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
 assert(!w.document.getElementById('feat-model-tg'));assert(!w.document.getElementById('feat-lfo-plus'));assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(dir,p.name+'.syx'),built.raw);fs.writeFileSync(path.join(dir,p.name+'.json'),JSON.stringify({tweaks:prepared.tweaks,mainOsSha:built.mainOsSha}));rows.push({name:p.name,sha:built.mainOsSha});console.log('PASS beat repeat browser',p.name,built.mainOsSha);
 }finally{w.close();}}fs.writeFileSync(path.join(dir,'cases.json'),JSON.stringify(rows,null,1));})().catch(e=>{console.error(e.stack);process.exitCode=1});
