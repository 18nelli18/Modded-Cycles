// Vrais contrôles du candidat : Chord seul, TG facultatif et machines facultatives.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=(process.argv[2]||'work/chord-independent-test')+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-chord-independent-test/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),cases=[];
function change(id,on){const e=d.getElementById('feat-'+id);assert(e,id);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
function build(name,syntakt=false){const chosen=a.chosenTweaks(),key=chosen.map(t=>t.id).join('+'),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:syntakt?st:undefined,refMods:a.REF_MODS,expectMainOsSha:a.REF_MAINOS[key]});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);cases.push({name,key,sha:b.mainOsSha});fs.writeFileSync('work/chord-independent-'+name+'-catalog.json',JSON.stringify({tweaks:chosen}));console.log('PASS',name,chosen.length,b.mainOsSha);return chosen;}
setTimeout(()=>{try{
change('chord-keys',true);let chosen=build('alone');assert.equal(chosen.length,1);assert(!d.getElementById('feat-model-tg').checked);assert(!d.getElementById('feat-midi-bank-bundle').checked);
change('model-tg',true);chosen=build('tg');assert.equal(chosen.length,2);change('model-tg',false);
change('macro',true);build('macro');change('macro',false);assert(d.getElementById('feat-chord-keys').checked);
change('acid',true);build('acid');change('acid',false);
change('syntakt',true);build('syntakt',true);change('syntakt',false);
change('midi-bank-bundle',true);chosen=build('bank-core');assert(!chosen.some(t=>/syntakt|macro|acid/.test(t.id)));
d.getElementById('select-all').click();build('bank-full',true);
change('midi-bank-bundle',false);build('tg-full',true);
change('model-tg',false);build('full-no-tg',true);
for(const lang of ['en','fr']){a.applyLang(lang);assert(d.getElementById('mod-chord-keys').textContent.includes(lang==='en'?'independent':'indépendant'));}
assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/chord-independent-refs.json',JSON.stringify({cases},null,1));console.log('PASS independent UI, reference hashes, containers, languages');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
