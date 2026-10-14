// Choix réels main, deux payloads B, références strictes et conteneurs validés.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=process.argv[2]+'/',vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const d=w.document,a=w.MCFlasherApp,os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx')),cases=[];
function change(id,on){const e=d.getElementById('feat-'+id);assert(e,id);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
function build(name){const chosen=a.chosenTweaks(),bank=chosen.find(t=>t.id==='midi-bank-bundle');if(bank){assert(bank.a_clear_lfo_undo&&bank.b_clear_lfo_undo&&bank.play_ui);assert(chosen.some(t=>t.id==='model-tg-st'));assert(!chosen.some(t=>t.id==='performance-core'));}
 const key=chosen.map(t=>t.id).join('+'),b=w.MCBuilder.build(os,w.MC_TWEAKS.device,chosen,{syntakt:st,refMods:a.REF_MODS,expectMainOsSha:a.REF_MAINOS[key]});assert(b.modsChecked);assert(w.MCFlasher.verify(b.raw).count>0);
 fs.writeFileSync('work/main-clear-led-browser-'+name+'.json',JSON.stringify({tweaks:chosen}));cases.push({name,key,sha:b.mainOsSha});console.log('PASS',name,b.mainOsSha);}
setTimeout(()=>{try{
 change('lfo-secondary',true);build('lfo-selection');
 d.getElementById('select-all').click();build('select-all');
 change('usb6',false);build('chord-no-usb6');change('chord-keys',false);build('plain-no-usb6');change('usb6',true);build('plain-usb6');
 for(const lang of ['en','fr']){a.applyLang(lang);assert(d.getElementById('mod-midi-bank-bundle').textContent.includes(lang==='en'?'FUNC + PLAY':'FUNC + PLAY'));}
 assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('work/main-clear-led-browser-refs.json',JSON.stringify({cases},null,1));console.log('PASS main TG startup retained, clear/Undo, choices, refs, EN/FR');
}catch(e){console.error(e.stack);process.exitCode=1}finally{w.close()}},50);
