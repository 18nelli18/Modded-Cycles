// Note 105 : filtre avec et sans Banque, les gros choix gardent beat repeat.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');process.env.RETROSYN_PAGE='docs/flasher-filter-load-test';
const {open,change}=require('./test_retrosyn_flasher'),out=path.resolve(__dirname,'../build/filter-load');fs.mkdirSync(out,{recursive:true});
const raw=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));
(async()=>{const rows=[];for(const p of [{name:'alone'},{name:'midi',midi:true},{name:'all-midi',all:true,midi:true},{name:'all-no-midi',all:true},{name:'all-no-midi-boot',all:true,boot:true},{name:'no-filter',all:true,midi:true,noFilter:true},{name:'all-midi-no-repeat',all:true,midi:true,noRepeat:true},{name:'all-no-midi-no-repeat',all:true,noRepeat:true}]){
 const {w,errors}=open();await new Promise(r=>setTimeout(r,30));try{
 if(p.all)w.document.getElementById('select-all').click();else change(w,'track-filter',true);change(w,'midi-out-bank',!!p.midi);if(p.boot)change(w,'boot-anim',true);if(p.noFilter)change(w,'track-filter',false);if(p.noRepeat)change(w,'control-all-beat-repeat',false);
 assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='track-filter').status,'experimental');assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank').status,'experimental');
 const result=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),raw,st),built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,result.tweaks,{syntakt:st,refMods:result.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));
 assert.equal(result.tweaks.some(t=>t.id==='midi-out-bank'),!!p.midi);if(p.all)assert.equal(result.tweaks.some(t=>t.id==='control-all-beat-repeat'),!p.noRepeat);
 fs.writeFileSync(path.join(out,p.name+'.json'),JSON.stringify({tweaks:result.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(path.join(out,p.name+'.syx'),built.raw);rows.push({name:p.name,sha:built.mainOsSha});console.log('PASS filter load',p.name,built.mainOsSha);
 }finally{w.close();}
}fs.writeFileSync(path.join(out,'cases.json'),JSON.stringify(rows));})().catch(e=>{console.error(e.stack);process.exitCode=1});
