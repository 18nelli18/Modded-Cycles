/* 2026-10-28-main256-fx-menu-fix : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.56",
    "file": "Supermodel_2.56_63c6b399e0e4.syx",
    "syxSha256": "63c6b399e0e4fffd678042e7ed98e7288fecad0642f0060dd52dc5cee538399d",
    "mainOsSha": "8f429d40da9d326a26f8d12724634cbb17717026d4939d1470280fd3b932d2ec",
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
    "publication_user_report": "okay go ahead and push to main",
    "status": "experimental",
    "inactive_fx_zero_bypass": true,
    "fx_menu_stack_helper_fixed": true
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
   "https://raw.githubusercontent.com/AveyCole/Supermodel/58cef0fade692b623e96d8e0c94888acce31bbbf/docs/flasher/"+meta.file];
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
