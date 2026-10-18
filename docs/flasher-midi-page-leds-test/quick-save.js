// Note113 : laisser le natif traiter le long FUNC+SETTINGS sans accord de mod utilise.
(()=>{const a=window.MCFlasherApp,b=window.MCBuilder,d=window.MCQuickSave,n=x=>typeof x==='string'?parseInt(x,16):x,hash=x=>b.hex(b.sha256(x));
 const previous=window.MCMainClearResolve;
 window.MCMainClearResolve=input=>previous(input).map(t=>{if(t.id!=='sample-wizard')return t;const result=JSON.parse(JSON.stringify(t)),p=result.append.parts.find(p=>p.hex&&n(p.dest)<=d.at&&d.at+d.size<=n(p.dest)+p.hex.length/2);if(!p)throw Error('Quick save: modifier body missing');const i=2*(d.at-n(p.dest));if(p.hex.slice(i,i+2*d.size)!==d.old)throw Error('Quick save: modifier body guard');p.hex=p.hex.slice(0,i)+d.hex+p.hex.slice(i+2*d.size);delete result.append.compressed_hex;a.REF_MODS[result.id]={w:hash(b.writesBytes(result)),p:hash(b.buildPayload(result.append,null,null))};return result;});window.MCQuickSaveReady=Promise.resolve();
})();
