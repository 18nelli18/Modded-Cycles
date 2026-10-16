// Extension experimentale : conserver les recettes et le noyau RAM testes.
(()=>{
 'use strict';
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMidiPersistence;
 const previous=window.MCMidiBankCompose,clone=x=>JSON.parse(JSON.stringify(x));
 const value=x=>typeof x==='string'?parseInt(x,16):x,hex=x=>(x>>>0).toString(16).padStart(8,'0');
 const hash=x=>b.hex(b.sha256(x)),BASE=0x40000400;
 const f=window.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank');f.status='experimental';delete f.hardwareTestedByOwner;
 a.registerFeatureTexts('midi-out-bank',{
  en:{label:'MIDI OUT Bank — saving test',short:'Experimental MIDI project saving. Stop playback, then Save Project.',desc:'Experimental persistence for the current independent MIDI Bank. Stop playback before Save Project. MIDI SAVED confirms the additional MIDI write and read-back check. Load a saved project and open B to restore its data; loading while playing waits until stopped. Includes notes/live timing, retrigger/chance settings, CC assignments/locks and both MIDI CC LFOs. Uses two recovery copies per pattern in a separate ModdedCycles folder; these files are outside Elektron project backups and SysEx exports. Older saving formats are not imported. Audio-side LFO 2 keeps its existing native saving. Hardware persistence is unverified. Keep backups and report the exact success/error popup.'},
  fr:{label:'Banque MIDI OUT — test sauvegarde',short:'Sauvegarde MIDI experimentale. Arretez la lecture puis Save Project.',desc:'Persistance experimentale pour la Banque MIDI autonome actuelle. Arretez avant Save Project. MIDI SAVED confirme ecriture et relecture des donnees MIDI. Chargez un projet sauvegarde puis ouvrez B pour restaurer ; en lecture, attente de Stop. Notes/timing live, retrigger/chance, assignations/locks CC et deux LFO CC inclus. Deux copies par pattern dans ModdedCycles, hors backups/SysEx Elektron. Les anciens formats ne sont pas importes. LFO 2 audio garde sa sauvegarde native actuelle. Persistance materielle non verifiee. Conservez vos sauvegardes et rapportez le popup exact.'}
 });
 const cache=new Map();
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const original=previous(input,cycles,syntakt),old=original.tweaks.find(t=>t.id==='midi-out-bank');if(!old)return original;
  const key=hash(b.writesBytes(old))+':'+original.refMods[old.id].p;if(cache.has(key))return clone(cache.get(key));
  const result=clone(original),bank=result.tweaks.find(t=>t.id===old.id),ap=bank.append;
  const origin=value(ap.dest),at=(origin+ap.size+15)&~15,raw=b.fromHex(d.hex),view=new DataView(raw.buffer),s=d.symbols;
  for(const off of d.reloc)view.setUint32(off,view.getUint32(off,false)+at,false);
  // Le dernier detour Load conserve exactement la chaine RAM existante.
  const load=bank.writes.find(w=>BASE+w.off===0x4006a660);if(!load||!load.new.startsWith('4ef9'))throw Error('MIDI save: unknown load chain');
  const oldLoad=parseInt(load.new.slice(4,12),16);
  d.api.forEach((name,i)=>{const address=name==='OLD_LOAD'?oldLoad:value(bank.symbols[name]||0);if(!address&&!['ml_gq_state','ml_gu_valid','SG_undo_valid'].includes(name))throw Error('MIDI save: missing bank API '+name);view.setUint32(s.mp_api+4*i,address,false);});
  const rawHex=b.hex(raw),marker='4ef9f0010096',pos=rawHex.indexOf(marker);if(pos<0||rawHex.indexOf(marker,pos+1)>=0)throw Error('MIDI save: load trampoline guard');raw.set(b.fromHex('4ef9'+hex(oldLoad)),pos/2);
  load.new='4ef9'+hex(at+s.mp_load_hook)+'4e71';
  // La garde UI actuelle reste active ; seul son pointeur drain est remplace.
  const safe=value(bank.symbols.midi_current_safe_ui),stagePart=ap.parts.find(p=>p.hex&&value(p.dest)<=safe&&safe<value(p.dest)+p.hex.length/2);
  if(!stagePart)throw Error('MIDI save: boot guard missing');
  const stage=b.fromHex(stagePart.hex),pointer=b.fromHex(hex(value(bank.symbols.ml_ui_drain)));let found=-1;
  for(let i=0;i+4<=stage.length;i+=2)if(stage.subarray(i,i+4).every((v,j)=>v===pointer[j])){if(found>=0)throw Error('MIDI save: ambiguous drain');found=i;}
  if(found<0)throw Error('MIDI save: drain guard');stage.set(b.fromHex(hex(at+s.mp_drain)),found);stagePart.hex=b.hex(stage);
  const hooks=[[0x4000f762,'4fefffcc48d77c1c','mp_save_entry_hook'],[0x4000f850,'4cd77c1c4fef0034','mp_save_exit_hook'],[0x4008b24a,'4fefffec48d7043c','mp_disk_read_hook'],[0x4008b3f6,'4fefffec48d7043c','mp_disk_write_hook']];
  for(const [address,stock,name] of hooks){if(result.tweaks.some(t=>t.writes.some(w=>w.off===address-BASE)))throw Error('MIDI save: occupied native hook');bank.writes.push({off:address-BASE,old:stock,new:'4ef9'+hex(at+s[name])+'4e71'});}
  ap.parts.push({dest:'0x'+hex(at),hex:b.hex(raw)});ap.size=at-origin+raw.length;
  for(const [name,offset] of Object.entries(s))if(name.startsWith('mp_'))bank.symbols[name]='0x'+hex(at+offset);
  bank.status='experimental';delete bank.hardwareTestedByOwner;delete bank.ram_only_rollback;bank.pending=['hardware_persistence_verification'];bank.persistence='MPI1';
  const container=b.parseContainer(b.unwrap(cycles).stream),main=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(main.off,main.off+main.size)).data;
  const packed=b.buildPayload(ap,syntakt,stock);if(BASE+stock.length+packed.length>0x40200000)throw Error('MIDI save: firmware size limit');ap.stored=packed.length;
  result.refMods[bank.id]={w:hash(b.writesBytes(bank)),p:hash(packed)};
  cache.set(key,clone(result));return result;
 };
 a.applyLang(document.documentElement.lang||'en');
})();
