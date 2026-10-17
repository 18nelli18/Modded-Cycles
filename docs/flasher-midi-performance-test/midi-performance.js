// Note 109 : extension test seulement, liee aux symboles du vrai build final.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMidiPerformanceData,clone=x=>JSON.parse(JSON.stringify(x)),n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 window.MCMidiPerformanceReady=window.MC909CurrentReady.then(()=>{
  const previous=window.MCMidiBankCompose;
  window.MCMidiBankCompose=(...args)=>{
   const result=clone(previous(...args)),bank=result.tweaks.find(t=>t.id==='midi-out-bank'),repeat=result.tweaks.find(t=>t.id==='control-all-beat-repeat'),config=result.tweaks.find(t=>t.symbols?.cac_mask);
   if(!bank||!repeat||!config)throw Error('MIDI performance: missing tested foundation');
   const bs=bank.symbols,rs=repeat.symbols,ap=repeat.append,origin=(n(ap.dest)+ap.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer),sy=d.symbols;
   for(const off of d.reloc)v.setUint32(off,v.getUint32(off,false)+origin,false);
   const get=(at,size)=>{for(const p of bank.append.parts){if(!p.hex)continue;const i=at-n(p.dest);if(i>=0&&i+size<=p.hex.length/2)return {p,i};}throw Error('MIDI performance: bank code range');};
   for(const [name,baseName,prologue] of [['step','ml_step','4fefffd448d73cfc'],['clock','ml_clock','4fefffd848d73c7c'],['enc','mlkc_enc','4fefffe848d70c1c']]){
    const at=n(bs[baseName]),{p,i}=get(at,8),old=p.hex.slice(2*i,2*i+16);
    if(old!==prologue)throw Error('MIDI performance: prologue guard '+baseName+' '+old);
    const tramp=sy['bp_'+name+'_original'];raw.set(b.fromHex(old+'4ef9'+h(at+8)),tramp);
    p.hex=p.hex.slice(0,2*i)+'4ef9'+h(origin+sy['bp_'+name])+'4e71'+p.hex.slice(2*i+16);
   }
   const api=[n(rs.br_keys),n(rs.br_requested),n(rs.br_cancel),n(config.symbols.cac_mask),n(bs.mlp_obj),n(bs.mlp_track),n(bs.ml_pattern),n(bs.ml_runtime),n(rs.br_divs),n(bs.ml_context),n(bs.ml_play_pattern),n(bs.ml_stop),0];
   api.forEach((value,i)=>{if(i<12&&!value)throw Error('MIDI performance: API guard '+i);v.setUint32(sy.bp_api+4*i,value,false);});
   const c=b.parseContainer(b.unwrap(args[1]).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
   // Le kit 909 reloge les descripteurs ; conserver aussi les deux filtres actuels.
   const filter=result.tweaks.find(t=>t.id==='wizard-continuous-filter');
   for(const off of [1104712,1104768]){
    const w=filter?.writes.find(w=>w.off===off);if(!w||w.new.length!==112)throw Error('MIDI performance: filter descriptor guard');
    const dest=0x46734000+(0x40000400+off-0x4010dce0);
    for(let i=0;i<56;i+=4){const at=dest+i,old=b.hex(stock.subarray(off+i,off+i+4)),nw=w.new.slice(2*i,2*i+8);if(old!==nw){if(bank.append.reloc.some(r=>n(r[0])===at))throw Error('MIDI performance: filter relocation occupied');bank.append.reloc.push(['0x'+h(at),old,nw]);}}
   }
   const packed=b.buildPayload(bank.append,null,stock),source=n(bank.append.at)+packed.length;
   ap.at='0x'+h(source);ap.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});ap.size=origin+raw.length-n(ap.dest);
   const loader=repeat.writes.find(w=>0x40000400+w.off===window.MCBeatRepeat.boot.at);if(!loader)throw Error('MIDI performance: loader missing');
   const boot=b.fromHex(loader.new),bv=new DataView(boot.buffer),bootSy=window.MCBeatRepeat.boot.symbols;
   bv.setUint32(bootSy.br_boot_source,source,false);bv.setUint32(bootSy.br_boot_size,ap.size,false);loader.new=b.hex(boot);
   repeat.symbols={...rs,...Object.fromEntries(Object.entries(sy).filter(([k])=>k.startsWith('bp_')).map(([k,value])=>[k,'0x'+h(origin+value)]))};
   for(const t of [bank,repeat]){delete t.append.compressed_hex;result.refMods[t.id]={w:hash(b.writesBytes(t)),p:hash(b.buildPayload(t.append,null,stock))};}
   return {...result,tweaks:result.tweaks.map(t=>({...t,status:'experimental',hardwareTestedByOwner:false}))};
  };
  window.MC909CurrentLabels.push('MIDI beat repeat test','B-side audio + MIDI Control All filter');
 });
})();
