// Note 108 : edition fixe, modules main courants et quatre WAV locaux.
(()=>{
 const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MC909CurrentData,previous=window.MCMidiBankCompose,samples={};let populated=null;
 const clone=x=>JSON.parse(JSON.stringify(x)),hash=x=>b.hex(b.sha256(x));
 window.MCMidiBankCompose=()=>{throw Error(document.documentElement.lang==='fr'?'Initialisation du profil 909.':'Initializing the 909 profile.');};
 window.MC909CurrentReady=new Promise(resolve=>setTimeout(()=>{
  const change=(id,on)=>{const el=document.getElementById('feat-'+id);if(!el)throw Error('909 profile: missing '+id);el.checked=on;el.dispatchEvent(new Event('change',{bubbles:true}));};
  document.getElementById('select-all').click();document.getElementById('super-clear').click();for(const id of d.features)change(id,true);
  const boot=d.startup;window.MC909CurrentLabels=['909 kit','Sample Wizard','Slide trigs','Per-track filter','ACID','SCRAMBLE','MIDI OUT Bank + project saving','MIDI Out/Thru','Sequence Genie','Latching mute','Second LFO','Control All Config','Control All Beat Repeat','909 startup'];
  window.MCMidiBankCompose=(input,cycles,syntakt)=>{
   if(!populated)throw Error(document.documentElement.lang==='fr'?'Choisissez les quatre samples WAV.':'Choose all four WAV samples.');
   const source=input.find(t=>t.id===d.original_id);if(!source)throw Error('909 profile: current ACID/Wizard source missing');
   const c=b.parseContainer(b.unwrap(cycles).stream),s=c.sections.find(s=>s.id===3),stock=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data;
   if(hash(b.writesBytes(source))!==d.original_ref.w||hash(b.buildPayload(source.append,null,stock))!==d.original_ref.p)throw Error('909 profile: source recipe SHA guard');
   const owner=input.find(t=>t.id==='sample-wizard');if(hash(b.writesBytes(owner))!==d.original_wizard_ref.w||hash(b.buildPayload(owner.append,null,stock))!==d.original_wizard_ref.p)throw Error('909 profile: Wizard source guard');
   for(const t of [populated,d.wizard,boot])a.REF_MODS[t.id]={w:hash(b.writesBytes(t)),p:t.append?hash(b.buildPayload(t.append,null,stock)):undefined};
   const prepared=previous(input.map(t=>t===source?clone(populated):t===owner?clone(d.wizard):t).concat(clone(boot)),cycles,null);
   if(prepared.tweaks.some(t=>t.id.startsWith('model-tg')))throw Error('909 profile: Model-TG forbidden');
   return {...prepared,tweaks:prepared.tweaks.map(t=>({...t,status:window.MC909Released?'tested':'experimental',hardwareTestedByOwner:!!window.MC909Released}))};
  };
  const refresh=()=>{if(a.state.os)a.loadOs(a.state.os.raw,a.state.os.name);};
  for(const key of ['ch','oh','crash','ride']){
   let revision=0;const input=document.getElementById('sample-'+key),status=document.getElementById('sample-status-'+key);
   input.addEventListener('change',async()=>{
    const ticket=++revision;delete samples[key];populated=null;status.textContent='';refresh();const file=input.files[0];if(!file)return;
    try{
     const raw=await new Promise((ok,no)=>{const r=new FileReader();r.onload=()=>ok(new Uint8Array(r.result));r.onerror=()=>no(r.error);r.readAsArrayBuffer(file);});if(ticket!==revision)return;
     samples[key]=window.MC909Samples.encode(raw);status.textContent=samples[key].seconds.toFixed(2)+' s / '+samples[key].data.length+' bytes';
     if(['ch','oh','crash','ride'].every(k=>samples[k])){const result=window.MC909Samples.populate(d.engine,samples);populated=result.tweak;document.getElementById('samples-status').textContent=result.used+' / '+d.engine.sample_slots.capacity+' bytes';}
    }catch(e){delete samples[key];populated=null;status.textContent=e.message;}refresh();
   });
  }
  window.MC909CurrentSamples=()=>clone(samples);resolve();
 },60));
})();
