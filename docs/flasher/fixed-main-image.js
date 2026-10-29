/* 2026-10-29-main257-trackfx : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.57",
    "file": "Supermodel_2.57_c7f9ca576591.syx",
    "syxSha256": "c7f9ca5765910ed6f3276664f71540c93d307572ca018318596ff6f2155fcc9b",
    "mainOsSha": "0eedf8953cb2ccdbafac05f43b13dfe48ecd67ac12f0f7241f94ee3c8ef3cd32",
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
      "version": "2.57",
      "edition": "2.57",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "c459a0d47c223131da9633287057930d6bee96cfedc944b81eb57c0821cf08b5",
      "native_os_protocol_version_unchanged": true,
      "hardware_tested": false
    },
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.57",
    "file": "Supermodel_Lite_2.57_4bc535b78454.syx",
    "syxSha256": "4bc535b78454601abd66352a9e4e78b52ae637eb64aec786ce9159ac07d02488",
    "mainOsSha": "f587c56075c182b8135808a91ddbe1dc9d9fa40e4d10b8237e04d92b3e8a5299",
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
      "version": "2.57",
      "edition": "LITE 2.57",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "3f1819eba2df10378bf7e48e63ca0c6584bba362157f0584c476ac424ee8a190",
      "native_os_protocol_version_unchanged": true,
      "hardware_tested": false
    },
    "legacy_removed": true,
    "vinyl_removed": true,
    "chordkeys_removed": true,
    "unique_machine_punch": true,
    "unassigned_secondary_lfos_pause": true
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/a887e15ff60b1e3c4be453af4155d6319c852756/docs/flasher/"+meta.file];
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
