/* 2026-10-29-main260-acid : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.60",
    "file": "Supermodel_2.60_9faeca94dc5e.syx",
    "syxSha256": "9faeca94dc5ef71905511aa8855ab555e475d827555dbe343e25a2af7800aea4",
    "mainOsSha": "6f4506b4a11e8d8d7374f3275acc4e52d622fb5e7356de99cbb0ce22c2871def",
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
      "version": "2.60",
      "edition": "2.60",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "dae1778cd5aaa7db3fa598fa2da085ffa7302e126490bafdb2266d9512a212cd",
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
    "per_track_fx_code_bytes": 50922,
    "acid_envelope_global": true,
    "acid_envelope_modes": [
      "A",
      "F",
      "AF"
    ],
    "acid_envelope_default": "F"
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.60",
    "file": "Supermodel_Lite_2.60_5defda326152.syx",
    "syxSha256": "5defda326152406506ccb1b925a41cf711231554f5c80ba42dd4b0d7fdfb0eed",
    "mainOsSha": "0a5506bdb109cb55d051c3521b201c39902338a6e2e92e4f5214a4f58cf22449",
    "requiresSyntakt": false,
    "source_build": 216,
    "new_clear_filter_defaults": true,
    "ui_idle_saves": true,
    "hardware_verified": false,
    "status": "experimental",
    "per_track_fx": true,
    "inactive_fx_zero_bypass": true,
    "startup_title": {
      "name": "Supermodel Lite",
      "version": "2.60",
      "edition": "LITE 2.60",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "245cbdfc8436858e9f8e5bb89a96b0209d9bbbed7c063c85f2d2a544eecb1340",
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
    "per_track_fx_code_bytes": 34456,
    "acid_envelope_global": false
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/40dbba58b815db761185e4b24b4a49b9726594d7/docs/flasher/"+meta.file];
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
