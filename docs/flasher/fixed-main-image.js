/* 2026-11-06-main306-wizard-func : images verifiees par edition, caches et sources independants. */
(()=>{
 "use strict";
 const catalogue={
  "full": {
    "id": "full",
    "productName": "Supermodel",
    "release": "3.06",
    "file": "Supermodel_Full_3.06_0f4dba3efc20.syx",
    "syxSha256": "0f4dba3efc20662d609d4de36f4fe48e94a387b215446c63685ec58626eccd47",
    "mainOsSha": "3ce0a23173c57c81fc96204d0afe340b5fa678decee65ffeeb7e22fa820bd1bd",
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
      "version": "3.06",
      "edition": "3.06",
      "code": 1074084460,
      "code_bytes": 794,
      "sha256": "5fa92dfa6e85b04c941277efa109713bd5c6b44d74de02ecb52166b71fb1c4ca",
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
    "delay_selector_order": [
      "PHASER",
      "DUCK",
      "DUB",
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
    "source_rebuild_complete": false,
    "granular_mode_labels": true,
    "genie_stopped_intro": true,
    "silent_commit_guard": true,
    "deep_stop_idle": true,
    "LOW_sample_rate": 48000,
    "master_retrig_optimized": true,
    "song_starts_at_highlighted_row": true,
    "slice_editor_physical_FUNC": true,
    "pattern_selection_latch": true,
    "governor_choice": true,
    "governor_default": "Lod",
    "wizard_upper_slice_keyboard": true,
    "wizard_pan_display": true,
    "silent_commit_fixed": true,
    "control_all_notice_restored": true,
    "track_swap": true,
    "track_swap_stopped_only": true,
    "governor_inverse": true,
    "master_fx_only": true,
    "fx_menu_row": false,
    "fx_pattern_save_fixed": true,
    "track_swap_levels_16bit": true,
    "track_swap_context_guard": true,
    "fx_live_pattern_switch_fixed": true,
    "build_revision": "wizard-func385",
    "telephone_delay_removed": true,
    "wizard_pan_hold_func": true,
    "wizard_numeric_level_and_pan": true
  },
  "lite": {
    "id": "lite",
    "productName": "Supermodel Lite",
    "release": "3.06",
    "file": "Supermodel_Lite_3.06_23df22bbd07f.syx",
    "syxSha256": "23df22bbd07fdf257c6d156b7adc25e53f2fb2fc9eead99df2729484e2c5e5c5",
    "mainOsSha": "ce3f2c730182478950ad2d6ece1ec3612c6b6e48e30259eed5e408318262aa9d",
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
      "version": "3.06",
      "edition": "LITE 3.06",
      "code": 1074084460,
      "code_bytes": 856,
      "sha256": "3576287a697487488ba9216f266cf8efe7fa1fd415c5753e5be7e38ab7200a03",
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
    "delay_selector_order": [
      "PHASER",
      "DUCK",
      "DUB",
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
    "source_rebuild_complete": false,
    "granular_mode_labels": true,
    "genie_stopped_intro": true,
    "silent_commit_guard": true,
    "deep_stop_idle": true,
    "LOW_sample_rate": 48000,
    "master_retrig_optimized": true,
    "song_starts_at_highlighted_row": true,
    "slice_editor_physical_FUNC": true,
    "pattern_selection_latch": true,
    "governor_choice": true,
    "governor_default": "Lod",
    "wizard_upper_slice_keyboard": false,
    "wizard_pan_display": true,
    "silent_commit_fixed": true,
    "control_all_notice_restored": true,
    "track_swap": true,
    "track_swap_stopped_only": true,
    "governor_inverse": true,
    "master_fx_only": true,
    "fx_menu_row": false,
    "fx_pattern_save_fixed": true,
    "track_swap_levels_16bit": true,
    "track_swap_context_guard": true,
    "fx_live_pattern_switch_fixed": true,
    "build_revision": "wizard-func385",
    "telephone_delay_removed": true,
    "wizard_pan_hold_func": true,
    "wizard_numeric_level_and_pan": true
  }
};
 for(const meta of Object.values(catalogue))Object.freeze(meta);
 Object.freeze(catalogue);
 const pending=new Map();
 async function load(meta){
  const sources=[new URL(meta.file,window.location.href).href,
   "https://raw.githubusercontent.com/AveyCole/Supermodel/e154ef78a5abd94ff5d0d24d83bb9d2de4648fad/docs/flasher/"+meta.file];
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
