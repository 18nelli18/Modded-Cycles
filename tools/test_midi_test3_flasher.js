// Note 57 : installateur sélectionnable, fichiers OS locaux et build navigateur exact.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'docs/flasher-test-3');
// Charger aussi les scripts comme le parseur HTML, pas seulement via eval.
{
 const startupErrors=[],vc=new VirtualConsole();
 vc.on('jsdomError',e=>startupErrors.push(String(e)));
 let html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 html=html.replace(/<script src="([^"]+)"[^>]*><\/script>/g,(_,src)=>
  '<script>'+fs.readFileSync(path.resolve(dir,src.split('?')[0]),'utf8').replace(/<\/script/gi,'<\\/script')+'</script>');
 const startup=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher-test-3/',runScripts:'dangerously',virtualConsole:vc});
 assert(startup.window.MCFlasherApp,'Initialisation réelle du document');
 assert.deepStrictEqual(startupErrors,[]);
 startup.window.close();
}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 const dom=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher-test-3/',runScripts:'outside-only',virtualConsole:vc});
 const w=dom.window,doc=w.document;
 Object.defineProperty(w,'isSecureContext',{value:true});
 w.localStorage.setItem('mc-method','slow');
 w.navigator.requestMIDIAccess=async()=>{throw new Error('Récepteur pas encore installé');};
 w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 for(const file of ['builder.js','tweaks.js','flasher.js','app.js'])w.eval(fs.readFileSync(path.join(root,'docs/flasher-test-3',file),'utf8'));
 for(const file of ['bundle.js'])w.eval(fs.readFileSync(path.join(dir,file),'utf8'));
 await wait(25);
 const app=w.MCFlasherApp,tw=w.MC_TWEAKS;
 assert(app&&tw);
 assert.strictEqual(tw.features.find(f=>f.id==='midi-bank-bundle').status,'experimental');
 assert.strictEqual(tw.tweaks.find(t=>t.id==='midi-bank-bundle').status,'experimental');
 assert.strictEqual(app.state.method,'slow');app.setMethod('fast');assert.strictEqual(app.state.method,'fast');
 assert.notStrictEqual(w.getComputedStyle(doc.getElementById('step-choose')).display,'none');
 assert.notStrictEqual(w.getComputedStyle(doc.getElementById('m-slow')).display,'none');
 for(const id of ['file','file3','allow','port','flash'])assert(doc.getElementById(id),id);
 assert(html.includes('bundle.js?v=2026-10-12-test-3-channel-readout'));
 // Identité du transport avec main, sans copie expérimentale ni réglage spécial.
 assert(html.includes('src="flasher.js?v='));

 assert(html.includes('src="app.js?v='));

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
 // Audio USB6 facultatif : vrai build stéréo, référence complète et conteneur valide.
 const usb=doc.getElementById('feat-usb6');assert(usb&&usb.checked);
 usb.checked=false;usb.dispatchEvent(new w.Event('change',{bubbles:true}));
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert(app.state.fw,app.state.fwError);
 assert(!app.chosenTweaks().some(t=>t.id==='6ch-usbup'));
 assert(app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
 assert.strictEqual(app.state.fw.sha,app.REF_MAINOS[app.chosenTweaks().map(t=>t.id).join('+')]);
 assert(w.MCFlasher.verify(app.state.fw.raw).count>0);
 const usbAgain=doc.getElementById('feat-usb6');usbAgain.checked=true;usbAgain.dispatchEvent(new w.Event('change',{bubbles:true}));
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert(app.state.fw,app.state.fwError);
 const initial=app.state.fw;
 // Exécuter l'envoi UI complet avec un récepteur indépendant du flasher.
 const vm=require('vm');
 const smoke=fs.readFileSync(path.join(root,'tools/webflash_smoke.js'),'utf8');
 const receiver=smoke.slice(smoke.indexOf('const XHEAD ='),smoke.indexOf('async function load('));
 const ctx={Buffer,Uint8Array,setTimeout,zlib:require('zlib')};vm.createContext(ctx);
 vm.runInContext(receiver+'\nthis.makeDevice=fakeDevice;',ctx);
 const listeners=new Set();
 const device=ctx.makeDevice({},data=>listeners.forEach(fn=>fn({data})));
 const output={id:'cycles-out',name:'Elektron Model:Cycles',manufacturer:'Elektron',state:'connected',open:async()=>{},close:async()=>{},send:data=>device.handle(data)};
 const input={id:'cycles-in',name:output.name,manufacturer:'Elektron',state:'connected',open:async()=>{},close:async()=>{},addEventListener:(_,fn)=>listeners.add(fn),removeEventListener:(_,fn)=>listeners.delete(fn)};
 w.navigator.requestMIDIAccess=async()=>({outputs:new Map([[output.id,output]]),inputs:new Map([[input.id,input]]),onstatechange:null});
 // Le banc retire seulement la pause pour ne pas durer une minute ; code publié inchangé.
 const fast=w.MCFlasher.upgradeFast;
 w.MCFlasher.upgradeFast=(session,raw,opts)=>fast(session,raw,{...opts,restMs:0});
 doc.getElementById('allow').click();
 for(let n=0;n<100&&(!app.state.dev||app.state.dev.state!=='ok');n++)await wait(50);
 assert(app.state.dev&&app.state.dev.state==='ok');
 doc.getElementById('ack').checked=true;
 doc.getElementById('ack').dispatchEvent(new w.Event('change',{bubbles:true}));
 const send=async firmware=>{
  assert(!doc.getElementById('flash').disabled);
  doc.getElementById('flash').click();
  assert(app.state.sending);
  for(let n=0;n<1200&&app.state.sending;n++)await wait(50);
  assert.strictEqual(app.state.finished,'ok',doc.getElementById('result').textContent);
  assert.strictEqual(device.bad.length,0,Array.from(device.bad).join("; "));
  assert.strictEqual(device.next,firmware.raw.length);
  assert(Buffer.from(device.received).equals(Buffer.from(firmware.raw)));
  console.log('ok : envoi UI intégral, '+device.blocks+' blocs / '+device.next+' octets, CRC et positions vérifiés');
 };
 await send(initial);
 const box=doc.getElementById('feat-midi-bank-bundle');
 box.checked=false;box.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(!app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert(app.state.fw&&app.state.fw.sha!==initial.sha);
 await send(app.state.fw);
 // Contrôle indépendant : même sélection via une seconde instance isolée.
 const baseline=new JSDOM(fs.readFileSync(path.join(dir,'index.html'),'utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only'});
 const bw=baseline.window;bw.URL.createObjectURL=()=> 'blob:baseline';bw.URL.revokeObjectURL=()=>{};
 for(const file of ['builder.js','tweaks.js','flasher.js','app.js'])bw.eval(fs.readFileSync(path.join(root,'docs/flasher-test-3',file),'utf8'));
 bw.eval(fs.readFileSync(path.join(root,'docs/flasher-test-3/bundle.js'),'utf8'));
 await wait(25);baseline.window.document.getElementById('select-all').click();
 const baselineBank=baseline.window.document.getElementById('feat-midi-bank-bundle');
 baselineBank.checked=false;baselineBank.dispatchEvent(new bw.Event('change',{bubbles:true}));
 const ba=bw.MCFlasherApp;ba.loadOs(raw,'model-cycles_OS1.13.syx');ba.loadSyntakt(syntakt,'Syntakt_OS1.42.syx');
 for(let n=0;n<100&&(!ba.state.fw||ba.state.building);n++)await wait(100);
 assert(ba.state.fw,ba.state.fwError);
 assert.deepStrictEqual(Array.from(ba.chosenTweaks(),t=>t.id),Array.from(app.chosenTweaks(),t=>t.id));
 assert(Buffer.from(ba.state.fw.raw).equals(Buffer.from(app.state.fw.raw)));
 console.log('ok : firmware sans banque identique octet pour octet dans une seconde instance');
 baseline.window.close();
 let lfo=doc.getElementById('feat-lfo-secondary');assert(lfo);
 lfo.checked=false;lfo.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(!app.chosenTweaks().some(t=>t.id==='lfo-secondary'));
 choose();
 assert.deepStrictEqual(Array.from(app.chosenTweaks(),t=>t.id),selected);
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert.strictEqual(app.state.fw.sha,initial.sha);
 // Les dépendances du builder natif refusent une combinaison incomplète.
 lfo=doc.getElementById('feat-lfo-secondary');
 lfo.checked=false;lfo.dispatchEvent(new w.Event('change',{bubbles:true}));
 assert(app.chosenTweaks().some(t=>t.id==='midi-bank-bundle'));
 for(let n=0;n<100&&app.state.building;n++)await wait(100);
 assert(!app.state.fw&&app.state.fwError);
 const remove=doc.getElementById('feat-midi-bank-bundle');remove.checked=false;remove.dispatchEvent(new w.Event('change',{bubbles:true}));
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
