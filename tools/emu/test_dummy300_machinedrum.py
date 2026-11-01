"""Coexistence Dummy et MD : installateurs reels, delegues dynamiques et masque."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
s=m['dummy300']['symbols'];assert r.r32(s['dy_md_present'])==1
mds=(R/'docs/flasher-optional/machinedrum-data.js').read_text();md=json.loads(mds[mds.index('=')+1:].strip().rstrip(';'))
for name,key in [('left','tiny_left'),('right','tiny_right'),('shown','shown'),('amp_gate','amp_gate'),('lfo_gate','lfo_gate')]:
 at=m['tiny_extra']['symbols'][key];patch=next((p for p in md['patches'] if p['at']==at),None)
 if patch and patch['new'].startswith('4ef9'):
  expected=int(patch['new'][4:12],16);assert r.r32(s['dy_next_'+name])==expected,(name,hex(r.r32(s['dy_next_'+name])),hex(expected))
for mask,expected in [(0x400000,28),(0x80000,25),(0x100000,26),(0x200000,27),(0x7fffff,6)]:
 r.w32(md['symbols']['md_mask'],mask);r.w32(s['rm_machine_valid'],0);assert r.call(s['mb_step'],5,1)==expected,(hex(mask),expected)
 assert bool(r.call(s['dy_allowed'],28))==bool(mask&0x400000)
print('PASS actual MD+Dummy native boot, dynamic icon/parameter delegates, five machine selections and bit22')
a.output.write_text(json.dumps(dict(native_MD_Dummy_boot=True,dynamic_MD_helpers_retained=True,dummy_selection_bit22=True,five_masks=True,hardware_tested=False),indent=2))