/* 2026-11-01-main299 : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "2.99",
    "file": "Supermodel_Full_2.99_9abe84ff1001.syx",
    "syxSha256": "9abe84ff10012a31097c57b09ba85be11ec52c514bdc23b4c540b24c72009f71",
    "mainOsSha": "4495e9bd7402385c7c7a4827622a8f1c5d7dccfbc09965fe8af7712caf7b142f",
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
      "version": "2.99",
      "edition": "2.99",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "69a78a29334ccb88c20cdc3b0467613dafbaeef28fe8560e77f9ae17a53e7140",
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
    ],
    "direct_pattern_jump": true,
    "trig_select": true,
    "track_selection_momentary": true,
    "wizard_plock_priority": true,
    "song_mode": true,
    "acid_articulation": true,
    "acid_arp_retrigger": true,
    "control_all_latch": true,
    "stock_machine_punch": true,
    "activity_masks": true,
    "wizard_usb_main_independent": true,
    "machine_confirmation": true,
    "live_cpu_monitor": true,
    "dx_monitor_global_gate": true,
    "ctrl_all_native_back_undo": true,
    "voice_stealing_resolved": false,
    "machine_selection_default": "Stk",
    "valid_21bit_sysex": true
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "2.99",
    "file": "Supermodel_Lite_2.99_fb5f8b3b593b.syx",
    "syxSha256": "fb5f8b3b593b3db0a8ea25161cf139fbd05bbecde35e23d85615ae5ea2570127",
    "mainOsSha": "2cc037e2887174bde5e809bc662c7f511179a666b8e08acac3cecaf2c4b1d64f",
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
      "version": "2.99",
      "edition": "LITE 2.99",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "af7a9ae81f0bfb813abb7c141c778ca5fe3e2cd67281a6b008c890553f0b22fa",
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
    ],
    "direct_pattern_jump": true,
    "trig_select": true,
    "track_selection_momentary": true,
    "wizard_plock_priority": true,
    "song_mode": true,
    "acid_articulation": false,
    "acid_arp_retrigger": false,
    "control_all_latch": true,
    "stock_machine_punch": true,
    "activity_masks": true,
    "wizard_usb_main_independent": true,
    "machine_confirmation": true,
    "live_cpu_monitor": true,
    "dx_monitor_global_gate": true,
    "ctrl_all_native_back_undo": true,
    "voice_stealing_resolved": false,
    "machine_selection_default": "Stk",
    "valid_21bit_sysex": true
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/98c7ec9f1cf4754ec936a26c962c59fbf0333d90/docs/flasher/"+meta.file];
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
