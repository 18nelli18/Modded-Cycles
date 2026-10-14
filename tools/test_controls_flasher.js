const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const dir=(process.argv[2]||'docs/flasher-controls-test').replace(/\/?$/,'/'),vc=new VirtualConsole(),errors=[];vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-controls-test/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const app=w.MCFlasherApp,d=w.document,cycles=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),syntakt=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
const change=(id,on)=>{const e=d.getElementById('feat-'+id);assert(e,id);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));};
const refs={},cases=[];
function buildCase(name){const chosen=app.chosenTweaks(),built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,chosen,{syntakt,refMods:app.REF_MODS});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);const key=chosen.map(t=>t.id).join('+');refs[key]=built.mainOsSha;cases.push({name,key,sha:built.mainOsSha,size:built.raw.length});console.log('PASS '+name+' '+built.mainOsSha);return {chosen,built};}
setTimeout(()=>{try{
 assert.equal(w.MC_TWEAKS.features.length,26);assert(!d.getElementById('feat-midi-both'));
 change('lfo-secondary',true);assert(!d.getElementById('feat-midi-bank-bundle').checked);buildCase('lfo-without-bank');
 change('lfo-secondary',false);change('control-all-config',true);buildCase('control-all-alone');change('control-all-config',false);d.getElementById('select-all').click();assert(d.getElementById('feat-control-all-config').checked);assert(d.getElementById('feat-chord-keys').checked);assert(d.getElementById('feat-model-tg').checked);assert(d.getElementById('feat-midi-bank-bundle').checked);
 const full=buildCase('full-with-ChordKeys');assert(full.chosen.some(t=>t.id==='chord-keys-supermodel'));const fullSnapshot=JSON.parse(JSON.stringify(full.chosen));
 const bank=full.chosen.find(t=>t.id==='midi-bank-bundle');assert(bank.ram_only_rollback);assert(!bank.writes.some(x=>[0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6].includes(0x40000400+x.off)));
 change('usb6',false);buildCase('full-noUSB6');change('chord-keys',false);buildCase('full-noChord-noUSB6');change('usb6',true);buildCase('full-noChord-USB6');
 for(const L of ['en','fr']){app.applyLang(L);assert(d.getElementById('mod-chord-keys').textContent.includes('Model-TG'));assert(!d.getElementById('feat-midi-both'));}
 fs.writeFileSync(process.argv[3]||'/private/tmp/supermodel-controls-refs.json',JSON.stringify({refs,cases},null,2));
 assert.equal(errors.length,0,errors.join('\n'));console.log('PASS EN/FR, all choices, RAM-only, hash references and full containers');
}finally{w.close();}},50);
