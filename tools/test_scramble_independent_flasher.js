// Contrôles réels : aucun support forcé, 32 backends et transferts identiques.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=(process.argv[2]||'work/scramble-independent-test')+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-midi-independent-test/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),cases=[];
function change(id,on){const el=d.getElementById('feat-'+id);assert(el,id);el.checked=on;el.dispatchEvent(new w.Event('change',{bubbles:true}));}
function reset(){for(const el of [...d.querySelectorAll('input[id^="feat-"]')])if(el.checked)change(el.id.slice(5),false);}
function build(name,engine=false){const chosen=a.chosenTweaks();const key=chosen.map(t=>t.id).join('+'),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:engine?st:undefined,refMods:a.REF_MODS,expectMainOsSha:a.REF_MAINOS[key]});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);fs.writeFileSync('work/scramble-independent-browser-'+name+'.json',JSON.stringify({tweaks:chosen}));cases.push({name,key,sha:b.mainOsSha});console.log('PASS',name,chosen.length,b.mainOsSha);}
setTimeout(()=>{try{
const ids=['model-tg','scale-gen','lfo-secondary','scramble','chord-keys'];
for(let bits=0;bits<(process.env.MIDI_ONLY_ENGINE?0:32);bits++){reset();change('midi-bank-bundle',true);const key=bits.toString(2).padStart(5,'0');for(let i=0;i<5;i++)if(key[i]==='1')change(ids[i],true);
 const selected=[...d.querySelectorAll('input[id^="feat-"]:checked:not(:disabled)')].map(e=>e.id.slice(5));assert.deepEqual(new Set(selected),new Set(['midi-bank-bundle',...ids.filter((id,i)=>key[i]==='1')]));build(key);}
for(const key of (process.env.MIDI_ONLY_ENGINE?['10000']:['00000','00001','01110','01111','10000','10001','11110','11111'])){reset();change('midi-bank-bundle',true);for(let i=0;i<5;i++)if(key[i]==='1')change(ids[i],true);change('syntakt',true);change('macro',true);change('acid',true);build(key+'-engines',true);}
for(const chord of [false,true])for(const engines of [false,true]){reset();change('scramble',true);if(chord)change('chord-keys',true);assert(!d.getElementById('feat-model-tg').checked);assert(!d.getElementById('feat-midi-bank-bundle').checked);if(engines){change('syntakt',true);change('macro',true);change('acid',true);}assert(!d.getElementById('feat-model-tg').checked);build('scramble-'+(chord?'chord':'alone')+(engines?'-engines':''),engines);}
for(const ids of [['scramble','model-tg'],['scramble','model-tg','chord-keys'],['scramble','scale-gen'],['scramble','scale-gen','chord-keys']]){reset();for(const id of ids)change(id,true);assert(!d.getElementById('feat-midi-bank-bundle').checked);build('legacy-'+ids.join('-'));}
reset();change('model-tg',true);assert(!d.getElementById('feat-midi-bank-bundle').checked);build('tg-only');reset();change('chord-keys',true);assert(!d.getElementById('feat-midi-bank-bundle').checked);assert(!d.getElementById('feat-model-tg').checked);build('chord-only');
reset();change('midi-bank-bundle',true);change('lfo-plus',true);assert(!d.getElementById('feat-midi-bank-bundle').checked);change('midi-bank-bundle',true);assert(!d.getElementById('feat-lfo-plus').checked);
reset();d.getElementById('select-all').click();build('select-all',true);
for(const lang of ['en','fr']){a.applyLang(lang);assert(d.getElementById('mod-midi-bank-bundle').textContent.includes(lang==='en'?'independent':'indépendant'));}
assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/scramble-independent-browser-refs.json',JSON.stringify({cases},null,1));console.log('PASS selections, hashes, containers, EN/FR');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
