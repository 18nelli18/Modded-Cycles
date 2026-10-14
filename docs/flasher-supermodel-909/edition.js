/* Édition fixe ; seules les tables et les données des quatre samples changent. */
(function(){
'use strict';
const original=window.MC_TWEAKS.tweaks,engine=original.find(t=>t.sample_slots),samples={};let populated=null;
window.MC909Labels=['909 kit','ACID','SCRAMBLE','MIDI OUT Bank','MIDI Out/Thru','Sequence Genie','Latching mute','Second LFO','Control All Config','SUPERMODEL by A.V. — 909 EDITION'];
window.MCMainClearResolve=()=>populated?original.map(t=>t===engine?populated:t):[];
window.MC909Refs=(raw,tweaks)=>{
 const b=window.MCBuilder,c=b.parseContainer(b.unwrap(raw).stream),s=c.sections.find(x=>x.id===3),main=b.aplibDepack(c.blob.subarray(s.off,s.off+s.size)).data,refs={};
 for(const t of tweaks)refs[t.id]={w:b.hex(b.sha256(b.writesBytes(t))),p:t.append?b.hex(b.sha256(b.buildPayload(t.append,null,main))):undefined};
 return refs;
};
function refresh(){
 const a=window.MCFlasherApp;if(a&&a.state.os)a.loadOs(a.state.os.raw,a.state.os.name);
}
function install(){
 for(const key of ['ch','oh','crash','ride']){
  let revision=0;const input=document.getElementById('sample-'+key),status=document.getElementById('sample-status-'+key);
  input.addEventListener('change',async()=>{
   const ticket=++revision;delete samples[key];populated=null;refresh();status.textContent='';
   const file=input.files[0];if(!file)return;
   status.textContent='Reading…';
   try{
    const raw=await new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>resolve(new Uint8Array(r.result));r.onerror=()=>reject(r.error);r.readAsArrayBuffer(file);});
    if(ticket!==revision)return;
    samples[key]=window.MC909Samples.encode(raw);
    status.textContent=samples[key].seconds.toFixed(2)+' s · '+samples[key].data.length.toLocaleString()+' bytes';
    if(['ch','oh','crash','ride'].every(k=>samples[k])){
     const p=window.MC909Samples.populate(engine,samples);populated=p.tweak;
     document.getElementById('samples-status').textContent=(document.documentElement.lang==='fr'?'Samples prêts : ':'Samples ready: ')+p.used.toLocaleString()+' / '+engine.sample_slots.capacity.toLocaleString()+' bytes';
    }
   }catch(e){populated=null;delete samples[key];status.textContent=e.message;document.getElementById('samples-status').textContent=e.message;}
   refresh();
  });
 }
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install);else install();
})();
