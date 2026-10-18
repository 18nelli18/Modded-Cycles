// References finales avant les compositions MIDI/audio : verification du runtime natif.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,previous=window.MCMidiBankCompose,hash=x=>b.hex(b.sha256(x));
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  for(const t of input.filter(t=>t.machine_selection!==undefined)){
   const ref=a.REF_MODS[t.id];if(!ref||hash(b.writesBytes(t))!==ref.w)throw Error('Machine selection: writes reference mismatch');
   const co=b.parseContainer(b.unwrap(cycles).stream),section=co.sections.find(s=>s.id===3),stock=b.aplibDepack(co.blob.subarray(section.off,section.off+section.size)).data;
   const packed=b.buildPayload(t.append,syntakt,stock);a.REF_MODS[t.id]={w:ref.w,p:hash(packed)};
  }
  return previous(input,cycles,syntakt);
 };
})();
