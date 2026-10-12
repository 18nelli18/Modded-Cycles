// La génération différée est toujours incluse, sans sous-case.
const fs=require('fs'),path=require('path'),assert=require('assert');
const {JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..');
(async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'docs/flasher/index.html'),'utf8'),{url:'https://aveycole.github.io/Modded-Cycles/flasher/',runScripts:'outside-only'});
 const w=dom.window,d=w.document;
 w.URL.createObjectURL=()=> 'blob:test';w.URL.revokeObjectURL=()=>{};
 for(const file of ['builder.js','tweaks.js','flasher.js','app.js'])w.eval(fs.readFileSync(path.join(root,'docs/flasher',file),'utf8'));
 await new Promise(r=>setTimeout(r,25));
 const toggle=(id,on)=>{const cb=d.getElementById('feat-'+id);if(cb.checked!==on)cb.click();};
 toggle('scale-gen',true);
 assert(!d.getElementById('queue-scale-gen'));
 const ids=()=>Array.from(w.MCFlasherApp.chosenTweaks(),x=>x.id);
 assert(ids().includes('scale-gen-queued'),ids());
 toggle('scramble',true);
 assert(ids().includes('scramble-gen-queued'),ids());
 toggle('scale-gen',false);toggle('scale-gen',true);
 assert(ids().includes('scale-gen-queued'));
 for(const lang of ['en','fr']){
  w.MCFlasherApp.applyLang(lang);
  assert(!d.getElementById('queue-scale-gen'));
 }
 d.getElementById('select-all').click();
 assert(ids().includes('scale-gen-st-queued'),ids());
 assert(ids().includes('scramble-st-gen-queued'),ids());
 assert(!ids().includes('scale-gen-st'));
 console.log('ok : Sequence Generator inclut queued sans case, SCRAMBLE compatible, Select All/ST et EN/FR');
 dom.window.close();
})().catch(e=>{console.error(e);process.exit(1);});
