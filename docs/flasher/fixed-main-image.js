/* 2026-10-27-main255-warp-grid */
/* Meme image approuvee ; chemin immuable et repli epingle, SHA obligatoire. */
(()=>{
  "use strict";
  const meta=Object.freeze({"mainOsSha": "4ad9b5bcc8cddd00db1a55bc52e0a46a175abcce89c3ee3f06a7a097530e3f85", "syxSha256": "c37e8a1a97a6849ff094a095caac5de54b39d9cc03ca0e88396b629d17bba05b", "file": "Supermodel_2.55_c37e8a1a97a6.syx"});
  const sources=[new URL(meta.file,window.location.href).href,
    "https://raw.githubusercontent.com/AveyCole/Modded-Cycles/main/docs/flasher/Supermodel_2.55_c37e8a1a97a6.syx"];
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
