// Note123 : seule la source compressee de ChordKeys suit la nouvelle fin Swarm.
window.MCSwarmChordLayout=(changed,input,b,a,syntakt,stock,saved)=>{
 const n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>x.toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 const ck=changed.find(t=>t.id==='chord-keys-supermodel'&&t.append);
 if(!ck||!a.isSelected('sample-wizard'))return changed;
 const before=input.filter(t=>t.append&&t.order<ck.order).sort((x,y)=>y.order-x.order)[0];
 if(!before||n(before.append.dest)<0x46700000||before.append.compress!=='aplib')return changed;
 const engine=changed.find(t=>t.id===before.id);if(engine===before)return changed;
 const source=n(engine.append.at)+b.buildPayload(engine.append,syntakt,stock).length,old=n(ck.append.at);
 if(source===old)return changed;
 if(n(before.append.at)+b.buildPayload(before.append,syntakt,stock).length!==old)throw Error('Swarm/Chord layout: original source guard');
 const ref=a.REF_MODS[ck.id];if(!ref||hash(b.writesBytes(ck))!==ref.w||hash(b.buildPayload(ck.append,syntakt,stock))!==ref.p)throw Error('Swarm/Chord layout: reference guard');
 const copy=JSON.parse(JSON.stringify(ck)),boot=copy.writes.find(w=>w.off+0x40000400===n(copy.symbols.chord_boot)),prefix='41f9'+h(old)+'43f9'+h(n(copy.append.dest));
 if(!boot?.new.startsWith(prefix))throw Error('Swarm/Chord layout: loader source guard');
 boot.new='41f9'+h(source)+boot.new.slice(12);copy.append.at='0x'+h(source);
 saved.set(ck.id,{w:ref.w,p:ref.p});a.REF_MODS[ck.id]={w:hash(b.writesBytes(copy)),p:ref.p};
 return changed.map(t=>t===ck?copy:t);
};
