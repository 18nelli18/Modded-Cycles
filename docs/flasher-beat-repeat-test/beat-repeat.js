// Note 99 : module autonome, aucune activation de Model-TG ni des FX master.
(()=>{
 'use strict';
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCBeatRepeat,ID='control-all-beat-repeat',BASE=0x40000400;
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,hex=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 window.MC_TWEAKS.features.push({id:ID,label:'Control All Beat Repeat',cat:'live',status:'experimental',variants:[{id:ID}],requires:null,excludes:[],credit:{kind:'by',who:'TinyGregAudio (MIT beat-repeat algorithm); independent adaptation by AveyCole / Modded-Cycles'},license:'LICENSE-Beat-Repeat.txt'});
 window.MC_TWEAKS.tweaks.push({id:ID,order:110,status:'experimental',writes:[],requires:[],conflicts:[]});
 a.registerFeatureTexts(ID,{
  en:{label:'Control All Beat Repeat',short:'Hold TRACK + RETRIG, then hold a TRIG for a tempo-synced repeat of the included audio tracks.',desc:'Experimental independent beat repeat. Active ONLY while holding TRACK + RETRIG: hold TRIG 1–16 to repeat the included audio tracks together. Follows Control All Config track selection when installed; otherwise all six tracks repeat. While both modifiers are held, the TRIG row shows repeat divisions instead of Control All options; release either modifier to restore normal options. Release either modifier to return to normal playback; release the TRIG to stop repeating. The newest held TRIG sets the rate. No dedicated screen, master FX or Model-TG installation. Rates 1–16: 1/64, 1/48, 1/32, 1/24, 1/16, 1/12, 1/8, 1/6, 3/16, 1/4, 1/3, 3/8, 1/2, 2/3, 3/4, one bar. Long slices halve at slow tempos to fit the audio history. MIDI output notes are not repeated. Hardware testing pending.'},
  fr:{label:'Beat Repeat collectif',short:'Maintenez TRACK + RETRIG puis un TRIG pour repeter les pistes audio incluses au tempo.',desc:'Beat repeat autonome experimental. Actif UNIQUEMENT avec TRACK + RETRIG maintenus : tenez TRIG 1–16 pour repeter les pistes audio incluses ensemble. Suit la selection Control All Config si installe ; sinon les six pistes repetent. Les deux modificateurs tenus, la rangee TRIG affiche les divisions au lieu des choix Control All ; relachez un modificateur pour retrouver les choix normaux. Relachez un modificateur pour revenir a la lecture normale ; relachez le TRIG pour arreter la repetition. Le dernier TRIG maintenu choisit la division. Aucun ecran dedie, FX master ou installation Model-TG. Divisions 1–16 : 1/64, 1/48, 1/32, 1/24, 1/16, 1/12, 1/8, 1/6, 3/16, 1/4, 1/3, 3/8, 1/2, 2/3, 3/4, une mesure. Les longues boucles sont reduites de moitie aux tempos lents pour tenir dans l historique. Notes MIDI sortantes non repetees. Test materiel attendu.'}
 });
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const active=a.isSelected(ID),base=previous(input.filter(t=>t.id!==ID),cycles,syntakt);if(!active)return base;
  const result={tweaks:clone(base.tweaks),refMods:{...base.refMods}};
  const container=b.parseContainer(b.unwrap(cycles).stream),main=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(main.off,main.off+main.size)).data;
  if(hash(stock)!==window.MC_TWEAKS.device.section_sha256)throw Error('Beat repeat: official Cycles OS required');
  const patched=stock.slice();let source=BASE+stock.length,origin=0x43000000;
  for(const t of result.tweaks.slice().sort((x,y)=>x.order-y.order)){
   for(const w of t.writes)patched.set(b.fromHex(w.new),w.off);
   if(t.append){const ap=t.append,packed=b.buildPayload(ap,syntakt,stock);source=Math.max(source,num(ap.at))+packed.length;origin=Math.max(origin,num(ap.dest)+ap.size);}
  }
  origin=(origin+15)&~15;
  const raw=b.fromHex(d.hex),view=new DataView(raw.buffer),s=d.symbols;
  for(const off of d.reloc)view.setUint32(off,view.getUint32(off,false)+origin,false);
  if(origin+raw.length>=0x47000000||source+raw.length>0x40200000)throw Error('Beat repeat: payload capacity');
  const read=(at,n)=>b.hex(patched.subarray(at-BASE,at-BASE+n));
  const key=read(0x4007240c,8),gain=read(0x4005982a,6),boot=read(0x40000530,10);
  if(key!=='206f00042028000c'&&!/^4ef9[0-9a-f]{8}(?:4e71|000c)$/.test(key))throw Error('Beat repeat: unknown key chain '+key);
  if(!/^4eb9[0-9a-f]{8}$/.test(gain))throw Error('Beat repeat: unknown audio chain');
  if(boot!=='4ebaff8041f9fc044000'&&!/^4ef9[0-9a-f]{8}4e714e71$/.test(boot)&&!/^4eb9[0-9a-f]{8}fc044000$/.test(boot))throw Error('Beat repeat: unknown startup chain '+boot);
  view.setUint32(s.br_old_key,key.startsWith('4ef9')?parseInt(key.slice(4,12),16):0,false);
  view.setUint32(s.br_old_gain,parseInt(gain.slice(4),16),false);
  const config=result.tweaks.find(t=>t.symbols?.cac_mask),oldTrackKey=parseInt(read(0x40100ee8,4),16),oldTrackLed=parseInt(read(0x40100f98,4),16);
  if(oldTrackKey!==(config?num(config.symbols.cac_keys):0x40024078)||oldTrackLed!==(config?num(config.symbols.cac_leds):0x40023d8c))throw Error('Beat repeat: unknown TRACK view');
  view.setUint32(s.br_mask_address,config?num(config.symbols.cac_mask):0,false);
  view.setUint32(s.br_old_track_keys,oldTrackKey,false);view.setUint32(s.br_old_track_leds,oldTrackLed,false);
  const wizard=result.tweaks.find(t=>t.id==='sample-wizard');
  if(wizard){if(!wizard.symbols.sx_side||!wizard.symbols.sx_on)throw Error('Beat repeat: missing stereo API');view.setUint32(s.br_side,num(wizard.symbols.sx_side),false);view.setUint32(s.br_side_on,num(wizard.symbols.sx_on),false);}
  const loader=b.fromHex(d.boot.hex),lv=new DataView(loader.buffer),ls=d.boot.symbols;
  for(const [name,value] of Object.entries({br_boot_source:source,br_boot_dest:origin,br_boot_size:raw.length,br_boot_next:/^4e[fb]9/.test(boot)?parseInt(boot.slice(4,12),16):0,br_boot_call:Number(boot.startsWith('4eb9'))}))lv.setUint32(ls[name],value,false);
  if(read(d.boot.at,loader.length)!==b.hex(stock.subarray(d.boot.at-BASE,d.boot.at-BASE+loader.length)))throw Error('Beat repeat: loader occupied by selection');
  const writes=[],add=(at,nw)=>writes.push({off:at-BASE,old:read(at,nw.length/2),new:nw});
  add(d.boot.at,b.hex(loader));add(BASE+d.redirect.off,d.redirect.new);
  add(0x4007240c,'4ef9'+hex(origin+s.br_key_hook)+'4e71');
  add(0x4005982a,'4eb9'+hex(origin+s.br_gain_hook));
  add(0x40000530,'4ef9'+hex(d.boot.at)+'4e714e71');
  add(0x40100ee8,hex(origin+s.br_track_keys));add(0x40100f98,hex(origin+s.br_track_leds));
  const symbols=Object.fromEntries(Object.entries(s).filter(([k])=>k.startsWith('br_')).map(([k,v])=>[k,'0x'+hex(origin+v)]));
  const t={id:ID,name:'Control All Beat Repeat',order:Math.max(110,...result.tweaks.map(t=>t.order+1)),status:'experimental',writes,requires:[],conflicts:[],symbols,append:{at:'0x'+hex(source),dest:'0x'+hex(origin),size:raw.length,parts:[{dest:'0x'+hex(origin),hex:b.hex(raw)}],reloc:[]},history_bytes:d.history_bytes*(wizard?2:1)};
  result.tweaks.push(t);result.refMods={...result.refMods,[ID]:{w:hash(b.writesBytes(t)),p:hash(raw)}};return result;
 };
 a.applyLang(document.documentElement.lang||'en');
})();
