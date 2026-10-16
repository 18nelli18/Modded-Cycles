// Note 103 : reutiliser le rendu actuel ; partager le choix de frontiere A/B.
(()=>{
 'use strict';
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCGenieTiming,previous=window.MCMidiBankCompose;
 const clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,hex=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x));
 a.registerFeatureTexts('scale-gen',{
  en:{label:'Sequence Genie — timing test',short:'Generate first; Queue selects Loop or Page on both sides.',desc:'SETTINGS + PAGE opens Sequence Genie. Generate is first and Queue is second. Click DATA on Queue, choose Loop (next selected-track loop) or Page (next 16-step page), then click to finish. During playback, Generate waits for that boundary on the audio A-side or MIDI B-side. The timing row replaces the incorrect Sound 0/1 display. Stop playback for A-side Undo. Experimental restoration; hardware verification pending.'},
  fr:{label:'Sequence Genie — test timing',short:'Generate puis Queue : Loop ou Page des deux cotes.',desc:'SETTINGS + PAGE ouvre Sequence Genie. Generate est premier, Queue deuxieme. Cliquer DATA sur Queue, choisir Loop (prochaine boucle de piste) ou Page (prochaine page de 16 pas), puis confirmer. En lecture, Generate attend cette frontiere cote audio A ou MIDI B. Remplace le faux Sound 0/1. Arreter pour Undo cote A. Restauration experimentale ; verification materielle attendue.'}
 });
 const feature=window.MC_TWEAKS.features.find(f=>f.id==='scale-gen');feature.status='experimental';delete feature.hardwareTestedByOwner;
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const original=previous(input,cycles,syntakt);if(!a.isSelected('scale-gen'))return original;
  const oldBank=original.tweaks.find(t=>t.id==='midi-out-bank');if(!oldBank)return original;
  const result=clone(original),bank=result.tweaks.find(t=>t.id===oldBank.id),sg=result.tweaks.find(t=>t.symbols?.sg_q_hook);
  if(!sg)throw Error('Genie timing: current audio menu missing');
  const native=num(sg.symbols.sg_render),entry=num(bank.symbols.sg_render),boundary=num(bank.symbols.ml_genie_boundary),helper=entry+6;
  const mode=0x4015fb80;
  function part(at,n){const p=bank.append.parts.find(p=>p.hex&&num(p.dest)<=at&&at+n<=num(p.dest)+p.hex.length/2);if(!p)throw Error('Genie timing: payload span missing');return [p,(at-num(p.dest))*2];}
  function read(at,n){const [p,i]=part(at,n);return p.hex.slice(i,i+2*n);}
  function patch(at,was,now){if(was.length!==now.length||read(at,was.length/2)!==was)throw Error('Genie timing: guarded body mismatch');const [p,i]=part(at,was.length/2);p.hex=p.hex.slice(0,i)+now+p.hex.slice(i+was.length);}
  if(read(entry,14)!=='4ab9'+hex(num(bank.symbols.sg_intro))+'67064ef9'+hex(num(bank.symbols.sg_large_intro)))throw Error('Genie timing: renderer ABI changed');
  const oldBoundary=read(boundary,6);if(!/^4a816600[0-9a-f]{4}$/.test(oldBoundary))throw Error('Genie timing: boundary ABI changed');
  // Exiger que le choix du menu courant pointe bien sur le mode Page/Loop.
  const fields=num(sg.symbols.sg_fields),slot=fields+14*16,owner=sg.writes.find(w=>w.off+0x40000400<=slot&&slot+16<=w.off+0x40000400+w.new.length/2);
  const off=(slot-owner?.off-0x40000400)*2;
  if(!owner||owner.new.slice(off,off+32)!==hex(mode)+'000000000000000100000000')throw Error('Genie timing: shared selector changed');
  const code=b.fromHex(d.hex),view=new DataView(code.buffer);
  for(const i of d.reloc.mode)view.setUint32(i,mode,false);
  for(const i of d.reloc.cont)view.setUint32(i,boundary+6,false);
  // Le renderer copie n'a plus d'entree : son debut libere heberge le helper.
  patch(helper,read(helper,code.length),b.hex(code));patch(entry,read(entry,6),'4ef9'+hex(native));patch(boundary,oldBoundary,'4ef9'+hex(helper));
  bank.symbols.genie_timing_boundary='0x'+hex(helper);bank.symbols.genie_timing_mode='0x'+hex(mode);bank.symbols.genie_timing_audio_render='0x'+hex(native);bank.status='experimental';bank.hardwareTestedByOwner=false;
  delete bank.append.compressed_hex;delete bank.append.stored;
  const container=b.parseContainer(b.unwrap(cycles).stream),main=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(main.off,main.off+main.size)).data,packed=b.buildPayload(bank.append,syntakt,stock);
  if(0x40000400+stock.length+packed.length>0x40200000)throw Error('Genie timing: firmware capacity');
  bank.append.stored=packed.length;result.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(packed)};return result;
 };
 a.applyLang(document.documentElement.lang||'en');
})();
