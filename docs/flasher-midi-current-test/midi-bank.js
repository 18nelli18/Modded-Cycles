// Banque RAM : relier des corps propres epingles aux supports A selectionnes.
// Les empreintes de CHAQUE recette d'origine sont verifiees avant composition.
(()=>{
 'use strict';
 const a=window.MCFlasherApp,b=window.MCBuilder,tw=window.MC_TWEAKS,data=window.MCMidiCurrent;
 const ID='midi-out-bank',BASE=0x40000400,END=0x40200000;
 const clone=x=>JSON.parse(JSON.stringify(x)),hex=n=>(n>>>0).toString(16).padStart(8,'0');
 const number=x=>typeof x==='string'?parseInt(x,16):x;
 const hash=x=>b.hex(b.sha256(x)),whash=t=>hash(b.writesBytes(t));
 const on=id=>a.isSelected(id),align=n=>(n+15)&~15;
 const LEDS=[0x400ff9b8,0x400ffa78,0x40103070,0x401031b4,0x40107e18];
 tw.features.push({id:ID,label:'MIDI OUT Bank',cat:'seq',status:'tested',hardwareTestedByOwner:true,variants:[{id:ID}],requires:null,excludes:[],credit:{kind:'by',who:'AveyCole / Modded-Cycles contributors; MIT performance helpers by TinyGregAudio'}});
 tw.tweaks.push({id:ID,order:99,writes:[],requires:[],conflicts:[],status:'tested'});
 const texts={en:{label:'MIDI OUT Bank',short:'Six parallel MIDI tracks. Install alone or with your chosen machines.',desc:'Independent RAM-only MIDI Bank, hardware tested by AveyCole. FUNC + SETTINGS + TRACK opens or closes B-side. SETTINGS + a gray knob assigns CC; hold a TRIG and turn the knob for CC locks. Retains slides, retrigger, chance, live recording and two MIDI CC LFOs. TEMPO opens the native tempo menu and returns to B. No other card is forced. B-side data is lost on power-off; Save Project saves A only. Hardware tested by AveyCole.'},fr:{label:'Banque MIDI OUT',short:'Six pistes MIDI paralleles. Seule ou avec les machines choisies.',desc:'Banque MIDI autonome en RAM, testee sur machine par AveyCole. FUNC + SETTINGS + TRACK ouvre/ferme B. SETTINGS + potard gris assigne le CC ; tenir un TRIG et tourner le potard cree un lock CC. Slides, retrigger, chance, enregistrement live et deux LFO CC conserves. TEMPO ouvre le menu natif puis revient a B. Aucune autre carte imposee. Donnees B perdues a extinction ; Save Project sauvegarde A seulement. Testee sur machine par AveyCole.'}};
 a.registerFeatureTexts(ID,texts);
 for(const id of ['scale-gen','scramble']){
  const f=tw.features.find(f=>f.id===id);if(!f)continue;
  const previous=Object.getOwnPropertyDescriptor(f,'requires'),value=f.requires;
  Object.defineProperty(f,'requires',{configurable:true,get:()=>on(ID)?null:(previous?.get?previous.get.call(f):value)});
 }
 function mainImage(raw){const c=b.parseContainer(b.unwrap(raw).stream),s=c.sections.find(s=>s.id===3);if(!s)throw Error('MIDI Bank: MAIN section missing');const image=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;if(hash(image)!==tw.device.section_sha256)throw Error('MIDI Bank: official Cycles OS required');return image;}
 function runtime(ap,syntakt,stock){
  const out=new Uint8Array(ap.size),dest=number(ap.dest),st=ap.syntakt?b.syntaktSection(syntakt,ap.syntakt.section):null;
  for(const p of ap.parts){const range=p.syntakt||p.cycles,bytes=range?(p.syntakt?st:stock).subarray(number(range[0])-BASE,number(range[1])-BASE):b.fromHex(p.hex);out.set(bytes,number(p.dest)-dest);}
  for(const [va,old,nw] of ap.reloc||[]){const i=number(va)-dest;if(b.hex(out.subarray(i,i+4))!==old)throw Error('MIDI Bank: relocation guard');out.set(b.fromHex(nw),i);}return out;
 }
 function remapHex(text,map,lo,hi,delta){
  let out=text;for(let i=0;i+8<=text.length;i+=4){const value=parseInt(text.slice(i,i+8),16),next=map.has(value)?map.get(value):(value>=lo&&value<hi?value+delta:value);if(next!==value)out=out.slice(0,i)+hex(next)+out.slice(i+8);}return out;
 }
 const cache=new Map();
 function compose(input,cycles,syntakt){
  if(!on(ID))return {tweaks:input,refMods:a.REF_MODS};
  const original=input.filter(t=>t.id!==ID),key=['scale-gen','lfo-secondary','scramble'].map(id=>Number(on(id))).join('');
  const stamp=key+':'+hash(new TextEncoder().encode(JSON.stringify(original)));
  if(cache.has(stamp))return clone(cache.get(stamp));
  const stock=mainImage(cycles),row=clone(data.variants[key]),rawOld=row.bank.append.parts[0].hex;
  if(hash(b.fromHex(rawOld))!==row.raw_sha256)throw Error('MIDI Bank: pinned backend hash mismatch');
  const payloads=new Map();
  for(const t of original){
   const ref=a.REF_MODS[t.id];if(!ref||whash(t)!==ref.w)throw Error('MIDI Bank: untrusted original writes '+t.id);
   if(t.append){const packed=b.buildPayload(t.append,syntakt,stock);if(hash(packed)!==ref.p)throw Error('MIDI Bank: untrusted original payload '+t.id);payloads.set(t.id,runtime(t.append,syntakt,stock));}
  }
  const oldPatched=b.applyWrites(stock,original).data;
  const result=clone(original),engine=result.find(t=>t.append&&number(t.append.dest)>=0x43000000);
  const owner=result.find(t=>['sample-wizard','supermodel-support-independent','supermodel-wave-support'].includes(t.id));
  const joint=engine?clone(engine.append):{dest:'0x43000000',size:0,parts:[],reloc:[]};
  const rootDest=number(joint.dest),midiAt=engine?align(rootDest+joint.size):rootDest;
  const oldLo=number(row.bank.append.dest),oldHi=oldLo+row.bank.append.size,delta=midiAt-oldLo,map=new Map([[oldHi,midiAt+row.bank.append.size]]);
  const bind=(old,newer)=>{if(!old||!newer)return;for(const [name,value] of Object.entries(old))if(!['blob_start','reserved_end'].includes(name)&&newer[name]!==undefined){const from=number(value),to=number(newer[name]);map.set(from,to);}};
  if(owner){
   bind(row.core.symbols,owner.symbols);
   const aliases={TG_blk_clk:'blk_clk',TG_key_state:'key_state',TG_mod_used:'mod_used',TG_scale_state:'scale_state',TG_set_held:'set_held',TG_show_popup:'show_popup',TG_slide_phase:'sld_phase',TG_snap_note:'snap_note'};
   for(const [from,to] of Object.entries(aliases))if(row.bank.symbols[from]&&owner.symbols?.[to])map.set(number(row.bank.symbols[from]),number(owner.symbols[to]));
  }
  for(const support of row.supports){const current=result.find(t=>t.id===support.id||t.id.startsWith(support.id.split('-st')[0]));if(current)bind(support.symbols,current.symbols);}
  // Les cibles de chaine peuvent etre des alias de symboles, pas des fonctions B.
  const moved=value=>map.has(value)?map.get(value):(value>=oldLo&&value<oldHi?value+delta:value);
  const syms=Object.fromEntries(Object.entries(row.bank.symbols).map(([k,v])=>[k,'0x'+hex(moved(number(v)))]));
  let raw=remapHex(rawOld,map,oldLo,oldHi,delta);
  const addPart=(at,text)=>{joint.parts.push({dest:'0x'+hex(at),hex:text});joint.size=Math.max(joint.size,at-rootDest+text.length/2);};
  addPart(midiAt,raw);
  let next=align(midiAt+raw.length/2),copies=[],protectedSpans=[];
  for(const t of result.filter(t=>t.append&&t!==engine)){
   const at=number(t.append.dest),bytes=payloads.get(t.id);
   if(at>=0x43000000)throw Error('MIDI Bank: unsupported second engine payload');
   const text=b.hex(bytes)+('00'.repeat((-bytes.length)&3));addPart(next,text);copies.push([next,at,text.length/8]);protectedSpans.push([at&~15,align(at+bytes.length)]);next=align(next+text.length/2);
  }
  // RETROSYN/Chord partage deja son code dans la charge moteurs.
  if(engine?.chord_source&&result.some(t=>t.id==='chord-keys-supermodel'&&!t.append)){
   const p=joint.parts.find(p=>p.dest===engine.chord_source);if(!p)throw Error('MIDI Bank: shared Chord source missing');copies.push([number(p.dest),0x401c383c,p.hex.length/8]);protectedSpans.push([0x401c3830,0x401c5dd0]);
  }
  let initializer=0;
  if(engine&&engine.append.compress!=='aplib'){
   // Les anciens chargeurs PACK font aussi l'init des SRAM et tables CHORD.
   // Les rappeler sur une source RAM non compressee garde exactement cet ABI.
   const ap=engine.append,rt=payloads.get(engine.id),pieces=ap.pack?ap.pack.map(([at,n])=>rt.subarray(number(at)-number(ap.dest),number(at)-number(ap.dest)+n)):[rt];
   const n=pieces.reduce((n,p)=>n+p.length,0),packed=new Uint8Array(n);let i=0;for(const p of pieces){packed.set(p,i);i+=p.length;}
   const source=next;addPart(source,b.hex(packed));next=align(next+packed.length);
   const stub=engine.writes.find(w=>w.off===0x4016cae8-BASE);if(!stub)throw Error('MIDI Bank: PACK startup missing');
   let body=stub.new;const sig='41f9'+hex(number(ap.at)),where=body.indexOf(sig);if(where<0)throw Error('MIDI Bank: PACK source missing');
   body=body.slice(0,where)+'41f9'+hex(source)+body.slice(where+12);
   const tail='4feffff048d700f04ef9400004ba';let off=body.indexOf(tail),size=14;
   if(off<0){off=body.indexOf('4ef9'+hex(number(owner?.symbols?.boot_extra_hook)));size=6;}
   if(off<0)throw Error('MIDI Bank: PACK return missing');body=body.slice(0,off)+'4e75'+'4e71'.repeat((size-2)/2)+body.slice(off+size*2);
   initializer=next;body=remapHex(body,new Map(),BASE+stub.off,BASE+stub.off+stub.new.length/2,initializer-BASE-stub.off);
   addPart(initializer,body);next=align(next+body.length/2);
  }
  const stageAt=next,stage=b.fromHex(data.boot.hex),bs=data.boot.symbols;
  const putLong=(name,value)=>new DataView(stage.buffer).setUint32(bs[name],value>>>0,false);
  putLong('midi_current_wizard',Number(result.some(t=>t.id==='sample-wizard')));putLong('midi_current_context',number(syms.ml_context));putLong('midi_current_drain',number(syms.ml_ui_drain));
  putLong('midi_current_init',initializer);
  if(copies.length>=8)throw Error('MIDI Bank: startup copy capacity');
  copies.forEach((r,i)=>r.forEach((v,j)=>new DataView(stage.buffer).setUint32(bs.midi_current_copies+12*i+4*j,v>>>0,false)));
  protectedSpans.sort((x,y)=>x[0]-y[0]);const merged=[];for(const r of protectedSpans){const last=merged.at(-1);if(last&&r[0]<=last[1])last[1]=Math.max(last[1],r[1]);else merged.push(r.slice());}
  if(merged.length>=8)throw Error('MIDI Bank: startup skip capacity');
  merged.forEach((r,i)=>r.forEach((v,j)=>new DataView(stage.buffer).setUint32(bs.midi_current_skips+8*i+4*j,v>>>0,false)));
  // Pas de service UI Banque avant sa premiere ouverture ; prepare reste dans ml_toggle.
  const uiOffset=number(syms.ml_ui_hook)-midiAt,call='4eb9'+hex(number(syms.ml_ui_drain));
  const ui=raw.slice(uiOffset*2,(uiOffset+80)*2),i=ui.indexOf(call);if(i<0||ui.indexOf(call,i+1)>=0)throw Error('MIDI Bank: UI guard site');
  raw=raw.slice(0,uiOffset*2+i)+'4eb9'+hex(stageAt+bs.midi_current_safe_ui)+raw.slice(uiOffset*2+i+12);
  joint.parts.find(p=>number(p.dest)===midiAt).hex=raw;
  const writes=[],read=(at,n)=>b.hex(oldPatched.subarray(at-BASE,at-BASE+n));
  const overlay=(at,nw,expected)=>{const old=read(at,nw.length/2);if(expected&&old!==expected)throw Error('MIDI Bank: hook guard '+at.toString(16)+' '+old+' != '+expected);writes.push({off:at-BASE,old,new:nw});};
  if(!owner){
   const core=clone(row.core);core.id='midi-bank-support';core.requires=[];core.conflicts=[];delete core.append;
   core.writes=core.writes.filter(w=>![0x130,0x400792f2-BASE,0x400792bc-BASE].includes(w.off)).map(w=>({...w,new:remapHex(w.new,map,oldLo,oldHi,delta)}));
   if(engine)engine.writes=engine.writes.filter(w=>!LEDS.includes(BASE+w.off));
   core.symbols=Object.fromEntries(Object.entries(core.symbols).map(([k,v])=>[k,'0x'+hex(moved(number(v)))]));result.push(core);
  }
  const withCore=b.applyWrites(stock,result).data;
  // Les seuls hooks musicaux repris du backend, hors chargement/cache historiques.
  const bootstrap=new Set([number(row.bank.symbols.ml_boot_copy),number(row.bank.symbols.ml_depack)]);
  const bootstrapRows=row.bank.writes.filter(w=>[...bootstrap].some(at=>BASE+w.off<=at&&at<BASE+w.off+w.new.length/2));
  const bootRedirs=new Set();for(const w of bootstrapRows)for(const r of row.bank.writes)if(r.new.length===8&&r.old===hex(BASE+w.off))bootRedirs.add(r.off);
  for(const w of row.bank.writes){
   if(w.off===0x130||[0x400792f2-BASE,0x400792bc-BASE].includes(w.off)||bootstrapRows.includes(w)||bootRedirs.has(w.off))continue;
   const nw=remapHex(w.new,map,oldLo,oldHi,delta),expected=remapHex(w.old,map,oldLo,oldHi,delta),at=BASE+w.off;
   const actual=b.hex(withCore.subarray(w.off,w.off+w.old.length/2));
   if(at===0x40184a22&&actual==='4eb940159350'&&expected==='203c40152d38'){
    // Genie actuel construit ses descripteurs avant de rendre le callback D0.
    // Garder ce helper et changer uniquement la valeur retour du renderer.
    const helper=0x40159350,code=b.hex(withCore.subarray(helper-BASE,helper-BASE+64)),i=code.indexOf(expected);
    if(i<0||code.indexOf(expected,i+1)>=0)throw Error('MIDI Bank: Genie render helper guard');
    writes.push({off:helper-BASE+i/2,old:expected,new:nw});continue;
   }   if(actual!==expected)throw Error('MIDI Bank: musical chain guard '+at.toString(16)+' '+actual+' != '+expected);
   writes.push({off:w.off,old:actual,new:nw});
  }
  let loader,decoder,after=0;
  if(engine){
   const stub=engine.writes.find(w=>w.off===0x4016cae8-BASE);if(!stub)throw Error('MIDI Bank: unknown machine startup');
   if(engine.append.compress==='aplib'){
    // Garder le decodeur, SRAM et tables CHORD du moteur deja valide.
    const source=number(engine.append.at),sig='41f9'+hex(source),where=stub.new.indexOf(sig);
    if(where<0)throw Error('MIDI Bank: machine source guard');
    overlay(BASE+stub.off+where/2,'41f9'+hex(BASE+stock.length),sig);
    const tail='4feffff048d700f04ef9400004ba';let off=stub.new.indexOf(tail),size=14;
    if(off<0){const target=owner?.symbols?.boot_extra_hook;if(!target)throw Error('MIDI Bank: machine return guard');off=stub.new.indexOf('4ef9'+hex(number(target)));size=6;}
    if(off<0)throw Error('MIDI Bank: machine startup return missing');
    overlay(BASE+stub.off+off/2,'4ef9'+hex(stageAt)+'4e71'.repeat((size-6)/2));
   }else{
    loader=0x4016cae8;decoder=loader+64;
    const d=bootstrapRows.find(w=>BASE+w.off===number(row.bank.symbols.ml_depack));if(!d)throw Error('MIDI Bank: decoder source');overlay(decoder,d.new);
   }
  }else if(owner?.id==='sample-wizard'){
   loader=0x4016cae8;decoder=loader+64;
   const d=bootstrapRows.find(w=>BASE+w.off===number(row.bank.symbols.ml_depack));if(!d)throw Error('MIDI Bank: Wizard decoder source');overlay(decoder,d.new);
   const red=read(0x400b1106,4);if(red==='4016cae8')overlay(0x400b1106,'40154ae4',red);else if(red!=='40154ae4')throw Error('MIDI Bank: startup sprite guard');
   overlay(0x40000530,'4ef9'+hex(loader)+'4e714e71');
  }else if(owner){
   const root=b.hex(oldPatched.subarray(0x130,0x13a));if(!root.startsWith('4ef9'))throw Error('MIDI Bank: independent support root');loader=parseInt(root.slice(4,12),16);
   const stub=owner.writes.find(w=>BASE+w.off===loader);if(!stub)throw Error('MIDI Bank: independent loader missing');
   const match=stub.new.match(/4eb9([0-9a-f]{8})/);if(!match)throw Error('MIDI Bank: independent decoder missing');decoder=parseInt(match[1],16);
  }else{
   loader=number(row.bank.symbols.ml_boot_copy);decoder=number(row.bank.symbols.ml_depack);
   for(const w of bootstrapRows){if(BASE+w.off===loader)continue;writes.push(clone(w));}
   for(const w of row.bank.writes.filter(w=>bootRedirs.has(w.off)))writes.push(clone(w));
   overlay(0x40000530,'4ef9'+hex(loader)+'4e714e71');
  }
  if(loader){const code='41f9'+hex(BASE+stock.length)+'43f9'+hex(rootDest)+'4fefffe848d7047c4eb9'+hex(decoder)+'4cd7047c4fef0018203c000cc1004e7b00024e714ef9'+hex(stageAt);overlay(loader,code);}
  for(let index=0;index<LEDS.length;index++){
   const at=LEDS[index],old=b.hex(withCore.subarray(at-BASE,at-BASE+4)),target=parseInt(old,16);
   const marker='4ef9'+hex(0xf0010000+4*index),s=b.hex(stage),offset=s.indexOf(marker);if(offset<0)throw Error('MIDI Bank: LED guard template');stage.set(b.fromHex('4ef9'+hex(target)),offset/2);
   writes.push({off:at-BASE,old,new:hex(stageAt+bs['midi_current_led'+index])});
  }
  addPart(stageAt,b.hex(stage));
  const blocks=merged.length?Math.ceil(Math.max(0,Math.max(...merged.map(r=>r[1]))-0x401ab750)/16384):0;
  for(const [at,value] of [[0x400792f2,0x401eb750+20*blocks],[0x400792bc,0x401eb750+20*(blocks+1)+16]])overlay(at,hex(value));
  for(const t of result)delete t.append;
  joint.at='0x'+hex(BASE+stock.length);joint.compress='aplib';joint.compress_cost=128;joint.compress_margin=0;delete joint.pack;delete joint.compressed_hex;delete joint.compress_depth;delete joint.stored;
  const recipe={id:ID,order:99,name:'Banque MIDI OUT autonome — RAM',device:'Model:Cycles',os:'1.13',section:3,status:'tested',requires:result.map(t=>t.id),conflicts:[],writes,symbols:{...syms,midi_current_stage:'0x'+hex(stageAt),midi_current_safe_ui:'0x'+hex(stageAt+bs.midi_current_safe_ui)},append:joint,cache_blocks:blocks,ram_only_rollback:true,midi_tempo_native:true,hardwareTestedByOwner:true};
  let packed=b.buildPayload(joint,syntakt,stock);
  if(BASE+stock.length+packed.length>END){joint.compress_cost=512;packed=b.buildPayload(joint,syntakt,stock);}
  if(BASE+stock.length+packed.length>END)throw Error('MIDI Bank: selected firmware exceeds storage limit');
  joint.stored=packed.length;
  const final=result.concat(recipe).sort((x,y)=>x.order-y.order),refMods={};
  for(const t of final)refMods[t.id]={w:whash(t),...(t.append?{p:hash(packed)}:{})};
  b.applyWrites(stock,final);
  const value={tweaks:final,refMods};cache.set(stamp,clone(value));return value;
 }
 window.MCMidiBankCompose=compose;
 a.applyLang(document.documentElement.lang||'en');
})();
