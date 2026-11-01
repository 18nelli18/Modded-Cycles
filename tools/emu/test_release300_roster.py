"""Roster3.00 : Dummy seulement Optional Full et bit22, Lite six machines."""
from pathlib import Path
src=Path(__file__).with_name('test_control_all_undo.py').read_text().split("if m.get('cpu_monitor'):")[0].split('held=set();')[0]
exec(compile(src,__file__,'exec'))
optional=m['scope']=='optional';full=m['edition']=='full'
assert bool(m.get('dummy300'))==(optional and full)
if optional and full:
 d=m['dummy300']['symbols'];r.w32(0x468d0ff0,0x7ffff);assert not r.call(d['dy_allowed'],28)
 r.w32(0x468d0ff0,0x400000);assert r.call(d['dy_allowed'],28)==1
 for i in range(6,28):assert not r.call(d['dy_allowed'],i)
 assert r.call(d['mb_step'],5,1)==28
 r.w32(0x468d0ff0,0x7ffff);assert r.call(d['mb_step'],5,1)==6
else:
 assert bytes(r.u.mem_read(0x400a7d96,6)).hex()=='2005e4a07201','Dummy audio detour in excluded edition'
 assert bytes(r.u.mem_read(0x400147a4,2)).hex()==('7018' if full else '7005')
 if not full:
  fn=m['activity_masks']['symbols']['mb_step'];current=0;seen={0}
  for i in range(30):
   r.w32(m['activity_masks']['symbols']['rm_machine_valid'],0);current=r.call(fn,current,1);seen.add(current)
  assert seen==set(range(6)),seen
assert bool(m.get('chord_storage300'))==optional
print('PASS roster',m['scope'],m['edition'],'Dummy bit22 only Optional Full; stock-six Lite; ChordKeys Optional')
a.output.write_text(json.dumps(dict(scope=m['scope'],edition=m['edition'],dummy_optional_full_only=True,dummy_checkbox_bit=22,lite_stock_six=True,chordkeys_optional_only=True),indent=2))