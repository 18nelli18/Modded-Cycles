"""Inventaire ferme des editions pour la reconstruction, sans publier de firmware.

Chaque edition garde un contrat explicite et une reference de comportement.
Une reference n'est pas une entree autorisee du futur constructeur propre.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gen_governor_recovery_test import read, BASE, START


def inventory(folder, scope, edition):
    meta = json.loads((folder/'BUILD.json').read_text(encoding='utf-8'))
    image_path = next(folder.glob('*.syx'))
    raw = image_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == meta['sha256']
    _, package, image, _ = read(image_path)
    end = int.from_bytes(image[0x40195ad0-BASE:0x40195ad4-BASE], 'big')-BASE
    modules = []
    for name, item in meta.items():
        if not isinstance(item, dict):
            continue
        if isinstance(item.get('code'), int) and isinstance(item.get('code_bytes'), int):
            modules.append(dict(name=name, start=item['code'], end=item['code']+item['code_bytes'],
                                bytes=item['code_bytes'], symbols=len(item.get('symbols', {})),
                                liveness='unresolved'))
    overlaps = []
    for i, left in enumerate(modules):
        for right in modules[i+1:]:
            lo, hi = max(left['start'], right['start']), min(left['end'], right['end'])
            if lo < hi:
                overlaps.append(dict(left=left['name'], right=right['name'], start=lo, end=hi))
    added_only = scope == 'additions'
    optional = scope == 'optional'
    machines = ([x for x in range(6, 25) if x != 21] if added_only else list(range(6)) if edition == 'lite'
                else list(range(25)) + [28] if optional else [x for x in range(25) if x != 21])
    contract = dict(stock_machines=not added_only, selectable_machine_ids=machines,
                    dummy=optional and edition == 'full', chordkeys=optional or added_only,
                    legacy=optional and edition == 'full',
                    machinedrum=optional and edition == 'full',
                    shared_controls_and_effects=True, stock_machine_punch=True,
                    machine_browser_default='Stk', release='3.00')
    return dict(scope=scope, edition=edition, contract=contract,
                behavior_reference=dict(folder=str(folder.resolve()), sha256=meta['sha256']),
                size=dict(syx=len(raw), container=len(package['blob']), decoded_main=len(image),
                          prefix=START, compressed_runtime=end-START, appended=len(image)-end),
                modules=modules, module_overlaps=overlaps,
                rebuild_ready=False, reason='Source ownership, roots and retired dependencies must be resolved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    editions = []
    for scope in ('main', 'optional'):
        for edition in ('full', 'lite'):
            editions.append(inventory(ROOT.parent/'sidechain-regression300/fixed'/scope/edition, scope, edition))
    editions.append(inventory(ROOT.parent/'clean-rebuild300/behavior/additions/full', 'additions', 'full'))
    report = dict(schema=1, purpose='Clean build contracts and ownership audit',
                  publication_authorized=False, editions=editions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    for item in editions:
        print(item['scope'], item['edition'], item['size']['syx'], 'bytes;',
              len(item['modules']), 'recorded modules;', len(item['module_overlaps']), 'overlapping claims')


if __name__ == '__main__':
    main()
