// Retarder DOMContentLoaded : reproduire les cases cochees avant wirePicker.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
let jsdom;try{jsdom=require('jsdom');}catch{jsdom=require('../build/retrosyn-ui/node_modules/jsdom');}
const dir=path.resolve('docs/flasher');
async function check(legacy){
 const html=fs.readFileSync(path.join(dir,'index.html'),'utf8'),errors=[],vc=new jsdom.VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
 const w=new jsdom.JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only',virtualConsole:vc}).window;
 try{
  w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
  let ready=false;const callbacks=[],add=w.document.addEventListener.bind(w.document);
  Object.defineProperty(w.document,'readyState',{get:()=>ready?'complete':'loading'});
  w.document.addEventListener=(type,fn,opts)=>{if(type==='DOMContentLoaded')callbacks.push(fn);else add(type,fn,opts);};
  for(const m of html.matchAll(/<script[^>]+src="([^"]+)"/g)){
   let code=fs.readFileSync(path.resolve(dir,m[1].split('?')[0]),'utf8');
   if(legacy&&m[1].startsWith('midi-machine-main.js'))code=code.replace('Promise.all([pageReady,','Promise.all([');
   w.eval(code);
  }
  await w.MCLfoDestinationsReady;await new Promise(r=>setTimeout(r,0));
  let finished=false;w.MCMidiMachineAllReady.then(()=>finished=true);await Promise.resolve();
  if(legacy){assert(finished);assert.equal(w.MCFlasherApp.chosenEngines().length,0);}
  else assert(!finished,'Preset emis avant connexion des handlers');
  ready=true;for(const fn of callbacks)fn.call(w.document,new w.Event('DOMContentLoaded'));
  await w.MCMidiMachineAllReady;
  if(legacy){assert.equal(w.MCFlasherApp.chosenEngines().length,0);console.log('PASS ancien ordre reproduit : cases cochees, aucun moteur Syntakt choisi');return;}
  const a=w.MCFlasherApp;assert.equal(a.chosenEngines().filter(e=>['sd','cp','toy','bits','swarm'].includes(e.code)).length,5);assert(a.chosenTweaks().some(t=>t.machine_selection===1023&&t.symbols.mm_encoder_hook));
  const os=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx'));a.loadOs(os,'Cycles.syx');
  assert.equal(a.state.fwError,'needs_syntakt');assert(!a.state.fw);assert.equal(w.document.getElementById('drop3-wrap').hidden,false);assert.equal(w.document.getElementById('file3').type,'file');
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS nouvel ordre : masque1023, cinq moteurs, Cycles seul demande Syntakt, aucun build incomplet');
 }finally{w.close();}
}
(async()=>{await check(true);await check(false);})().catch(e=>{console.error(e.stack);process.exitCode=1;});
