const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE='docs/flasher';
const {JSDOM,VirtualConsole}=require('jsdom');
const root=path.resolve(__dirname,'..'),build=path.join(root,'build/volume-pan-toggle');
async function open(){
 const errors=[],vc=new VirtualConsole(),dir=path.join(root,'docs/flasher'),html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
 const w=new JSDOM(html,{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only',virtualConsole:vc}).window;
 w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};vc.on('jsdomError',e=>errors.push(String(e)));
 const menu=JSON.parse(fs.readFileSync(path.join(build,'pad-mode-data.json'),'utf8'));
 let deferredPadMode='',deferredMidiSafety='',deferredStepRec='',deferredLfo='',beatRepeatBoot=null;
 for(const m of html.matchAll(/<script[^>]+src="([^"]+)"/g)){
  const name=m[1].split('?')[0];
  if(name==='pad-mode-data.js')w.MCPadMode=menu;
  else if(name==='beat-repeat-data.js'){
   const source=fs.readFileSync(path.resolve(dir,name),'utf8');w.eval(source);beatRepeatBoot=w.MCBeatRepeat?.boot?JSON.parse(JSON.stringify(w.MCBeatRepeat.boot)):null;w.__testBeatRepeatBoot=beatRepeatBoot;
  }
  else if(name==='pad-mode.js')deferredPadMode=fs.readFileSync(path.join(root,'tools/web','pad-mode.js'),'utf8');
  else if(name==='midi-safety-release.js')deferredMidiSafety=fs.readFileSync(path.join(dir,name),'utf8');
  else if(name==='step-rec-solo-main.js')deferredStepRec=fs.readFileSync(path.join(root,'tools/web',name),'utf8');
  else if(name==='lfo-destinations.js')deferredLfo=fs.readFileSync(path.resolve(dir,name),'utf8');
  else {
   let source=fs.readFileSync(path.resolve(dir,name),'utf8');
   if(name==='step-rec-solo-main.js')source=source.replace("if(stepAt!==beatEnd||soloAt+soloHex.length/2>0x467b0000)throw Error('Step Recorder: expected free tail after the fixed beat-repeat payload');", "if(stepAt!==beatEnd||soloAt+soloHex.length/2>0x467b0000)throw Error('Step Recorder: expected free tail start='+stepAt.toString(16)+' beatEnd='+beatEnd.toString(16)+' soloEnd='+(soloAt+soloHex.length/2).toString(16));");
    w.eval(source.replaceAll('window.MCBeatRepeat.boot','window.__testBeatRepeatBoot'));
  }
 }
 if(!deferredPadMode||!deferredMidiSafety||!deferredStepRec||!deferredLfo)throw Error('A required test module is missing from the page');
 w.MCMidiSafetyReady=Promise.resolve();
 deferredStepRec=deferredStepRec.replace("if(stepAt!==beatEnd||soloAt+soloHex.length/2>0x467b0000)throw Error('Step Recorder: expected free tail after the fixed beat-repeat payload');", "if(stepAt!==beatEnd||soloAt+soloHex.length/2>0x467b0000)throw Error('Step Recorder layout: start='+stepAt.toString(16)+' beatEnd='+beatEnd.toString(16));");
 w.eval(deferredStepRec.replaceAll('window.MCBeatRepeat.boot','window.__testBeatRepeatBoot'));
 await w.MCStepRecSoloReady;
 w.eval(deferredLfo.replaceAll('window.MCBeatRepeat.boot','window.__testBeatRepeatBoot'));
 await w.MCLfoDestinationsReady;
 w.eval(deferredMidiSafety.replaceAll('window.MCBeatRepeat.boot','window.__testBeatRepeatBoot'));
 await w.MCMidiSafetyReady;
 w.eval(deferredPadMode.replaceAll('window.MCBeatRepeat.boot','window.__testBeatRepeatBoot'));
 await w.MCPadModeReady;
 return {w,errors,beatRepeatBoot};
}
(async()=>{
 fs.mkdirSync(build,{recursive:true});
 const {w,errors,beatRepeatBoot}=await open();
 try{
  if(!beatRepeatBoot)throw Error('Test fixture did not load beat-repeat boot metadata');
  await Promise.all(Object.keys(w).filter(k=>k.endsWith('Ready')&&w[k]?.then).map(k=>w[k]));
  if(beatRepeatBoot)w.__testBeatRepeatBoot=beatRepeatBoot;
  w.document.getElementById('select-all')?.click();
  const filter=w.document.getElementById('feat-track-filter');
  if(process.env.TEST_NO_FILTER==='1'){if(filter?.checked)filter.click();}
  else if(filter&&!filter.checked)filter.click();
  const a=w.MCFlasherApp,tweaks=a.chosenTweaks();
  assert(!a.state.selectionError,a.state.selectionError);
  assert(tweaks.some(t=>t.id==='level-pan-values'),'numeric volume/pan feature missing from fixed main profile');
  assert(tweaks.some(t=>t.id==='6ch-usbup'),'USB 2ch/6ch menu missing');
  const os=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/model-cycles_OS1.13.syx')));
  const st=Uint8Array.from(fs.readFileSync(path.join(root,'firmware/Syntakt_OS1.42.syx')));
  // The source hook changed to honor Mod Setup's Num toggle. The hosted flasher
  // bundle is intentionally untouched while this remains a test-only build, so
  // pull the freshly generated canonical tweak directly into this test image.
  const freshLevelPan=JSON.parse(fs.readFileSync(path.join(root,'tweaks/model-cycles_OS1.13/46-level-pan-values.json'),'utf8'));
  const oldLevelPan=tweaks.findIndex(t=>t.id==='level-pan-values');
  assert(oldLevelPan>=0,'numeric volume/pan tweak missing from composition');
  tweaks[oldLevelPan]=freshLevelPan;
  const p=w.MCMidiBankCompose(tweaks,os,st),num=x=>typeof x==='string'?parseInt(x,16):x;
  p.refMods[freshLevelPan.id]={w:w.MCBuilder.hex(w.MCBuilder.sha256(w.MCBuilder.writesBytes(freshLevelPan)))};
  assert(p.tweaks.some(t=>t.id==='step-rec')&&p.tweaks.some(t=>t.id==='latching-mute-solo'),'Step Recorder or solo missing from test profile');
  assert(process.env.TEST_NO_FILTER==='1'?!p.tweaks.some(t=>t.id==='track-filter'):p.tweaks.some(t=>t.id==='track-filter'||t.id==='wizard-continuous-filter'),
    (process.env.TEST_NO_FILTER==='1'?'per-track filter should be excluded from this test':'main profile must retain the per-track filter')+
    '; tweaks='+p.tweaks.map(t=>t.id).join(','));
  const pad=p.tweaks.find(x=>x.id==='pad-selection');
  const lp=p.tweaks.find(x=>x.id==='level-pan-values');
  assert(pad&&lp,'composed test profile lacks Pad Setup or numeric volume/pan');
  const api=num(pad.symbols.wf_api),origin=api-num(w.MCPadMode.symbols.wf_api),partOwner=p.tweaks.find(x=>x.append?.parts?.some(y=>num(y.dest)===origin));
  assert(partOwner,'Pad Setup runtime part not found');
  const lpDisabled=num(lp.symbols.lp_disabled);assert(lpDisabled===num(lp.symbols.lp_lvl)+31,'numeric volume/pan disable byte must be the reserved state byte');
  const part=partOwner.append.parts.find(y=>num(y.dest)===origin),raw=w.MCBuilder.fromHex(part.hex),apiOff=api-origin;
  assert(apiOff+36<=raw.length,'Pad Setup API table too short for numeric toggle');
  const view=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);
  view.setUint32(apiOff+32,lpDisabled,false);
  part.hex=w.MCBuilder.hex(raw);
  const hash=x=>w.MCBuilder.hex(w.MCBuilder.sha256(x));
  const container=w.MCBuilder.parseContainer(w.MCBuilder.unwrap(os).stream),section=container.sections.find(s=>s.id===3);
  const stock=w.MCBuilder.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data;
  p.refMods[partOwner.id]={...p.refMods[partOwner.id],p:hash(w.MCBuilder.buildPayload(partOwner.append,st,stock))};
  const built=w.MCBuilder.build(os,w.MC_TWEAKS.device,p.tweaks,{syntakt:st,refMods:p.refMods});
  assert(built.modsChecked,'firmware composition checks failed');
  assert(w.MCFlasher.verify(built.raw).count>0,'SYX checksum verification failed');
  const syx=path.join(build,'volume-pan-toggle-test.syx');fs.writeFileSync(syx,built.raw);
  fs.writeFileSync(path.join(build,'volume-pan-toggle-test.json'),JSON.stringify({sha256:built.mainOsSha,tweaks:p.tweaks.map(x=>x.id),padApi:{address:'0x'+api.toString(16),numericToggleAddress:'0x'+lpDisabled.toString(16)}},null,2));
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS composed fixed-main test, USB 2ch/6ch retained, numeric volume/pan included');
  console.log('PASS Pad Setup Num row points at lp_disabled; standard SYX verification passed');
  console.log(`${syx} (${built.raw.length} bytes; ${built.mainOsSha})`);
 }finally{w.close();}
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
