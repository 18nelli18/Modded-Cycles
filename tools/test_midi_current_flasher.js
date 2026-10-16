// Cases navigateur reelles ; les fichiers officiels restent locaux.
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict');
process.env.RETROSYN_PAGE=process.env.RETROSYN_PAGE||'docs/flasher';
const {open,change}=require('./test_retrosyn_flasher');
const dir=path.resolve(__dirname,'../build/midi-current');fs.mkdirSync(dir,{recursive:true});
const cycles=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/model-cycles_OS1.13.syx'))),syntakt=Uint8Array.from(fs.readFileSync(path.resolve(__dirname,'../firmware/Syntakt_OS1.42.syx')));
const profiles=[];
for(let n=0;n<8;n++)profiles.push({name:'supports-'+n,features:['scale-gen','lfo-secondary','scramble'].filter((_,i)=>n&(1<<i))});
for(const features of [['chord-keys'],['sample-wizard'],['sample-wizard','chord-keys'],['retrosyn'],['retrosyn','sample-wizard'],['retrosyn','chord-keys'],['retrosyn','sample-wizard','chord-keys'],['syntakt'],['macro'],['acid']])profiles.push({name:features.join('-'),features});
profiles.push({name:'all',all:true},{name:'all-boot',all:true,animation:'boot-anim'},{name:'all-native',all:true,native:true});
(async()=>{const rows=[];for(const p of profiles){
 if(process.env.MIDI_CASE&&p.name!==process.env.MIDI_CASE)continue;
 const {w,errors}=open();await new Promise(r=>setTimeout(r,40));
 try{
  const overview=w.document.querySelector('a[href="quick-reference.md"]');
  assert(overview.closest('p').nextElementSibling.querySelector('a[href="convert.html"]'),'converter below overview');
  assert(!w.document.body.textContent.includes('MIDI OUT Bank is now exclusive'));
  assert.equal(w.MC_TWEAKS.features.find(f=>f.id==='midi-out-bank').status,'tested');
  for(const lang of ['en','fr']){w.MCFlasherApp.applyLang(lang);assert(w.document.getElementById('det-midi-out-bank').textContent.includes('RAM'));}
  change(w,'midi-out-bank',true);
  if(p.all)w.document.getElementById('select-all').click();
  for(const id of p.features||[])change(w,id,true);
  if(p.animation)change(w,p.animation,true);
  if(p.native)change(w,'sample-wizard',false);
  const selected=w.MC_TWEAKS.features.filter(f=>w.MCFlasherApp.isSelected(f.id)).map(f=>f.id);
  if(!p.all)assert.deepEqual(new Set(selected),new Set(['midi-out-bank',...p.features]),'no forced cards: '+p.name);
  else for(const f of w.MC_TWEAKS.features)if(!['boot-anim','supermodel-startup',...(p.native?['sample-wizard','sample-preview','synth-attack','track-filter']:[])].includes(f.id))assert(selected.includes(f.id),'all lost '+f.id);
  assert(!selected.includes('model-tg'));assert(!selected.includes('lfo-plus'));
  const input=w.MCFlasherApp.chosenTweaks(),r=w.MCMidiBankCompose(input,cycles,syntakt);
  const built=w.MCBuilder.build(cycles,w.MC_TWEAKS.device,r.tweaks,{syntakt,refMods:r.refMods});
  assert(built.modsChecked);assert(w.MCFlasher.verify(built.raw).count>0);assert.equal(errors.length,0,errors.join('\n'));
  const bank=r.tweaks.find(t=>t.id==='midi-out-bank');
  assert(!bank.writes.some(w=>[0x4000f762,0x4000f850,0x4008b24a,0x4008b3f6].includes(w.off+0x40000400)),'disk hooks absent');
  fs.writeFileSync(path.join(dir,p.name+'.syx'),built.raw);fs.writeFileSync(path.join(dir,p.name+'.json'),JSON.stringify({tweaks:r.tweaks,mainOsSha:built.mainOsSha}));
  rows.push({name:p.name,sha:built.mainOsSha,selected,stored:bank.append.stored,cache_blocks:bank.cache_blocks});
  console.log('PASS',p.name,bank.append.stored,'bytes',built.mainOsSha);
 }finally{w.close();}
 }fs.writeFileSync(path.join(dir,'cases.json'),JSON.stringify(rows,null,1));})().catch(e=>{console.error(e.stack);process.exitCode=1});
