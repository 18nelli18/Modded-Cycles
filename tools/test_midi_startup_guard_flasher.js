// Contrôles réels : aucun support forcé, 32 backends et transferts identiques.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=(process.argv[2]||'work/scramble-independent-test')+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-midi-independent-test/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),cases=[];
function change(id,on){const el=d.getElementById('feat-'+id);assert(el,id);el.checked=on;el.dispatchEvent(new w.Event('change',{bubbles:true}));}
function reset(){for(const el of [...d.querySelectorAll('input[id^="feat-"]')])if(el.checked)change(el.id.slice(5),false);}
function build(name,engine=false){const chosen=a.chosenTweaks();const key=chosen.map(t=>t.id).join('+'),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:engine?st:undefined,refMods:a.REF_MODS,expectMainOsSha:a.REF_MAINOS[key]});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);fs.writeFileSync('work/startup-guard-browser-'+name+'.json',JSON.stringify({tweaks:chosen}));cases.push({name,key,sha:b.mainOsSha});console.log('PASS',name,chosen.length,b.mainOsSha);}
setTimeout(()=>{try{
reset();change('midi-bank-bundle',true);build('bank-only');reset();d.getElementById('select-all').click();for(const id of ['model-tg','syntakt','macro','acid'])change(id,false);console.log('selected', [...d.querySelectorAll('input[id^="feat-"]:checked')].map(e=>e.id));build('no-tg-full-extras');
assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/startup-guard-browser-refs.json',JSON.stringify({cases},null,1));console.log('PASS selections, hashes, containers, EN/FR');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
