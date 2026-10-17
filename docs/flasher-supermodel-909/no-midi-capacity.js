// Note 104 : compression commune Wizard/moteurs seulement en cas de manque de place.
(()=>{
 'use strict';const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCNoMidiCapacity,previous=window.MCMidiBankCompose;
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,hex=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x)),align=x=>(x+15)&~15,BASE=0x40000400;
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const original=previous(input,cycles,syntakt);if(a.isSelected('midi-out-bank'))return original;const extra=a.isSelected('control-all-beat-repeat')?window.MCBeatRepeat.hex.length/2:256;
  const container=b.parseContainer(b.unwrap(cycles).stream),main=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(main.off,main.off+main.size)).data;
  const apps=original.tweaks.filter(t=>t.append);let end=BASE+stock.length;
  for(const t of apps)end=Math.max(end,num(t.append.at))+b.buildPayload(t.append,syntakt,stock).length;
  if(end+extra<=0x40200000)return original;
  const oldWizard=apps.find(t=>t.id==='sample-wizard'),oldEngine=apps.find(t=>t!==oldWizard&&t.append.compress==='aplib');
  if(apps.length!==2||!oldWizard||!oldEngine)return original;
  const result={...original,tweaks:clone(original.tweaks),refMods:{...original.refMods}},wizard=result.tweaks.find(t=>t.id===oldWizard.id),engine=result.tweaks.find(t=>t.id===oldEngine.id),ap=engine.append,wp=wizard.append;
  for(const t of [oldWizard,oldEngine]){const ref=original.refMods[t.id];if(hash(b.writesBytes(t))!==ref.w||hash(b.buildPayload(t.append,syntakt,stock))!==ref.p)throw Error('No MIDI capacity: trusted recipe changed');}
  if(num(ap.dest)<0x46700000||num(wp.at)!==BASE+stock.length||num(wp.dest)!==num(wp.at)||wp.compress||wp.size%4)throw Error('No MIDI capacity: unsupported Wizard layout');
  const wizardBytes=b.buildPayload(wp,syntakt,stock);if(wizardBytes.length!==wp.size)throw Error('No MIDI capacity: Wizard size changed');
  const stub=engine.writes.find(w=>w.off===0x4016cae8-BASE);if(!stub)throw Error('No MIDI capacity: engine bootstrap missing');
  const source='41f9'+hex(num(ap.at)),sourceAt=stub.new.indexOf(source);if(sourceAt<0||stub.new.indexOf(source,sourceAt+1)>=0)throw Error('No MIDI capacity: source guard');
  const tail='4ef9'+hex(num(wizard.symbols.boot_extra_hook));if(!stub.new.endsWith(tail))throw Error('No MIDI capacity: Wizard chain guard');
  const callAt=stub.new.lastIndexOf('4eb9',stub.new.length-tail.length-1);
  if(callAt<0||callAt+12!==stub.new.length-tail.length)throw Error('No MIDI capacity: engine init guard');
  const init=parseInt(stub.new.slice(callAt+4,callAt+12),16),dest=num(ap.dest),copyAt=align(dest+ap.size),stageAt=align(copyAt+wizardBytes.length),stage=b.fromHex(d.hex),view=new DataView(stage.buffer);
  if(init<dest||init>=dest+ap.size||stageAt+stage.length>=0x47000000)throw Error('No MIDI capacity: runtime bounds');
  for(const [name,value] of Object.entries({capacity_source:copyAt,capacity_dest:num(wp.dest),capacity_count:wizardBytes.length/4}))view.setUint32(d.symbols[name],value,false);
  if(view.getUint32(d.symbols.capacity_init+2,false)!==0xf0010000)throw Error('No MIDI capacity: stage template guard');view.setUint32(d.symbols.capacity_init+2,init,false);
  ap.parts.push({dest:'0x'+hex(copyAt),hex:b.hex(wizardBytes)},{dest:'0x'+hex(stageAt),hex:b.hex(stage)});ap.size=stageAt+stage.length-dest;ap.at='0x'+hex(BASE+stock.length);ap.compress_cost=512;ap.compress_margin=0;delete ap.compressed_hex;delete ap.stored;
  stub.new=stub.new.slice(0,callAt)+'4eb9'+hex(stageAt)+stub.new.slice(callAt+12);stub.new=stub.new.slice(0,sourceAt)+ '41f9'+hex(BASE+stock.length)+stub.new.slice(sourceAt+12);
  delete wizard.append;engine.symbols={...engine.symbols,no_midi_capacity_stage:'0x'+hex(stageAt),no_midi_capacity_wizard:'0x'+hex(copyAt)};engine.status='experimental';engine.hardwareTestedByOwner=false;
  const packed=b.buildPayload(ap,syntakt,stock);if(BASE+stock.length+packed.length+extra>0x40200000)throw Error('No MIDI capacity: joint payload still full');ap.stored=packed.length;
  result.refMods[wizard.id]={w:hash(b.writesBytes(wizard))};result.refMods[engine.id]={w:hash(b.writesBytes(engine)),p:hash(packed)};return result;
 };
})();
