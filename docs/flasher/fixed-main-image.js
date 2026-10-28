/* 2026-10-27-main256-full215 : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
 "full": {
  "id": "full",
  "productName": "Supermodel",
  "release": "2.56",
  "file": "Supermodel_2.56_c00942b054d0.syx",
  "syxSha256": "c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6",
  "mainOsSha": "a82d10eaccea90141951015a1e4b38ad732fdd2b32b17a4b45e37d3bfbad137e",
  "requiresSyntakt": true,
  "source_build": 215,
  "hardware_source_sha256": "c00942b054d0478e117ee889ee80761e91c77b30d3a0465122d5dec000f912e6",
  "title_only_change": false,
  "base_source_build": 208,
  "new_clear_filter_defaults": true,
  "ui_idle_saves": true,
  "hardware_verified": false,
  "full_lfo2_pattern_storage": true,
  "lfo_menu_musical_controls": true,
  "tiny_sustain_punch": true,
  "clipboard_allocation_bytes": 164,
  "publication_user_report": "Okay, push 215 as main full build"
 },
 "lite": {
  "id": "lite",
  "productName": "Supermodel Lite",
  "release": "2.56",
  "file": "Supermodel_Lite_2.56_df9b8d2241e2.syx",
  "syxSha256": "df9b8d2241e28df96f81d51b68fba171ac6bd8d09daf70233deb2b7b4d04cd3f",
  "mainOsSha": "81b9c3df268dbdd2fc7de046a5f8d2e49e5f79267de8d598941ffde5533f56c1",
  "requiresSyntakt": false,
  "source_build": 211,
  "hardware_source_sha256": "269388b3187af386115a986a50774f8c831906c5a36ad259249b2b949b886fa7",
  "title_only_change": false,
  "base_source_build": 207,
  "new_clear_filter_defaults": true,
  "ui_idle_saves": true,
  "hardware_verified": false,
  "hardware_user_report": "Seems much more responsive now. and dx works.",
  "boot_hardware_verified": true,
  "encoder_hardware_verified": true,
  "dx_hardware_verified": true
 }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Modded-Cycles/40a6a5dec35380b3d57985d0fb0fdb2c30e85cc8/docs/flasher/"+meta.file];
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
