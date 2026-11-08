"""Selection Optional3.06 : execute le roster natif et le parcours DATA."""
from pathlib import Path
import json,argparse
from test_seq_gen_menu import Rig
p=argparse.ArgumentParser();p.add_argument('--reference',type=Path,required=True);p.add_argument('--generated',type=Path,required=True);a=p.parse_args();base=a.reference;out=a.generated;m=json.loads((base/'final/optional/full/BUILD.json').read_text());s=m['dummy300']['symbols'];rows=json.loads((out/'rows.json').read_text())
for row in rows:
 mask=row['mask'];r=Rig((base/'cold/optional/full/native.bin').read_bytes(),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(0x46700000,0x300000);r.u.mem_write(0x46700000,(out/f'mask-{mask}.bin').read_bytes());r.u.mem_map(0xfc070000,0x1000)
 # Lite a son propre roster ; les compositions non nulles gardent dy_allowed.
 if not mask:continue
 want=[i for i in range(28) if i<6 or mask&(1<<(i-6))];actual=[i for i in range(29) if r.call(s['dy_allowed'],i)];assert actual==want,(mask,actual,want)
 current=0;seen={0}
 for _ in range(32):
  r.w32(s['rm_machine_valid'],0);current=r.call(s['mb_step'],current,1);seen.add(current)
 assert seen==set(want),(mask,seen,want)
 print('PASS real selector and DATA roster',hex(mask),actual,flush=True)
 row['native_roster_verified']=True
(out/'proof.json').write_text(json.dumps(rows,indent=2)+'\n')
