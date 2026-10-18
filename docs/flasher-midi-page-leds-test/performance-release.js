// Notes115/116 : fonctions confirmees, aucun diagnostic ni dependance repeat imposee.
(()=>{
 const b=window.MCBuilder,a=window.MCFlasherApp,BASE=0x40000400;
 const n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 const previous=window.MCMidiBankCompose;
 function quick(r,args,stock){
  if(!r.tweaks.some(t=>t.id==='latching-mute'))return;
  const d=window.MCBeatRepeat,code=window.MCQuickSaveExit.hex;
  let owner=r.tweaks.find(t=>t.id==='control-all-beat-repeat')||r.tweaks.find(t=>t.id==='midi-out-bank'),origin;
  const patched=b.applyWrites(stock,r.tweaks).data,read=(at,len)=>b.hex(patched.subarray(at-BASE,at-BASE+len));
  if(read(0x40100c44,4)!=='40148744')throw Error('Quick save: mute vtable guard');
  const q={id:'quick-save-exit',order:Math.max(...r.tweaks.map(t=>t.order))+1,status:'tested',hardwareTestedByOwner:true,requires:['latching-mute'],conflicts:[],writes:[],symbols:{}};
  if(owner){origin=(n(owner.append.dest)+owner.append.size+15)&~15;owner.append.parts.push({dest:'0x'+h(origin),hex:code});owner.append.size=origin+code.length/2-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;owner.symbols.qs_exit='0x'+h(origin);
   if(owner.id==='control-all-beat-repeat'){const w=owner.writes.find(w=>w.off+BASE===d.boot.at),raw=b.fromHex(w.new);new DataView(raw.buffer).setUint32(d.boot.symbols.br_boot_size,owner.append.size,false);w.new=b.hex(raw);}
  }else{
   let source=BASE+stock.length;origin=0x43000000;
   for(const t of r.tweaks)if(t.append){source=Math.max(source,n(t.append.at))+b.buildPayload(t.append,args[2],stock).length;origin=Math.max(origin,n(t.append.dest)+t.append.size);}origin=(origin+15)&~15;
   const boot=read(0x40000530,10);if(boot!=='4ebaff8041f9fc044000'&&!/^4ef9[0-9a-f]{8}4e714e71$/.test(boot)&&!/^4eb9[0-9a-f]{8}fc044000$/.test(boot))throw Error('Quick save: startup chain guard');
   const raw=b.fromHex(d.boot.hex),v=new DataView(raw.buffer);for(const [key,value] of Object.entries({br_boot_source:source,br_boot_dest:origin,br_boot_size:code.length/2,br_boot_next:/^4e[fb]9/.test(boot)?parseInt(boot.slice(4,12),16):0,br_boot_call:Number(boot.startsWith('4eb9'))}))v.setUint32(d.boot.symbols[key],value,false);
   if(read(d.boot.at,raw.length)!==b.hex(stock.subarray(d.boot.at-BASE,d.boot.at-BASE+raw.length)))throw Error('Quick save: loader occupied');
   q.writes.push({off:d.boot.at-BASE,old:read(d.boot.at,raw.length),new:b.hex(raw)},{...d.redirect},{off:0x130,old:boot,new:'4ef9'+h(d.boot.at)+'4e714e71'});
   q.append={at:'0x'+h(source),dest:'0x'+h(origin),size:code.length/2,parts:[{dest:'0x'+h(origin),hex:code}],reloc:[]};owner=q;
  }
  if(origin+code.length/2>=0x47000000)throw Error('Quick save: runtime capacity');
  q.writes.push({off:0x40100c44-BASE,old:'40148744',new:h(origin)});q.symbols.qs_exit='0x'+h(origin);r.tweaks.push(q);
  for(const t of new Set([q,owner]))r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};
 }

 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const c=b.parseContainer(b.unwrap(args[1]).stream),section=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(section.off,section.off+section.size)).data;quick(r,args,stock);
  const arp=r.tweaks.find(t=>t.id==='arp');
  if(arp){const off=0x4016cc6a-BASE,w=arp.writes.find(w=>w.off<=off&&off+4<=w.off+w.new.length/2);if(!w)throw Error('Oct0: A menu missing');const i=2*(off-w.off);if(w.new.slice(i,i+8)!=='48680001')throw Error('Oct0: A menu guard');w.new=w.new.slice(0,i)+'2f084e71'+w.new.slice(i+8);r.refMods[arp.id]={...r.refMods[arp.id],w:hash(b.writesBytes(arp))};}
  const bank=r.tweaks.find(t=>t.id==='midi-out-bank');if(!bank)return r;
  const repeat=r.tweaks.find(t=>t.id==='control-all-beat-repeat'),owner=repeat||bank,d=window.MCMidiCursor;
  const origin=(n(owner.append.dest)+owner.append.size+15)&~15,raw=b.fromHex(d.hex),rv=new DataView(raw.buffer);
  for(const off of d.reloc)rv.setUint32(off,rv.getUint32(off,false)+origin,false);
  rv.setUint32(d.symbols.cg_obj,n(bank.symbols.mlp_obj),false);
  ['ml_context','ml_clock_state','ml_play_pattern','ml_start_context','ml_bank_follow','ml_clock_durations','ml_cond_init','ml_cond_history'].forEach((key,i)=>{if(!bank.symbols[key])throw Error('MIDI phase: missing '+key);rv.setUint32(d.symbols.phase_api+4*i,n(bank.symbols[key]),false);});
  const at=n(bank.symbols.ml_native_tick),tp=bank.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+152<=n(p.dest)+p.hex.length/2);if(!tp)throw Error('MIDI entry: native tick missing');
  let i=2*(at-n(tp.dest)),body=tp.hex.slice(i,i+304);
  if(body.slice(84,100)!=='4ab9'+h(n(bank.symbols.ml_start_serial))+'6700'||body.slice(104,120)!=='b5f9'+h(n(bank.symbols.ml_start_context))+'6600'||body.slice(260,280)!=='2f032f024eb9'+h(n(bank.symbols.ml_audio_tick)))throw Error('MIDI entry: transport guard');
  for(const [off,old,nw] of [[0x32,'005c','0050'],[0x3c,'0052','0046']]){const pos=i+2*off;if(tp.hex.slice(pos,pos+4)!==old)throw Error('MIDI entry: branch guard');tp.hex=tp.hex.slice(0,pos)+nw+tp.hex.slice(pos+4);}
  const hookAt=n(bank.symbols.ml_audio_hook),hp=bank.append.parts.find(p=>p.hex&&n(p.dest)<=hookAt&&hookAt+6<=n(p.dest)+p.hex.length/2);i=2*(hookAt-n(hp.dest));if(hp.hex.slice(i,i+12)!=='4eb940053330')throw Error('MIDI phase: native call guard');hp.hex=hp.hex.slice(0,i)+'4eb9'+h(origin+d.symbols.phase_tick)+hp.hex.slice(i+12);
  const hook=bank.writes.find(w=>w.off===0x4008e8c4-BASE);if(!hook||hook.new!=='4ef9'+h(n(bank.symbols.mlp_pulse_guard))+'4e714e71')throw Error('MIDI cursor: pulse hook guard');hook.new='4ef9'+h(origin+d.symbols.cg_guard)+'4e714e71';
  const led=n(bank.symbols.mlp_led),end=n(bank.symbols.mlp_cursor),lp=bank.append.parts.find(p=>p.hex&&n(p.dest)<=led&&end<=n(p.dest)+p.hex.length/2);if(!lp||end-led>2048)throw Error('MIDI cursor: LED guard');i=2*(led-n(lp.dest));body=lp.hex.slice(i,2*(end-n(lp.dest)));const pattern='4eb94008e8c4',pos=body.indexOf(pattern);if(pos<0||body.indexOf(pattern,pos+1)>=0)throw Error('MIDI cursor: private call guard');lp.hex=lp.hex.slice(0,i+pos)+'4eb9'+h(n(bank.symbols.mlp_pad_pulse))+lp.hex.slice(i+pos+12);
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});
  const oct=(origin+raw.length+3)&~3,octRaw=window.MCArpZero.hex,start=n(bank.symbols.mlp_retrigger_render),op=bank.append.parts.find(p=>p.hex&&n(p.dest)<=start&&start<n(p.dest)+p.hex.length/2);if(!op)throw Error('Oct0: B menu missing');const begin=2*(start-n(op.dest)),where=op.hex.indexOf('588f0c8200000002',begin);if(where<0||where-begin>4096)throw Error('Oct0: B menu guard');op.hex=op.hex.slice(0,where+4)+'4eb9'+h(oct)+op.hex.slice(where+16);
  owner.append.parts.push({dest:'0x'+h(oct),hex:octRaw});owner.append.size=oct+octRaw.length/2-n(owner.append.dest);
  if(oct+octRaw.length/2>=0x47000000)throw Error('MIDI helpers: runtime capacity');
  for(const key of ['cg_guard','phase_join','phase_tick','phase_api'])owner.symbols[key]='0x'+h(origin+d.symbols[key]);owner.symbols.octave_draw='0x'+h(oct);
  delete bank.append.compressed_hex;delete bank.append.stored;

  r.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(b.buildPayload(bank.append,args[2],stock))};
  if(repeat){const source=n(bank.append.at)+b.buildPayload(bank.append,args[2],stock).length;repeat.append.at='0x'+h(source);const loader=repeat.writes.find(w=>BASE+w.off===window.MCBeatRepeat.boot.at);if(!loader)throw Error('MIDI cursor: loader guard');const boot=b.fromHex(loader.new),v=new DataView(boot.buffer);v.setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,source,false);v.setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,repeat.append.size,false);loader.new=b.hex(boot);r.refMods[repeat.id]={w:hash(b.writesBytes(repeat)),p:hash(b.buildPayload(repeat.append,args[2],stock))};}
  return r;
 };
 const feature=window.MC_TWEAKS.features.find(f=>f.id==='arp');if(feature){feature.status='tested';feature.hardwareTestedByOwner=true;}
 a.registerFeatureTexts('arp',{en:{label:'Arpeggiator',short:'Held-note arp; Oct0 uses only the held notes.',desc:'FUNC + RETRIG opens direction and Oct. Hold RETRIG with notes, or use A.On. Oct0 cycles only held notes; 1–3 add octave copies. Existing saved settings keep their sound. Hardware confirmed by AveyCole on 17 October 2026.'},fr:{label:'Arpegiateur',short:'Arpege des notes tenues ; Oct0 sans octave ajoutee.',desc:'FUNC + RETRIG : direction et Oct. Tenir RETRIG avec les notes, ou utiliser A.On. Oct0 parcourt seulement les notes tenues ; 1–3 ajoutent des octaves. Les anciens reglages conservent leur son. Confirme par AveyCole le17/10/2026.'}});
 window.MCPerformanceReleaseReady=Promise.resolve();a.applyLang(document.documentElement.lang||'en');
})();
