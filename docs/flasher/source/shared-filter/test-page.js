// Le vrai checklist : chaque choix doit réellement modifier le firmware.
const fs=require('fs'),assert=require('assert'),{JSDOM}=require('jsdom'),dir='work/wizard-filter-integration/page/';
const w=new JSDOM(fs.readFileSync(dir+'index.html','utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher-sample-wizard-options-test/',runScripts:'outside-only'}).window;w.URL.createObjectURL=()=>'';w.URL.revokeObjectURL=()=>{};
const errors=[];w.addEventListener('error',e=>errors.push(String(e.error||e.message)));
for(const f of ['builder.js','tweaks.js','flasher.js','app.js','bundle.js','catalogue.js','compose.js','wizard-refs.js','wizard.js','queue-choice.js','shared-filter.js'])w.eval(fs.readFileSync(dir+f,'utf8'));
const a=w.MCFlasherApp,d=w.document,b=w.MCBuilder,cy=Uint8Array.from(fs.readFileSync('firmware/model-cycles_OS1.13.syx')),st=Uint8Array.from(fs.readFileSync('firmware/Syntakt_OS1.42.syx'));
function set(id,v){const e=d.getElementById('feat-'+id);assert(e,id);if(e.checked===v)return;e.checked=v;e.dispatchEvent(new w.Event('change',{bubbles:true}));}
function clear(){d.getElementById('super-clear').click();}
const cases=[],failures=[];
function test(name,expect){const c=a.chosenTweaks(),need=c.some(t=>t.append?.syntakt);if(expect!==undefined)assert.equal(need,expect,name+' Syntakt requirement');const result=b.build(cy,w.MC_TWEAKS.device,c,{syntakt:need?st:undefined,refMods:a.REF_MODS});assert(result.modsChecked,name+' references');assert(w.MCFlasher.verify(result.raw).count);fs.writeFileSync('work/wizard-filter-integration/case-'+name+'.json',JSON.stringify({tweaks:c,sha:result.mainOsSha}));cases.push({name,sha:result.mainOsSha});console.log('PASS real checklist',name,c.length,'recipes',need?'Syntakt':'no Syntakt');return c;}
setTimeout(()=>{try{
 assert(!d.getElementById('feat-model-tg'));assert(w.MC_TWEAKS.features.length>=27);assert(d.getElementById('feat-sample-wizard'));
 clear();set('sample-wizard',true);test('wizard-only',false);
 for(const id of ['scale-gen','scramble','chord-keys','lfo-secondary','supermodel-performance','macro','acid','wave-supermodel','sample-preview','track-filter','lfo-plus']){clear();set('sample-wizard',true);set(id,true);try{test('pair-'+id,false)}catch(e){failures.push({id,error:e.message});console.log('FAIL pair',id,e.message);}}
 clear();for(const id of ['sample-wizard','macro','acid','wave-supermodel','chord-keys','lfo-secondary','scale-gen','scramble','supermodel-performance'])set(id,true);test('own-machines',false);
 clear();d.getElementById('select-all').click();assert(a.isSelected('sample-wizard'));assert(!a.isSelected('model-tg'));assert(a.isSelected('chord-keys'));assert(a.isSelected('wave-supermodel'));const all=test('select-all',true);assert(all.some(t=>t.id==='wizard-machines-255'));assert(a.isSelected('track-filter'));assert(a.isSelected('lfo-secondary'));assert(all.some(t=>t.id==='wizard-shared-filter')); 
 set('syntakt',false);test('select-all-no-syntakt',false);set('macro',false);test('select-all-no-macro',false);set('acid',false);test('select-all-no-acid',false);set('wave-supermodel',false);test('controls-no-extra-machines',false);
 set('track-filter',false);set('sample-wizard',false);test('main-controls-without-wizard',false);
 
 clear();set('scale-gen',true);test('queue-no-wizard-core',false);
 set('scramble',true);set('lfo-secondary',true);set('chord-keys',true);test('queue-no-wizard-controls',false);
 set('wave-supermodel',true);test('queue-no-wizard-wave',false);
 clear();d.getElementById('select-all').click();set('track-filter',false);set('sample-wizard',false);test('queue-no-wizard-all',true);
 a.applyLang('fr');assert(d.body.textContent.includes('Sample Wizard'));a.applyLang('en');assert(!errors.length,errors.join('\n'));
 fs.writeFileSync('work/sample-wizard-options/page-cases.json',JSON.stringify(cases));fs.writeFileSync('work/sample-wizard-options/pair-failures.json',JSON.stringify(failures));assert(!failures.length,JSON.stringify(failures));console.log('PASS complete selectable checklist EN/FR, independent options, strict references and signed containers');
 }catch(e){console.error(e.stack);process.exitCode=1;}finally{w.close();}},50);
