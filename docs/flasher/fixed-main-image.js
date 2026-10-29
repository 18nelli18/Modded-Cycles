/* 2026-10-29-main258-filter : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.58",
    "file": "Supermodel_2.58_dec88b00faca.syx",
    "syxSha256": "dec88b00faca94e7ee58c808a05c1624611b9403b29cbaa745a804bfeb012e32",
    "mainOsSha": "bbb50b04bcdcd05317b5af00e86a66292914298faae4412580a01b2d69d9fb9d",
    "requiresSyntakt": true,
    "source_build": 215,
    "new_clear_filter_defaults": true,
    "ui_idle_saves": true,
    "hardware_verified": false,
    "status": "experimental",
    "per_track_fx": true,
    "inactive_fx_zero_bypass": true,
    "startup_title": {
      "name": "Supermodel",
      "version": "2.58",
      "edition": "2.58",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "bbc985b4d202cf1291bc7e730f77d8f21c92a5f5c7ff99d7b084d78cfc89c18e",
      "native_os_protocol_version_unchanged": true,
      "hardware_tested": false
    },
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true,
    "filter_deferred_new_sound_low": true,
    "double_stop_fx_reset": true,
    "per_track_fx_code_bytes": 41056
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.58",
    "file": "Supermodel_Lite_2.58_a46b2fe88f1c.syx",
    "syxSha256": "a46b2fe88f1c4ad08cfbae96882725a2821891508231c7f7730672cdecd68946",
    "mainOsSha": "388833cb22d3f47b3df57108b0a368d5a3226821fbe853914111196347ef2ba1",
    "requiresSyntakt": false,
    "source_build": 216,
    "new_clear_filter_defaults": true,
    "ui_idle_saves": true,
    "hardware_verified": false,
    "status": "experimental",
    "per_track_fx": true,
    "inactive_fx_zero_bypass": false,
    "startup_title": {
      "name": "Supermodel Lite",
      "version": "2.58",
      "edition": "LITE 2.58",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "98be8bf1a5da5fa560466b549d21966eca95b6928ffc1fa14142e1ec363a673b",
      "native_os_protocol_version_unchanged": true,
      "hardware_tested": false
    },
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true,
    "filter_deferred_new_sound_low": true,
    "double_stop_fx_reset": true,
    "per_track_fx_code_bytes": 34456
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/97987303f46fe7c6d1750bc0590ee4b606c5aa1c/docs/flasher/"+meta.file];
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
