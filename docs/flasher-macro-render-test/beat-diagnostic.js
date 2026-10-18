// Note 111 : observateur CPU/CUT seulement ; noyau audio principal conserve.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,ID='audio-load-diagnostic',clone=x=>JSON.parse(JSON.stringify(x)),num=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 window.MCBeatDiagnosticReady=new Promise(resolve=>setTimeout(resolve,80)).then(()=>{
 const previous=window.MCMidiBankCompose,normal=clone(window.MCBeatRepeat);
 window.MC_TWEAKS.features.push({id:ID,label:'Audio load diagnostic',cat:'live',status:'experimental',variants:[{id:ID}],requires:'control-all-beat-repeat',excludes:[]});
 window.MC_TWEAKS.tweaks.push({id:ID,order:120,writes:[],requires:[],conflicts:[],status:'experimental'});
 a.registerFeatureTexts(ID,{en:{label:'Audio load diagnostic',short:'Release TRACK + RETRIG: CPU average / peak and CUT count.',desc:'Select at least one SY engine to provide the existing load meter. Hold TRACK + RETRIG during the problem, then release either button. CPU shows average / peak load. CUT counts distinct tracks fading or suspended by the load governor during the hold, including already suspended tracks. The governor is observed only. Diagnostic, not a repair; current Swarm LITE and audio processing are retained.'},fr:{label:'Diagnostic charge audio',short:'Relacher TRACK + RETRIG : CPU moyenne/pic et compteur CUT.',desc:'Choisir au moins un moteur SY pour le compteur de charge existant. Maintenir TRACK + RETRIG puis relacher un bouton. CPU moyenne/pic ; CUT compte les pistes distinctes en fondu ou suspendues pendant le combo. Regulateur observe sans modification. Diagnostic, pas correction ; Swarm LITE et audio actuels conserves.'}});
 window.MCMidiBankCompose=(input,cycles,syntakt)=>{
  const enabled=a.isSelected(ID);Object.assign(window.MCBeatRepeat,clone(enabled?window.MCBeatDiagnostic:normal));
  const result=previous(input.filter(t=>t.id!==ID),cycles,syntakt);if(!enabled)return result;
  const gov=result.tweaks.find(t=>t.gov)?.gov,beat=result.tweaks.find(t=>t.id==='control-all-beat-repeat');
  if(!gov||!beat)throw Error('Audio load diagnostic: select Control All Beat Repeat and at least one SY engine');
  const p=beat.append.parts[0],raw=b.fromHex(p.hex),v=new DataView(raw.buffer),origin=num(p.dest);
  for(const [name,value] of [['br_load_address',gov.gov_load],['br_avg_address',gov.gov_avg],['br_fading_address',gov.gov_fading],['br_stolen_address',gov.gov_stolen]]){
   const off=num(beat.symbols[name])-origin;if(!value||v.getUint32(off,false)!==0)throw Error('Audio load diagnostic: meter pointer guard');v.setUint32(off,num(value),false);
  }
  p.hex=b.hex(raw);beat.status='experimental';beat.hardwareTestedByOwner=false;
  result.refMods={...result.refMods,[beat.id]:{w:hash(b.writesBytes(beat)),p:hash(b.buildPayload(beat.append,syntakt,null))}};return result;
 };
 a.applyLang(document.documentElement.lang||'en');
 });
})();
