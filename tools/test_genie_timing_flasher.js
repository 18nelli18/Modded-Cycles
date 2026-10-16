// Note 103 : compositions navigateur signees et absence de modification sans Genie.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE=process.env.GENIE_TIMING_BASELINE?'docs/flasher':'docs/flasher-genie-timing-test';
const {open,change}=require('./test_retrosyn_flasher'),out=path.resolve(__dirname,'../build/genie-timing'+(process.env.GENIE_TIMING_BASELINE?'-baseline':''));fs.mkdirSync(out,{recursive:true});
const raw=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));
(async()=>{for(const p of [{name:'audio',sg:true},{name:'midi',sg:true,midi:true},{name:'wizard',sg:true,midi:true,wizard:true},{name:'all',all:true,sg:true,midi:true},{name:'no-genie',midi:true}]){
 const {w,errors}=open();await new Promise(r=>setTimeout(r,30));try{
 if(p.all)w.document.getElementById('select-all').click();else{if(p.sg)change(w,'scale-gen',true);if(p.midi)change(w,'midi-out-bank',true);if(p.wizard)change(w,'sample-wizard',true);}
 const result=w.MCMidiBankCompose(w.MCFlasherApp.chosenTweaks(),raw,st),bank=result.tweaks.find(t=>t.id==='midi-out-bank');
 if(bank)assert.equal(!!bank.symbols.genie_timing_boundary,!!p.sg&&!process.env.GENIE_TIMING_BASELINE);
 const built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,result.tweaks,{syntakt:st,refMods:result.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(out,p.name+'.json'),JSON.stringify({tweaks:result.tweaks,mainOsSha:built.mainOsSha}));fs.writeFileSync(path.join(out,p.name+'.syx'),built.raw);console.log('PASS timing browser',p.name,built.mainOsSha);
 }finally{w.close();}
}})().catch(e=>{console.error(e.stack);process.exitCode=1});
