"""Le selecteur Optional refuse28 et garde toutes les autres selections permises."""
from pathlib import Path
s=Path(__file__).with_name('profile_voice_filter343.py').read_text().split('coefficients=Counter()')[0]
exec(compile(s,__file__,'exec'))
d=meta['dummy300'];sy=d['symbols'];rows=[]
for md in [0,1]:
 e.uc.mem_write(sy['dy_md_present'],struct.pack('>I',md))
 for mask in [0,1,0x7ffff,0x3fffff,0x7fffff]:
  e.uc.mem_write(0x468d0ff0,struct.pack('>I',mask));e.uc.mem_write(0x469c423c,struct.pack('>I',mask))
  expected_mask=mask if md or mask else 0x7ffff
  values=[e.call(sy['dy_allowed'],m) for m in range(30)]
  assert values==[int(m<6 or (m<28 and ((expected_mask>>(m-6))&1))) for m in range(30)],(md,mask,values)
  rows.append(dict(md=md,mask=mask,allowed=[i for i,v in enumerate(values) if v]))
for item in meta['dummy_removed302']['erased']:
 # Les entrees de delegation remettent six octets au debut des anciens corps.
 at=item['at'];raw=bytes(e.uc.mem_read(at,item['bytes']))
 if at in [sy['dy_voice'],sy['dy_icon_bitmap'],sy['dy_name']]:assert not any(raw)
assert bytes(e.uc.mem_read(0x400a7d96,6))==bytes.fromhex('2005e4a07201')
args.output.write_text(json.dumps(dict(rows=rows,Dummy_selectable=False,voice_hook_removed=True),indent=2)+'\n')
print('PASS300 allowed-machine checks; Dummy audio hook, name and art removed',flush=True)
