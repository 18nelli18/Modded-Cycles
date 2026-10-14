// Choix réels main, deux payloads B, références strictes et conteneurs validés.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=process.argv[2]+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
assert(w.MC_TWEAKS.features.find(f=>f.id==='midi-bank-bundle').desc.includes('both LFOs'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),cases=[];
function change(id,on){const e=d.getElementById('feat-'+id);assert(e,id);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
function build(name){const chosen=a.chosenTweaks(),bank=chosen.find(t=>t.id==='midi-bank-bundle');if(bank){assert(bank.a_clear_lfo_undo&&bank.b_clear_lfo_undo&&bank.play_ui);assert(chosen.some(t=>t.id==='model-tg-st'));assert(!chosen.some(t=>t.id==='performance-core'));}
 const key=chosen.map(t=>t.id).join('+'),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:st,refMods:a.REF_MODS,expectMainOsSha:a.REF_MAINOS[key]});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);
 fs.writeFileSync('work/main-chord-optional-browser-'+name+'.json',JSON.stringify({tweaks:chosen}));cases.push({name,key,sha:b.mainOsSha});console.log('PASS',name,b.mainOsSha);}
setTimeout(()=>{try{
change('chord-keys',true);let chosen=a.chosenTweaks();assert(chosen.some(t=>t.id==='model-tg-st'));assert(!d.getElementById('feat-midi-bank-bundle').checked);assert(!d.getElementById('feat-syntakt').checked);assert(!d.getElementById('feat-macro').checked);assert(!d.getElementById('feat-acid').checked);build('chord-tg-only');
for(const id of ['macro','acid','syntakt']){change(id,true);build('chord-tg-'+id);change(id,false);assert(d.getElementById('feat-chord-keys').checked);}
change('lfo-secondary',true);change('scale-gen',true);change('scramble',true);build('chord-tg-performance');
d.getElementById('select-all').click();build('select-all');change('midi-bank-bundle',false);build('select-all-without-bank');change('midi-bank-bundle',true);build('bank-restored');change('chord-keys',false);build('bank-no-chord');
for(const lang of ['en','fr']){a.applyLang(lang);const f=w.MC_TWEAKS.features.find(f=>f.id==='chord-keys');assert(f.desc.includes(lang==='en'?'does not require MIDI Bank':'sans imposer Banque MIDI'));}
assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/main-chord-optional-browser-refs.json',JSON.stringify({cases},null,1));console.log('PASS TG retained; no implicit Bank/machines; strict refs; existing Bank clear/LED retained');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
