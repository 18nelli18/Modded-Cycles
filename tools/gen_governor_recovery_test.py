"""Candidat prive charge/vols de voix : reconstruction depuis le conteneur officiel.

Les recettes approuvees v17 servent de reference epinglee. Aucun fichier main
n'est ecrit. Filtres legers et raccourcis audio sont des options privees. Emulation requise.
"""
import argparse,hashlib,json,os,struct,subprocess,sys
from pathlib import Path
from mtlib import aplib,container
from mtlib.syx import unwrap,wrap,BYTES_PER_MSG
import aplib_grow
ROOT=Path(__file__).resolve().parents[1]
BASE=0x40000400;START=0x401aa140-BASE;RUNTIME=0x46700000;TAIL=0x467ab360;ORIGIN=0x467c7000
OUT=ROOT/'output/firmware';SRC=ROOT/'tools/machines/gov_recovery'
PIN={'all-features':'3087145e4f5d597e2b9574d33de55dd71056ea63cb5d473b52ee47dc0095851b','no-filter':'ef678c0feb5f96ebf8af471b3eb071e015cb41c673d73a6f19511115d425a1c6'}
def read(path):
 stream,info=unwrap(path.read_bytes());pkg=container.parse(stream);s=next(s for s in pkg['sections'] if s['id']==3)
 image,ops=aplib.depack(pkg['blob'][s['off']:s['off']+s['size']]);return info,pkg,image,ops
def runtime_offset(at):
 if 0x80001c5c<=at<0x800074b4:return at-0x80001c5c
 if 0x8000cac0<=at<0x8000eae0:return 0x5858+at-0x8000cac0
 assert RUNTIME<=at<TAIL;return at-RUNTIME
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--profile',choices=tuple(PIN),default='all-features')
 p.add_argument('--title-version',help='Version de release affichee (defaut : BUILD.json du flasher)')
 p.add_argument('--check',action='store_true',help='Reconstruire et verifier le candidat prive existant sans reecrire son SysEx')
 p.add_argument('--stage',action='store_true',help='Ecrire dans staging, publication privee apres preuves seulement')
 for flag in ('polivoks','wizard','unity-amp','repeat-fades','repeat-record','trx-kick','chord-opt','syntakt-opt','feral','junior','elder','elder-icon','chorus','crusher','crusher-wet','repeat-latch','tiny-extra','tiny-order','feral-playable','scramble-mask','keep-params','wizard-isolation','shadow','machine-icons','themed-icons','split-sends','center-delay','fx-menu','fx-settings','fx-overlay','vinyl-dust','new-delays','delay-repair','delay-quality','shimmer-clean','octave-delay','octave-polish','scramble-decay-fix','scramble-decay-native','cloud','cloud-repair','ps1','ps1-only','fx-cpu-opt','dx-func-fix','fx-idle-opt','voice-fx-opt','all-fx-opt','ps1-cache-opt','filter-pair-opt','ps1-fast-opt','lean-fx','no-shimmer','stock-fx-format-fix','speak','speak-clear','speak-smooth','speak-level','speak-adult','speak-soft','speak-speed-fix','cheap-fx','speak-talk','dub-distinct','speak-bright','duck','extra-fx','fx-input-fix','gated','gated-phaser96','gate-predelay','legacy','speech-reverb','polish','retrosyn-private','bank-safe','bank-guard','fundamentals','elder-level','wave-starter','fx-project','fx-pattern','sidechain','combo-flip','submenu-align','sidechain-label','track-abbrev','compact-controls','sidechain-mute','menu-handoff','sidechain-fx','punch','mod-overlay','mod-return','mod-direct','mod-held','midi-isolation','mod-nested','shadow-punch','midi-boundary','scroll-preserve','midi-cleanup','mute-quant','punch-fast','punch-peak','audio-headroom','voice-headroom','mixer-headroom','dub-stereo','macro-cache','bank-chunks','bank-queue','legacy-fast','engine-headroom','legacy-routing','speech-acid-headroom','groove-strum','mod-hierarchy','wizard-display','wizard-volume','va-machines','click-repair','filter-modes','filter-center','lfo-polarity','resonance-label','mod-redraw-guard','braids-scale','scale-modes','four-lfos','gate-buffer-safe','lfo-lazy-start','scale-startup-safe','lfo-options','lfo-compact-ram','sound-polarity','sound-copy','copy-live','lxr-drums','copy-track-lookup','estus-controls','estus-advanced','estus-engine-read','copy-command','copy-four','estus-opt','live-clear','clear-commit','destination-abi','estus-plocks','page-length','page-dark','page-warp','page-grid','warp-live','warp-irq','filter-gesture','track-pages','filter-key-guard','filter-native-keys','estus-filter-priority','stock-six','stock-services','stock-audio','filter-defaults','ui-idle'):p.add_argument('--'+flag,action='store_true')
 p.add_argument('--legacy-cart',type=Path,help='Cartouche DX7 privee, jamais copiee aux sources')
 p.add_argument('--legacy-classics',type=Path,help='Cartouche utilisateur pour les remplacements prives')
 a=p.parse_args();a.filter_defaults|=a.ui_idle; a.estus_filter_priority|=a.filter_defaults; a.stock_services|=a.stock_audio; a.stock_six|=a.stock_services;a.estus_filter_priority|=a.stock_six;a.filter_native_keys|=a.estus_filter_priority;a.filter_key_guard|=a.filter_native_keys;a.track_pages|=a.filter_key_guard;a.filter_gesture|=a.track_pages;a.warp_irq|=a.filter_gesture;a.warp_live|=a.warp_irq;a.page_grid|=a.warp_live;a.page_warp|=a.page_grid;a.page_dark|=a.page_warp;a.page_length|=a.page_dark;a.estus_plocks|=a.page_length;a.destination_abi|=a.estus_plocks;a.clear_commit|=a.destination_abi;a.live_clear|=a.clear_commit;a.estus_opt|=a.live_clear;a.copy_four|=a.estus_opt;a.copy_command|=a.copy_four;a.estus_engine_read|=a.copy_command;a.estus_advanced|=a.estus_engine_read;a.estus_controls|=a.estus_advanced;a.copy_track_lookup|=a.estus_controls;a.lxr_drums|=a.copy_track_lookup;assert not (a.lxr_drums and a.va_machines);a.copy_live|=a.lxr_drums;a.sound_copy|=a.copy_live;a.sound_polarity|=a.sound_copy;a.lfo_compact_ram|=a.sound_polarity;a.lfo_options|=a.lfo_compact_ram;a.four_lfos|=a.lfo_options;a.scale_startup_safe|=a.lfo_options;a.scale_modes|=a.scale_startup_safe;a.gate_buffer_safe|=a.scale_startup_safe;a.four_lfos|=a.lfo_lazy_start;a.gate_buffer_safe|=a.lfo_lazy_start;a.resonance_label|=a.gate_buffer_safe;a.scale_modes|=a.four_lfos;a.braids_scale|=a.scale_modes;a.mod_redraw_guard|=a.braids_scale;a.resonance_label|=a.mod_redraw_guard;a.lfo_polarity|=a.resonance_label;a.filter_center|=a.lfo_polarity;a.filter_modes|=a.filter_center;a.click_repair|=a.filter_modes;a.wizard_volume|=a.va_machines or a.click_repair;a.wizard_display|=a.wizard_volume;a.mod_hierarchy|=a.wizard_display;a.groove_strum|=a.mod_hierarchy;a.speech_acid_headroom|=a.groove_strum;a.legacy_routing|=a.speech_acid_headroom;a.engine_headroom|=a.legacy_routing;a.legacy_fast|=a.engine_headroom;a.bank_queue|=a.legacy_fast;a.bank_chunks|=a.bank_queue;assert not a.bank_chunks or a.bank_queue or a.check,"v150 retire : utiliser --bank-queue";a.dub_stereo|=a.macro_cache or a.bank_chunks;assert not (a.bank_chunks and a.macro_cache),"Tests transport et DSP separes";assert not (a.dub_stereo and a.mixer_headroom),"DUB148 utilise la base146";a.voice_headroom|=a.mixer_headroom or a.dub_stereo;a.audio_headroom|=a.voice_headroom;a.punch_peak|=a.audio_headroom;a.punch_fast|=a.punch_peak;a.mute_quant|=a.punch_fast;a.midi_cleanup|=a.mute_quant;a.scroll_preserve|=a.midi_cleanup;a.midi_boundary|=a.scroll_preserve;a.shadow_punch|=a.midi_boundary;a.mod_nested|=a.shadow_punch;a.midi_isolation|=a.mod_nested;a.mod_held|=a.midi_isolation;a.mod_direct|=a.mod_held;a.mod_return|=a.mod_direct;a.mod_overlay|=a.mod_return;a.punch|=a.mod_overlay;a.sidechain_fx|=a.punch;a.menu_handoff|=a.sidechain_fx;a.sidechain_mute|=a.menu_handoff;a.compact_controls|=a.sidechain_mute;a.track_abbrev|=a.compact_controls;a.sidechain_label|=a.track_abbrev;a.submenu_align|=a.sidechain_label;a.combo_flip|=a.submenu_align;a.sidechain|=a.combo_flip;a.fx_pattern|=a.sidechain;a.fx_project|=a.fx_pattern;a.wave_starter|=a.fx_project;a.elder_level|=a.wave_starter;a.retrosyn_private|=a.elder_level;a.fundamentals|=a.elder_level;a.bank_guard|=a.fundamentals;a.bank_safe|=a.bank_guard;a.polish|=a.retrosyn_private or a.bank_safe;a.speech_reverb|=a.polish;a.legacy|=a.speech_reverb;assert not a.legacy or a.legacy_cart;a.gate_predelay|=a.legacy;a.gated_phaser96|=a.gate_predelay;a.gated|=a.gated_phaser96;a.fx_input_fix|=a.gated;a.extra_fx|=a.fx_input_fix;a.duck|=a.extra_fx;a.dub_distinct|=a.duck;a.speak_bright|=a.duck;a.speak_talk|=a.speak_bright;a.cheap_fx|=a.dub_distinct;a.speak_speed_fix|=a.cheap_fx or a.speak_talk;a.speak_soft|=a.speak_speed_fix;assert not (a.cheap_fx and a.speak_adult and not a.speak_talk);a.speak_level|=a.speak_adult or a.speak_soft;a.speak_smooth|=a.speak_level;a.speak_clear|=a.speak_smooth;a.speak|=a.speak_clear;a.stock_fx_format_fix|=a.speak;a.no_shimmer|=a.stock_fx_format_fix;a.lean_fx|=a.no_shimmer;a.ps1_fast_opt|=a.lean_fx;a.filter_pair_opt|=a.ps1_fast_opt;a.ps1_cache_opt|=a.filter_pair_opt;a.all_fx_opt|=a.ps1_cache_opt;a.voice_fx_opt|=a.all_fx_opt;a.fx_idle_opt|=a.voice_fx_opt;a.dx_func_fix|=a.fx_idle_opt;a.fx_cpu_opt|=a.dx_func_fix;a.ps1_only|=a.fx_cpu_opt;a.ps1|=a.ps1_only;a.cloud_repair|=a.ps1 and not a.ps1_only;a.cloud|=a.cloud_repair;a.scramble_decay_native|=a.cloud or a.ps1_only;a.scramble_decay_fix|=a.scramble_decay_native;a.octave_polish|=a.scramble_decay_fix;a.octave_delay|=a.octave_polish;a.delay_quality|=a.shimmer_clean or a.octave_delay;a.delay_repair|=a.delay_quality;a.new_delays|=a.delay_repair;a.vinyl_dust|=a.new_delays;a.fx_overlay|=a.vinyl_dust;a.fx_settings|=a.fx_overlay;a.fx_menu|=a.fx_settings;a.center_delay|=a.fx_menu;a.split_sends|=a.center_delay;a.themed_icons|=a.split_sends;a.machine_icons|=a.themed_icons;a.shadow|=a.machine_icons;a.wizard_isolation|=a.shadow;a.keep_params|=a.wizard_isolation;a.scramble_mask|=a.keep_params;a.feral_playable|=a.scramble_mask;a.tiny_order|=a.feral_playable;a.tiny_extra|=a.tiny_order;a.repeat_latch|=a.tiny_extra;a.crusher_wet|=a.repeat_latch;a.crusher|=a.crusher_wet;a.chorus|=a.crusher;a.elder_icon|=a.chorus;a.elder|=a.elder_icon;a.junior|=a.elder;a.feral|=a.junior;a.syntakt_opt|=a.feral;a.chord_opt|=a.syntakt_opt;assert not (a.trx_kick and a.chord_opt);a.wizard|=a.trx_kick or a.chord_opt;a.repeat_record|=a.trx_kick or a.chord_opt;a.repeat_fades|=a.repeat_record;a.unity_amp|=a.repeat_fades
 assert not a.repeat_record or a.wizard
 assert not a.unity_amp or (a.wizard and (a.profile=='no-filter' or a.repeat_fades))
 a.polivoks|=a.wizard and a.profile=='all-features'
 assert not a.polivoks or a.profile=='all-features'
 version='v211' if a.ui_idle and a.stock_audio else 'v210' if a.ui_idle else 'v209' if a.filter_defaults and a.stock_audio else 'v208' if a.filter_defaults else 'v207' if a.stock_audio else 'v206' if a.stock_services else 'v205' if a.stock_six else 'v204' if a.estus_filter_priority else 'v203' if a.filter_native_keys else 'v202' if a.filter_key_guard else 'v201' if a.track_pages else 'v200' if a.filter_gesture else 'v199' if a.warp_irq else 'v198' if a.warp_live else 'v197' if a.page_grid else 'v195' if a.page_warp else 'v194' if a.page_dark else 'v193' if a.page_length else 'v191' if a.estus_plocks else 'v189' if a.destination_abi else 'v188' if a.clear_commit else 'v187' if a.live_clear else 'v186' if a.estus_opt else 'v185' if a.copy_four else 'v184' if a.copy_command else 'v183' if a.estus_engine_read else 'v182' if a.estus_advanced else 'v181' if a.estus_controls else 'v180' if a.copy_track_lookup else 'v179' if a.lxr_drums else 'v178' if a.copy_live else 'v177' if a.sound_copy else 'v176' if a.sound_polarity else 'v175' if a.lfo_compact_ram else 'v174' if a.lfo_options else ('v173' if a.four_lfos or a.lfo_lazy_start else 'v172') if a.scale_startup_safe else 'v171' if a.lfo_lazy_start else ('v170' if a.four_lfos else 'v169') if a.gate_buffer_safe else ('v168adult' if a.speak_adult else 'v168') if a.four_lfos else ('v167adult' if a.speak_adult else 'v167') if a.scale_modes else ('v166adult' if a.speak_adult else 'v166') if a.braids_scale else ('v165adult' if a.speak_adult else 'v165') if a.mod_redraw_guard else ('v164adult' if a.speak_adult else 'v164') if a.resonance_label else ('v163adult' if a.speak_adult else 'v163') if a.lfo_polarity else ('v162badult' if a.speak_adult else 'v162b') if a.filter_center else ('v162adult' if a.speak_adult else 'v162') if a.filter_modes else ('v161adult' if a.speak_adult else 'v161') if a.click_repair else ('v160adult' if a.speak_adult else 'v160') if a.va_machines else ('v159adult' if a.speak_adult else 'v159') if a.wizard_volume else ('v158adult' if a.speak_adult else 'v158') if a.wizard_display else ('v157adult' if a.speak_adult else 'v157') if a.mod_hierarchy else ('v156adult' if a.speak_adult else 'v156') if a.groove_strum else ('v155adult' if a.speak_adult else 'v155') if a.speech_acid_headroom else ('v154adult' if a.speak_adult else 'v154') if a.legacy_routing else ('v153adult' if a.speak_adult else 'v153') if a.engine_headroom else ('v152adult' if a.speak_adult else 'v152') if a.legacy_fast else ('v151adult' if a.speak_adult else 'v151') if a.bank_queue else ('v150adult' if a.speak_adult else 'v150') if a.bank_chunks else ('v149adult' if a.speak_adult else 'v149') if a.macro_cache else ('v148adult' if a.speak_adult else 'v148') if a.dub_stereo else ('v147adult' if a.speak_adult else 'v147') if a.mixer_headroom else ('v146adult' if a.speak_adult else 'v146') if a.voice_headroom else ('v145adult' if a.speak_adult else 'v145') if a.audio_headroom else ('v144adult' if a.speak_adult else 'v144') if a.punch_peak else ('v143adult' if a.speak_adult else 'v143') if a.punch_fast else ('v142adult' if a.speak_adult else 'v142') if a.mute_quant else ('v141adult' if a.speak_adult else 'v141') if a.midi_cleanup else ('v140adult' if a.speak_adult else 'v140') if a.scroll_preserve else ('v139adult' if a.speak_adult else 'v139') if a.midi_boundary else ('v138adult' if a.speak_adult else 'v138') if a.shadow_punch else ('v137adult' if a.speak_adult else 'v137') if a.mod_nested else ('v136adult' if a.speak_adult else 'v136') if a.midi_isolation else ('v135adult' if a.speak_adult else 'v135') if a.mod_held else ('v134adult' if a.speak_adult else 'v134') if a.mod_direct else ('v133adult' if a.speak_adult else 'v133') if a.mod_return else ('v132adult' if a.speak_adult else 'v132') if a.mod_overlay else ('v131adult' if a.speak_adult else 'v131') if a.punch else ('v130adult' if a.speak_adult else 'v130') if a.sidechain_fx else ('v129adult' if a.speak_adult else 'v129') if a.menu_handoff else ('v128adult' if a.speak_adult else 'v128') if a.sidechain_mute else ('v127adult' if a.speak_adult else 'v127') if a.compact_controls else ('v126adult' if a.speak_adult else 'v126') if a.track_abbrev else ('v125adult' if a.speak_adult else 'v125') if a.sidechain_label else ('v124adult' if a.speak_adult else 'v124') if a.submenu_align else ('v123adult' if a.speak_adult else 'v123') if a.combo_flip else ('v122adult' if a.speak_adult else 'v122') if a.sidechain else ('v121adult' if a.speak_adult else 'v121') if a.fx_pattern else ('v120adult' if a.speak_adult else 'v120') if a.fx_project else ('v115adult' if a.speak_adult else 'v115') if a.wave_starter else ('v111adult' if a.speak_adult else 'v111') if a.elder_level else ('v106retro' if a.retrosyn_private else 'v106adult' if a.speak_adult else 'v106') if a.fundamentals else ('v105retro' if a.retrosyn_private else 'v105adult' if a.speak_adult else 'v105') if a.bank_guard else ('v104retro' if a.retrosyn_private else 'v104adult' if a.speak_adult else 'v104') if a.bank_safe else 'v103retro' if a.retrosyn_private else ('v103adult' if a.speak_adult else 'v103') if a.polish else ('v101adult' if a.speak_adult else 'v101') if a.speech_reverb else ('v100adult' if a.speak_adult else 'v100') if a.legacy else ('v99adult' if a.speak_adult else 'v99') if a.gate_predelay else ('v98adult' if a.speak_adult else 'v98') if a.gated_phaser96 else ('v97adult' if a.speak_adult else 'v97') if a.gated else ('v94adult' if a.speak_adult else 'v94') if a.fx_input_fix else ('v93adult' if a.speak_adult else 'v93') if a.extra_fx else ('v91adult' if a.speak_adult else 'v91') if a.duck else ('v90adult' if a.speak_adult else 'v90') if a.speak_bright else ('v89adult' if a.speak_adult else 'v89') if a.speak_talk or a.dub_distinct else 'v88' if a.cheap_fx else ('v87adult' if a.speak_adult else 'v87') if a.speak_speed_fix else ('v86adult' if a.speak_adult else 'v86') if a.speak_soft else 'v85-adult-private' if a.speak_adult else ('v85' if a.profile=='all-features' else 'v85nf') if a.speak_level else ('v84' if a.profile=='all-features' else 'v84nf') if a.speak_smooth else ('v83' if a.profile=='all-features' else 'v83nf') if a.speak_clear else ('v82' if a.profile=='all-features' else 'v82nf') if a.speak else ('v81' if a.profile=='all-features' else 'v81nf') if a.stock_fx_format_fix else ('v80' if a.profile=='all-features' else 'v80nf') if a.no_shimmer else ('v79' if a.profile=='all-features' else 'v79nf') if a.lean_fx else ('v78' if a.profile=='all-features' else 'v78nf') if a.ps1_fast_opt else ('v77' if a.profile=='all-features' else 'v77nf') if a.filter_pair_opt else ('v76' if a.profile=='all-features' else 'v76nf') if a.ps1_cache_opt else ('v75' if a.profile=='all-features' else 'v75nf') if a.all_fx_opt else ('v74' if a.profile=='all-features' else 'v74nf') if a.voice_fx_opt else ('v73' if a.profile=='all-features' else 'v73nf') if a.fx_idle_opt else ('v72' if a.profile=='all-features' else 'v72nf') if a.dx_func_fix else ('v71' if a.profile=='all-features' else 'v71nf') if a.fx_cpu_opt else ('v70' if a.profile=='all-features' else 'v70nf') if a.ps1_only else ('v69' if a.profile=='all-features' else 'v69nf') if a.ps1 else ('v68' if a.profile=='all-features' else 'v68nf') if a.cloud_repair else ('v67' if a.profile=='all-features' else 'v67nf') if a.cloud else ('v66' if a.profile=='all-features' else 'v66nf') if a.scramble_decay_native else ('v65' if a.profile=='all-features' else 'v65nf') if a.scramble_decay_fix else ('v64' if a.profile=='all-features' else 'v64nf') if a.octave_polish else ('v63' if a.profile=='all-features' else 'v63nf') if a.octave_delay else ('v62' if a.profile=='all-features' else 'v62nf') if a.shimmer_clean else ('v61' if a.profile=='all-features' else 'v61nf') if a.delay_quality else ('v60' if a.profile=='all-features' else 'v60nf') if a.delay_repair else ('v59' if a.profile=='all-features' else 'v59nf') if a.new_delays else ('v58' if a.profile=='all-features' else 'v58nf') if a.vinyl_dust else ('v57' if a.profile=='all-features' else 'v57nf') if a.fx_overlay else ('v56' if a.profile=='all-features' else 'v56nf') if a.fx_settings else ('v55' if a.profile=='all-features' else 'v55nf') if a.fx_menu else ('v54' if a.profile=='all-features' else 'v54nf') if a.center_delay else ('v53' if a.profile=='all-features' else 'v53nf') if a.split_sends else ('v51' if a.profile=='all-features' else 'v51nf') if a.themed_icons else ('v50' if a.profile=='all-features' else 'v50nf') if a.machine_icons else ('v49' if a.profile=='all-features' else 'v49nf') if a.shadow else ('v48' if a.profile=='all-features' else 'v48nf') if a.wizard_isolation else ('v47' if a.profile=='all-features' else 'v47nf') if a.keep_params else ('v46' if a.profile=='all-features' else 'v46nf') if a.scramble_mask else ('v45' if a.profile=='all-features' else 'v45nf') if a.feral_playable else ('v44' if a.profile=='all-features' else 'v44nf') if a.tiny_order else ('v43' if a.profile=='all-features' else 'v43nf') if a.tiny_extra else ('v42' if a.profile=='all-features' else 'v42nf') if a.repeat_latch else ('v41' if a.profile=='all-features' else 'v41nf') if a.crusher_wet else ('v40' if a.profile=='all-features' else 'v40nf') if a.crusher else ('v39' if a.profile=='all-features' else 'v39nf') if a.chorus else ('v36' if a.profile=='all-features' else 'v36nf') if a.elder_icon else ('v35' if a.profile=='all-features' else 'v35nf') if a.elder else ('v34' if a.profile=='all-features' else 'v34nf') if a.junior else ('v33' if a.polivoks else 'v33nf') if a.feral else ('v32' if a.polivoks else 'v32nf') if a.syntakt_opt else ('v31' if a.polivoks else 'v31nf') if a.chord_opt else ('v30' if a.polivoks else 'v30nf') if a.trx_kick else ('v26' if a.polivoks else 'v26nf') if a.repeat_record else 'v25' if a.repeat_fades and a.polivoks else 'v24' if a.repeat_fades else 'v23' if a.unity_amp else 'v22' if a.wizard and a.profile=='no-filter' else 'v21' if a.wizard else 'v20' if a.polivoks else 'v19'
 source=OUT/(a.profile+'-macro-names-test-v17.syx');assert hashlib.sha256(source.read_bytes()).hexdigest()==PIN[a.profile]
 meta=json.loads(source.with_suffix('.json').read_text());info,pkg,image,_=read(source)
 official=ROOT/'firmware/model-cycles_OS1.13.syx';device=json.loads((ROOT/'tweaks/model-cycles_OS1.13/device.json').read_text());assert hashlib.sha256(official.read_bytes()).hexdigest()==device['stock_syx_sha256']
 oi,op,stock,stockops=read(official);prefix=bytearray(image[:START]);oldend=int.from_bytes(prefix[0x40195ad0-BASE:0x40195ad4-BASE],'big')-BASE
 packed=image[START:oldend];rt,ops=aplib.depack(struct.pack('>II',len(packed),sum(packed)&0xffffffff)+packed);oldrt=bytes(rt);rt=bytearray(rt)
 tail=bytearray(image[oldend:]);assert TAIL+len(tail)<ORIGIN
 build=OUT/('governor-recovery-'+version);build.mkdir(exist_ok=True)
 cross=str(ROOT.parent/'retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-');os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ['PATH']
 patches=[]
 def patch(at,old,new,area=rt):
  off=runtime_offset(at) if area is rt else at-BASE if area is prefix else at-TAIL
  assert bytes(area[off:off+len(old)])==old,(hex(at),'source guard')
  assert len(old)==len(new);area[off:off+len(old)]=new
  patches.append(dict(at=hex(at),old=old.hex(),new=new.hex(),storage='runtime' if area is rt else 'prefix' if area is prefix else 'tail'))
 aliases={k:v for k,v in meta['dx_symbols'].items() if k in ('dx_enabled','dx_peak','dx_over','dx_new','dx_beat_api')}
 if a.repeat_fades:
  aliases.update({k:meta['beat_repeat_symbols'][k] for k in ('br_valid','br_start','br_length','br_excluded','br_lane_wet','br_side','br_side_on','br_history')});aliases.update(rr_native_mode=0x467ab734 if a.polivoks else 0x467ab6c8)
  if not a.polivoks:aliases.update(rr_native_plain=0x467ab724)
  else:aliases.update(rr_native_render=0x467ab9fe)
  aliases.update({k:meta['beat_repeat_symbols'][k] for k in ('br_active','br_wet','br_keys')})
 # Delegation aux fonctions originales : instructions entieres, jamais du padding.
 tramp='.text\n'
 for name,at,n in [('gr_dx_before_original',meta['dx_symbols']['dx_before'],6)]:
  raw=oldrt[runtime_offset(at):runtime_offset(at)+n] if at>=0x80000000 or at<TAIL else tail[at-TAIL:at-TAIL+n]
  assert raw.hex()==('2f0243f946732000' if 'gate' in name else '2239fc07000c' if 'after' in name else '2039'+struct.pack('>I',aliases['dx_enabled']).hex()),(name,raw.hex())
  tramp+=f'.globl {name}\n{name}:\n.byte '+','.join(str(b) for b in raw)+f'\njmp {at+n:#x}\n'
 if a.repeat_record and not a.polivoks:
  at=0x467abcec;raw=bytes(tail[at-TAIL:at-TAIL+8]);assert raw.hex()=='4feffddc48d744fc'
  tramp+='\n.globl rr_native_render\nrr_native_render:\n.byte '+','.join(str(b) for b in raw)+f'\njmp {at+8:#x}\n'
 if a.trx_kick:
  raw=bytes(prefix[0x400aa08c-BASE:0x400aa094-BASE]);assert raw.hex()=='4fefffec48d71c0c'
  tramp+='\n.globl md_original_update\nmd_original_update:\n.byte '+','.join(str(b) for b in raw)+'\njmp 0x400aa094\n'
 (build/'tramp.S').write_text(tramp)
 objects=[]
 sources=[SRC/'recovery.c',SRC/'hooks.S',build/'tramp.S']+([ROOT/'tools/machines/polivoks_lite/coefficients.c',ROOT/'tools/machines/polivoks_lite/filter.S'] if a.polivoks else [])
 if a.wizard:sources += [ROOT/'tools/machines/polivoks_lite/coefficients.c',ROOT/'tools/machines/polivoks_lite/wizard.S']
 if a.unity_amp:sources += [ROOT/'tools/machines/cpu_audit/unity_amp.S']
 if a.repeat_fades:sources += [ROOT/'tools/machines/cpu_audit/repeat_fades.c']
 if a.repeat_fades and a.polivoks:sources += [ROOT/'tools/machines/cpu_audit/repeat_tail.S']
 if a.chord_opt:sources += [ROOT/'tools/machines/chord_cpu/oscillator.S']
 if a.trx_kick:
  from machinedrum_assets import prepare
  sources += [ROOT/'tools/machines/machinedrum'/name for name in ('trx_bd.c','controls.c','bridge.c')] + [prepare(ROOT,build)]
 for i,src in enumerate(sources):
  extra=['-DPF_WIZARD=1','-DPF_COEFF_NAME=pw_coeff','-DPF_F_ADDRESS=0x401bbe5c','-DPF_Q_ADDRESS=0x401bbe74'] if a.wizard and src.name=='coefficients.c' and (not a.polivoks or i>3) else []
  if a.repeat_fades and a.polivoks and src.name=='repeat_fades.c':extra+=['-DRR_LOCAL_PLAIN=1']
  if a.repeat_record and src.name=='repeat_fades.c':extra+=['-DRR_FAST_RECORD=1','-DRR_RECORD_UNROLL=4']
  if a.speech_acid_headroom and src.name=='repeat_fades.c':extra+=['-DRR_HOT155=1']
  if a.filter_pair_opt and src.name=='filter.S':extra+=['-DPF_PAIR_OPT=1']
  if a.trx_kick and src.parent.name=='machinedrum':extra+=['-O2']
  obj=build/f'{i}.o';objects.append(obj);subprocess.run([cross+'gcc.exe','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-Wall','-Wextra','-Werror',*extra,'-c',str(src),'-o',str(obj)],check=True)
 ld=build/'module.ld';elf=build/'module.elf';binary=build/'module.bin'
 ld.write_text(f'SECTIONS {{ .text {ORIGIN:#x} : {{ *(.text*) *(.rodata*) }} . = ALIGN(4); .data : {{ *(.data*) }} .bss : {{ *(.bss*) *(COMMON) }} . = ALIGN(4); gr_end = .; {'.hot 0x80007490 : { *(.hot) }' if a.unity_amp else ''} }}\n'+'\n'.join(f'PROVIDE({k} = {v:#x});' for k,v in dict(aliases,gr_epilogue=0x8000747a).items()))
 libs=[subprocess.check_output([cross+'gcc.exe','-mcpu=54418','-print-libgcc-file-name'],text=True).strip()] if a.trx_kick else []
 subprocess.run([cross+'ld.exe','-T',str(ld),'-o',str(elf),*map(str,objects),*libs],check=True);subprocess.run([cross+'objcopy.exe','-O','binary','-j','.text','-j','.data',str(elf),str(binary)],check=True)
 sy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(elf)],text=True).splitlines() if len(r.split())==3}
 blob=binary.read_bytes().ljust(sy['gr_end']-ORIGIN,b'\0');assert ORIGIN+len(blob)<0x46800000
 tail.extend(bytes(ORIGIN-TAIL-len(tail)));tail.extend(blob)
 for at,target,n,area in [(0x8000e8f0,sy['gr_trig'],8,rt),(0x80007398,0x80007468,10,rt),(meta['dx_symbols']['dx_before'],sy['gr_dx_before'],6,tail),(meta['dx_symbols']['dx_beat_key'],sy['gr_beat_key'],6,tail)]:
  off=runtime_offset(at) if area is rt else at-BASE if area is prefix else at-TAIL;old=bytes(area[off:off+n]);patch(at,old,b'\x4e\xf9'+struct.pack('>I',target)+b'\x4e\x71'*((n-6)//2),area)
 # Fragment chaud dans 76 octets de padding SRAM deja copies au boot.
 obj=build/'finish.o';finishelf=build/'finish.elf';finishbin=build/'finish.bin'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(SRC/'finish.S'),'-o',str(obj)],check=True)
 (build/'finish.ld').write_text('SECTIONS { .text 0x80007468 : { *(.text*) } }\n'+''.join(f'PROVIDE({k} = {sy[k]:#x});\n' for k in ('gr_record','gr_recover_entry')))
 subprocess.run([cross+'ld.exe','-T',str(build/'finish.ld'),'-o',str(finishelf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(finishelf),str(finishbin)],check=True)
 finish=finishbin.read_bytes();assert len(finish)==40,len(finish)
 fsy={r.split()[2]:int(r.split()[0],16) for r in subprocess.check_output([cross+'nm.exe','-n',str(finishelf)],text=True).splitlines() if len(r.split())==3}
 assert fsy['gr_epilogue']==0x8000747a,fsy
 patch(0x80007468,bytes(len(finish)),finish)
 patch(0x8000e70e,bytes.fromhex('e1894c421001'),b'\x4e\xb9'+struct.pack('>I',sy['gr_load']))
 scan_at=0x8000735e;obj=build/'scan.o';scanelf=build/'scan.elf';scanbin=build/'scan.bin'
 subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(SRC/'scan.S'),'-o',str(obj)],check=True)
 (build/'scan.ld').write_text(f'SECTIONS {{ .text {scan_at:#x} : SUBALIGN(2) {{ *(.text*) }} }}\nPROVIDE(GR_LOUD = 0x80007394);')
 subprocess.run([cross+'ld.exe','-T',str(build/'scan.ld'),'-o',str(scanelf),str(obj)],check=True);subprocess.run([cross+'objcopy.exe','-O','binary',str(scanelf),str(scanbin)],check=True)
 scan=scanbin.read_bytes();assert len(scan)==38,scan.hex()
 patch(scan_at,bytes.fromhex('740078072218d28384812218d28384812218d28384812218d283848153846ae4d683b4836410'),scan)
 if a.polivoks:
  # Le boot resident copie ce corps depuis son unique occurrence du runtime.
  marker=bytes.fromhex('202f000841f9401bbd604ab00c0067000258')
  assert oldrt.count(marker)==1
  site=oldrt.index(marker);assert RUNTIME+site==0x467a539a
  patch(RUNTIME+site,oldrt[site:site+6],b'\x4e\xf9'+struct.pack('>I',sy['pf_run']))
 if a.wizard:
  # Le lecteur mid et le lecteur side atteignent cette meme fonction resident.
  wizard_entry=bytes.fromhex('4fefffe848ef0c1c00042e042e8741f9401bbe8c')
  assert oldrt.count(wizard_entry)==1
  site=oldrt.index(wizard_entry);assert RUNTIME+site==0x46797998
  patch(RUNTIME+site,oldrt[site:site+10],b'\x4e\xf9'+struct.pack('>I',sy['pw_run'])+b'\x4e\x71'*2)
 if a.unity_amp:
  hotbin=build/'amp-hot.bin'
  subprocess.run([cross+'objcopy.exe','-O','binary','-j','.hot',str(elf),str(hotbin)],check=True)
  hot=hotbin.read_bytes();assert len(hot)==36 and sy['audit_unity']==0x80007490
  patch(0x80007490,bytes(len(hot)),hot)
  patch(0x400a9710,bytes.fromhex('2c2802a02e2802a4'),b'\x4e\xf9'+struct.pack('>I',sy['audit_amp'])+b'\x4e\x71',prefix)
 if a.repeat_fades:
  patch(0x467ab790 if a.polivoks else 0x467ab7b8,bytes.fromhex('4fefff5848d75cfc' if a.polivoks else '4fefff50721f'),b'\x4e\xf9'+struct.pack('>I',sy['rr_tracks'])+(b'\x4e\x71' if a.polivoks else b''),tail)
  if a.polivoks:patch(0x467abd84,bytes.fromhex('4ebafc78508f'),b'\x4e\xf9'+struct.pack('>I',sy['rr_audio_tail']),tail)
  elif a.repeat_record:patch(0x467abcec,bytes.fromhex('4feffddc48d744fc'),b'\x4e\xf9'+struct.pack('>I',sy['rr_render'])+b'\x4e\x71',tail)
 if a.chord_opt:patch(0x400a8906,bytes.fromhex('287c8000caa8'),b'\x4e\xf9'+struct.pack('>I',sy['chord_fast']),prefix)
 if a.trx_kick:
  # Nom court distinct pour identifier le moteur installe, sans agrandir la chaine.
  patch(0x401300d8,b'Kick\0',b'MDBD\0',prefix)
  patch(0x40125a36,b'KICK\0',b'MDBD\0',prefix)
  for at,target,guard in [(0x400aa08c,'md_kick_update','4fefffec48d71c0c'),(0x400aa3c4,'md_kick_render','4e56ffec48d7040c')]:patch(at,bytes.fromhex(guard),b'\x4e\xf9'+struct.pack('>I',sy[target])+b'\x4e\x71',prefix)
 if a.syntakt_opt:
  # Seule fonction remplacee, a adresse fixe et dans sa taille native SRAM.
  at=0x80001d9e;n=0x154;off=runtime_offset(at);original=bytes(rt[off:off+n])
  assert hashlib.sha256(original).hexdigest()=='ff0a17584977c8d714e68ed5fac84fda11e6053294aa454791ebf41459af9390'
  obj=build/'syntakt-osc.o';elfosc=build/'syntakt-osc.elf';binosc=build/'syntakt-osc.bin'
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(ROOT/'tools/machines/syntakt_cpu/oscillator.S'),'-o',str(obj)],check=True)
  subprocess.run([cross+'ld.exe','-e','st_osc_fast',f'-Ttext={at:#x}',str(obj),'-o',str(elfosc)],check=True)
  subprocess.run([cross+'objcopy.exe','-O','binary',str(elfosc),str(binosc)],check=True)
  osc=binosc.read_bytes();assert 0<len(osc)<=n and len(osc)%2==0
  patch(at,original,osc+b'\x4e\x71'*((n-len(osc))//2))
 if a.voice_fx_opt:
  # Resonateur natif : meme62octets SRAM, pas de detour vers SDRAM.
  at=0x80003470;n=62;off=runtime_offset(at);original=bytes(rt[off:off+n])
  assert hashlib.sha256(original).hexdigest()=='a0da28143232af80209202c832e63258facc81c522e00d7793fa97cd253ca217'
  obj=build/'syntakt-resonator.o';elfres=build/'syntakt-resonator.elf';binres=build/'syntakt-resonator.bin'
  subprocess.run([cross+'gcc.exe','-mcpu=54418','-c',str(ROOT/'tools/machines/syntakt_cpu/resonator.S'),'-o',str(obj)],check=True)
  subprocess.run([cross+'ld.exe','-e','st_resonator_fast',f'-Ttext={at:#x}',str(obj),'-o',str(elfres)],check=True)
  subprocess.run([cross+'objcopy.exe','-O','binary',str(elfres),str(binres)],check=True)
  res=binres.read_bytes();assert len(res)==n
  patch(at,original,res)
  meta['syntakt_resonator_opt']=dict(address=at,bytes=n,hardware_tested=False)
 feral_meta=None
 if a.feral:
  from feral_assets import prepare as feral_prepare,address as feral_address,CODE as FERAL_ORIGIN
  import build_machine_identity_test as identity
  feral_blob,feral_meta=feral_prepare(ROOT,build)
  assert TAIL+len(tail)<FERAL_ORIGIN
  tail.extend(bytes(FERAL_ORIGIN-TAIL-len(tail)));tail.extend(feral_blob)
  # Index15 conserve : aucune renumerotation des autres machines.
  for at,value,expected in [(0x46789084,feral_meta['update'],0x4677c000),(0x467890cc,feral_meta['render'],0x4677c2f2)]:patch(at,struct.pack('>I',expected),struct.pack('>I',value))
  at=0x4678903c;old=bytes(rt[at-RUNTIME:at-RUNTIME+4]);patch(at,old,struct.pack('>I',feral_meta['name']))
  # Quatre controles identiques a ceux du firmware source ; DEC par defaut50.
  for k in range(5):
   at=0x4678ad60+56*k;old=bytes(rt[at-RUNTIME:at-RUNTIME+56]);new=bytearray(old)
   if k<4:
    src_at=feral_address(0x43034000+56*(76+k));desc=feral_blob[src_at-FERAL_ORIGIN:src_at-FERAL_ORIGIN+56]
    for off in (8,12,16,44,52):new[off:off+4]=desc[off:off+4]
   else:struct.pack_into('>I',new,16,0x3200)
   patch(at,old,bytes(new))
  profile=dict(machine=15,name='Feral',icon='F',**{'class':'SYNTH'},style='FERAL',str=3,dex=4,mag=5)
  identity.ICONS['F']=['11111','11000','11000','11110','11000','11000','11000']
  for table,render in [('identity_stats',identity.stats),('identity_icons',identity.icon)]:
   descriptor=meta[table]+9*28;off=descriptor-TAIL;ptr=int.from_bytes(tail[off+16:off+20],'big');pixels=render(profile)
   old=bytes(tail[ptr-TAIL:ptr-TAIL+len(pixels)]);assert len(old)==len(pixels);patch(ptr,old,pixels,tail)
  meta['machine_identities'][9]=profile
 junior_meta=None
 if a.junior:
  from junior_assets import prepare as junior_prepare,CODE as JUNIOR_ORIGIN
  jr_blob,junior_meta=junior_prepare(ROOT,build,'ELDER' if a.elder else 'JUNIOR');js=junior_meta['symbols']
  assert TAIL+len(tail)<JUNIOR_ORIGIN
  tail.extend(bytes(JUNIOR_ORIGIN-TAIL-len(tail)));tail.extend(jr_blob)
  # Emplacement16 RETROSYN conserve ; les dix-sept autres machines restent fixes.
  for at,target in [(0x46789088,js['junior_update']),(0x467890d0,js['junior_render'])]:
   old=bytes(rt[at-RUNTIME:at-RUNTIME+4]);assert 0x46785000<=int.from_bytes(old,'big')<0x46788000
   patch(at,old,struct.pack('>I',target))
  at=0x46789040;old=bytes(rt[at-RUNTIME:at-RUNTIME+4]);patch(at,old,struct.pack('>I',js['junior_name']))
  defaults=[0,0,0,0,50]
  for k in range(5):
   at=0x4678ae78+56*k;old=bytes(rt[at-RUNTIME:at-RUNTIME+56]);new=bytearray(old)
   for off,val in [(8,0),(12,0x7f00),(16,defaults[k]<<8),(44,js['junior_labels']+8*k),(52,js['junior_short_labels']+8*k)]:struct.pack_into('>I',new,off,val)
   patch(at,old,bytes(new))
  profile=dict(machine=16,name='ELDER' if a.elder else 'JUNIOR',icon='elder-gameboy' if a.elder_icon else 'E' if a.elder else 'J',**{'class':'SYNTH'},style='CHIP',str=3,dex=5,mag=4)
  identity.ICONS['E']=['11111','11000','11000','11110','11000','11000','11111']
  identity.ICONS['J']=['11111','00011','00011','00011','11011','11011','01110']
  elder_icon_pixels=None
  if a.elder_icon:
   art=json.loads((ROOT/'tools/machines/junior/artwork/elder-gameboy.json').read_text())
   assert art['width']==art['height']==34 and len(art['rows'])==34 and all(len(row)==34 and set(row)<=set('.#') for row in art['rows'])
   elder_icon_pixels=identity.encode([[int(c=='#') for c in row] for row in art['rows']])
   assert len(elder_icon_pixels)==272
   assert elder_icon_pixels==(ROOT/'tools/machines/junior/artwork/elder-gameboy_34x34.bin').read_bytes()
   junior_meta['icon']='elder-gameboy';junior_meta['icon_sha256']=hashlib.sha256(elder_icon_pixels).hexdigest()
  for table,render in [('identity_stats',identity.stats),('identity_icons',identity.icon)]:
   descriptor=meta[table]+10*28;off=descriptor-TAIL;ptr=int.from_bytes(tail[off+16:off+20],'big');pixels=elder_icon_pixels if a.elder_icon and table=='identity_icons' else render(profile)
   old=bytes(tail[ptr-TAIL:ptr-TAIL+len(pixels)]);assert len(old)==len(pixels);patch(ptr,old,pixels,tail)
  meta['machine_identities'][10]=profile
 chorus_meta=None
 if a.chorus:
  from chorus_assets import apply as chorus_apply
  chorus_meta=chorus_apply(ROOT,build,prefix,rt,tail,meta,patch,slow_modes=a.crusher_wet,format_fix=a.stock_fx_format_fix)
 crush_meta=None
 if a.crusher:
  from crush_assets import apply as crush_apply
  meta['stereo_chorus']=chorus_meta
  crush_meta=crush_apply(ROOT,build,prefix,tail,meta,patch,wet=a.crusher_wet,split_sends=a.split_sends,center_delay=a.center_delay,cpu_opt=a.voice_fx_opt,lean_fx=a.lean_fx)
 latch_meta=None
 if a.repeat_latch:
  from repeat_latch_assets import apply as latch_apply
  latch_meta=latch_apply(ROOT,build,tail,meta,patch,advanced=a.fx_menu)
 shadow_meta=None
 if a.shadow:
  from shadow_assets import prepare as shadow_prepare
  shadow_blob,shadow_meta=shadow_prepare(ROOT,build,punch_distortion=a.shadow_punch);at=shadow_meta['code'];assert not any(rt[at-RUNTIME:at-RUNTIME+len(shadow_blob)]);assert not any(rt[shadow_meta['bss']-RUNTIME:shadow_meta['end']-RUNTIME]);patch(at,bytes(len(shadow_blob)),shadow_blob)
 speak_meta=None;speak_blob=None
 if a.speak:
  from speak_assets import prepare as speak_prepare
  speak_blob,speak_meta=speak_prepare(ROOT,build,0,clear=a.speak_clear,smooth=a.speak_smooth,level=a.speak_level,adult=a.speak_adult,soft=a.speak_soft,speed_fix=a.speak_speed_fix,talk=a.speak_talk,bright=a.speak_bright,pitch_fix=a.speech_reverb,sheen=a.polish,fast=a.mixer_headroom,headroom=a.speech_acid_headroom)
 legacy_meta=None;legacy_blob=None
 if a.legacy:
  from dx7_assets import prepare as legacy_prepare
  legacy_blob,legacy_meta=legacy_prepare(ROOT,build,0,0,a.legacy_cart,classics_path=a.legacy_classics,optimize=a.polish,bank_safe=a.bank_safe,bank_guard=a.bank_guard,bank_chunks=a.bank_chunks,bank_queue=a.bank_queue,legacy_fast=a.legacy_fast,legacy_deep=a.engine_headroom,legacy_routing=a.legacy_routing)
 retro_meta=None;retro_blob=None
 if a.retrosyn_private:
  from retrosyn_private_assets import prepare as retro_prepare
  retro_blob,retro_meta=retro_prepare(ROOT,build)
 punch_meta=None;punch_blob=None
 if a.punch:
  from punch_assets import prepare as punch_prepare
  punch_blob,punch_meta=punch_prepare(ROOT,build,fast=a.punch_fast,peak=a.punch_peak,hot=a.voice_headroom)
 va_meta=None;va_blob=None;va_deferred=[]
 if a.va_machines:
  from va160_assets import prepare as va_prepare
  va_blob,va_meta=va_prepare(ROOT,build)
 lxr_meta=None;lxr_segments=[]
 if a.lxr_drums:
  from lxr178_assets import prepare as lxr_prepare
  lxr_segments,lxr_meta=lxr_prepare(ROOT,build,named_controls=a.estus_controls,advanced=a.estus_advanced,engine_read=a.estus_engine_read,copy_build=a.copy_command,optimize=a.estus_opt,live_clear=a.live_clear,plocks=a.estus_plocks,filter_priority=a.estus_filter_priority)
 tiny_meta=None
 if a.tiny_extra:
  from tiny_extra_assets import apply as tiny_apply
  selected_patch=patch;va_kw={}
  if a.lxr_drums:
   from tiny_extra178_assets import apply as tiny_apply
   va_kw={'lxr':lxr_meta}
   def selected_patch(at,old,new,area=rt):
    if area is tail and 0x4683c000<=at<0x46840000:va_deferred.append((at,old,new))
    else:patch(at,old,new,area)
  if a.va_machines:
   from tiny_extra160_assets import apply as tiny_apply
   va_kw={'va':va_meta}
   def selected_patch(at,old,new,area=rt):
    if area is tail and 0x4683c000<=at<0x46840000:va_deferred.append((at,old,new))
    else:patch(at,old,new,area)
  tiny_meta=tiny_apply(ROOT,build,prefix,rt,tail,oldrt,meta,selected_patch,reorder=a.tiny_order,shadow=shadow_meta,speak=speak_meta,legacy=legacy_meta,retro=retro_meta,punch=punch_meta,**va_kw)
 if a.machine_icons:
  import build_machine_identity_test as icon_identity
  for machine,name in [(17,'midi-five-pin'),(13,'acid-tb303'),(15,'feral-cheetah')]:
   at=meta['identity_icons']+(machine-6)*28;ptr=int.from_bytes(tail[at-TAIL+16:at-TAIL+20],'big');art=ROOT/'tools/machines/shadow/artwork'/(name+'_34x34.bin');pixels=art.read_bytes();assert len(pixels)==272;patch(ptr,bytes(tail[ptr-TAIL:ptr-TAIL+272]),pixels,tail)
  shadow_meta['icons'].update({'MIDI Out':'midi-five-pin','ACID':'acid-tb303','Feral':'feral-cheetah'})
 if a.themed_icons:
  for machine,name in [(7,'sd-vintage-snare'),(8,'clap-hands'),(9,'toy-spinning-top'),(10,'bits-binary-chip'),(11,'swarm-bees'),(12,'macro-dna')]:
   at=meta['identity_icons']+(machine-6)*28;ptr=int.from_bytes(tail[at-TAIL+16:at-TAIL+20],'big');pixels=(ROOT/'tools/machines/shadow/artwork'/(name+'_34x34.bin')).read_bytes();assert len(pixels)==272;patch(ptr,bytes(tail[ptr-TAIL:ptr-TAIL+272]),pixels,tail)
  shadow_meta['remaining_themed_icons']={7:'snare',8:'clap',9:'spinning top',10:'binary chip',11:'bees',12:'DNA'}
 playable_meta=None
 if a.feral_playable:
  from feral_playable_assets import apply as playable_apply
  playable_meta=playable_apply(ROOT,build,prefix,rt,tail,meta,patch)
 scramble_meta=None
 if a.scramble_mask:
  from scramble_mask_assets import apply as scramble_apply
  scramble_meta=scramble_apply(ROOT,build,prefix,rt,tail,meta,patch,short_labels=a.keep_params,decay_fix=a.scramble_decay_fix,native_decay=a.scramble_decay_native,delete_reset=a.speak_level,per_pattern=a.sidechain)
 keep_meta=None
 if a.keep_params:
  from keep_params_assets import apply as keep_apply
  meta['scramble_mask']=scramble_meta
  keep_meta=keep_apply(ROOT,build,prefix,tail,meta,patch,isolate=a.wizard_isolation,midi_isolate=a.midi_isolation,midi_boundary=a.midi_boundary,scroll_preserve=a.scroll_preserve,midi_cleanup=a.midi_cleanup,max_machine=27 if a.va_machines else 24 if a.lxr_drums else 23 if a.punch else 22 if a.retrosyn_private else 21 if a.legacy else 20 if a.speak else 19 if a.shadow else 18)
 fx_meta=None
 if a.fx_menu:
  from fx_menu_assets import apply as fx_apply
  meta.update(recovery_symbols=sy,stereo_chorus=chorus_meta,delay_crush=crush_meta,repeat_latch=latch_meta,tiny_extra=tiny_meta,legacy=legacy_meta)
  fx_meta=fx_apply(ROOT,build,prefix,tail,meta,patch,settings_shortcuts=a.fx_settings,overlay=a.fx_overlay,dust=a.vinyl_dust,new_delays=a.new_delays,delay_repair=a.delay_repair,delay_quality=a.delay_quality,shimmer_clean=a.shimmer_clean,octave_delay=a.octave_delay,octave_polish=a.octave_polish,cloud=a.cloud,cloud_repair=a.cloud_repair,ps1=a.ps1,cpu_opt=a.fx_cpu_opt,dx_func_fix=a.dx_func_fix,idle_opt=a.fx_idle_opt,voice_opt=a.voice_fx_opt,active_opt=a.all_fx_opt,ps1_cache_opt=a.ps1_cache_opt,ps1_fast_opt=a.ps1_fast_opt,lean_fx=a.lean_fx,no_shimmer=a.no_shimmer,speak=a.speak,cheap_fx=a.cheap_fx,dub_distinct=a.dub_distinct,duck=a.duck,extra_fx=a.extra_fx,input_fix=a.fx_input_fix,gated=a.gated,gated_phaser96=a.gated_phaser96,gate_predelay=a.gate_predelay,legacy=a.legacy,speech_reverb=a.speech_reverb,polish=a.polish,retrosyn_private=a.retrosyn_private,bank_safe=a.bank_safe,bank_guard=a.bank_guard,sidechain_returns=a.sidechain_fx,punch=a.punch,dub_stereo=a.dub_stereo,gate_buffer_safe=a.gate_buffer_safe,estus=a.lxr_drums)
 if a.speak:
  speak_blob,speak_meta=speak_prepare(ROOT,build,fx_meta['symbols']['fx_popup'],clear=a.speak_clear,smooth=a.speak_smooth,level=a.speak_level,adult=a.speak_adult,soft=a.speak_soft,speed_fix=a.speak_speed_fix,talk=a.speak_talk,bright=a.speak_bright,pitch_fix=a.speech_reverb,sheen=a.polish,fast=a.mixer_headroom,headroom=a.speech_acid_headroom)
  at=speak_meta['code'];assert fx_meta['symbols']['fx_bss_end']<=at and speak_meta['end']<=fx_meta['ps1_hot_address']
  old=bytes(tail[at-TAIL:at-TAIL+len(speak_blob)]);assert len(old)==len(speak_blob) and not any(old)
  patch(at,old,speak_blob,tail)
  patch(0x401005bc,struct.pack('>I',fx_meta['symbols']['fx_popup']),struct.pack('>I',speak_meta['symbols']['speak_popup']),prefix)
 if a.legacy:
  legacy_blob,legacy_meta=legacy_prepare(ROOT,build,speak_meta['symbols']['speak_popup'],fx_meta['aliases']['fx_notice'],a.legacy_cart,classics_path=a.legacy_classics,optimize=a.polish,bank_safe=a.bank_safe,bank_guard=a.bank_guard,bank_chunks=a.bank_chunks,bank_queue=a.bank_queue,legacy_fast=a.legacy_fast,legacy_deep=a.engine_headroom,legacy_routing=a.legacy_routing)
  at=legacy_meta['code'];assert at>=0x46850000 and legacy_meta['end']<0x468b0000
  assert TAIL+len(tail)<at;tail.extend(bytes(at-TAIL-len(tail)));tail.extend(legacy_blob)
  def legacy_j(addr):return b'\x4e\xf9'+struct.pack('>I',addr)
  patch(0x4007f694,bytes.fromhex('487940f1bf24'),legacy_j(legacy_meta['symbols']['dx7_din_rx']),prefix)
  patch(0x4007f6a8,bytes.fromhex('4fefffd848d77c7c'),legacy_j(legacy_meta['symbols']['dx7_usb_rx'])+b'\x4e\x71',prefix)
  patch(0x401005bc,struct.pack('>I',speak_meta['symbols']['speak_popup']),struct.pack('>I',legacy_meta['symbols']['dx7_popup']),prefix)
 if a.retrosyn_private:
  at=retro_meta['code'];assert TAIL+len(tail)<at;tail.extend(bytes(at-TAIL-len(tail)));tail.extend(retro_blob)
 if a.punch:
  at=punch_meta['code'];assert punch_meta['end']<retro_meta['code'];old=bytes(tail[at-TAIL:at-TAIL+len(punch_blob)]);assert len(old)==len(punch_blob) and not any(old);patch(at,old,punch_blob,tail)
 if a.lxr_drums:
  for at,old,new in va_deferred:patch(at,old,new,tail)
 if a.va_machines:
  for at,old,new in va_deferred:patch(at,old,new,tail)
  at=va_meta['code'];assert TAIL+len(tail)<at;tail.extend(bytes(at-TAIL-len(tail)));tail.extend(va_blob)
  meta['va_machines']=va_meta
 if a.fundamentals:
  from fundamentals_assets import apply as fundamentals_apply
  meta['fundamentals']=fundamentals_apply(ROOT,build,prefix,rt,tail,meta,patch,fx_meta,tiny_meta,shadow_gain=a.combo_flip,shadow_extra=a.submenu_align,punch=punch_meta,acid_fast=a.engine_headroom,acid_hot=a.speech_acid_headroom)
 if a.wave_starter:
  from wave_starter_assets import apply as wave_starter_apply
  meta['wave_starter']=wave_starter_apply(ROOT,build,rt,tail,meta,patch,tiny_meta,legacy_meta,prefix,private_pool_safe=a.lfo_compact_ram)
 if a.sidechain:
  from sidechain_assets import apply as sidechain_apply
  meta['sidechain']=sidechain_apply(ROOT,build,prefix,rt,tail,meta,patch,fx_meta,compact=a.combo_flip,arrow=a.submenu_align,short_label=a.sidechain_label,track_abbrev=a.track_abbrev,compact_controls=a.compact_controls,mute_option=a.sidechain_mute,fx_returns=a.sidechain_fx,fast=a.voice_headroom)
 if a.fx_project:
  from fx_project_assets import apply as fx_project_apply
  meta['fx_project']=fx_project_apply(ROOT,build,prefix,rt,tail,meta,patch,fx_meta,patterns=a.fx_pattern,tiny=tiny_meta,retro=retro_meta)
 if a.combo_flip:
  from gesture_swap_assets import apply as gesture_swap_apply
  meta['gesture_swap']=gesture_swap_apply(ROOT,build,prefix,rt,tail,meta,patch,once=a.submenu_align,menu_handoff=a.menu_handoff)
 if a.mod_overlay:
  from mod_overlay_assets import apply as mod_overlay_apply
  meta.update(fx_menu=fx_meta,legacy=legacy_meta,punch=punch_meta)
  meta['mod_overlay']=mod_overlay_apply(ROOT,build,prefix,rt,tail,meta,patch,popup_return=a.mod_return,direct_popup=a.mod_direct,held_popup=a.mod_held,nested_popup=a.mod_nested,popup_labels=a.wizard_volume,popup_priority=a.lfo_polarity,redraw_guard=a.mod_redraw_guard)
 if a.mute_quant:
  from mute_quant_assets import apply as mute_quant_apply
  meta['mute_quant']=mute_quant_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.audio_headroom:
  from audio_headroom145_assets import apply as headroom_apply
  meta['audio_headroom']=headroom_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.mixer_headroom:
  from mixer_headroom147_assets import apply as mixer_apply
  meta['mixer_headroom']=mixer_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.groove_strum:
  from groove_strum_assets import apply as groove_apply
  meta['private_retrosyn']=retro_meta
  meta['groove_strum']=groove_apply(ROOT,build,prefix,rt,tail,meta,patch,hierarchy=a.mod_hierarchy,groove_switch=a.wizard_display,human_apply=a.click_repair,filter_modes=a.filter_modes,lfo_polarity=False,lfo_options=a.lfo_options,lfo_compact_ram=a.lfo_compact_ram,filter_key_guard=a.filter_key_guard,ui_idle=a.ui_idle)
 if a.wizard_display:
  from wizard_display_assets import apply as display_apply
  meta['wizard_display']=display_apply(ROOT,build,prefix,rt,tail,meta,patch,volume=a.wizard_volume)
 if a.bank_queue:
  # Hors donnees WAVE, apres HALL et avant l'art PUNCH ; aucun etat147/149.
  lo=0x468a8000;hi=legacy_meta['symbols']['dx7_chunks_end']
  assert meta['audio_headroom']['hall']['end']<=lo<hi<0x468ae000
  assert not a.macro_cache and not a.mixer_headroom
  assert len(tail)>=hi-TAIL and not any(tail[lo-TAIL:hi-TAIL])
  meta['bank_queue']=dict(code=lo,end=hi,slots_per_port=40,usable_per_port=39,frame_max=139,hardware_tested=False)
 if a.macro_cache:
  from macro_cache149_assets import apply as macro_cache_apply
  meta['macro_cache']=macro_cache_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.click_repair:
  from click161_assets import apply as click_apply
  meta['click_repair']=click_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.filter_modes:
  from filter162_assets import apply as filter_apply
  meta['filter_modes']=filter_apply(ROOT,build,prefix,rt,tail,meta,patch,center=a.filter_center,gesture=a.filter_gesture,key_guard=a.filter_key_guard,native_keys=a.filter_native_keys,defaults=a.filter_defaults,ui_idle=a.ui_idle)
 if a.lfo_polarity:
  from polarity163_assets import apply as polarity_apply
  meta['lfo_polarity']=polarity_apply(ROOT,build,prefix,rt,tail,meta,patch,wave_safe=a.lfo_options,sound_polarity=a.sound_polarity,sound_copy=a.sound_copy,copy_live=a.copy_live,copy_track_lookup=a.copy_track_lookup,copy_command=a.copy_command,copy_four=a.copy_four,clear_commit=a.clear_commit,filter_defaults=a.filter_defaults,ui_idle=a.ui_idle)
 if a.resonance_label:
  from resonance164_assets import apply as resonance_apply
  meta['resonance_label']=resonance_apply(ROOT,build,prefix,rt,tail,meta,patch)
 if a.braids_scale:
  if a.scale_modes:
   from scale167_assets import apply as scale_apply
  else:
   from scale166_assets import apply as scale_apply
  meta['braids_scale']=scale_apply(ROOT,build,prefix,rt,tail,meta,patch,**({'startup_safe':a.scale_startup_safe,'compact_labels':a.lfo_options} if a.scale_modes else {}))
 if a.four_lfos:
  from lfo168_assets import apply as lfo_apply
  meta['four_lfos']=lfo_apply(ROOT,build,prefix,rt,tail,meta,patch,lazy_start=a.lfo_lazy_start,count_option=a.lfo_options,wave_safe=a.lfo_options,compact_ram=a.lfo_compact_ram,sound_polarity=a.sound_polarity,copy_four=a.copy_four,live_clear=a.live_clear,clear_commit=a.clear_commit,destination_abi=a.destination_abi,filter_defaults=a.filter_defaults,ui_idle=a.ui_idle)
 if a.copy_four:
  lp=meta['lfo_polarity']['symbols'];mx=meta['four_lfos']['symbols'];api=lp['lp_copy_api'];values=[mx[k] for k in ('mx_extra','mx_polarity','mx_copy_prepare','mx_copy_commit','mx_copy_redraw')]
  patch(api,bytes(20),struct.pack('>5I',*values),tail)
 if a.lxr_drums:
  if a.estus_controls:
   previous_popup=int.from_bytes(prefix[0x401005bc-BASE:0x401005c0-BASE],'big')
   old_symbols=lxr_meta['symbols'];lxr_segments,lxr_meta=lxr_prepare(ROOT,build,named_controls=True,previous_popup=previous_popup,advanced=a.estus_advanced,engine_read=a.estus_engine_read,copy_build=a.copy_command,optimize=a.estus_opt,live_clear=a.live_clear,plocks=a.estus_plocks,filter_priority=a.estus_filter_priority,aliases={'estus_menu':meta['fx_menu']['aliases']['menu'],'estus_fx_open':meta['fx_menu']['symbols']['fx_menu_open'],'estus_wf_api':meta['symbols']['wf_api'],'estus_notice':meta['fx_menu']['symbols']['fx_notice']})
   assert all(old_symbols[k]==lxr_meta['symbols'][k] for k in ('lxr178_update','lxr178_render','lxr178_name','lxr178_labels','lxr178_short_labels'))
   patch(0x401005bc,struct.pack('>I',previous_popup),struct.pack('>I',lxr_meta['symbols']['lxr178_popup']),prefix)
   from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
   ui=meta['four_lfos']['symbols']['mx_frame'];raw=bytes(tail[ui-TAIL:ui-TAIL+24]);n=0
   for ins in Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040).disasm(raw,ui):
    assert not ins.mnemonic.startswith('b') and 'pc' not in ins.op_str.lower(),(ins.mnemonic,ins.op_str)
    n+=ins.size
    if n>=6:break
   ui_tramp=raw[:n]+bytes.fromhex('4ef9')+struct.pack('>I',ui+n)
   ui_target=lxr_meta['symbols']['lxr178_ui_old']
   for i,(lo,chunk) in enumerate(lxr_segments):
    if lo<=ui_target and ui_target+32<=lo+len(chunk):
     z=bytearray(chunk);off=ui_target-lo;assert not any(z[off:off+32]);z[off:off+len(ui_tramp)]=ui_tramp;lxr_segments[i]=(lo,bytes(z));break
   else:raise AssertionError('ESTUS UI trampoline missing')
   patch(ui,raw[:n],bytes.fromhex('4ef9')+struct.pack('>I',lxr_meta['symbols']['lxr178_ui_frame'])+bytes.fromhex('4e71')*((n-6)//2),tail)
  if a.estus_advanced:
   from capstone import Cs,CS_ARCH_M68K,CS_MODE_BIG_ENDIAN,CS_MODE_M68K_040
   enc=meta['fx_menu']['symbols']['fx_encoder'];raw=bytes(tail[enc-TAIL:enc-TAIL+32]);n=0
   for ins in Cs(CS_ARCH_M68K,CS_MODE_BIG_ENDIAN|CS_MODE_M68K_040).disasm(raw,enc):
    assert not ins.mnemonic.startswith('b') and 'pc' not in ins.op_str.lower(),(ins.mnemonic,ins.op_str)
    n+=ins.size
    if n>=6:break
   tramp=raw[:n]+bytes.fromhex('4ef9')+struct.pack('>I',enc+n)
   target=lxr_meta['symbols']['estus_old_encoder']
   for i,(lo,chunk) in enumerate(lxr_segments):
    if lo<=target and target+32<=lo+len(chunk):
     z=bytearray(chunk);off=target-lo;assert not any(z[off:off+32]);z[off:off+len(tramp)]=tramp;lxr_segments[i]=(lo,bytes(z));break
   else:raise AssertionError('ESTUS encoder trampoline missing')
   patch(enc,raw[:n],bytes.fromhex('4ef9')+struct.pack('>I',lxr_meta['symbols']['estus_encoder'])+bytes.fromhex('4e71')*((n-6)//2),tail)
  reset=0x400a7ab8;reset_old=bytes(prefix[reset-BASE:reset-BASE+10]);assert reset_old==bytes.fromhex('206f0004203cfff40000')
  trampoline=reset_old+bytes.fromhex('4ef9')+struct.pack('>I',reset+10)
  target=lxr_meta['symbols']['lxr178_old_reset']
  for i,(lo,raw) in enumerate(lxr_segments):
   if lo<=target and target+32<=lo+len(raw):
    b=bytearray(raw);off=target-lo;assert not any(b[off:off+32]);b[off:off+len(trampoline)]=trampoline;lxr_segments[i]=(lo,bytes(b));break
  else:raise AssertionError('ESTUS reset trampoline missing')
  patch(reset,reset_old,bytes.fromhex('4ef9')+struct.pack('>I',lxr_meta['symbols']['lxr178_reset_hook'])+bytes.fromhex('4e71')*2,prefix)
  lxr_meta['native_voice_reset_hook']=hex(reset)
  for at,raw in lxr_segments:
   old=bytes(tail[at-TAIL:at-TAIL+len(raw)]);assert len(old)==len(raw) and not any(old),('ESTUS occupied',hex(at),len(raw))
   patch(at,old,raw,tail)
  lxr_meta['segments']=[dict(at=at,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for at,raw in lxr_segments]
  meta['estus']=lxr_meta
 if a.page_length:
  from page193_assets import apply as page_apply
  meta['page_length']=page_apply(ROOT,build,prefix,rt,tail,meta,patch,dark=a.page_dark,warp=a.page_warp,grid=a.page_grid,track=a.track_pages)
 if a.stock_six:
  if a.stock_services:
   from stock206_assets import apply as stock_six_apply
  else:
   from stock205_assets import apply as stock_six_apply
  meta['stock_six']=stock_six_apply(ROOT,build,prefix,rt,tail,dict(meta,tiny_extra=tiny_meta,speak=speak_meta,feral=feral_meta,feral_playable=playable_meta,legacy=legacy_meta,fx_menu=fx_meta,junior=junior_meta,shadow=shadow_meta,punch=punch_meta),patch,**({'connect_offset':True} if a.stock_audio else {}))
 if int(''.join(ch for ch in version if ch.isdigit()))>=204:
  from title204_assets import apply as title_apply,flasher_release
  release_version,release_file=flasher_release(ROOT) if not a.title_version else (a.title_version,'--title-version')
  meta['title_screen']=title_apply(ROOT,build,prefix,patch,release_version,lite=a.stock_six)
  meta['title_screen']['release_source']=release_file
 allowed=set(i for p in patches if p['storage']=='runtime' for i in range(runtime_offset(int(p['at'],16)),runtime_offset(int(p['at'],16))+len(bytes.fromhex(p['old']))))
 assert {i for i,(x,y) in enumerate(zip(oldrt,rt)) if x!=y}<=allowed
 if a.ui_idle:
  from ui_idle210_assets import apply as idle_apply
  meta['ui_idle']=idle_apply(ROOT,build,prefix,rt,tail,meta,patch)
 stream=aplib.repack(bytes(rt),ops,bytes(x!=y for x,y in zip(rt,oldrt)));assert aplib.depack(stream)[0]==bytes(rt)
 struct.pack_into('>I',prefix,0x40195ad0-BASE,BASE+START+len(stream)-8);struct.pack_into('>I',prefix,0x40195ad8-BASE,len(tail))
 data=bytes(prefix)+stream[8:]+bytes(tail);assert 0<len(data)-len(image)<(1600000 if a.four_lfos else 1300000 if a.sidechain else 1100000 if a.retrosyn_private else 1000000 if a.legacy else 650000 if a.ps1 else 590000 if a.cloud else 520000 if a.delay_quality else 460000 if a.new_delays else 420000 if a.fx_menu else 320000 if a.chorus else 260000 if a.junior else 200000 if a.trx_kick or a.feral else 16384),(len(data),len(image))
 dirty=bytearray(len(data));dirty[:START]=bytes(x!=y for x,y in zip(prefix,stock));dirty[START:]=b'\1'*(len(data)-START)
 section=aplib_grow.repack_grow(data,stockops,dirty,START);assert aplib.depack(section)[0]==data
 if a.stock_six:
  from bootstrap205_assets import pack as bootstrap_safe_pack
  section,meta['bootstrap_packing']=bootstrap_safe_pack(section)
 plains=[]
 for s in op['sections']:
  try:plains.append(aplib.depack(op['blob'][s['off']:s['off']+s['size']])[0])
  except Exception:pass
 key=container.find_key(plains,op['blob'][:-container.DIGEST_LEN],op['blob'][-container.DIGEST_LEN:]);assert key
 rebuilt=container.rebuild(op,{3:section},key);raw=wrap(container.build_stream(rebuilt,BYTES_PER_MSG),oi['product'],oi['start_seq'])
 destdir=OUT/('staging' if a.stage else 'validation' if a.unity_amp else '');destdir.mkdir(exist_ok=True)
 dest=destdir/(a.profile+('-polivoks-cpu-trim-test-' if a.repeat_fades and a.polivoks else '-wizard-polivoks-cpu-trim-test-' if a.repeat_fades else '-wizard-polivoks-unity-cpu-test-' if a.unity_amp else '-wizard-polivoks-cpu-test-' if a.wizard and not a.polivoks else '-polivoks-cpu-test-' if a.polivoks else '-cpu-recovery-test-')+version+'.syx')
 assert not a.check or (dest.exists() and dest.read_bytes()==raw),'private build out of date'
 if not a.check:dest.write_bytes(raw)
 _,final,after,_=read(dest);assert after==data
 for s in op['sections']:
  if s['id']==3:continue
  t=next(t for t in final['sections'] if t['id']==s['id']);assert op['blob'][s['off']:s['off']+s['size']]==final['blob'][t['off']:t['off']+t['size']]
 meta.update(base=source.name,base_sha256=PIN[a.profile],sha256=hashlib.sha256(raw).hexdigest(),main_os_sha256=hashlib.sha256(after).hexdigest(),hardware_tested=False,release=None,main_changed=False,recovery_symbols=sy,recovery_patches=patches,runtime_tail_end=hex(sy['gr_end']),diagnostics='DX A/P/O/N',governor_thresholds_unchanged=True,polivoks_inspired=a.polivoks or a.wizard,filter_pair_opt=a.filter_pair_opt,shared_filter_enabled=a.profile=='all-features',shared_filter_polivoks=a.polivoks,filter_topology=('2-pole nonlinear lowpass' if a.polivoks or a.wizard else 'unchanged'),wizard_polivoks=a.wizard,unity_amp=a.unity_amp,repeat_fades=a.repeat_fades,repeat_record=a.repeat_record,trx_kick=a.trx_kick,chord_osc_optimized=a.chord_opt,syntakt_osc_optimized=a.syntakt_opt,feral_replaces_tiny=a.feral,feral=feral_meta,junior_replaces_retrosyn=a.junior,elder_replaces_retrosyn=a.elder,elder_gameboy_icon=a.elder_icon,junior=junior_meta,stereo_chorus=chorus_meta,delay_crush=crush_meta,repeat_latch=latch_meta,tiny_extra=tiny_meta,fx_menu=fx_meta,feral_playable=playable_meta,scramble_mask=scramble_meta,keep_params=keep_meta,shadow=shadow_meta,speak=speak_meta,legacy=legacy_meta,private_retrosyn=retro_meta,punch=punch_meta,private_adult_speak=a.speak_adult,public_release_allowed=not (a.speak_adult or a.legacy),machinedrum_source_sha256=('68542e30917b9918ccaee2b2237df62c8a00479938680b85aca93ce4fbca44c8' if a.trx_kick else None),md_rate_adapter=('linear 147/160' if a.trx_kick else None),md_kick_label=('MDBD' if a.trx_kick else None),md_integer_product_bits=(64 if a.trx_kick else None),md_arithmetic=('software64-no-emac' if a.trx_kick else None))
 if not a.check:dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
 print('CHECKED' if a.check else 'BUILT',dest.name,meta['sha256'],'module bytes',len(blob),flush=True)
if __name__=='__main__':main()
