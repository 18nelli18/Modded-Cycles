// Note126 : raccorder les detours MIDI apres les autres options, sans banque B.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCMidiMachineAll,n=x=>typeof x==='string'?parseInt(x,16):x,h=x=>(x>>>0).toString(16).padStart(8,'0'),hash=x=>b.hex(b.sha256(x)),BASE=0x40000400;
window.MCMidiMachineAllReady=Promise.all([window.MCLfoDestinationsReady,window.MCBeatDiagnosticReady]).then(()=>{
 window.MC_TWEAKS.features.push({id:'midi-out-machine',label:'MIDI Out machine',cat:'sound',status:'experimental',variants:[{id:'midi-out-machine'}],excludes:[]});
 window.MC_TWEAKS.tweaks.push({id:'midi-out-machine',order:120,status:'experimental',writes:[]});
 a.registerFeatureTexts('midi-out-machine',{en:{label:'MIDI Out machine',short:'Silent A-side machine: notes, 12 assignable CCs, locks, routing and two MIDI LFOs.',desc:'Select MIDI Out from MACHINES on any A-side track. Keep the normal notes/grid. Hold SETTINGS and turn a gray knob to assign its CC; turn it alone to send values. FUNC + TRACK opens Track Setup: Channel, Output, KbT and Pad Note. Stock-style menu: DATA selects a row; press DATA before editing. Switching back to audio restores the target machine’s default sound parameters, preserving notes, pattern and pitch. FUNC + PAGE keeps normal pattern length editing. Press LFO to cycle MIDI LFO 1, MIDI LFO 2, and the track screen; BACK returns to the track screen. The first eight gray knobs edit Speed, Mult, Fade, CC destination, Wave, Phase, Mode, Depth on an LFO page. Hold steps and turn assigned CC knobs for locks; live recording records CC locks. Save the project normally. No internal audio and no B-side bank. Fixed Select All test preset; hardware verification pending.'},fr:{label:'Machine MIDI Out',short:'Machine A silencieuse : notes,12CC assignables, locks, routage et deux LFO MIDI.',desc:'Choisir MIDI Out dans MACHINES sur une piste A. Notes/grille habituelles conservees. Tenir SETTINGS et tourner un potard gris pour assigner son CC ; tourner seul pour envoyer sa valeur. FUNC + TRACK ouvre Track Setup : canal, port, KbT et note de pad. Menu natif : DATA choisit une ligne ; cliquer avant de modifier. Le retour audio retablit les parametres sonores par defaut du moteur cible, notes/pattern/Pitch conserves. FUNC + PAGE conserve la longueur native. LFO parcourt LFO MIDI1, LFO MIDI2 puis ecran de piste ; BACK revient au principal. Les huit premiers potards : vitesse, multiplicateur, fade, destination CC, forme, phase, mode, profondeur. Tenir des pas et tourner les CC pour des locks ; enregistrement live des locks CC disponible. Sauvegarder le projet normalement. Aucun audio interne ni banque B. Preset complet fixe de test ; verification materielle attendue.'}});
 a.applyLang(document.documentElement.lang||'en');
 const previous=window.MCMidiBankCompose;
 window.MCMidiBankCompose=(...args)=>{
  const prior=previous(args[0].filter(t=>t.id!=='midi-out-machine'),args[1],args[2]),r={...prior,tweaks:JSON.parse(JSON.stringify(prior.tweaks)),refMods:{...prior.refMods}};
  if(a.isSelected('midi-out-bank'))throw Error('MIDI machine preset: B-side bank must be off');
  const engine=r.tweaks.find(t=>t.symbols?.mm_encoder_hook);if(!engine)throw Error('MIDI machine preset: full machine catalogue required');
  const sy=Object.fromEntries(Object.entries(engine.symbols).map(([k,v])=>[k,n(v)]));
  const container=b.parseContainer(b.unwrap(args[1]).stream),section=container.sections.find(s=>s.id===3),stock=b.aplibDepack(container.blob.subarray(section.off,section.off+section.size)).data,patched=b.applyWrites(stock,r.tweaks).data;
  const q={id:'midi-out-machine',status:'experimental',order:Math.max(...r.tweaks.map(t=>t.order))+1,writes:[],symbols:engine.symbols};
  function writeApi(at,value){let p=engine.append.parts.find(p=>p.hex&&n(p.dest)<=at&&at+4<=n(p.dest)+p.hex.length/2);if(!p){if(at<n(engine.append.dest)||at+4>n(engine.append.dest)+engine.append.size)throw Error('MIDI machine: API outside reservation '+h(at));p={dest:'0x'+h(at),hex:'00000000'};engine.append.parts.push(p);}const i=2*(at-n(p.dest));p.hex=p.hex.slice(0,i)+h(value)+p.hex.slice(i+8);}
  const support=r.tweaks.find(t=>t.symbols?.set_held&&t.symbols?.mod_used);
  if(!support)throw Error('MIDI machine: shared SETTINGS state missing');
  writeApi(sy.mm_ui_api,n(support.symbols.set_held));writeApi(sy.mm_ui_api+4,n(support.symbols.mod_used));
  function hook(site,expected,name){const old=b.hex(patched.subarray(site-BASE,site-BASE+expected.length/2));let target=0;if(old!==expected){if(!old.startsWith('4ef9'))throw Error('MIDI machine: hook guard '+h(site));target=parseInt(old.slice(4,12),16);}q.writes.push({off:site-BASE,old,new:'4ef9'+h(sy[name])+'4e71'.repeat((expected.length/2-6)/2)});return target;}
  for(const [site,expected,name] of d.hooks){
   const target=hook(site,expected,name);
   const live={'mm_key_on_hook':0,'mm_pad_on_hook':1,'mm_key_off_hook':2,'mm_pad_off_hook':3};
   const ui={'mm_encoder_hook':2,'mm_draw_hook':3,'mm_ui_key_hook':4};
   const storage={'mm_save2_hook':0,'mm_save1_hook':1,'mm_load_hook':2};
   if(name in live)writeApi(sy.mm_live_api+4*live[name],target);
   else if(name in ui)writeApi(sy.mm_ui_api+4*ui[name],target);
   else if(name in storage)writeApi(sy.mm_storage_api+4*storage[name],target);
   else if(name==='mm_sequence_hook'){writeApi(sy.mm_sequence_api,target);writeApi(sy.mm_sequence_api+4,Number(!!target));}
   else if(target)throw Error('MIDI machine: unhandled delegate '+name);
  }
  const call=b.hex(patched.subarray(0x400597c6-BASE,0x400597cc-BASE));if(!call.startsWith('4eb9'))throw Error('MIDI LFO: call guard');writeApi(sy.mm_lfo_api,parseInt(call.slice(4),16));q.writes.push({off:0x400597c6-BASE,old:call,new:'4eb9'+h(sy.mm_lfo_dispatch)});
  delete engine.append.compressed_hex;delete engine.append.stored;
  const beat=r.tweaks.find(t=>t.id==='control-all-beat-repeat');
  if(beat){const source=n(engine.append.at)+b.buildPayload(engine.append,args[2],stock).length;beat.append.at='0x'+h(source);const w=beat.writes.find(w=>w.off+BASE===window.MCBeatRepeat.boot.at),raw=b.fromHex(w.new);new DataView(raw.buffer).setUint32(window.MCBeatRepeat.boot.symbols.br_boot_source,source,false);w.new=b.hex(raw);r.refMods[beat.id]={w:hash(b.writesBytes(beat)),p:hash(b.buildPayload(beat.append,args[2],stock))};}
  r.refMods[engine.id]={w:hash(b.writesBytes(engine)),p:hash(b.buildPayload(engine.append,args[2],stock))};r.refMods[q.id]={w:hash(b.writesBytes(q))};r.tweaks.push(q);return r;
 };
 function select(id,value){const e=document.getElementById('feat-'+id);if(e&&e.checked!==value){e.checked=value;e.dispatchEvent(new Event('change',{bubbles:true}));}}
 for(const f of window.MC_TWEAKS.features)select(f.id,!['midi-out-bank','model-tg','lfo-triple','lfo-quad','startup-animation'].includes(f.id));
 for(const id of Array.from(document.querySelectorAll('input[id^="eng-"]'),el=>el.id)){const el=document.getElementById(id);if(!el.checked){el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}));}}
 select('sample-wizard',true);select('retrosyn',true);select('tiny',true);select('lfo-secondary',true);select('audio-load-diagnostic',true);select('midi-out-bank',false);
 // Ce premier essai est un preset fixe, pas une promesse de combinaisons non prouvees.
 window.MC_TWEAKS.features=window.MC_TWEAKS.features.filter(f=>f.id!=='midi-out-bank');a.applyLang(document.documentElement.lang||'en');
 function freeze(){for(const e of document.querySelectorAll('input[id^="feat-"],input[id^="eng-"],button[data-off],#select-all,#super-clear'))e.disabled=true;}
 freeze();const observer=new MutationObserver(freeze);for(const id of ['features','mod-sel']){const el=document.getElementById(id);if(el)observer.observe(el,{subtree:true,childList:true});}
});})();
