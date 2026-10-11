#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Génère le maintien des niveaux pendant FUNC + RELOAD PTN (notes/58).
Code original MIT dans tools/machines/reload_keep_levels, en masque libéré.
Usage : python3 tools/gen_reload_keep_levels.py --cycles model-cycles_OS1.13.syx [--check].
"""
import argparse
import hashlib
import json
import pathlib
import re
import shutil
import struct
import subprocess
import tempfile
import build
import sprites
from mtlib import aplib, container
from mtlib.syx import unwrap
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / 'tools/machines/reload_keep_levels'
OUT = ROOT / 'tweaks/model-cycles_OS1.13/52-reload-keep-levels.json'
BASE = 0x40000400
CAVE = 0x4014a890
HOOK = 0x400107a4
STOCK_SHA = 'cc99d4f0175d34d1e91d046e6ec85a5e8ab58ab9edbb3c24406acd48cb99ee98'
CROSS = next((p for p in ('m68k-linux-gnu-', 'm68k-elf-') if shutil.which(p+'as')), 'm68k-elf-')
def run(tool, *args):
    return subprocess.check_output([CROSS+tool, *map(str,args)], text=True)
def main_os(path):
    stream, _ = unwrap(pathlib.Path(path).read_bytes())
    c = container.parse(stream)
    section = next(s for s in c['sections'] if s['id']==3)
    stock = aplib.depack(c['blob'][section['off']:section['off']+section['size']])[0]
    if hashlib.sha256(stock).hexdigest()!=STOCK_SHA:
        raise SystemExit('MAIN OS officiel 1.13 requis')
    return stock

def build_tweak(stock):
    if hashlib.sha256(stock).hexdigest()!=STOCK_SHA:
        raise ValueError('MAIN OS officiel 1.13 requis')
    for va, raw in ((HOOK,'4eb94005d080'), (0x4001c19c,'4eb9400107d8'),
                    (0x400106de,'4fefffe448d70c3c'), (0x400107d8,'4e56ffc4')):
        if stock[va-BASE:va-BASE+len(raw)//2].hex()!=raw:
            raise ValueError(f'Code de rechargement inattendu en {va:#x}')
    with tempfile.TemporaryDirectory() as td:
        d=pathlib.Path(td)
        run('as','-mcpu=54418',SRC/'reload_keep_levels.S','-o',d/'code.o')
        run('ld','-T',SRC/'reload_keep_levels.ld','-o',d/'code.elf',d/'code.o')
        run('objcopy','-O','binary','-j','.cave',d/'code.elf',d/'code.bin')
        code=(d/'code.bin').read_bytes()
        symbols={m[2]:int(m[1],16) for line in run('nm','-n',d/'code.elf').splitlines()
                 if (m:=re.match(r'([0-9a-f]+)\s+\w\s+(\S+)',line))}
    size, ptr, _, shared=sprites.MASKS[CAVE]
    if symbols['reload_keep_levels']!=CAVE or len(code)>size:
        raise ValueError('Code hors du masque libéré')
    if stock[CAVE-BASE:CAVE-BASE+size]!=stock[shared-BASE:shared-BASE+size]:
        raise ValueError('Masques différents')
    if stock[ptr-BASE:ptr-BASE+4]!=struct.pack('>I',CAVE):
        raise ValueError('Pointeur de masque inattendu')
    writes=[sprites.redirect_write(CAVE),
            dict(off=CAVE-BASE,old=stock[CAVE-BASE:CAVE-BASE+len(code)].hex(),new=code.hex()),
            dict(off=HOOK-BASE,old=stock[HOOK-BASE:HOOK-BASE+6].hex(),
                 new=struct.pack('>HI',0x4eb9,symbols['reload_keep_levels']).hex())]
    tweak=dict(id='reload-keep-levels',order=52,name='Recharger le pattern en gardant les niveaux',
      description=['Un appui bref sur FUNC + PATTERN (RELOAD PTN) garde les niveaux actuels des six pistes ; le reste du pattern et PAN se rechargent normalement.',
                   'Aucun changement de sauvegarde ; le maintien du raccourci et les rechargements du menu gardent le comportement d’origine.',
                   f'Code MIT de {len(code)} octets dans un masque libéré ; sans état ou recopie au démarrage. tools/gen_reload_keep_levels.py, notes/58.'],
      device='Model:Cycles',os='1.13',section=3,conflicts=[],symbols={'reload_keep_levels':hex(CAVE)},
      writes=sorted(writes,key=lambda w:w['off']))
    patched,dirty=build.apply_writes(stock,[tweak])
    assert patched[HOOK-BASE:HOOK-BASE+6]==bytes.fromhex(writes[-1]['new'])
    return tweak

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles',required=True)
    ap.add_argument('--check',action='store_true')
    a=ap.parse_args()
    text=json.dumps(build_tweak(main_os(a.cycles)),indent=1,ensure_ascii=False)+'\n'
    if a.check:
        if not OUT.exists() or OUT.read_text()!=text:
            raise SystemExit('JSON différent : relancer le générateur')
        print('ok : recette à jour')
    else:
        OUT.write_text(text);print('ok : recette écrite')
if __name__=='__main__': main()
