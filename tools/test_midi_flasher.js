// Note 57 : installateur fixe, fichiers OS locaux et build navigateur exact.
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
 assert.strictEqual(app.state.method,'fast');app.setMethod('slow');assert.strictEqual(app.state.method,'fast');
 assert.strictEqual(w.getComputedStyle(doc.getElementById('step-choose')).display,'none');
 assert.strictEqual(w.getComputedStyle(doc.getElementById('m-slow')).display,'none');
 for(const id of ['file','file3','allow','port','flash'])assert(doc.getElementById(id),id);
 assert(html.includes('bundle.js?v=2026-10-11-midi-bank-tg-first-test'));
 const selected=Array.from(app.chosenTweaks(),t=>t.id);
 assert.deepStrictEqual(selected,Array.from(w.MC_BUNDLE_IDS));
 for(const id of ['model-tg-st','midi-live-both','lfo-secondary','scale-gen-st-queued','scramble-st-gen-queued','midi-bank-bundle'])assert(selected.includes(id),id);
 assert(!selected.includes('midi-both'));
 for(const lang of ['en','fr']){
  app.applyLang(lang);
  const notice=doc.querySelector('#midi-bank-notice [data-l="'+lang+'"]');assert(notice);
  assert(doc.getElementById('midi-bank-notice').textContent.includes('RAM'));
  assert(app.chosenLabels().some(text=>text.includes(lang==='en'?'MIDI Bank':'Banque MIDI')));
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
 // Une image déjà modifiée ne doit pas contourner le build fixe.
 app.loadOs(app.state.fw.raw,'already-modded.syx');assert(!app.state.os&&app.state.osError);
 assert.strictEqual(errors.length,0,errors.join('\n'));
 console.log('ok : bundle fixe avec TG/Live MIDI/LFO 2, EN/FR et limites RAM ; uploads Cycles/Syntakt et transfert rapide seuls');
 console.log('ok : vrai build navigateur, chaque mod et SHA MAIN OS vérifiés, conteneur signé valide ; OS déjà modifié refusé');
 dom.window.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
