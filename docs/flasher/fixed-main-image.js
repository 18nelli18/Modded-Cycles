/* 2026-10-28-main256-playability : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.56",
    "file": "Supermodel_2.56_fec67ab4282a.syx",
    "syxSha256": "fec67ab4282a68b3c5538e76c87fba0c3d16e5cff5f6c15b5bb54202d952cb58",
    "mainOsSha": "a91f0f56fa007004883ab582b94024383a679bf2d31815981d4234013e6d86f3",
    "requiresSyntakt": true,
    "source_build": 215,
    "new_clear_filter_defaults": true,
    "ui_idle_saves": true,
    "hardware_verified": false,
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true,
    "visible_machine_count": 24,
    "publication_user_report": "Push these to main and keep the machine optional flasher the same.",
    "status": "experimental"
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.56",
    "file": "Supermodel_Lite_2.56_b5220ffdcf54.syx",
    "syxSha256": "b5220ffdcf541a9109c389de4d6a9a38eba4539f173ee2ba960603221926f563",
    "mainOsSha": "d38cc90b677d57865d20dc64310cb1c0803fc66f0aa4a46fa4b52aea031e41e3",
    "requiresSyntakt": false,
    "source_build": 216,
    "new_clear_filter_defaults": true,
    "ui_idle_saves": true,
    "hardware_verified": false,
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true,
    "visible_machine_count": 6,
    "publication_user_report": "Push these to main and keep the machine optional flasher the same.",
    "status": "experimental"
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/566d8b45a669528436bddae202030d2b7a0aa71e/docs/flasher/"+meta.file];
  let failure;
  for(const url of sources)try{
   const response=await fetch(url,{cache:"no-store"});
   if(!response.ok)throw new Error("Verified main firmware image could not be loaded");
   const raw=new Uint8Array(await response.arrayBuffer());
   if(window.MCBuilder.hex(window.MCBuilder.sha256(raw))!==meta.syxSha256)throw new Error("Verified main firmware image checksum mismatch");
   const checked=window.MCFlasher.verify(raw);
   if(!checked.count)throw new Error("Verified main firmware image has no valid SYX packets");
   return raw;
  }catch(error){failure=error}
  throw failure;
 }
 function get(edition="full"){
  const meta=catalogue[edition];
  if(!meta)return Promise.reject(new Error("Unknown firmware edition"));
  if(!pending.has(edition))pending.set(edition,load(meta).catch(error=>{pending.delete(edition);throw error}));
  return pending.get(edition).then(raw=>raw.slice());
 }
 window.MCFirmwareImages=catalogue;
 window.MCFirmwareImageLoad=get;
 window.MCFirmwareEdition="full";
 window.MCFixedMainImageMeta=catalogue.full;
 window.MCFixedMainImageLoad=()=>get("full");
 window.MCFixedMainImageReady=get("full");
 window.MCFixedMainImageReady.catch(()=>{});
})();
