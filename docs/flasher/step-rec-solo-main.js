// Ajoute l'enregistrement pas a pas et le solo au firmware fixe principal.
// Le payload est range dans la plage libre deja reservee a la selection des machines.
(()=>{
const a=window.MCFlasherApp,b=window.MCBuilder,D=window.MCStepRecSoloData,BASE=0x40000400;
const number=x=>typeof x==='string'?parseInt(x,16):x;
const hex=x=>(x>>>0).toString(16).padStart(8,'0');
const hash=x=>b.hex(b.sha256(x));
window.MCStepRecSoloReady=window.MCMidiSafetyReady.then(()=>{
 if(!D||!D.step||!D.solo)throw Error('Step Recorder: release data missing');
 const previous=window.MCMidiBankCompose;
 if(typeof previous!=='function')throw Error('Step Recorder: fixed main composer missing');
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const container=b.parseContainer(b.unwrap(args[1]).stream),section=container.sections.find(s=>s.id===3);
  const stock=b.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data;
  const engine=r.tweaks.find(t=>t.id==='machine-selection-1023-wizard');
  const beat=r.tweaks.find(t=>t.id==='control-all-beat-repeat');
  const mute=r.tweaks.find(t=>t.id==='latching-mute');
  if(!engine||!engine.append||!beat||!beat.append||!mute)throw Error('Step Recorder: main payload or latching mute missing');

  const step=JSON.parse(JSON.stringify(D.step)),runtime=step.runtime_payload;
  if(runtime.target_tweak!==beat.id)throw Error('Step Recorder: beat-repeat payload target mismatch');
  delete step.runtime_payload;
  const stepHex=runtime.hex,soloHex=D.solo.hex;
  const stepAt=number(runtime.dest),soloAt=number(D.solo.dest);
  if(stepAt+stepHex.length/2!==soloAt)throw Error('Step Recorder: solo payload is not adjacent to recorder');
  const beatStart=number(beat.append.dest),beatEnd=beatStart+beat.append.size;
  if(stepAt<beatEnd||soloAt+soloHex.length/2>0x467b0000)throw Error('Step Recorder: fixed runtime would overlap the preceding beat-repeat payload');
  beat.append.parts.push({dest:runtime.dest,hex:stepHex},{dest:D.solo.dest,hex:soloHex});
  const partEnd=Math.max(0,...beat.append.parts.filter(p=>p.hex).map(p=>number(p.dest)+p.hex.length/2));
  beat.append.size=Math.max(soloAt+soloHex.length/2,partEnd)-beatStart;
  const boot=window.MCBeatRepeat.boot,loader=beat.writes.find(w=>w.off+BASE===boot.at);
  if(!loader)throw Error('Step Recorder: beat-repeat boot loader missing');
  const bootCode=b.fromHex(loader.new);
  new DataView(bootCode.buffer).setUint32(boot.symbols.br_boot_size,beat.append.size,false);
  loader.new=b.hex(bootCode);

  const latchWrite=mute.writes.find(w=>w.off===1344098);
  if(!latchWrite)throw Error('Solo: latching-mute exit code guard missing');
  const exitOffset=0x4014873A-0x40148662,oldExit='4239401487ed',newExit='4eb9'+hex(number(D.solo_symbols.solo_exit));
  if(latchWrite.new.slice(exitOffset*2,(exitOffset+6)*2)!==oldExit)throw Error('Solo: exit hook source changed');
  latchWrite.new=latchWrite.new.slice(0,exitOffset*2)+newExit+latchWrite.new.slice((exitOffset+6)*2);

  const solo={id:'latching-mute-solo',status:'tested',order:119,writes:[
   {off:0x40023550-BASE,old:'4eb940013904',new:'4eb9'+hex(number(D.solo_symbols.solo_pad))},
   {off:0x401487c0-BASE,old:'ffffffffffffffff',new:'0000000000000000'}
  ]};
  r.tweaks.push(step,solo);
  r.tweaks.sort((x,y)=>(x.order||0)-(y.order||0));
  r.refMods[step.id]={w:hash(b.writesBytes(step))};
  r.refMods[solo.id]={w:hash(b.writesBytes(solo))};
  r.refMods[mute.id]={w:hash(b.writesBytes(mute))};
  r.refMods[beat.id]={w:hash(b.writesBytes(beat)),p:hash(b.buildPayload(beat.append,args[2],stock))};
  return r;
 };
});
})();
