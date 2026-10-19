// Note130 : promotion du menu pad seul, sans mutation du catalogue ou sampler.
(()=>{const b=window.MCBuilder,d=window.MCPadMode,BASE=0x40000400,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCPadModeReady=Promise.all([window.MCMacroFineReady]).then(()=>{
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  const co=b.parseContainer(b.unwrap(args[1]).stream),sec=co.sections.find(s=>s.id===3),stock=b.aplibDepack(co.blob.subarray(sec.off,sec.off+sec.size)).data,patched=b.applyWrites(stock,r.tweaks).data,read=(at,len)=>b.hex(patched.subarray(at-BASE,at-BASE+len));
  const common=r.tweaks.find(t=>t.symbols?.set_held),beat=r.tweaks.find(t=>t.id==='control-all-beat-repeat'),owner=r.tweaks.filter(t=>t.append).sort((x,y)=>n(y.append.at)-n(x.append.at))[0],origin=(n(owner.append.dest)+owner.append.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer);
  if(!beat||!beat.symbols?.br_popup||!d.symbols.wf_usb_popup)throw Error('USB mode: Pad Setup or popup data missing');
  for(const at of d.reloc)v.setUint32(at,v.getUint32(at,false)+origin,false);
  const hooks=[[0x400775f8,'wf_encoder_hook'],[0x40077720,'wf_key_hook'],[0x4001b22a,'wf_draw_hook']],values=[];
  for(const [at] of hooks){const old=read(at,8);if(!old.startsWith('4ef9'))throw Error('Pad mode: UI chain guard');values.push(parseInt(old.slice(4,12),16));}
  const scramble=r.tweaks.find(t=>t.symbols?.sc_key);if(!scramble)throw Error('Pad tap: SCRAMBLE handler missing');values.push(0,common?n(common.symbols.set_held):0,common?n(common.symbols.mod_used):0,n(scramble.symbols.sc_key));values.forEach((value,i)=>v.setUint32(d.symbols.wf_api+4*i,value,false));v.setUint32(d.symbols.wf_usb_popup,n(beat.symbols.br_popup),false);
  const q={id:'pad-selection',status:'experimental',order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[],symbols:{}};
  for(const [at,symbol] of hooks)q.writes.push({off:at-BASE,old:read(at,8),new:'4ef9'+h(origin+d.symbols[symbol])+'4e71'});
  if(read(0x4001d372,6)!=='4a0766d84a03')throw Error('Pad mode: native pad guard');q.writes.push({off:0x4001d372-BASE,old:'4a0766d84a03',new:'4ef9'+h(origin+d.symbols.wf_pad)});
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});owner.append.size=origin+raw.length-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;
  if(!owner.append.compress){const w=owner.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at);if(!w)throw Error('Pad mode: loader guard');const code=b.fromHex(w.new);new DataView(code.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,owner.append.size,false);w.new=b.hex(code);}
  for(const [name,at] of Object.entries(d.symbols))if(name.startsWith('wf_'))q.symbols[name]='0x'+h(origin+at);
  r.tweaks.push(q);for(const t of [owner,q])r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};return r;
 };
});})();
