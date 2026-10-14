// Conversion, construction locale et absence de transfert automatique.
const fs=require('fs'),assert=require('assert'),{JSDOM,VirtualConsole}=require('jsdom');
const sampleDir=process.argv[3];assert(sampleDir,'Pass a local directory containing the four test WAV files.');
const dir=process.argv[2]+'/',errors=[],vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(String(e)));
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-supermodel-909/',runScripts:'outside-only',virtualConsole:vc}).window;
w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
for(const f of ['builder.js','profile.js','flasher.js','samples.js','edition.js','app.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const files={ch:'TR-909Hat C 01.wav',oh:'TR-909Hat O 03.wav',crash:'TR-909Crash.wav',ride:'TR-909Ride.wav'};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{try{
 await sleep(100);const a=w.MCFlasherApp,raw=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx'));
 a.loadOs(raw,'model-cycles_OS1.13.syx');assert(!a.state.fw);
 for(const [key,name] of Object.entries(files)){
  const input=w.document.getElementById('sample-'+key),file=new w.File([Uint8Array.from(fs.readFileSync(sampleDir+'/'+name))],name,{type:'audio/wav'});
  Object.defineProperty(input,'files',{value:[file],configurable:true});input.dispatchEvent(new w.Event('change'));await sleep(100);
 }
 await sleep(500);assert(a.state.fw,a.state.fwError);assert.equal(a.state.fw.kind,'built');assert.equal(a.chosenTweaks().length,9);assert.equal(a.chosenLabels().length,10);assert(a.state.fw.modsRef);assert(w.document.getElementById('flash').disabled);
 const info=w.MCFlasher.verify(a.state.fw.raw);assert(info.count>0);
 fs.writeFileSync('work/model909/browser-upload-private.syx',Buffer.from(a.state.fw.raw));fs.writeFileSync('work/model909/browser-upload-catalog-private.json',JSON.stringify({tweaks:a.chosenTweaks()}));
 console.log('PASS local WAV uploads / official OS / 9 recipes / signed firmware / no automatic MIDI transfer',a.state.fw.sha);
 const before=a.state.fw.sha;
 const input=w.document.getElementById('sample-ch');Object.defineProperty(input,'files',{value:[],configurable:true});input.dispatchEvent(new w.Event('change'));await sleep(30);assert(!a.state.fw);
 const bad=new w.File([new Uint8Array(44)],'bad.wav');Object.defineProperty(input,'files',{value:[bad],configurable:true});input.dispatchEvent(new w.Event('change'));await sleep(50);assert(!a.state.fw);assert(w.document.getElementById('sample-status-ch').textContent.includes('WAVE'));
 assert.throws(()=>w.MC909Samples.encode(new Uint8Array(44)),/WAVE/);
 assert(!errors.length,errors);console.log('PASS missing/invalid WAV invalidates cached firmware',before);
}catch(e){console.error(e.stack);process.exitCode=1;}finally{w.close();}})();
