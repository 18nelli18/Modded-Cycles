// Note 109 : extension test, liee aux vrais symboles ; profil 909 ou checklist main.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMidiPerformanceData,clone=x=>JSON.parse(JSON.stringify(x)),n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 const ready=window.MC909CurrentReady||new Promise(resolve=>setTimeout(resolve,60));
 window.MCMidiPerformanceReady=ready.then(()=>{
  const previous=window.MCMidiBankCompose;
  window.MCMidiBankCompose=(...args)=>{
   const result=clone(previous(...args)),bank=result.tweaks.find(t=>t.id==='midi-out-bank'),repeat=result.tweaks.find(t=>t.id==='control-all-beat-repeat'),config=result.tweaks.find(t=>t.symbols?.cac_mask),filter=result.tweaks.find(t=>t.id==='wizard-continuous-filter');
   if(!bank)return result;
   const bs=bank.symbols,rs=repeat?.symbols||{},owner=repeat||bank,ap=owner.append,origin=(n(ap.dest)+ap.size+15)&~15,raw=b.fromHex(d.hex),v=new DataView(raw.buffer),sy=d.symbols;
   for(const off of d.reloc)v.setUint32(off,v.getUint32(off,false)+origin,false);
   const get=(at,size)=>{for(const p of bank.append.parts){if(!p.hex)continue;const i=at-n(p.dest);if(i>=0&&i+size<=p.hex.length/2)return {p,i};}throw Error('MIDI performance: bank code range');};
   const hooks=[['step','ml_step','4fefffd448d73cfc'],['clock','ml_clock','4fefffd848d73c7c'],['enc','mlkc_enc','4fefffe848d70c1c'],['menu','mlp_menu_key','4feffff448d7040c'],['view_enc','mlp_enc','4feffff048d7041c'],['render','mlp_render','4ab9'+h(n(bs.mlkc_show))],['led','mlp_led','4fefffe848d70c3c']];
   for(const [name,baseName,prologue] of hooks){
    const size=prologue.length/2,at=n(bs[baseName]),{p,i}=get(at,size),old=p.hex.slice(2*i,2*i+2*size);
    if(old!==prologue)throw Error('MIDI performance: prologue guard '+baseName+' '+old);
    raw.set(b.fromHex(old+(size===6?'4e71':'')+'4ef9'+h(at+size)),sy['bp_'+name+'_original']);
    p.hex=p.hex.slice(0,2*i)+'4ef9'+h(origin+sy['bp_'+name])+(size===8?'4e71':'')+p.hex.slice(2*i+2*size);
   }
   const local=name=>origin+sy[name];
   const pointer=at=>{let value;for(const t of result.tweaks)for(const w of t.writes||[]){const i=at-0x40000400-w.off;if(i>=0&&i+4<=w.new.length/2)value=n(w.new.slice(2*i,2*i+8));}return value;};
   const trackKeys=pointer(0x40100ee8)||0x40024078,trackLeds=pointer(0x40100f98)||0x40023d8c;
   const api=[n(rs.br_keys)||local('bp_zero'),n(rs.br_requested)||local('bp_none'),n(rs.br_cancel)||local('bp_zero'),config?n(config.symbols.cac_mask):local('bp_mask'),n(bs.mlp_obj),n(bs.mlp_track),n(bs.ml_pattern),n(bs.ml_runtime),n(rs.br_divs)||local('bp_zero'),n(bs.ml_context),n(bs.ml_play_pattern),n(bs.ml_stop),n(rs.br_key)||0,n(rs.br_leds)||0,n(bs.TG_blk_clk),n(bs.mlp_redraw),n(bs.mlkc_show),n(bs.mlkc_time),Number(!!filter),n(bs.TG_set_held),n(bs.ml_genie_settings),n(bs.mlp_func),Number(!!config),trackKeys,trackLeds];
   api.forEach((value,i)=>{if(![18,22,12,13].includes(i)&&!value)throw Error('MIDI performance: API guard '+i);v.setUint32(sy.bp_api+4*i,value,false);});
   const c=b.parseContainer(b.unwrap(args[1]).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
   // Reporter le filtre aussi dans une table moteurs relogee, si elle existe.
   if(filter)for(const off of [1104712,1104768]){
    const w=filter.writes.find(w=>w.off===off);if(!w||w.new.length!==112)throw Error('MIDI performance: filter descriptor guard');
    const va=0x40000400+off,part=bank.append.parts.find(p=>p.cycles&&n(p.cycles[0])<=va&&va+56<=n(p.cycles[1])&&n(p.dest)>=0x43000000);
    if(!part)continue;
    const dest=n(part.dest)+va-n(part.cycles[0]);
    for(let i=0;i<56;i+=4){const at=dest+i,old=b.hex(stock.subarray(off+i,off+i+4)),nw=w.new.slice(2*i,2*i+8);if(old!==nw){if(bank.append.reloc.some(r=>n(r[0])===at))throw Error('MIDI performance: filter relocation occupied');bank.append.reloc.push(['0x'+h(at),old,nw]);}}
   }
   for(const [at,name,old] of [[0x40100ee8,'bp_track_keys',trackKeys],[0x40100f98,'bp_track_leds',trackLeds]]){
    const off=at-0x40000400,w=owner.writes.find(w=>w.off===off);
    if(w)w.new=h(local(name));else owner.writes.push({off,old:h(old),new:h(local(name))});
   }
   ap.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});ap.size=origin+raw.length-n(ap.dest);
   if(repeat){
    const packed=b.buildPayload(bank.append,args[2],stock),source=n(bank.append.at)+packed.length;ap.at='0x'+h(source);
    const loader=repeat.writes.find(w=>0x40000400+w.off===window.MCBeatRepeat.boot.at);if(!loader)throw Error('MIDI performance: loader missing');
    const boot=b.fromHex(loader.new),bv=new DataView(boot.buffer),bootSy=window.MCBeatRepeat.boot.symbols;
    bv.setUint32(bootSy.br_boot_source,source,false);bv.setUint32(bootSy.br_boot_size,ap.size,false);loader.new=b.hex(boot);
   }
   owner.symbols={...owner.symbols,...Object.fromEntries(Object.entries(sy).filter(([k])=>k.startsWith('bp_')).map(([k,value])=>[k,'0x'+h(origin+value)]))};
   for(const t of new Set([bank,owner])){delete t.append.compressed_hex;result.refMods[t.id]={w:hash(b.writesBytes(t)),p:hash(b.buildPayload(t.append,args[2],stock))};}
   return {...result,tweaks:result.tweaks.map(t=>({...t,status:'experimental',hardwareTestedByOwner:false}))};
  };
  if(window.MC909CurrentLabels)window.MC909CurrentLabels.push('MIDI repeat from A/B','B-side filter controls: audio + MIDI');
 });
})();
