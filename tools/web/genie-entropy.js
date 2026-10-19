// Note132 : premiere graine Genie variable, confirme sur appareil par AveyCole.
(()=>{const b=window.MCBuilder,d=window.MCGenieEntropy,BASE=0x40000400,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCGenieEntropyReady=Promise.resolve(window.MCPadModeReady).then(()=>{
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},genie=r.tweaks.find(t=>t.symbols?.sg_seed_ok),owner=r.tweaks.find(t=>t.id==='control-all-beat-repeat');
  if(!genie||!owner)throw Error('Genie seed: fixed preset owner missing');
  const origin=(n(owner.append.dest)+owner.append.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer);
  for(const at of d.reloc)v.setUint32(at,v.getUint32(at,false)+origin,false);v.setUint32(d.symbols.ge_resume,n(genie.symbols.sg_seed_ok),false);
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});owner.append.size=origin+raw.length-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;
  const q={id:'genie-initial-seed',order:Math.max(...r.tweaks.map(t=>t.order))+1,status:'tested',hardwareTestedByOwner:true,writes:[{off:n(genie.symbols.sg_seed_ok)-12-BASE,old:'2e2a001866062e3c6d2b79f5',new:'4ef9'+h(origin+d.symbols.ge_seed)+'4e714e714e71'}],symbols:{}};
  for(const [key,value] of Object.entries(d.symbols))if(key.startsWith('ge_'))q.symbols[key]='0x'+h(origin+value);
  if(!owner.append.compress){const loader=owner.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at);if(!loader)throw Error('Genie seed: loader guard');const code=b.fromHex(loader.new);new DataView(code.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,owner.append.size,false);loader.new=b.hex(code);}
  r.tweaks.push(q);const co=b.parseContainer(b.unwrap(args[1]).stream),sec=co.sections.find(s=>s.id===3),stock=b.aplibDepack(co.blob.subarray(sec.off,sec.off+sec.size)).data;
  for(const t of [owner,q])r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};return r;
 };
});})();
