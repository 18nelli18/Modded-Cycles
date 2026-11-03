"""Depart Song selectionne et FUNC physique dans l'editeur de slices.

Code UI dans l'ancien logement du profiler retire ; aucun cout ISR ajoute.
"""
from pathlib import Path
import hashlib
import os
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE, CODE, LIMIT = 0x46700000, 0x4679f000, 0x4679f800


def apply(meta, native, runtime, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    assert meta.get('detailed_profile_removed', {}).get('normal_DX_retained')
    assert not any(runtime[CODE-BASE:LIMIT-BASE]), 'logement profiler non libre'
    sy = meta['acid_articulation']['symbols']
    aliases = {name: sy[name] for name in ('sg_song', 'sg_cursor', 'sg_page', 'sg_sync',
               'entries', 'row_map', 'sg_active', 'sg_current', 'sg_end', 'count', 'seen', 'last', 'project', 'sg_cancel', 'fx_notice')}
    cross = 'H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH'] = str(Path(cross).parent) + os.pathsep + os.environ.get('PATH', '')

    def run(tool, *args):
        return subprocess.check_output([cross+tool+'.exe', *map(str, args)], text=True)

    objects = []
    for name in ('song.c', 'playback.c', 'slice-func367.S'):
        obj = out/(Path(name).stem+'.o')
        run('gcc', '-mcpu=54418', '-Os', '-ffreestanding', '-fno-builtin', '-fno-pic',
            '-fno-common', '-Wall', '-Wextra', '-Werror', '-DSG_LAUNCH_ONLY',
            '-c', ROOT/'tools/machines/song'/name, '-o', obj)
        objects.append(obj)
    script = f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} .forbidden 0 (NOLOAD) : {{ *(.data*) *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\n'
    script += f'ASSERT(SIZEOF(.forbidden)==0,"nouvel etat interdit")\nASSERT(ADDR(.text)+SIZEOF(.text)<={LIMIT:#x},"UI pleine")\n'
    script += ''.join(f'{name} = {value:#x};\n' for name, value in aliases.items())
    (out/'controls.ld').write_text(script)
    run('ld', '--orphan-handling=error', '-T', out/'controls.ld', '-e', 'sg_start', '-o', out/'controls.elf', *objects)
    run('objcopy', '-O', 'binary', out/'controls.elf', out/'controls.bin')
    blob = (out/'controls.bin').read_bytes()
    symbols = {p[2]: int(p[0], 16) for line in run('nm', out/'controls.elf').splitlines() if len(p := line.split()) == 3}
    assert len(blob) <= LIMIT-CODE
    patches = []
    def patch(image, at, old, new, origin, region):
        assert bytes(image[at-origin:at-origin+len(old)]) == old, hex(at)
        assert len(old) == len(new)
        image[at-origin:at-origin+len(old)] = new
        patches.append(dict(at=at, old=old.hex(), new=new.hex(), region=region))
    patch(runtime, CODE, bytes(len(blob)), blob, BASE, 'runtime')
    entry = sy['sg_start']
    assert bytes(runtime[entry-BASE:entry-BASE+6]) == bytes.fromhex('203940a78874')
    patch(runtime, entry, bytes(runtime[entry-BASE:entry-BASE+6]),
          b'\x4e\xf9'+struct.pack('>I', symbols['sg_start']), BASE, 'runtime')
    entry = sy['sg_prepare_transport']
    assert bytes(runtime[entry-BASE:entry-BASE+6]) == bytes.fromhex('4feffff4700a')
    patch(runtime, entry, bytes(runtime[entry-BASE:entry-BASE+6]),
          b'\x4e\xf9'+struct.pack('>I', symbols['sg_restart_transport367']), BASE, 'runtime')
    # Seul TST sle_func du lecteur de slices epingle, pas les autres modificateurs.
    at = 0x401aed4c
    patch(native, at, bytes.fromhex('4ab9401bcc70'), b'\x4e\xb9'+struct.pack('>I', symbols['slice_func367']),
          0x40000400, 'native')
    return dict(code=CODE, code_bytes=len(blob), symbols=symbols, patches=patches,
                sha256=hashlib.sha256(blob).hexdigest(), selected_row_start=True,
                loop_keeps_entire_song=True, slice_editor_uses_physical_FUNC=True,
                new_state_bytes=0, added_audio_hooks=0, hardware_tested=False)
