/* UI privee, generation isolee, cache borne et envois du flasheur existant. */
(()=>{
'use strict';
const B=window.MCBuilder,O=window.MCOptionalBuilder,base=window.MCOptionalBaseEditions,descriptions=window.MCOptionalDescriptions;
const machines=[[6,'Sample Wizard'],[7,'SD Vintage'],[8,'CP Vintage'],[9,'SY Toy'],[10,'SY Bits'],[11,'Swarm Lite'],[12,'MACRO'],[13,'ACID'],[14,'WAVE'],[15,'Feral'],[16,'ELDER'],[18,'TINY'],[19,'Shadow'],[20,'SPEAK'],[21,'LEGACY'],[22,'RETROSYN'],[23,'PUNCH'],[24,'ESTUS'],[17,'MIDI Out']];
let mask=O.ALL,revision=0,os=null,context=null,current=null,pending=null;
window.MCFirmwareImages={...base};window.MCFixedMainImageMeta=base.full;
window.MCFixedMainImageReady=Promise.resolve();window.MCOptionalBusy=false;
async function load(meta){
 const urls=[new URL(meta.file,document.baseURI).href,'https://raw.githubusercontent.com/AveyCole/Supermodel/97987303f46fe7c6d1750bc0590ee4b606c5aa1c/docs/flasher/'+meta.file];let error;
 for(const url of urls)try{const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw Error('Could not load verified base');const raw=new Uint8Array(await r.arrayBuffer());if(B.hex(B.sha256(raw))!==meta.syxSha256)throw Error('Base firmware checksum mismatch');window.MCFlasher.verify(raw);return raw}catch(e){error=e}throw error;
}
let sources;function sourceFiles(){if(!sources)sources=Promise.all([load(base.full),load(base.lite)]).catch(e=>{sources=null;throw e});return sources}
function status(en,fr){const el=document.getElementById('optional-status');if(el)el.textContent=window.MCFlasherApp?.state.lang==='fr'?fr:en}
function controls(st){for(const node of document.querySelectorAll('#optional-picker input,#optional-picker button'))node.disabled=!!st.sending}
window.MCOptionalRender=controls;
window.MCFirmwareImageLoad=async edition=>{if(pending)await pending;if(!current||edition!==current.edition)throw Error('Machine selection is not ready');return current.raw.slice()};
function schedule(){
 const app=window.MCFlasherApp;if(!app||app.state.sending)return;
 const id=++revision,choice=mask,raw=app.state.os?.raw;
 window.MCOptionalFailed=null;
 if(!raw||!app.state.os.stock){status('Load official Cycles OS 1.13 below to build this selection.','Chargez ci-dessous lâ€™OS officiel Cycles 1.13 pour construire ce choix.');return}
 window.MCOptionalBusy=true;app.state.fw=null;app.state.buildKey=null;app.state.building=true;app.render();
 status('Preparing your machine selectionâ€¦','PrÃ©paration de votre sÃ©lectionâ€¦');
 pending=(async()=>{await new Promise(r=>setTimeout(r,30));const [full,lite]=await sourceFiles();if(id!==revision)return;
  if(!context)context=O.prepare(full,lite,raw,window.MCOptionalRecipe);
  const result=context.build(choice);if(id!==revision)return;
  current=result;const edition=result.edition,hex=choice.toString(16).padStart(5,'0');
  window.MCFirmwareImages={...base,[edition]:{...base[edition],syxSha256:result.syxSha256,mainOsSha:result.mainOsSha,requiresSyntakt:choice!==0,productName:choice===0?'Supermodel Lite':'Supermodel Machine Optional',downloadName:choice===0?`Supermodel_Lite_${base.lite.release}.syx`:`Supermodel_Optional_${base.full.release}_${hex}.syx`}};
  window.MCOptionalBusy=false;pending=null;app.state.cache={};app.setEdition(edition);
  const count=machines.filter(([id])=>choice&(1<<(id-6))).length;
  status(`${count} added machines Â· firmware ready`,`${count} machines ajoutÃ©es Â· firmware prÃªt`);
 })().catch(e=>{if(id!==revision)return;pending=null;window.MCOptionalBusy=false;window.MCOptionalFailed=e.message;app.state.fw=null;app.state.building=false;app.state.fwError=e.message;status(e.message,e.message);app.render()});
}
window.MCOptionalSync=st=>{if(st.os?.raw!==os){os=st.os?.raw;context=null;schedule()}};
function show(){for(const input of document.querySelectorAll('#optional-grid input'))input.checked=!!(mask&(1<<(Number(input.dataset.machine)-6)))}
function setMask(next){if(window.MCFlasherApp.state.sending)return false;O.validateMask(next);mask=next;show();schedule();return true}
function init(){
 const grid=document.getElementById('optional-grid');for(const [id,name] of machines){const label=document.createElement('label'),input=document.createElement('input'),body=document.createElement('span'),title=document.createElement('strong');input.type='checkbox';input.checked=true;input.dataset.machine=id;input.addEventListener('change',()=>{if(!setMask(input.checked?mask|(1<<(id-6)):mask&~(1<<(id-6))))show()});title.textContent=name;body.append(title);for(const lang of ['en','fr']){const desc=document.createElement('small');desc.dataset.l=lang;desc.textContent=descriptions[id][lang];body.append(desc)}label.append(input,body);grid.append(label)}
 document.getElementById('optional-all').addEventListener('click',()=>setMask(O.ALL));document.getElementById('optional-none').addEventListener('click',()=>setMask(0));
 window.MCOptionalUI={setMask,get mask(){return mask},get result(){return current},get context(){return context},machines};schedule();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
