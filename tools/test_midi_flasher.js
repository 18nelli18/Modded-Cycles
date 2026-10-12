// Note 57 : installateur sélectionnable, fichiers OS locaux et build navigateur exact.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'docs/flasher-midi-test');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 const dom=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher-midi-test/',runScripts:'outside-only',virtualConsole:vc});
 const w=dom.window,doc=w.document;
 Object.defineProperty(w,'isSecureContext',{value:true});
 w.localStorage.setItem('mc-method','slow');
 w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 for(const file of ['builder.js','tweaks.js','flasher.js'])w.eval(fs.readFileSync(path.join(root,'docs/flasher',file),'utf8'));
 for(const file of ['bundle.js','app.js'])w.eval(fs.readFileSync(path.join(dir,file),'utf8'));
 await wait(25);
 const app=w.MCFlasherApp,tw=w.MC_TWEAKS;
 assert(app&&tw);
 assert.strictEqual(app.state.method,'slow');app.setMethod('fast');assert.strictEqual(app.state.method,'fast');
 assert.notStrictEqual(w.getComputedStyle(doc.getElementById('step-choose')).display,'none');
 assert.notStrictEqual(w.getComputedStyle(doc.getElementById('m-slow')).display,'none');
 for(const id of ['file','file3','allow','port','flash'])assert(doc.getElementById(id),id);
 assert(html.includes('bundle.js?v=2026-10-11-midi-bank-main-flasher'));
 // Identité du transport avec main, sans copie expérimentale ni réglage spécial.
 assert(html.includes('../flasher/flasher.js?v='));
 assert(!fs.existsSync(path.join(dir,'flasher.js')));
 const mainApp=fs.readFileSync(path.join(root,'docs/flasher/app.js'),'utf8');
 const testApp=fs.readFileSync(path.join(dir,'app.js'),'utf8');
 // Les textes de carte sont ajoutés juste avant init, donc comparer jusqu’à setMethod.
 const methods=text=>text.slice(text.indexOf('async function flash()'),text.indexOf('function init()')).split('FEAT.en["midi-bank-bundle"]')[0];
 assert.strictEqual(methods(testApp).trim(),methods(mainApp).trim());
 assert.strictEqual(app.chosenTweaks().length,0);
 const choose=()=>{const box=doc.getElementById('feat-midi-bank-bundle');assert(box);box.checked=true;box.dispatchEvent(new w.Event('change',{bubbles:true}));};
 choose();
 const selected=Array.from(app.chosenTweaks(),t=>t.id);
 assert.deepStrictEqual(selected,Array.from(w.MC_BUNDLE_IDS));
 for(const id of ['model-tg-st','midi-live-both','lfo-secondary','scale-gen-st-queued','scramble-st-gen-queued','midi-bank-bundle'])assert(selected.includes(id),id);
 assert(!selected.includes('midi-both'));
 for(const lang of ['en','fr']){
  app.applyLang(lang);
  assert(doc.getElementById('mod-midi-bank-bundle').textContent.includes('RAM'));
  assert(app.chosenLabels().some(text=>text.includes(lang==='en'?'MIDI OUT Bank':'Banque MIDI OUT')));
 }
 const raw=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/model-cycles_OS1.13.syx')));
 const syntakt=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/Syntakt_OS1.42.syx')));
 app.loadOs(raw,'model-cycles_OS1.13.syx');assert(!app.state.fw);
 app.loadSyntakt(syntakt,'Syntakt_OS1.42.syx');
 for(let n=0;n<100&&(!app.state.fw||app.state.building);n++)await wait(100);
 assert(app.state.fw,app.state.fwError);
 assert(app.state.fw.ref&&app.state.fw.modsRef);
 assert.strictEqual(app.state.fw.sha,app.REF_MAINOS[selected.join('+')]);
 const verified=w.MCFlasher.verify(app.state.fw.raw);assert(verified.count>0);
 // Les choix modifient réellement le build ; banque seulement pour son bundle validé.
 const initial=app.state.fw;
 const box=doc.getElementById('feat-midi-bank-bundle');
 box.checked=false;box.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(!app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert(app.state.fw&&app.state.fw.sha!==initial.sha);
 let lfo=doc.getElementById('feat-lfo-secondary');assert(lfo);
 lfo.checked=false;lfo.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(!app.chosenTweaks().some(t=>t.id==='lfo-secondary'));
 choose();
 assert.deepStrictEqual(Array.from(app.chosenTweaks(),t=>t.id),selected);
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert.strictEqual(app.state.fw.sha,initial.sha);
 // Un changement incompatible enlève automatiquement la banque.
 lfo=doc.getElementById('feat-lfo-secondary');
 lfo.checked=false;lfo.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(!app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
 assert(!app.chosenLabels().some(text=>text.includes('Banque MIDI OUT')));
 for(let n=0;n<100&&(!app.state.fw||app.state.building);n++)await wait(100);
 assert(app.state.fw,app.state.fwError);
 app.setMethod('slow');assert.strictEqual(app.state.method,'slow');
 assert.notStrictEqual(w.getComputedStyle(doc.getElementById('alt')).display,'none');
 // Le chargement suit aussi le comportement de main pour un OS modifié.
 app.loadOs(initial.raw,'already-modded.syx');assert(app.state.os&&!app.state.os.stock);
 assert.strictEqual(errors.length,0,errors.join('\n'));
 console.log('ok : sélections effectives, banque optionnelle validée avec TG/Live MIDI/LFO 2, EN/FR et limites RAM ; transferts rapide/classique et téléchargement');
 console.log('ok : vrai build navigateur, chaque mod et SHA MAIN OS vérifiés, conteneur signé valide ; comportement de chargement identique à main');
 dom.window.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
