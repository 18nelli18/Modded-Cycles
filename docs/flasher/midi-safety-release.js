// Correctifs MIDI/Chord confirmes sur appareil par AveyCole ; aucun diagnostic.
(()=>{const D=window.MCMidiSafetyData,a=window.MCFlasherApp,b=window.MCBuilder,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCMidiSafetyReady=window.MCGenieEntropyReady.then(()=>{
 const entry=JSON.parse(JSON.stringify(D.entry));entry.engine.id=window.MCMachineCombinationData.wizard[1023].engine.id;entry.engine_sha256=hash(Uint8Array.from(unescape(encodeURIComponent(JSON.stringify(entry.engine))),c=>c.charCodeAt(0)));window.MCMachineCombinationData.wizard[1023]=entry;window.MCWizardCatalogue.variants[1023]=entry;
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
 const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},engine=r.tweaks.find(t=>t.gov),beat=r.tweaks.find(t=>t.id==='control-all-beat-repeat'),st=args[2];
 if(!engine||!beat)throw Error('MIDI/Chord repair: fixed preset required');
 const container=b.parseContainer(b.unwrap(args[1]).stream),section=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data;
 function patch(t,at,hex,expected){const part=t.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+hex.length/2<=n(p.dest)+p.hex.length/2);if(!part)throw Error('MIDI/Chord repair: payload guard');const i=2*(at-n(part.dest));if(expected&&part.hex.slice(i,i+expected.length)!==expected)throw Error('MIDI/Chord repair: source guard');part.hex=part.hex.slice(0,i)+hex+part.hex.slice(i+hex.length);}

 {
  const d=D.module,sy=Object.fromEntries(Object.entries(engine.symbols).map(([k,v])=>[k,n(v)])),secondary=r.tweaks.find(t=>t.id==='lfo-secondary'),ck=r.tweaks.find(t=>t.id==='chord-keys-supermodel'),ld=r.tweaks.find(t=>t.symbols?.ld_api),patched=b.applyWrites(stock,r.tweaks).data,aux={id:'midi-safety',status:'tested',hardwareTestedByOwner:true,order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[],symbols:{...engine.symbols,chord_audio_update:'0x'+h(d.chord.symbols.chord_audio_update)}};
  function nativePatch(at,expected,replacement){if(b.hex(patched.subarray(at-0x40000400,at-0x40000400+expected.length/2))!==expected)throw Error('MIDI/Chord repair: native guard '+h(at));aux.writes.push({off:at-0x40000400,old:expected,new:replacement});}
  function api(at,value){const p=engine.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+4<=n(p.dest)+p.hex.length/2);if(p)patch(engine,at,h(value));else engine.append.parts.push({dest:'0x'+h(at),hex:h(value)});}
  api(sy.mm_ui_api+20,n(secondary.symbols.lf2p_obj));api(sy.mm_name_api,n(ld.symbols.ld_api));
  nativePatch(0x4002650e,'4eb9'+h(n(ld.symbols.ld_first)),'4eb9'+h(sy.mm_primary_name));
  const bridge=n(secondary.symbols.lf2n_write);nativePatch(bridge,'4fefffe848d7041c','4ef9'+h(sy.mm_secondary_bridge)+'4e71');api(sy.mm_secondary_resume,bridge+8);
  for(const [at,key] of [[0x400817aa,'mm_live_producer_on'],[0x40081552,'mm_live_producer_off']])nativePatch(at,'4eb94008a5d0','4ef9'+h(sy[key]));
  const chordSource=0x4672e900+n(ck.symbols.chord_audio_update)-0x401c383c;patch(engine,chordSource,'4ef9'+h(d.chord.symbols.chord_audio_update));
  nativePatch(n(ck.symbols.chord_audio_ratios),'4aab0054','4aaf002c');
  r.tweaks.push(aux);r.refMods[aux.id]={w:hash(b.writesBytes(aux))};
 }
 if(true){
  const d=D.idle,origin=(n(beat.append.dest)+beat.append.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer),dispatch=n(engine.symbols.mm_lfo_dispatch);
  for(const off of d.reloc)v.setUint32(off,v.getUint32(off,false)+origin,false);
  v.setUint32(d.symbols.il_seen,n(engine.symbols.mm_lfo_seen),false);v.setUint32(d.symbols.il_api,n(engine.symbols.mm_lfo_api),false);const machine=engine.machine_names.indexOf('MIDI Out');if(machine<0)throw Error('MIDI/Chord repair: machine missing');v.setUint32(d.symbols.il_machine,machine<<8,false);
  const part=engine.append.parts.find(p=>p.hex&&n(p.dest)<=dispatch&&dispatch+10<=n(p.dest)+p.hex.length/2);if(!part)throw Error('MIDI/Chord repair: part missing');const i=2*(dispatch-n(part.dest)),old=part.hex.slice(i,i+20);if(!(old.startsWith('4fef')&&old.slice(8,12)==='4280'&&old.slice(12,16)==='48d7'))throw Error('MIDI idle: prologue guard');
  raw.set(b.fromHex(old+'4ef9'+h(dispatch+10)),d.symbols.il_original);patch(engine,dispatch,'4ef9'+h(origin+d.symbols.il_entry)+'4e714e71',old);
  beat.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});beat.append.size=origin+raw.length-n(beat.append.dest);for(const [key,value] of Object.entries(d.symbols))if(key.startsWith('il_'))beat.symbols[key]='0x'+h(origin+value);
 }
 if(true){
  const d=D.fade,origin=(n(beat.append.dest)+beat.append.size+15)&~15,raw=b.fromHex(d.hex),fade=n(engine.gov.voice_after),source=n(engine.append.dest)+fade-0x80001c5c;
  const data=D.fadeLoop,part=engine.append.parts.find(p=>p.hex&&n(p.dest)<=source&&source+256<=n(p.dest)+p.hex.length/2);if(!part)throw Error('Cut fade: SRAM source guard');const i=2*(source-n(part.dest)),body=part.hex.slice(i,i+512),where=body.indexOf(data.old_loop);if(!(where>=0&&body.indexOf(data.old_loop,where+1)<0))throw Error('Cut fade: loop guard');
  patch(engine,source+where/2,'4eb9'+h(origin+d.symbols.cf_fade)+'4e71'.repeat((data.old_loop.length/2-6)/2),data.old_loop);
  beat.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});beat.append.size=origin+raw.length-n(beat.append.dest);for(const [key,value] of Object.entries(d.symbols))if(key.startsWith('cf_'))beat.symbols[key]='0x'+h(origin+value);
 }
 delete engine.append.compressed_hex;delete engine.append.stored;const sourceEnd=n(engine.append.at)+b.buildPayload(engine.append,st,stock).length;beat.append.at='0x'+h(sourceEnd);
 const loader=beat.writes.find(wr=>wr.off+0x40000400===window.MCBeatRepeat.boot.at),boot=b.fromHex(loader.new);new DataView(boot.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,sourceEnd,false);new DataView(boot.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,beat.append.size,false);loader.new=b.hex(boot);
 for(const t of [engine,beat]){if(t.append){delete t.append.compressed_hex;delete t.append.stored;}r.refMods[t.id]={w:hash(b.writesBytes(t)),p:hash(b.buildPayload(t.append,st,stock))};}
 if(r.tweaks.some(t=>t.symbols?.br_load_address||t.symbols?.br_observe_before||t.id==='audio-load-diagnostic'))throw Error('MIDI/Chord repair: diagnostics forbidden in main');
 return r;
 };
});})();
