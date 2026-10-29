/* 2026-10-29-main261-pots : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.61",
    "file": "Supermodel_2.61_2eb4b07f45ee.syx",
    "syxSha256": "2eb4b07f45ee24b7d9f198b09094db358b1d995fa8111b80daf6e114f9fac5c6",
    "mainOsSha": "319afdd6695068b7fe72e7e8aebd6db33a37b19fbf15673b08c544b55381cbf7",
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
      "version": "2.61",
      "edition": "2.61",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "d88777be7737709a6f943d7b292b1bcb02ed492e0b6819ffbada02f22b8b6500",
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
    "per_track_fx_code_bytes": 60238,
    "acid_envelope_global": true,
    "acid_envelope_modes": [
      "A",
      "F",
      "AF"
    ],
    "acid_envelope_default": "F",
    "pots_delay": true,
    "delay_selector_order": [
      "PHASER",
      "DUCK",
      "DUB",
      "POTS",
      "PING PONG",
      "DELAY",
      "CRUSH 1",
      "CRUSH 2"
    ]
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.61",
    "file": "Supermodel_Lite_2.61_7f000ba151c2.syx",
    "syxSha256": "7f000ba151c24b77e40d92fa8a640910e375ffd4eee2064f677eeb7697012c51",
    "mainOsSha": "5e5f17f509ef430597a31e88ac7dff4a5f818ff6a9fecda5430954fc72acb4c8",
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
      "version": "2.61",
      "edition": "LITE 2.61",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "fe83025fe12a8326be2c6765886590383eb828b8f89059fcf35503853c48f1a4",
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
    "per_track_fx_code_bytes": 43766,
    "acid_envelope_global": false,
    "pots_delay": true,
    "delay_selector_order": [
      "PHASER",
      "DUCK",
      "DUB",
      "POTS",
      "PING PONG",
      "DELAY",
      "CRUSH 1",
      "CRUSH 2"
    ]
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/fc181fdd17044282435ed4830f853b660595eafa/docs/flasher/"+meta.file];
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
