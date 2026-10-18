// Note121 : matrice des interactions modifiees, firmware signe et diagnostic absent.
const fs=require('fs'),assert=require('node:assert/strict');
const {open,change}=require('./test_retrosyn_flasher');
const raw=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx'));
const st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
const out='build/lfo-release';fs.mkdirSync(out,{recursive:true});
function engine(w,code,on){const e=w.document.getElementById('eng-'+code);e.checked=on;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
function noDiagnostics(w,tweaks){
 assert(!w.MCBeatDiagnostic&&!w.MCAudioLoad&&!w.document.getElementById('feat-audio-load-diagnostic'));
 for(const t of tweaks){assert(!/diagnostic/.test(t.id));assert(!Object.keys(t.symbols||{}).some(k=>/^br_(load_address|avg_address|load_peak|filter_|cut_seen)/.test(k)),t.id);for(const p of t.append?.parts||[])if(p.hex)for(const s of ['FILTER CODE OK','RESET QUEUED','RESET PENDING'])assert(!Buffer.from(p.hex,'hex').includes(Buffer.from(s)));}
}
const cases=[];
for(const wizard of [false,true])for(let flags=0;flags<(wizard?32:8);flags++)cases.push({profile:'all',wizard,flags,lfo:!!(flags&1),midi:!!(flags&2),repeat:!!(flags&4),attack:wizard&&!!(flags&8),filter:wizard&&!!(flags&16)});
for(const [profile,wizard] of [['stock',false],['wizard',true],['retro',false],['retro',true],['tiny',false],['macro',false],['acid',false],['sd',true],['user',true]])cases.push({profile,wizard,lfo:true,midi:false,repeat:true,attack:wizard,filter:wizard});
for(const animation of ['none','supermodel-startup','boot-anim'])cases.push({profile:'retro',wizard:true,lfo:true,midi:true,repeat:true,attack:true,filter:true,animation});
cases.push({profile:'stock',wizard:false,lfo:false,midi:false,repeat:false,attack:false,filter:false});
cases.push({profile:'wizard',wizard:true,lfo:true,midi:false,repeat:false,attack:true,filter:true});
cases.push({profile:'retro',wizard:false,lfo:false,midi:false,repeat:false,attack:false,filter:false});
(async()=>{let checked=0;
 for(let i=Number(process.env.LFO_RELEASE_START||0);i<(process.env.LFO_RELEASE_AUDIO_ONLY?40:cases.length);i++){
  const c=cases[i],{w,errors}=open();try{
   await w.MCLfoDestinationsReady;w.document.getElementById('super-clear').click();
   if(c.profile==='all')w.document.getElementById('select-all').click();
   else {change(w,'arp',true);for(const id of c.profile==='user'?['trig-preview','trig-hold','trigless-dim','macro','acid','syntakt','tiny','retrosyn','latching-mute','chord-keys','sample-preview','browser-scroll','multiline-browser']:c.profile==='stock'||c.profile==='wizard'?[]:c.profile==='sd'?['syntakt']:[c.profile==='retro'?'retrosyn':c.profile])change(w,id,true);}
   if(c.profile==='sd'||c.profile==='user')for(const code of ['sd','cp','toy','bits','swarm'])engine(w,code,c.profile==='sd'?code==='sd':['sd','cp','swarm'].includes(code));
   change(w,'sample-wizard',c.wizard);change(w,'synth-attack',!!c.attack);change(w,'track-filter',!!c.filter);change(w,'lfo-secondary',c.lfo);change(w,'midi-out-bank',c.midi);change(w,'control-all-beat-repeat',c.repeat);
   if(c.animation){for(const f of w.MC_TWEAKS.features.filter(f=>/boot|startup/.test(f.id)))if(w.document.getElementById('feat-'+f.id))change(w,f.id,false);if(c.animation!=='none'){change(w,c.animation,true);assert(w.MCFlasherApp.isSelected(c.animation));}}
   const a=w.MCFlasherApp,b=w.MCBuilder,chosen=a.chosenTweaks();assert(chosen.length,a.state.selectionError);assert.equal(a.isSelected('sample-wizard'),c.wizard);assert.equal(a.isSelected('midi-out-bank'),c.midi);assert.equal(a.isSelected('control-all-beat-repeat'),c.repeat);assert.equal(a.isSelected('lfo-secondary'),c.lfo);assert.equal(a.isSelected('synth-attack'),!!c.attack||!!c.filter);assert.equal(a.isSelected('track-filter'),!!c.filter);
   const composed=w.MCMidiBankCompose(chosen,raw,c.profile==='all'||c.profile==='sd'||c.profile==='user'?st:null);noDiagnostics(w,composed.tweaks);assert(composed.tweaks.some(t=>t.id==='lfo-destinations'&&t.status==='tested'&&t.hardwareTestedByOwner));
   const built=b.build(raw,w.MC_TWEAKS.device,composed.tweaks,{syntakt:st,refMods:composed.refMods});assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);
   if(i===39&&process.env.LFO_RELEASE_AUDIO_ONLY){const prior=w.MCLfoDestinationsBaseCompose(chosen,raw,st),before=b.build(raw,w.MC_TWEAKS.device,prior.tweaks,{syntakt:st,refMods:prior.refMods});for(const[suffix,recipe,firmware]of [['before',prior,before],['after',composed,built]]){fs.writeFileSync(out+'/audio-'+suffix+'.json',JSON.stringify({tweaks:recipe.tweaks,mainOsSha:firmware.mainOsSha}));fs.writeFileSync(out+'/audio-'+suffix+'.syx',firmware.raw);}console.log('PASS matching release audio baseline prepared');}
   const prefix=out+'/'+i;fs.writeFileSync(prefix+'.json',JSON.stringify({tweaks:composed.tweaks,mainOsSha:built.mainOsSha,requestedSelection:c,selection:{...c,attack:a.isSelected('synth-attack'),filter:a.isSelected('track-filter')}}));fs.writeFileSync(prefix+'.syx',built.raw);assert(!errors.length,errors.join('\n'));checked++;console.log('PASS signed release',i,JSON.stringify(c),built.mainOsSha);
  }finally{w.close();}
 }
 console.log('PASS release matrix',checked,'compositions; no diagnostics');
})().catch(e=>{console.error(e.stack);process.exitCode=1});
