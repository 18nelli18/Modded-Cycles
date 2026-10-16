const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
let jsdom;try{jsdom=require('jsdom');}catch{jsdom=require('../build/retrosyn-ui/node_modules/jsdom');}const {JSDOM,VirtualConsole}=jsdom;
const dir=path.resolve(process.env.RETROSYN_PAGE||path.join(__dirname,'../docs/flasher')),out=path.resolve(__dirname,'../build');
function open(){const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');const w=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only',virtualConsole:vc}).window;w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};for(const m of html.matchAll(/<script[^>]+src="([^"]+)"/g))w.eval(fs.readFileSync(path.resolve(dir,m[1].split('?')[0]),'utf8'));return {w,errors};}
function change(w,id,on){const box=w.document.getElementById('feat-'+id);assert(box,id);box.checked=on;box.dispatchEvent(new w.Event('change',{bubbles:true}));}
module.exports={open,change};
if(require.main===module)(async()=>{const cases=[[false,false,false],[false,true,false],[true,false,false],[true,true,false]];if(process.argv.includes('--select-all'))cases.push([true,true,true]);for(const [full,wizard,selectAll] of cases){const {w,errors}=open();await new Promise(r=>setTimeout(r,50));try{
if(w.MCRetrosynTestProfile){w.MCRetrosynTestProfile('solo');change(w,'retrosyn',false);}
assert(!w.document.getElementById('feat-model-tg'));assert(!w.MC_TWEAKS.features.some(f=>f.id==='model-tg'));
if(full){change(w,'syntakt',true);for(const code of ['sd','cp','toy','bits','swarm']){const box=w.document.getElementById('eng-'+code);box.checked=true;box.dispatchEvent(new w.Event('change',{bubbles:true}));}for(const id of ['macro','acid','wave-supermodel','tiny'])change(w,id,true);}
if(wizard)change(w,'sample-wizard',true);change(w,'retrosyn',true);
if(selectAll){w.document.getElementById('select-all').click();change(w,'retrosyn',true);}
const a=w.MCFlasherApp,t=a.chosenTweaks(),expected=full?(wizard?'retrosyn-all-machines-wizard':'retrosyn-all-machines'):(wizard?'retrosyn-wizard':'retrosyn');
assert(t.some(t=>t.id===expected),JSON.stringify(t.map(t=>t.id)));assert.equal(t.some(t=>t.id==='sample-wizard'),wizard);
assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='retrosyn').status,'tested');assert.throws(()=>w.MCBuilder.build(null,null,[{id:'model-tg-st'}]),/Model-TG/);
for(const lang of ['fr','en']){a.applyLang(lang);assert(w.document.getElementById('det-retrosyn').textContent.includes(lang==='fr'?'Combinaisons partielles':'Partial engine'));}
if(full)assert(t.find(t=>t.id===expected).machine_names.includes('TINY'));
if(process.argv.includes('--build')){const raw=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),st=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));const built=w.MCBuilder.build(raw,w.MC_TWEAKS.device,t,{syntakt:st,refMods:a.REF_MODS});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);fs.writeFileSync(path.join(out,expected+(selectAll?'-select-all':'')+'.syx'),built.raw);fs.writeFileSync(path.join(out,expected+(selectAll?'-select-all':'')+'-browser.json'),JSON.stringify({tweaks:t,mainOsSha:built.mainOsSha}));console.log('ok signed browser build',expected,built.mainOsSha);}
assert.equal(errors.length,0,errors.join('\n'));console.log('ok main UI',expected);
}finally{w.close();}}})().catch(e=>{console.error(e.stack);process.exitCode=1;});
