"""Construire les editions2.99 depuis leurs bases2.75 epinglees, memes sources partagees."""
from pathlib import Path
import argparse,json,os,subprocess,sys,shutil
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--scope',choices=['main','optional'],required=True);p.add_argument('--edition',choices=['full','lite'],required=True);a=p.parse_args()
source=R.parent/'control-all-latch-stock-screen-test/full' if (a.scope,a.edition)==('main','full') else R.parent/'release275/final'/a.scope/a.edition
out=R.parent/'release299'/a.scope/a.edition
cycles=Path('H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx')
chain=[('gen_single_modulator_comparison.py','294'),('gen_control_all_undo_test.py','295'),('gen_steady_modulator_comparison.py','296'),('gen_sparse_static_comparison.py','298'),('gen_cpu_monitor_comparison.py','299')]
for tool,stage in chain:
 target=out/stage;m=json.loads((source/'BUILD.json').read_text(encoding='utf-8'))
 subprocess.run([sys.executable,str(R/'tools'/tool),'--source',str(next(source.glob('*.syx'))),'--metadata',str(source/'BUILD.json'),'--cycles',str(cycles),'--output',str(target),'--expected-sha256',m['sha256']],cwd=R,check=True)
 source=target
final=R.parent/'release299/final'/a.scope/a.edition;final.mkdir(parents=True,exist_ok=True)
m0=json.loads((source/'BUILD.json').read_text(encoding='utf-8'))
if (final/'BUILD.json').exists():assert m0['sha256']==json.loads((final/'BUILD.json').read_text(encoding='utf-8'))['sha256'],'Release bytes changed'
shutil.copyfile(next(source.glob('*.syx')),final/next(source.glob('*.syx')).name)
m=json.loads((source/'BUILD.json').read_text(encoding='utf-8'));m.update(release='2.99',edition=a.edition,scope=a.scope);(final/'BUILD.json').write_text(json.dumps(m,indent=2)+'\n')
print('FINAL',a.scope,a.edition,m['sha256'],flush=True)
