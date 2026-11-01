"""Assembler3.00 : Dummy uniquement Optional Full, stockage CK Optional, export commun."""
from pathlib import Path
import json,subprocess,sys,concurrent.futures,shutil
R=Path(__file__).resolve().parents[1];root=R.parent/'release300';cycles='H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx'
def build(pair):
 scope,ed=pair;source=R.parent/'release300-test/recent-cuts'/('full' if pair==('main','full') else scope+'/'+ed)
 chain=[]
 if pair==('optional','full'):chain.append(('gen_dummy300_comparison.py','dummy'))
 if scope=='optional':chain.append(('gen_chord_storage300_comparison.py','chord-storage'))
 chain.append(('gen_transfer_native300_comparison.py','export'))
 for tool,stage in chain:
  m=json.loads((source/'BUILD.json').read_text());dest=root/'stages'/scope/ed/stage
  r=subprocess.run([sys.executable,str(R/'tools'/tool),'--source',str(next(source.glob('*.syx'))),'--metadata',str(source/'BUILD.json'),'--cycles',cycles,'--output',str(dest),'--expected-sha256',m['sha256']],cwd=R,capture_output=True,text=True)
  if r.returncode:raise RuntimeError((pair,tool,r.stdout,r.stderr))
  source=dest;print('BUILT',scope,ed,stage,flush=True)
 final=root/'final'/scope/ed;final.mkdir(parents=True,exist_ok=True);m=json.loads((source/'BUILD.json').read_text());m.update(release='3.00',scope=scope,edition=ed,dummy_available=pair==('optional','full'),dummy_selection_bit=22 if pair==('optional','full') else None)
 shutil.copyfile(next(source.glob('*.syx')),final/'Supermodel_3.00_Release.syx');(final/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n');print('FINAL',scope,ed,m['sha256'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(build,([tuple(sys.argv[1:3])] if len(sys.argv)==3 else [('main','full'),('main','lite'),('optional','full'),('optional','lite')])))