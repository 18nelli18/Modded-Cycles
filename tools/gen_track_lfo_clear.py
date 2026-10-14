#!/usr/bin/env python3
"""Adaptateurs A clear/Undo : deux LFO, sans déplacer les anciennes recettes.

Produit du code propre à intégrer dans le RAW MIDI réservé par le parent.
--cycles OS1.13 --catalog sélection.json --output work/a-clear-lfo-undo.json
Le code ne contient aucune routine extraite ; les deux petits anciens JSR vérifient l'OS.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import struct
import subprocess
import tempfile

import build
from chord_keys_pr87 import load_stock

ROOT = pathlib.Path(__file__).resolve().parent
HOOKS = ((0x40021c2a, 'avcl_undo', '4eb940018c50'),
         (0x40021c50, 'avcl_clear', '4eb940019582'))


def generate(stock, catalog, address=0x401ce400, capacity=4096):
    """Assembler nos wrappers à adresse fixe ; symboles ABI importés du catalogue."""
    tweaks = catalog['tweaks'] if isinstance(catalog, dict) else catalog
    lfo = next(t for t in tweaks if t['id'] == 'lfo-secondary')
    bank = next(t for t in tweaks if t['id'] == 'midi-bank-bundle')
    imports = {'A_LF2_context': int(lfo['symbols']['lf2_context'], 16),
               'A_LF2_epoch': int(lfo['symbols']['lf2n_epoch'], 16),
               'A_audio_owner': int(bank['symbols']['ml_audio_lfo_owner'], 16)}
    cross = next((p for p in ('m68k-elf-', 'm68k-linux-gnu-') if shutil.which(p + 'as')), None)
    if cross is None:
        raise RuntimeError('binutils ColdFire requis')
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d)
        subprocess.run([cross+'as', '-march=cfv4e', '-o', str(p/'a.o'),
                        str(ROOT/'machines/track_lfo_clear/clear.s')], check=True)
        linker = 'SECTIONS { .text '+hex(address)+' : { *(.text*) } }\n'
        linker += '\n'.join(f'{k} = {v:#x};' for k,v in imports.items())+'\n'
        (p/'a.ld').write_text(linker)
        subprocess.run([cross+'ld', '-T', str(p/'a.ld'), '-e', 'avcl_clear',
                        '-o', str(p/'a.elf'), str(p/'a.o')], check=True)
        subprocess.run([cross+'objcopy', '-O', 'binary', str(p/'a.elf'), str(p/'a.bin')], check=True)
        code = (p/'a.bin').read_bytes()
        nm = subprocess.check_output([cross+'nm', '--defined-only', str(p/'a.elf')], text=True)
        symbols = {s.split()[2]: hex(int(s.split()[0], 16)) for s in nm.splitlines()
                   if len(s.split()) == 3 and s.split()[2].startswith('avcl_')}
    if len(code) > capacity:
        raise ValueError(f'code {len(code)} > réservation {capacity}')
    writes = []
    for va,sym,expected in HOOKS:
        old = stock[va-build.BASE:va-build.BASE+6]
        if old.hex() != expected:
            raise ValueError(f'OS inconnu en {va:#x}')
        for t in tweaks:
            for w in t['writes']:
                lo = build.BASE+w['off']; hi = lo+len(bytes.fromhex(w['new']))
                if max(lo,va)<min(hi,va+6):
                    raise ValueError(f'accroche occupée par {t["id"]}: {va:#x}')
        writes.append(dict(off=va-build.BASE,old=old.hex(),
                           new=(b'\x4e\xb9'+struct.pack('>I',int(symbols[sym],16))).hex()))
    return dict(id='a-track-clear-lfo-undo',status='experimental',writes=writes,symbols=symbols,
                raw=dict(dest=hex(address),size=len(code),hex=code.hex(),sha256=hashlib.sha256(code).hexdigest()),
                imports={k:hex(v) for k,v in imports.items()},
                contract='UI selected A track clear/Undo; native sequence record + both LFO cfg/phases; no disk IO')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cycles',required=True);p.add_argument('--catalog',required=True)
    p.add_argument('--output',required=True);p.add_argument('--address',type=lambda x:int(x,0),default=0x401ce400)
    p.add_argument('--capacity',type=int,default=4096);p.add_argument('--check',action='store_true')
    a=p.parse_args(); t=generate(load_stock(a.cycles),json.loads(pathlib.Path(a.catalog).read_text()),a.address,a.capacity)
    s=json.dumps(t,ensure_ascii=False,indent=1)+'\n';out=pathlib.Path(a.output)
    if a.check:
        assert out.read_text()==s, 'recette à régénérer'
    else:
        out.write_text(s)
    print(f'ok : A clear/Undo, {t["raw"]["size"]} octets propres, fin {t["symbols"]["avcl_end"]}')


if __name__=='__main__':
    main()
