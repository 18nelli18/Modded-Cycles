/* 2026-11-01-main300-sc1 : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "3.00",
    "file": "Supermodel_Full_3.00_17c197d2b2b9.syx",
    "syxSha256": "17c197d2b2b943f9b98f151c5a912515ab864412a507f0c19865fd6eb6eed21b",
    "mainOsSha": "56f57621f2a2077159d1b1996bf2df3b56b29c3a6ebdce67849bd7376728102f",
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
    "smp_export_unclipped": true,
    "sidechain_muted_live": true,
    "sidechain_muted_live_hardware_confirmed": false
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "3.00",
    "file": "Supermodel_Lite_3.00_78bd1f2a75f8.syx",
    "syxSha256": "78bd1f2a75f89e466ca12e015b42354cf4583415fc5706bb1b992f88a978807f",
    "mainOsSha": "880d2782ea5a2ff7e2a0135639297108165701082b1ba40fbbc4f039c3fe6459",
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
    "smp_export_unclipped": true,
    "sidechain_muted_live": true,
    "sidechain_muted_live_hardware_confirmed": false
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/09bf0729f62a38ca9f516b965af4d731cee4f5f5/docs/flasher/"+meta.file];
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
