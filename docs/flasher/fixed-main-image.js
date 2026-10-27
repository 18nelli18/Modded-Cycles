/* 2026-10-27-main254-page-length-dark */
/* Meme image approuvee ; chemin immuable et repli epingle, SHA obligatoire. */
(()=>{
  "use strict";
  const meta=Object.freeze({"mainOsSha": "bf71efa56d4780d67b6fd538129d40f0f9968148207f5fee9f786aed82cb61f4", "syxSha256": "da908d5ff722164d1fb8efaf38f508a1197a1a23b73fe27bd6e2c72d0ef4d6e1", "file": "Supermodel_2.54_da908d5ff722.syx"});
  const sources=[new URL(meta.file,window.location.href).href,
    "https://raw.githubusercontent.com/AveyCole/Modded-Cycles/14fa072c99aa0f05b10a080d27c74074720b2f99/docs/flasher/Supermodel_2.54_da908d5ff722.syx"];
  let pending;
  async function load(){
    let failure;
    for(const url of sources){
      try{
        const response=await fetch(url,{cache:"no-store"});
        if(!response.ok)throw Error("Verified main firmware image could not be loaded");
        const raw=new Uint8Array(await response.arrayBuffer());
        if(window.MCBuilder.hex(window.MCBuilder.sha256(raw))!==meta.syxSha256)
          throw Error("Verified main firmware image checksum mismatch");
        window.MCFlasher.verify(raw);
        return raw;
      }catch(error){failure=error;}
    }
    throw failure;
  }
  function get(){
    if(!pending)pending=load().catch(error=>{pending=null;throw error;});
    return pending.then(raw=>raw.slice());
  }
  window.MCFixedMainImageMeta=meta;
  window.MCFixedMainImageLoad=get;
  window.MCFixedMainImageReady=get();
  window.MCFixedMainImageReady.catch(()=>{});
})();
