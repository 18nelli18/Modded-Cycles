// Builds reels de la page de sauvegarde ; aucune image officielle publiee.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
const main=process.argv.includes('--main');
process.env.RETROSYN_PAGE=main?'docs/flasher':'docs/flasher-midi-save-current-test';
const {open,change}=require('./test_retrosyn_flasher');
const dir=path.resolve(__dirname,main?'../build/midi-persistence-main':'../build/midi-persistence');fs.mkdirSync(dir,{recursive:true});
const tested=main?JSON.parse(fs.readFileSync(path.resolve(__dirname,'../build/midi-persistence/cases.json'),'utf8')):null;
const read=name=>Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/'+name)));
const cycles=read('model-cycles_OS1.13.syx'),syntakt=read('Syntakt_OS1.42.syx');
const profiles=[{name:'alone'},{name:'supports',features:['scale-gen','lfo-secondary','scramble']},{name:'wizard-chord',features:['sample-wizard','chord-keys']},{name:'all',all:true},{name:'all-native',all:true,native:true}];
(async()=>{const rows=[];for(const p of profiles){
 const {w,errors}=open();await new Promise(r=>setTimeout(r,50));try{
  const feature=w.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank');assert.equal(feature.status,main?'tested':'experimental');assert.equal(!!feature.hardwareTestedByOwner,main);
  change(w,'midi-out-bank',true);if(p.all)w.document.getElementById('select-all').click();for(const id of p.features||[])change(w,id,true);if(p.native)change(w,'sample-wizard',false);
  if(p.name==='alone')assert.equal(JSON.stringify(w.MC_TWEAKS.features.filter(f=>w.MCFlasherApp.isSelected(f.id)).map(f=>f.id)),JSON.stringify(['midi-out-bank']));
  for(const lang of ['en','fr']){w.MCFlasherApp.applyLang(lang);assert(w.document.getElementById('det-midi-out-bank').textContent.includes('MIDI SAVED'));}
  const prepared=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),cycles,syntakt),bank=prepared.tweaks.find(t=>t.id==='midi-out-bank');
  assert.equal(bank.status,main?'tested':'experimental');assert.equal(!!bank.hardwareTestedByOwner,main);assert.equal(bank.persistence,'MPI1');assert(!bank.ram_only_rollback);
  const built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,prepared.tweaks,{syntakt,refMods:prepared.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
  if(main){assert.equal(built.mainOsSha,tested.find(c=>c.name===p.name).sha,'main must equal hardware-tested candidate');for(const lang of ['en','fr']){w.MCFlasherApp.applyLang(lang);const text=w.document.getElementById('det-midi-out-bank').textContent;assert(text.includes(lang==='en'?'only when you enter B-side and only while playback is stopped':'uniquement en entrant cote B et uniquement lorsque la lecture est arretee'));}assert(w.document.getElementById('midi-saving-status'));}
  for(const va of [0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6])assert(bank.writes.some(w=>w.off+0x40000400===va));
  assert(!w.document.getElementById('feat-model-tg'));assert(!w.document.getElementById('feat-lfo-plus'));assert.equal(errors.length,0,errors.join('\n'));
  fs.writeFileSync(path.join(dir,p.name+'.syx'),built.raw);fs.writeFileSync(path.join(dir,p.name+'.json'),JSON.stringify({tweaks:prepared.tweaks,mainOsSha:built.mainOsSha}));
  rows.push({name:p.name,sha:built.mainOsSha,stored:bank.append.stored});console.log('PASS saving browser build',p.name,bank.append.stored,built.mainOsSha);
 }finally{w.close();}
}fs.writeFileSync(path.join(dir,'cases.json'),JSON.stringify(rows,null,1));})().catch(e=>{console.error(e.stack);process.exitCode=1});
