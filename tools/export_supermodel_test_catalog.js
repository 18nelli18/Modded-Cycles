// Exporter les choix réels du flasher et prouver les deux exclusions visuelles.
const fs=require('fs'),assert=require('assert'),{JSDOM}=require('jsdom');
const [dir,target]=process.argv.slice(2);
const dom=new JSDOM(fs.readFileSync(dir+'/index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-midi-cc-save-test/',runScripts:'outside-only'}),w=dom.window,d=w.document;
w.navigator.requestMIDIAccess=async()=>{throw Error('not connected')};w.URL.createObjectURL=()=> 'blob:test';
for(const name of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js'])w.eval(fs.readFileSync(dir+'/'+name,'utf8'));
setTimeout(()=>{try{
const app=w.MCFlasherApp,click=id=>d.getElementById('feat-'+id).click();
d.getElementById('select-all').click();
let chosen=app.chosenTweaks();assert.deepStrictEqual(Array.from(chosen,t=>t.id),Array.from(w.MC_BUNDLE_IDS));assert(chosen.some(t=>t.id==='supermodel-startup'));assert(!chosen.some(t=>t.id==='boot-anim'));
assert(chosen.some(t=>t.id==='midi-bank-bundle'));assert(!chosen.find(t=>t.id==='midi-bank-bundle').requires.includes('boot-anim'));
click('boot-anim');assert(!app.chosenTweaks().some(t=>t.id==='supermodel-startup'));assert(app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
click('supermodel-startup');assert(!app.chosenTweaks().some(t=>t.id==='boot-anim'));
for(const lang of ['en','fr']){app.applyLang(lang);assert(d.getElementById('mod-supermodel-startup').textContent.includes('by A.V.'));}
d.getElementById('select-all').click();chosen=app.chosenTweaks();
const materialized=chosen.map(t=>{const copy={...t};if(t.append)copy.append={...t.append,compress_depth:t.append.compress_depth,compress_cost:t.append.compress_cost};return copy;});
fs.writeFileSync(target,JSON.stringify({device:w.MC_TWEAKS.device,tweaks:materialized},null,1)+'\n');
console.log('ok : Select All préfère SUPERMODEL ; ancien/nouveau exclusifs ; banque reste sélectionnée ; EN/FR');dom.window.close();
}catch(e){console.error(e);process.exitCode=1;dom.window.close();}},50);
