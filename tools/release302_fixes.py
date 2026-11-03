"""Reconstruit les corrections retenues de349 sur chacune des quatre editions.

Les essais retires (LOW24k, CHORD24k, sortie acceleree et autres regressions)
ne sont pas rejoues. Chaque generateur conserve ses gardes binaires.
"""
from pathlib import Path
def apply(meta,native,runtime,sram,stock,out):
 out=Path(out)
 def invoke(key,module,*args,**kwargs):
  import importlib
  result=importlib.import_module(module).apply(meta,*args,out/key,**kwargs)
  meta[key]=result;return result
 invoke('fx_wake_recovery','fx_wake303',native,runtime,stock)
 invoke('diagnostic_midi','diagnostic_midi303',native,runtime,stock)
 invoke('exact_zero_voices','exact_zero_voice304',runtime,sram)
 invoke('eco_hall','eco_hall305',runtime,sparse=True)
 invoke('hall_merged_gain','eco_hall305',runtime,sparse=True,merged=True)
 invoke('delay_static','delay_static307',native,runtime)
 invoke('filter_single_div','filter_div307',runtime,full_cache=True)
 meta['filter_restore_48k']={'rate':48000,'idle_sleep_unchanged':True,'half_rate_trial_excluded':True}
 invoke('chord_second','chord_second308',native,runtime,sram)
 invoke('filter_unroll','filter_unroll308',runtime)
 invoke('fx_energy','fx_energy309',native,runtime,sram)
 invoke('silent_commit_guard','silent_commit310',native,runtime,sram)
 q=invoke('quality_economy','quality311',native,runtime,sram)
 for key,d in q['modules'].items():meta[key].update(code_bytes=d['code_bytes'],sha256=d['sha256'],symbols=d['symbols'],quality_unchanged=False)
 invoke('diagnostic_midi','diagnostic_midi303',native,runtime,sram,upgrade=True)
 d=invoke('fx_scan_unroll','fx_scan312',runtime)
 for k in ['code_bytes','symbols','sha256']:meta['fx_energy'][k]=d[k]
 d=invoke('panic_stock','panic_stock313',runtime)
 for key,field in [('code_bytes','scan_bytes'),('sha256','scan_sha256'),('symbols','scan_symbols')]:meta['fx_energy'][key]=d[field]
 invoke('post_static','post_static314',native,runtime,dry_bypass=True)
 invoke('upgrade_remote_data','upgrade_key317',runtime)
 invoke('deep_idle_wake','deep_idle329',native,runtime,automatic_stop=True)
 invoke('remote_panel','remote_panel318',native,runtime)
 d=invoke('hall_fractional_ramp','hall_ramp322',runtime,opt='-O2',fractional=True);meta['hall_merged_gain'].update(d)
 meta['detailed_profile_removed']={'complete_IRQ_accounting_retained':True,'normal_DX_retained':True,'overrun_and_cut_counters_retained':True}
 invoke('sram_audio','sram_audio337',native,runtime,sram,include_delay=True,include_delay_filter=True,full_delay=True,prefer_chord=True)
 invoke('ui_fixes348','ui_fixes348',native,runtime)
 invoke('wizard_names349','wizard_names349',native,runtime)
 invoke('dummy_removed302','remove_dummy302',native,runtime)
 from eco_stock_reverb306 import apply as eco
 meta['eco_stock_reverb']=eco(native)
 meta['release302_fixes']={'comparison_base':'3.49','LOW_rate':48000,'governor_thresholds_changed':False,'voice_stealing_resolved':False,'filter_sequence_clear_resolved':False}
