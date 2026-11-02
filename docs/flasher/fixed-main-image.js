/* 2026-11-01-main301 : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "3.01",
    "file": "Supermodel_Full_3.01_46dd09a1d0cd.syx",
    "syxSha256": "46dd09a1d0cdf6d4923a9bc9016b6ebb839ceb22482565fe73412b762d7f2f47",
    "mainOsSha": "4054978302bdf9d0e7e4a2c030d292a662211272fcd5ba0307e48797a6f89c9a",
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
      "version": "3.01",
      "edition": "3.01",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "12ff167916fdb9c660b5df8a7b60b9bd51ee8992a2e808f2b778f3a260fb74df",
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
    "sidechain_muted_live_hardware_confirmed": false,
    "lean_layout": true,
    "wizard_explicit_lock_scope": true,
    "wizard_sample_parameter_inheritance": true,
    "source_rebuild_complete": false
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "3.01",
    "file": "Supermodel_Lite_3.01_ec1959ea52a8.syx",
    "syxSha256": "ec1959ea52a8359f5971dc11adae9bc8dc9ede5df9f95deffa0591a0d7e29985",
    "mainOsSha": "641bae4ed0c309486d4ccc14da374df98ffd81d583faeb85fce807a27fa8f618",
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
      "version": "3.01",
      "edition": "LITE 3.01",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "4ab019d4c5e13f6cd54672c47c13c680e1f74f1933b86728f3a45fd95fc3277e",
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
    "sidechain_muted_live_hardware_confirmed": false,
    "lean_layout": true,
    "wizard_explicit_lock_scope": true,
    "wizard_sample_parameter_inheritance": true,
    "source_rebuild_complete": false
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/c2edfd8d871c0bebc979481a039464334d977c7a/docs/flasher/"+meta.file];
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
