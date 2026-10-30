"""Generer la recette Optional TRX-B2/SD/CH sans distribuer de tables ROM.

python tools/gen_optional_machinedrum.py --cycles officiel.syx --md MD1.63.syx
  --cross m68k-elf- [--check] [--work-folder build/optional-machinedrum]
Les fichiers firmware de travail restent locaux et ignores par Git. Note203.
"""
from pathlib import Path
import argparse,hashlib,json,os,runpy,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--cycles',type=Path,required=True);p.add_argument('--md',type=Path,required=True)
p.add_argument('--base',type=Path);p.add_argument('--cross');p.add_argument('--check',action='store_true')
p.add_argument('--work-folder',type=Path,default=ROOT/'build/optional-machinedrum')
a=p.parse_args();mapping=json.loads((ROOT/'tools/machines/md/base-map.json').read_text())
base=(a.base or ROOT/'docs/flasher'/mapping['source_file']).resolve()
assert hashlib.sha256(base.read_bytes()).hexdigest()==mapping['source_sha256'],'Optional2.61 epingle requis'
assert hashlib.sha256(a.cycles.read_bytes()).hexdigest()=='44fe586269631a0ca7da25a3383fc6733c314809505fc3cc52f1e0ed9800640c','Cycles1.13 officiel requis'
cross=a.cross or os.environ.get('M68K_CROSS') or next((n for n in ('m68k-linux-gnu-','m68k-elf-') if shutil.which(n+'gcc')),None)
if not cross:
 local='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
 if Path(local+'gcc.exe').exists():cross=local
if not cross:p.error('toolchain ColdFire absent : fournir --cross')
a.work_folder=a.work_folder.resolve();(a.work_folder/'probe').mkdir(parents=True,exist_ok=True)
os.environ.update(MD_WORK=str(a.work_folder),MD_BASE_FILE=str(base),MD_ROM=str(a.md.resolve()),MD_CYCLES=str(a.cycles.resolve()),M68K_CROSS=cross,MD_EXE='.exe' if os.name=='nt' else '')
sys.path[:0]=[str(ROOT/'tools/optional_md'),str(ROOT/'tools'),str(ROOT.parent/'boot-check-deps')]
for name in ('catalogue_probe.py','compile_probe.py','sparse_probe.py','export_recipe.py'):runpy.run_path(str(ROOT/'tools/optional_md'/name),run_name='__main__')
generated=(a.work_folder/'machinedrum-data.js').read_bytes();target=ROOT/'docs/flasher-optional/machinedrum-data.js'
if a.check:assert target.read_bytes()==generated,'Recette MD non reproductible : verifier le compilateur et regenerer'
else:target.write_bytes(generated)
print('PASS recette MD reproductible, tables ROM absentes de la recette publique')
