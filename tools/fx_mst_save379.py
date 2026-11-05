"""Correction privee MST : initialiser MFT1 au premier geste FX ordinaire.

Reutilise les fonctions et donnees installees ; aucune IRQ ni E/S ajoutee.
Le corps corrige est extrait de slot-state.c pour eviter deux implementations.
"""
from pathlib import Path
import hashlib
import os
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE, CODE, END = 0x46700000, 0x467a0400, 0x467a0800
CROSS = 'H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta, native, runtime, sram, out):
    assert meta['release'] == '3.05' and not meta.get('fx_mst_save379')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    assert not any(runtime[CODE-BASE:END-BASE])
    for profile in meta.values():
        if not isinstance(profile, dict):
            continue
        for name in ('code', 'bss'):
            at, size = profile.get(name), profile.get(name+'_bytes', 0)
            if isinstance(at, int) and isinstance(size, int) and size:
                assert END <= at or at+size <= CODE, (name, profile)
    assert any(e['kind'] == 'remove' and e['address'] <= CODE and
               END <= e['address'] + e['bytes']
               for e in meta['clean_layout']['retirement']['edits'])
    sy = meta['per_track_fx']['symbols']
    aliases = {**meta['fx_menu']['symbols'], **meta['per_track_fx'].get('aliases', {}), **sy}
    source = (ROOT/'tools/machines/track_fx/slot-state.c').read_text()
    def function(name):
        start = source.index(name + '(')
        start = source.rfind('\n', 0, start) + 1
        end = source.index('\n', source.index('}', start))
        return source[start:end] + '\n'
    c = out/'mst-save.c'
    c.write_text('typedef unsigned int u32; typedef unsigned char u8;\n'
        'extern u32 ready,pending,current; extern volatile u32 mf_mode,ch_mode,cr_mode;\n'
        'extern volatile u8 mf_live[48];\n'
        'extern void seed(void),import_params(void),capture(void);\n' +
        function('pattern') + function('rev_light') + function('del_light') +
        function('rev_ok') + function('del_ok') + function('mf_legacy_capture'))
    os.environ['PATH'] = str(Path(CROSS).parent) + os.pathsep + os.environ['PATH']
    def run(tool, *args):
        return subprocess.check_output([CROSS+tool+'.exe', *map(str, args)], text=True)
    obj, elf, binary, ld = [out/('mst-save.'+ext) for ext in ('o','elf','bin','ld')]
    run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic',
        '-fno-stack-protector','-Wall','-Wextra','-Werror','-c',c,'-o',obj)
    needed = [line.split()[-1] for line in run('nm','-u',obj).splitlines()]
    assert all(name in aliases for name in needed), needed
    ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} }}\n' +
                  ''.join(f'{name} = {aliases[name]:#x};\n' for name in needed))
    run('ld','-T',ld,'-o',elf,obj)
    run('objcopy','-O','binary','-j','.text',elf,binary)
    raw = binary.read_bytes()
    assert 6 < len(raw) <= END-CODE
    symbols = {v[2]: int(v[0],16) for line in run('nm',elf).splitlines()
               if len(v := line.split()) == 3}
    entry = sy['mf_legacy_capture']
    before = bytes(runtime[entry-BASE:entry-BASE+6])
    assert before == b'\x4a\xb9'+struct.pack('>I',sy['ready']), before.hex()
    runtime[CODE-BASE:CODE-BASE+len(raw)] = raw
    runtime[entry-BASE:entry-BASE+6] = b'\x4e\xf9'+struct.pack('>I',symbols['mf_legacy_capture'])
    return dict(code=CODE, code_bytes=len(raw), end=END, entry=entry,
        old=before.hex(), target=symbols['mf_legacy_capture'],
        symbols={'mst_legacy_capture':symbols['mf_legacy_capture']},
        source_sha256=hashlib.sha256(c.read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(raw).hexdigest(),
        added_file_io=False, added_audio_irq_work=False, hardware_tested=False)
