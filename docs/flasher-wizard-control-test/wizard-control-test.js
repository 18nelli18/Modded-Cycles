// Test130 : pipeline courant, payload propre reloge, trois hooks UI et deux lectures DSP.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCWizardControl,BASE=0x40000400,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCWizardControlReady=Promise.all([window.MCMacroFineReady,window.MCBeatDiagnosticReady]).then(()=>{
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const stockContainer=b.parseContainer(b.unwrap(args[1]).stream),section=stockContainer.sections.find(s=>s.id===3),stock=b.aplibDepack(stockContainer.blob.subarray(section.off,section.off+section.size)).data,patched=b.applyWrites(stock,r.tweaks).data;
  const read=(at,len)=>b.hex(patched.subarray(at-BASE,at-BASE+len));
  const wizard=r.tweaks.find(t=>t.id==='sample-wizard'),engine=r.tweaks.find(t=>t.symbols?.mm_params),common=r.tweaks.find(t=>t.symbols?.set_held);
  if(!wizard||!engine)throw Error('Wizard control: full preset required');
  const owner=r.tweaks.filter(t=>t.append).sort((x,y)=>n(y.append.at)-n(x.append.at))[0],origin=(n(owner.append.dest)+owner.append.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer);
  for(const at of d.reloc)v.setUint32(at,v.getUint32(at,false)+origin,false);
  const hooks=[[0x400775f8,'wf_encoder_hook'],[0x40077720,'wf_key_hook'],[0x4001b22a,'wf_draw_hook']],values=[];
  for(const [at] of hooks){const old=read(at,8);if(!old.startsWith('4ef9'))throw Error('Wizard control: UI chain guard');values.push(parseInt(old.slice(4,12),16));}
  values.push(n(engine.symbols.mm_params),common?n(common.symbols.set_held):0,common?n(common.symbols.mod_used):0);
  values.forEach((value,i)=>v.setUint32(d.symbols.wf_api+4*i,value,false));
  const q={id:'wizard-control-test',status:'experimental',order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[],symbols:{}};
  for(const [at,symbol] of hooks)q.writes.push({off:at-BASE,old:read(at,8),new:'4ef9'+h(origin+d.symbols[symbol])+'4e71'});
  if(read(0x4001d372,6)!=='4a0766d84a03')throw Error('Wizard control: pad guard');
  q.writes.push({off:0x4001d372-BASE,old:'4a0766d84a03',new:'4ef9'+h(origin+d.symbols.wf_pad)});
  const changed=new Set([wizard,owner,q]);
  const bodyRead=(at,len)=>{
   let actual=at;
   if(!wizard.append&&engine.symbols.no_midi_capacity_wizard)actual=n(engine.symbols.no_midi_capacity_wizard)+at-(BASE+stock.length);
   for(const t of r.tweaks.filter(t=>t.append)){
    const p=t.append.parts.find(p=>p.hex&&n(p.dest)<=actual&&actual+len<=n(p.dest)+p.hex.length/2);
    if(p){changed.add(t);delete t.append.compressed_hex;delete t.append.stored;const i=2*(actual-n(p.dest));return {p,i,old:p.hex.slice(i,i+2*len)};}
   }
   throw Error('Wizard control: sampler body missing '+h(actual));
  };
  // Les deux lectures natives sont chacune mvsw + bge + moveq zero (8octets).
  for(const [at,symbol,expected] of [[n(wizard.symbols.sp_flt_go),'wf_cut','736a001a6c027200'],[n(wizard.symbols.sp_flt_fok),'wf_res','796a001c6c027800']]){
   const part=bodyRead(at,8);if(part.old!==expected)throw Error('Wizard control: coefficient guard '+h(at)+' '+part.old);
   part.p.hex=part.p.hex.slice(0,part.i)+'4eb9'+h(origin+d.symbols[symbol])+'4e71'+part.p.hex.slice(part.i+16);
  }
  if(wizard.append){delete wizard.append.compressed_hex;delete wizard.append.stored;}
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});owner.append.size=origin+raw.length-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;
  if(!owner.append.compress){const w=owner.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at);if(!w)throw Error('Wizard control: loader guard');const code=b.fromHex(w.new);new DataView(code.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,owner.append.size,false);w.new=b.hex(code);}
  // Modifier le sampler change la longueur compressee du catalogue commun.
  // Replacer la source du dernier payload et son chargeur, sans changer ses VA.
  let cursor=BASE+stock.length;
  for(const t of r.tweaks.filter(t=>t.append)){
   if(n(t.append.at)!==cursor){
    if(t!==owner)throw Error('Wizard control: unexpected payload order');
    t.append.at='0x'+h(cursor);const loader=t.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at);
    if(!loader)throw Error('Wizard control: source loader missing');
    const code=b.fromHex(loader.new);new DataView(code.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,cursor,false);loader.new=b.hex(code);
   }
   cursor+=b.buildPayload(t.append,args[2],stock).length;
  }
  if(cursor>0x40200000)throw Error('Wizard control: payload capacity');
  for(const [name,at] of Object.entries(d.symbols))if(name.startsWith('wf_'))q.symbols[name]='0x'+h(origin+at);
  r.tweaks.push(q);for(const t of changed)r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};
  return r;
 };
});})();
