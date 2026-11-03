"""Prepare les quatre editions3.03 et leurs captures froides, hors site public."""
from pathlib import Path
import concurrent.futures
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent/'release303'


def build(pair):
    scope, edition = pair
    if scope == 'main':
        source = ROOT.parent/'controls367'/('final-v2/main/full' if edition == 'full' else 'main-lite')
        cold = ROOT.parent/'controls367'/('final-v2/cold/main/full' if edition == 'full' else 'main-lite-cold')
        flags = []
    else:
        source = ROOT.parent/'release302/final/optional'/edition
        cold = ROOT.parent/'release302/cold/optional'/edition
        flags = ['--without-stage-profile', '--voice-filter-unroll', '--native-finish',
                 '--phase-sram', '--native-biquad', '--filter-lut350', '--eco-delay356',
                 '--restore-hall-capture', str(cold), '--routing-core363',
                 '--routing-post364', '--retrig-plain367', '--song-cursor367']
    dest = WORK/'final'/scope/edition
    dest.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(ROOT/'tools/rebuild300_pack.py'), '--reference', str(source),
               '--capture', str(cold), '--cycles',
               'H:/CREATURE-source/retrosyn-integration-step-rec-solo/firmware/model-cycles_OS1.13.syx',
               '--output', str(dest), '--release', '3.03', '--compression-candidates', '8',
               '--compression-history', *flags]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (dest/'build.log').write_text(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError((pair, result.stdout, result.stderr))
    subprocess.run([sys.executable, str(ROOT/'tools/emu/capture_rebuild300_boot.py'),
                    '--build', str(dest), '--output', str(WORK/'cold'/scope/edition)], cwd=ROOT, check=True)
    print('PASS BUILD/COLD', scope, edition, flush=True)


if __name__ == '__main__':
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(build, [('main', 'full'), ('main', 'lite'),
                              ('optional', 'full'), ('optional', 'lite')]))
