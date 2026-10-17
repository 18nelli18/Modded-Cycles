// Note 112 : optimisations test seulement, diagnostic conserve.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCAudioLoad,clone=x=>JSON.parse(JSON.stringify(x)),n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 window.MCAudioLoadReady=window.MCBeatDiagnosticReady.then(()=>{
 Object.assign(window.MCBeatDiagnostic,clone(d.repeat));
 const filterFeature=window.MC_TWEAKS.features.find(f=>f.id==='track-filter');filterFeature.status='experimental';filterFeature.hardwareTestedByOwner=false;
 const resolve=window.MCMainClearResolve;
 window.MCMainClearResolve=input=>resolve(input).map(t=>{
  if(!a.isSelected('track-filter')||t.id!=='sample-wizard')return t;
  const result=clone(t),f=d.filter,p=result.append.parts.find(p=>p.hex&&n(p.dest)<=f.at&&f.at+f.size<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Audio load: filter body missing');
  const i=2*(f.at-n(p.dest));if(hash(b.fromHex(p.hex.slice(i,i+2*f.size)))!==f.old_sha256)throw Error('Audio load: current filter guard');p.hex=p.hex.slice(0,i)+f.hex+p.hex.slice(i+2*f.size);delete result.append.compressed_hex;
  const inner=d.inner_call;if(inner){const q=result.append.parts.find(p=>p.hex&&n(p.dest)<=inner.at&&inner.at+inner.old.length/2<=n(p.dest)+p.hex.length/2);if(!q)throw Error('Wizard transition: inner filter call missing');const j=2*(inner.at-n(q.dest));if(q.hex.slice(j,j+inner.old.length)!==inner.old)throw Error('Wizard transition: inner filter call guard');q.hex=q.hex.slice(0,j)+inner.new+q.hex.slice(j+inner.old.length);}
  a.REF_MODS[result.id]={w:hash(b.writesBytes(result)),p:hash(b.buildPayload(result.append,null,null))};result.status='experimental';result.hardwareTestedByOwner=false;return result;
 });
 function filterProbe(result,syntakt,stock){
  const repeat=result.tweaks.find(t=>t.id==='control-all-beat-repeat');if(!repeat?.symbols.br_filter_f_address)return result;
  const wizard=result.tweaks.find(t=>t.id==='sample-wizard'),enabled=a.isSelected('track-filter')&&wizard;
  const values={br_filter_code_address:enabled?d.filter.at:0,br_filter_code_size:enabled?d.filter.probe_size:0,br_filter_code_hash:enabled?d.filter.probe_hash:0,br_filter_state_address:enabled?n(wizard.symbols.gflt_y1):0,br_filter_f_address:enabled?n(wizard.symbols.gflt_f):0,br_filter_q_address:enabled?n(wizard.symbols.gflt_q):0,br_filter_mk_address:enabled?n(wizard.symbols.gflt_mk):0,br_filter_modes_address:enabled?d.filter.mode_address:0};
  for(const [key,value] of Object.entries(values)){
   const at=n(repeat.symbols[key]),part=repeat.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+4<=n(p.dest)+p.hex.length/2);if(!part)throw Error('Filter probe: '+key);
   const off=2*(at-n(part.dest));part.hex=part.hex.slice(0,off)+h(value)+part.hex.slice(off+8);
  }
  delete repeat.append.compressed_hex;result.refMods[repeat.id]={w:hash(b.writesBytes(repeat)),p:hash(b.buildPayload(repeat.append,syntakt,stock))};return result;
 }
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args),c=b.parseContainer(b.unwrap(args[1]).stream),section=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(section.off,section.off+section.size)).data;if(!prior.tweaks.some(t=>t.id==='midi-out-bank'))return filterProbe(prior,args[2],stock);const result=clone(prior),bank=result.tweaks.find(t=>t.id==='midi-out-bank');
  const repeat=result.tweaks.find(t=>t.id==='control-all-beat-repeat'),owner=repeat||bank,ap=owner.append,origin=(n(ap.dest)+ap.size+15)&~15,sy=d.slides.symbols,raw=b.fromHex(d.slides.hex),v=new DataView(raw.buffer),bs=bank.symbols;
  for(const off of d.slides.reloc)v.setUint32(off,v.getUint32(off,false)+origin,false);
  const at=n(bs.mlkc_slide_tick),p=bank.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+8<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Audio load: slide body missing');const i=2*(at-n(p.dest)),old=p.hex.slice(i,i+16);if(old!=='4fefffd448d73cfc')throw Error('Audio load: slide prologue guard');
  raw.set(b.fromHex(old+'4ef9'+h(at+8)),sy.ao_tick_original);p.hex=p.hex.slice(0,i)+'4ef9'+h(origin+sy.ao_tick)+'4e71'+p.hex.slice(i+16);
  for(const [i,key] of ['ml_clock_state','ml_play_pattern','mlkcq_owner','mlkc_slide_rate','mlkc_slide_cursor','mlkc_slide_states'].entries()){if(!bs[key])throw Error('Audio load: slide API '+key);v.setUint32(sy.ao_api+4*i,n(bs[key]),false);}
  ap.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});ap.size=origin+raw.length-n(ap.dest);
  delete bank.append.compressed_hex;
  if(repeat){const source=n(bank.append.at)+b.buildPayload(bank.append,args[2],stock).length;ap.at='0x'+h(source);const loader=repeat.writes.find(w=>0x40000400+w.off===window.MCBeatRepeat.boot.at);if(!loader)throw Error('Audio load: repeat boot missing');const boot=b.fromHex(loader.new),bv=new DataView(boot.buffer),bootSy=window.MCBeatRepeat.boot.symbols;bv.setUint32(bootSy.br_boot_source,source,false);bv.setUint32(bootSy.br_boot_size,ap.size,false);loader.new=b.hex(boot);}
  owner.symbols={...owner.symbols,...Object.fromEntries(Object.entries(sy).filter(([key])=>key.startsWith('ao_')).map(([key,value])=>[key,'0x'+h(origin+value)]))};
  for(const t of new Set([bank,owner])){delete t.append.compressed_hex;result.refMods[t.id]={w:hash(b.writesBytes(t)),p:hash(b.buildPayload(t.append,args[2],stock))};t.status='experimental';t.hardwareTestedByOwner=false;}
  return filterProbe(result,args[2],stock);
 };
 });
})();
