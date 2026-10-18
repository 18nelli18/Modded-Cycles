// End Wizard utilise un descripteur continu du meme slot ; RC Type909 reste binaire.
(()=>{const b=window.MCBuilder,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MC909WizardEndReady=Promise.all([window.MCLfoDestinationsReady,window.MC909SamplePreviewReady]).then(()=>{
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},bank=r.tweaks.find(t=>t.id==='midi-out-bank');if(!bank)throw Error('909 Wizard End: payload missing');
  function locate(at,len){
   const find=x=>bank.append.parts.find(p=>p.hex&&n(p.dest)<=x&&x+len<=n(p.dest)+p.hex.length/2);
   let p=find(at);if(p)return [p,at-n(p.dest)];
   const stage=n(bank.symbols.midi_current_stage),part=bank.append.parts.find(p=>p.hex&&n(p.dest)<=stage&&stage<n(p.dest)+p.hex.length/2);if(!part)throw Error('909 Wizard End: boot mapping missing');
   const offset=stage-n(part.dest)+window.MCMidiCurrent.boot.symbols.midi_current_copies,raw=b.fromHex(part.hex),v=new DataView(raw.buffer);
   for(let k=0;k<8;k++){const src=v.getUint32(offset+12*k,false),dest=v.getUint32(offset+12*k+4,false),words=v.getUint32(offset+12*k+8,false);if(!src)break;if(dest<=at&&at+len<=dest+4*words){const moved=src+at-dest;p=find(moved);if(p)return [p,moved-n(p.dest)];}}
   throw Error('909 Wizard End: unmapped code '+h(at));
  }
  for(const q of window.MC909WizardEnd.patches){const[p,i]=locate(q.at,q.old.length/2);if(p.hex.slice(2*i,2*i+q.old.length)!==q.old)throw Error('909 Wizard End: source guard '+h(q.at));p.hex=p.hex.slice(0,2*i)+q.new+p.hex.slice(2*i+q.old.length);}
  delete bank.append.compressed_hex;delete bank.append.stored;
  const c=b.parseContainer(b.unwrap(args[1]).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
  r.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(b.buildPayload(bank.append,args[2],stock))};
  const beat=r.tweaks.find(t=>t.id==='control-all-beat-repeat');if(beat){const source=n(bank.append.at)+b.buildPayload(bank.append,args[2],stock).length;beat.append.at='0x'+h(source);const w=beat.writes.find(w=>w.off+0x40000400===window.MCBeatRepeat.boot.at),raw=b.fromHex(w.new);new DataView(raw.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,source,false);w.new=b.hex(raw);r.refMods[beat.id]={w:hash(b.writesBytes(beat)),p:hash(b.buildPayload(beat.append,args[2],stock))};}
  return r;
 };
});})();
