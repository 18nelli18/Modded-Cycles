/* 2026-10-27-main253-samples-layout */
/* Meme image approuvee ; chemin immuable et repli epingle, SHA obligatoire. */
(()=>{
  "use strict";
  const meta=Object.freeze({"mainOsSha": "69e7ea9c3f7c35e7e22e33d757376bc473370d8a574f72d7afeac17cdcec8626", "syxSha256": "6a729fbf198b50768ec1bfade96d6627ab11f08cea210f452586927d207a3282", "file": "Supermodel_2.53_6a729fbf198b.syx"});
  const sources=[new URL(meta.file,window.location.href).href,
    "https://raw.githubusercontent.com/AveyCole/Modded-Cycles/89557e1/docs/flasher/all-features-usb-2ch-default.syx"];
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
