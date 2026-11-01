/* 2026-11-01-main300 : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "3.00",
    "file": "Supermodel_Full_3.00_d9d04fe30eef.syx",
    "syxSha256": "d9d04fe30eef7838c1e7eefec3ca1e6b0360bda425e385647df53cbb593d102e",
    "mainOsSha": "8de19e968993bd1db77cc3267a47606c8d072c7c3842739234283118f7cd273f",
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
      "version": "3.00",
      "edition": "3.00",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "511b738dd9c4ee755edd1c4e8c3203420d2a37067bb41885817efc7a1ee0a86e",
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
    "valid_21bit_sysex": true,
    "dummy_available": false,
    "chordkeys_pattern_storage": false,
    "recent_cuts_page": true,
    "wizard_sustained_plocks": true,
    "filter_pattern_storage": true,
    "smp_export_unclipped": true
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "3.00",
    "file": "Supermodel_Lite_3.00_40bd76d276b1.syx",
    "syxSha256": "40bd76d276b19ffa07d7b3905cb7802360ffdbb5edc9d5ac7dcfcacd49e67f5c",
    "mainOsSha": "dc221b04ac0667cb77e5d6e7aaf456366393dfd328230c52170df895308e7597",
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
      "version": "3.00",
      "edition": "LITE 3.00",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "26fb16e81d63031e2fb986007a3678730a296c74903a2ae9b5fba3cb9cc16f8c",
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
    "valid_21bit_sysex": true,
    "dummy_available": false,
    "chordkeys_pattern_storage": false,
    "recent_cuts_page": true,
    "wizard_sustained_plocks": true,
    "filter_pattern_storage": true,
    "smp_export_unclipped": true
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/cca2e5b494bec0841cdcf67e075644c9ddedc889/docs/flasher/"+meta.file];
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
