// Note130 : promotion du menu pad seul, sans mutation du catalogue ou sampler.
(()=>{const b=window.MCBuilder,d=window.MCPadMode,bootMeta=window.MCBeatRepeat?.boot,BASE=0x40000400,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCPadModeReady=Promise.all([window.MCMacroFineReady]).then(()=>{
 const previous=window.MCMidiBankCompose,canonicalLevelPan=window.MCLevelPanCanonical;
 if(!canonicalLevelPan||canonicalLevelPan.id!=='level-pan-values')throw Error('Mod Setup: canonical volume/pan module missing');
 window.MCMidiBankCompose=(...args)=>{
  const input=args[0].map(t=>t.id===canonicalLevelPan.id?JSON.parse(JSON.stringify(canonicalLevelPan)):t),prior=previous(input,...args.slice(1)),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const co=b.parseContainer(b.unwrap(args[1]).stream),sec=co.sections.find(s=>s.id===3),stock=b.aplibDepack(co.blob.subarray(sec.off,sec.off+sec.size)).data,patched=b.applyWrites(stock,r.tweaks).data,read=(at,len)=>b.hex(patched.subarray(at-BASE,at-BASE+len));
  const common=r.tweaks.find(t=>t.symbols?.set_held),levelPan=r.tweaks.find(t=>t.symbols?.lp_disabled),owner=r.tweaks.filter(t=>t.append).sort((x,y)=>n(y.append.at)-n(x.append.at))[0],stepRuntime=window.MCStepRecSoloData?.step?.runtime_payload,soloRuntime=window.MCStepRecSoloData?.solo;
  if(!levelPan)throw Error('Mod Setup: numeric volume/pan state missing');
  const appendEnd=n(owner.append.dest)+owner.append.size,soloEnd=stepRuntime&&soloRuntime?n(soloRuntime.dest)+soloRuntime.hex.length/2:appendEnd,origin=(Math.max(appendEnd,soloEnd)+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer);
  for(const at of d.reloc)v.setUint32(at,v.getUint32(at,false)+origin,false);
  const hooks=[[0x400775f8,'wf_encoder_hook'],[0x40077720,'wf_key_hook'],[0x4001b22a,'wf_draw_hook']],values=[];
  for(const [at] of hooks){const old=read(at,8);if(!old.startsWith('4ef9'))throw Error('Pad mode: UI chain guard');values.push(parseInt(old.slice(4,12),16));}
  const scramble=r.tweaks.find(t=>t.symbols?.sc_key);if(!scramble)throw Error('Pad tap: SCRAMBLE handler missing');values.push(0,common?n(common.symbols.set_held):0,common?n(common.symbols.mod_used):0,n(scramble.symbols.sc_key),0,n(levelPan.symbols.lp_disabled));values.forEach((value,i)=>v.setUint32(d.symbols.wf_api+4*i,value,false));
  const q={id:'pad-selection',status:'experimental',order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[],symbols:{}};
  for(const [at,symbol] of hooks)q.writes.push({off:at-BASE,old:read(at,8),new:'4ef9'+h(origin+d.symbols[symbol])+'4e71'});
  if(read(0x4001d372,6)!=='4a0766d84a03')throw Error('Pad mode: native pad guard');q.writes.push({off:0x4001d372-BASE,old:'4a0766d84a03',new:'4ef9'+h(origin+d.symbols.wf_pad)});
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});owner.append.size=origin+raw.length-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;
  if(!owner.append.compress){if(!bootMeta)throw Error('Pad mode: beat-repeat loader metadata missing');const w=owner.writes.find(w=>w.off+BASE===bootMeta.at);if(!w)throw Error('Pad mode: loader guard');const code=b.fromHex(w.new);new DataView(code.buffer).setUint32(bootMeta.symbols.br_boot_size,owner.append.size,false);w.new=b.hex(code);}
  for(const [name,at] of Object.entries(d.symbols))if(name.startsWith('wf_'))q.symbols[name]='0x'+h(origin+at);
  r.tweaks.push(q);for(const t of [owner,q])r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};return r;
 };
});})();
