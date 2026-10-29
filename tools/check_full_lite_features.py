"""Comparer les fonctions partagees ; seules les optimisations MACRO sont exclues."""
from pathlib import Path
import argparse,json
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--full',type=Path,required=True);p.add_argument('--lite',type=Path,required=True)
p.add_argument('--output',type=Path,required=True);a=p.parse_args()
f=json.loads((a.full/'BUILD.json').read_text());l=json.loads((a.lite/'BUILD.json').read_text())
fp,lp=f['per_track_fx'],l['per_track_fx']
machine_only={'cymbal_fixed_filter_path','harmonics_exact_target_cache','harmonics_zero_trailing_partials','macro_fold_steady_parameter'}
shared=[k for k,v in fp.items() if isinstance(v,bool) and k not in machine_only]
for k in shared:assert fp[k]==lp.get(k),(k,fp[k],lp.get(k))
for k in ['four_lfos','lfo_reload','lfo_polarity','lfo_workflow','filter_modes','groove_strum','mute_quant','sidechain','fx_project','repeat_latch']:
 assert k in f and k in l,k
assert f['filter_modes']['types']==l['filter_modes']['types']
assert f['fx_menu']['delay_selector_order']==l['fx_menu']['delay_selector_order']
assert f['fx_menu']['reverb_selector_order']==l['fx_menu']['reverb_selector_order']
assert f['per_track_fx']['acid_envelope_menu']=='Mod Setup > Global > ACID'
assert 'acid_envelope_modes' not in lp
report=dict(full=f['sha256'],lite=l['sha256'],shared_boolean_features=shared,machine_only_exceptions=sorted(machine_only),shared_subsystems=10,filter_and_FX_choices_equal=True,ACID_Full_only=True,hardware_tested=False)
a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS Full/Lite shared features;',len(shared),'matching flags; ACID is machine-specific')
