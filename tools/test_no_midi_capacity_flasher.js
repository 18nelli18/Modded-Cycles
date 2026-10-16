// Note 104 : toutes machines sans Banque ; les selections plus petites restent identiques.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE=process.env.CAPACITY_PAGE||(process.env.CAPACITY_BASELINE?'docs/flasher':'docs/flasher-no-midi-capacity-test');
const {open,change}=require('./test_retrosyn_flasher'),out=path.resolve(__dirname,'../build',process.env.CAPACITY_OUT||('no-midi-capacity'+(process.env.CAPACITY_BASELINE?'-baseline':'')));fs.mkdirSync(out,{recursive:true});
const raw=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));
(async()=>{const rows=[];for(const p of [{name:'all-no-midi',all:true},{name:'all-no-midi-boot',all:true,boot:true},{name:'all-no-midi-no-retrosyn',all:true,noRetro:true},{name:'all-no-wizard',all:true,noWizard:true},{name:'all-midi',all:true,midi:true},{name:'alone'}]){
 const {w,errors}=open();await new Promise(r=>setTimeout(r,30));try{
 if(p.all)w.document.getElementById('select-all').click();else change(w,'control-all-beat-repeat',true);
 if(!p.midi)change(w,'midi-out-bank',false);if(p.boot)change(w,'boot-anim',true);if(p.noRetro)change(w,'retrosyn',false);if(p.noWizard)change(w,'sample-wizard',false);
 let result;try{result=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),raw,st);}catch(e){if(process.env.CAPACITY_BASELINE&&String(e).includes('Beat repeat: payload capacity')){console.log('REPRO baseline capacity',p.name);continue;}throw e;}
 assert.equal(result.tweaks.some(t=>t.id==='midi-out-bank'),!!p.midi);assert(result.tweaks.some(t=>t.id==='control-all-beat-repeat'));
 if(process.env.CAPACITY_PAGE==='docs/flasher'){assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank').status,'experimental');if(p.midi)assert.equal(result.tweaks.find(t=>t.id==='midi-out-bank').status,'experimental');}
 const built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,result.tweaks,{syntakt:st,refMods:result.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(out,p.name+'.json'),JSON.stringify({tweaks:result.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(path.join(out,p.name+'.syx'),built.raw);rows.push({name:p.name,sha:built.mainOsSha});console.log('PASS capacity',p.name,built.mainOsSha);
 }finally{w.close();}
}fs.writeFileSync(path.join(out,'cases.json'),JSON.stringify(rows));})().catch(e=>{console.error(e.stack);process.exitCode=1});
