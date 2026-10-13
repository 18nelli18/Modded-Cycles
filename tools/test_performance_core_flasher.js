// Note65 : vraie page isolée, quatre cartes sans TG et compilation navigateur.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'docs/flasher-core-test');
(async()=>{
 const errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 assert(!html.includes('bundle.js'));assert(html.includes('2026-10-12-performance-core-test-2'));
 const dom=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher-core-test/',runScripts:'outside-only',virtualConsole:vc});
 const w=dom.window;Object.defineProperty(w,'isSecureContext',{value:true});w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 for(const f of ['builder.js','tweaks.js','flasher.js','app.js'])w.eval(fs.readFileSync(path.join(dir,f),'utf8'));
 await new Promise(r=>setTimeout(r,20));
 const app=w.MCFlasherApp,tw=w.MC_TWEAKS;assert(app&&tw);
 const ids=['performance-core','latching-mute','trig-preview','lfo-secondary'];
 assert.deepStrictEqual(Array.from(tw.features,f=>f.id),ids);
 assert(!tw.tweaks.some(t=>t.id.startsWith('model-tg')));
 for(const lang of ['en','fr']){
  app.applyLang(lang);assert(w.document.getElementById('select-all-note').textContent.includes(lang==='en'?'four options':'quatre options'));w.document.getElementById('more-performance-core').click();
  assert(w.document.getElementById('det-performance-core').textContent.includes(lang==='en'?'sampler':'sampler'));
  w.document.getElementById('more-performance-core').click();
 }
 w.document.getElementById('select-all').click();
 assert.deepStrictEqual(Array.from(app.chosenTweaks(),t=>t.id),ids);
 const raw=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/model-cycles_OS1.13.syx')));
 const results=[];
 for(let mask=0;mask<16;mask++){
  const chosen=tw.tweaks.filter((t,i)=>mask&(1<<i));
  const key=chosen.map(t=>t.id).join('+');
  const result=w.MCBuilder.build(raw,tw.device,chosen,{refMods:app.REF_MODS});
  if(app.REF_MAINOS[key])assert.strictEqual(result.mainOsSha,app.REF_MAINOS[key],key);
  assert(!chosen.length||result.modsChecked);assert(result.raw.length>0);
  assert(w.MCFlasher.verify(result.raw).count>0);
  results.push({ids:chosen.map(t=>t.id),sha:result.mainOsSha});
 }
 fs.writeFileSync(path.join(root,'../performance-core-browser-proof.json'),JSON.stringify(results));
 assert.deepStrictEqual(errors,[]);dom.window.close();
 console.log('ok : EN/FR, quatre cartes indépendantes de TG, Select all ; seize builds navigateur vérifiés');
})().catch(e=>{console.error(e);process.exitCode=1;});
