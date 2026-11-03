"""Demarrage reel des sorties du constructeur navigateur Optional et MD."""
from pathlib import Path
import hashlib,json
from capture_rebuild300_boot import capture
W=Path(__file__).resolve().parents[3]/'release302'
base=json.loads((W/'final/optional/full/BUILD.json').read_text())
for name in ['md-mask-3fffff.syx','opt-mask-1.syx']:
 folder=W/'selection'/name[:-4];folder.mkdir(parents=True,exist_ok=True)
 raw=(W/'delivery'/name).read_bytes();(folder/name).write_bytes(raw)
 m=dict(base,sha256=hashlib.sha256(raw).hexdigest());(folder/'BUILD.json').write_text(json.dumps(m))
 capture(folder,folder/'cold')
 raw=(folder/'cold/runtime.bin').read_bytes();sy=base['dummy300']['symbols']
 assert raw[sy['dy_name']-0x46700000:sy['dy_name']-0x46700000+6]==bytes(6)
 print('PASS selection cold boot without Dummy:',name,flush=True)
