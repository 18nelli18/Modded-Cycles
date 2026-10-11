// Note 58 : page LFO 2 réelle, sélection compatible et firmware navigateur.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'),main=process.argv.includes('--main'),dir=path.join(root,main?'docs/flasher':'docs/flasher-lfo-test');
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
(async()=>{
 const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
 const dom=new JSDOM(fs.readFileSync(path.join(dir,'index.html'),'utf8'),{
  url:'https://aveycole.github.io/Modded-Cycles/flasher-lfo-test/',runScripts:'outside-only',virtualConsole:vc});
 const w=dom.window,doc=w.document;
 Object.defineProperty(w,'isSecureContext',{value:true});
 w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 for(const file of ['builder.js','tweaks.js','flasher.js','app.js'])w.eval(fs.readFileSync(path.join(dir,file),'utf8'));
 await wait(20);
 const app=w.MCFlasherApp,tw=w.MC_TWEAKS;
 assert(app&&tw&&doc.getElementById('feat-lfo-secondary'));
 if(!main)assert(doc.getElementById('lfo-test-notice').textContent.includes('RAM'));
 assert(tw.features.find(f=>f.id==='lfo-secondary').status==='tested');
 for(const lang of ['en','fr']){
  app.applyLang(lang);doc.getElementById('more-lfo-secondary').click();
  const detail=doc.getElementById('det-lfo-secondary');
  assert(detail.textContent.includes('RAM'));
  assert(detail.querySelector('a.feat-guide').href.endsWith(main?'guide/#lfo-secondary':'guide.html#lfo-secondary'));
  doc.getElementById('more-lfo-secondary').click();
 }
 app.applyLang('en');doc.getElementById('feat-lfo-secondary').click();
 assert.deepStrictEqual(Array.from(app.chosenTweaks(),t=>t.id),['lfo-secondary']);
 doc.getElementById('select-all').click();
 const selected=Array.from(app.chosenTweaks(),t=>t.id);
 for(const id of ['lfo-secondary','model-tg-st','midi-live-both','scale-gen-st-queued','scramble-st-gen-queued'])assert(selected.includes(id),id);
 assert(!selected.includes('midi-both'));
 console.log('ok : EN/FR, limites RAM et guide local ; LFO seul et Select all avec Model-TG/Live MIDI prioritaires');
 const raw=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/model-cycles_OS1.13.syx')));
 const syntakt=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/Syntakt_OS1.42.syx')));
 const byId=new Map(tw.tweaks.map(t=>[t.id,t]));let count=0;
 for(const [key,hash] of Object.entries(app.REF_MAINOS)){
  if(!key.split('+').includes('lfo-secondary'))continue;
  const chosen=key.split('+').map(id=>byId.get(id));assert(chosen.every(Boolean));
  const result=w.MCBuilder.build(raw,tw.device,chosen,{syntakt,refMods:app.REF_MODS});
  assert.strictEqual(result.mainOsSha,hash,key);assert(result.modsChecked,key);
  assert(result.raw.length>0);count++;
 }
 assert(count>30);console.log('ok : '+count+' sélections LFO 2, firmware navigateur identique aux hashes Python, chaque mod vérifié');
 const full=w.MCBuilder.build(raw,tw.device,Array.from(app.chosenTweaks()),{syntakt,refMods:app.REF_MODS});
 assert(full.modsChecked);
 fs.writeFileSync(path.join(root,'../lfo2-select-all-proof.json'),JSON.stringify({ids:selected,sha:full.mainOsSha}));
 console.log('ok : vrai Select all construit, tous les mods vérifiés ; empreinte conservée pour comparaison Python');
 assert.strictEqual(errors.length,0,errors.join('\n'));
 dom.window.close();
})().catch(error=>{console.error(error);process.exitCode=1;});
