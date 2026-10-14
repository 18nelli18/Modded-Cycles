// Note78 : vrais choix UI, dépendances minimales et builds sans OS Syntakt.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=(process.argv[2]||'docs/flasher-controls-test')+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-controls-test/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),syntakt=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
function change(id,on){const e=d.getElementById('feat-'+id);assert(e,id);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
const cases=[],refs={};function build(name,st=false){const chosen=a.chosenTweaks(),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:st?syntakt:undefined,refMods:a.REF_MODS});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);const key=chosen.map(t=>t.id).join('+');refs[key]=b.mainOsSha;cases.push({name,key,sha:b.mainOsSha});console.log('PASS',name,b.mainOsSha);fs.writeFileSync('work/optional-'+name+'-catalog.json',JSON.stringify({tweaks:chosen}));return chosen;}
setTimeout(()=>{try{
change('midi-bank-bundle',true);let chosen=build('stock-core');assert(!chosen.some(t=>/syntakt|macro|acid/.test(t.id)));assert(!d.getElementById('feat-chord-keys').checked);assert(!d.getElementById('feat-usb6').checked);assert.equal(chosen.length,6);
change('macro',true);build('macro');change('acid',true);build('macro-acid');change('macro',false);build('acid');change('acid',false);change('syntakt',true);build('syntakt',true);
d.getElementById('select-all').click();build('full-chord',true);change('chord-keys',false);build('full',true);change('syntakt',false);change('macro',false);change('acid',false);build('stock-extras');
for(const lang of ['en','fr']){a.applyLang(lang);assert(d.getElementById('mod-midi-bank-bundle').textContent.includes(lang==='en'?'optional':'facultatifs'));}
assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/optional-refs.json',JSON.stringify({refs,cases},null,1));console.log('PASS optional machines, core UI, language, source hashes and containers');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
