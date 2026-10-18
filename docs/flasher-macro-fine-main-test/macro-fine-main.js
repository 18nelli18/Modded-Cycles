// Accordage fin dans PITCH natif ; FINE et le DSP lo-fi restent inchanges.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMacroFine,BASE=0x40000400,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
window.MCMacroFineReady=Promise.all([window.MCMidiMachineAllReady,window.MCBeatDiagnosticReady]).then(()=>{
 const previous=window.MCMidiBankCompose;window.MCMacroFineBaseCompose=previous;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(...args);if(!a.isSelected('macro'))return prior;
  const r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}},container=b.parseContainer(b.unwrap(args[1]).stream),section=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data,patched=b.applyWrites(stock,r.tweaks).data;
  const read=(at,len)=>b.hex(patched.subarray(at-BASE,at-BASE+len)),knob=read(0x4001e8da,8),key=read(0x40077720,8);if(!/^4eb9[0-9a-f]{8}4e71$/.test(knob)||(!key.startsWith('4ef9')&&key!=='4fefffa048d77cfc'))throw Error('MACRO fine: hook guard');
  const owner=r.tweaks.filter(t=>t.append).sort((x,y)=>n(y.append.at)-n(x.append.at))[0];if(!owner)throw Error('MACRO fine: payload required');
  const origin=(n(owner.append.dest)+owner.append.size+15)&~15,raw=b.fromHex(d.hex),view=new DataView(raw.buffer);
  for(const i of d.reloc)view.setUint32(i,view.getUint32(i,false)+origin,false);
  const index=6+Number(a.isSelected('sample-wizard'))+a.chosenEngines().filter(e=>['sd','cp','toy','bits','swarm'].includes(e.code)).length,used=r.tweaks.find(t=>t.symbols?.mod_used);
  for(const [i,value] of [index,used?n(used.symbols.mod_used):0,parseInt(knob.slice(4,12),16),key.startsWith('4ef9')?parseInt(key.slice(4,12),16):0,used?.symbols?.set_held?n(used.symbols.set_held):0].entries())view.setUint32(d.symbols.mf_api+4*i,value,false);
  owner.append.parts.push({dest:'0x'+h(origin),hex:b.hex(raw)});owner.append.size=origin+raw.length-n(owner.append.dest);delete owner.append.compressed_hex;delete owner.append.stored;
  if(!owner.append.compress){const w=owner.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at);if(!w)throw Error('MACRO fine: loader guard');const code=b.fromHex(w.new);new DataView(code.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_size,owner.append.size,false);w.new=b.hex(code);}
  const q={id:'macro-fine-test',status:'experimental',order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[{off:0x4001e8da-BASE,old:knob,new:'4eb9'+h(origin+d.symbols.mf_knob)+'4e71'},{off:0x40077720-BASE,old:key,new:'4ef9'+h(origin+d.symbols.mf_key_hook)+'4e71'}],symbols:{macro_fine_index:'0x'+h(index)}};
  for(const [name,at] of Object.entries(d.symbols))if(name.startsWith('mf_'))q.symbols[name]='0x'+h(origin+at);
  r.tweaks.push(q);for(const t of [owner,q])r.refMods[t.id]={w:hash(b.writesBytes(t)),...(t.append?{p:hash(b.buildPayload(t.append,args[2],stock))}:{})};return r;
 };
 a.registerFeatureTexts('macro',{en:{label:'MACRO',short:'SETTINGS + PITCH: fine tune. FUNC + PITCH: Lo-Fi.',desc:'Test adds fine pitch on SETTINGS + PITCH at1/128semitone per step (about0.78cent). Normal pitch changes retain the fine fraction. FUNC + PITCH remains sample-rate/bit reduction. Fine adjustment is saved in native PITCH and does not change the synthesis code. CPU/CUT diagnostic available. Hardware verification pending.'},fr:{label:'MACRO',short:'SETTINGS + PITCH : accord fin. FUNC + PITCH : Lo-Fi.',desc:'Test : SETTINGS + PITCH accorde a1/128demi-ton par pas (environ0,78cent). PITCH normal conserve la fraction fine. FUNC + PITCH reste reduction frequence/bits. Accord sauvegarde dans PITCH natif, sans changer le code de synthese. Diagnostic CPU/CUT disponible. Verification materielle attendue.'}});a.applyLang(document.documentElement.lang||'en');
});})();
