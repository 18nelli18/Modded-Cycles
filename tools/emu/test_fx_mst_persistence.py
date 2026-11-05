"""Regression MST : code ColdFire compile contre capture froide 3.05.

Les E/S fichiers et le codec natif sont simules. Aucun resultat appareil.
Sans --cross, execute le module original pour reproduire le defaut.
"""
import argparse
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools/emu'), str(ROOT / 'tools')]
import test_fx_menu_control as fx

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--cold', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--cross', help='Prefixe des executables m68k-elf, sans gcc.exe')
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
m = json.loads((a.build / 'BUILD.json').read_text())
fx.metadata = m
fx.boot = lambda _: ((a.cold / 'native.bin').read_bytes(),
                        [(0x46700000, (a.cold / 'runtime.bin').read_bytes())])
source = inspect.getsource(fx.fixture).replace(
    "m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())", 'm=metadata')
source = source.replace("**m['fx_menu']['symbols']",
    "**m['fx_menu']['symbols'],**m['per_track_fx']['symbols'],**m['fx_project']['symbols']")
exec(compile(source, 'mst-fixture', 'exec'), fx.__dict__)
r, s, held, log, files, key, turn, data, bind = fx.fixture('unused')

if a.cross:
    os.environ['PATH'] = str(Path(a.cross).parent) + os.pathsep + os.environ['PATH']
    def cross(tool, *args):
        return subprocess.check_output([a.cross + tool + '.exe', *map(str, args)], text=True)
    obj = a.output / 'slot-state.o'
    cross('gcc', '-mcpu=54418', '-O2', '-ffreestanding', '-fno-builtin', '-fno-pic',
          '-fno-stack-protector', '-c', ROOT / 'tools/machines/track_fx/slot-state.c', '-o', obj)
    aliases = {}
    for group in m.values():
        if isinstance(group, dict):
            aliases.update(group.get('aliases', {}))
            aliases.update(group.get('symbols', {}))
    aliases.update(s)
    needed = [line.split()[-1] for line in cross('nm', '-u', obj).splitlines()]
    assert all(name in aliases for name in needed), needed
    ld = a.output / 'slot.ld'
    ld.write_text('SECTIONS { .text 0x46c00000 : { *(.text*) *(.rodata*) } '
                  '.data : { *(.data*) } .bss 0x46c10000 (NOLOAD) : { *(.bss*) *(COMMON) } }\n' +
                  ''.join(f'{name} = {aliases[name]:#x};\n' for name in needed))
    elf = a.output / 'slot.elf'
    cross('ld', '-T', ld, '-o', elf, obj)
    binary = a.output / 'slot.bin'
    cross('objcopy', '-O', 'binary', elf, binary)
    sy = {v[2]: int(v[0], 16) for line in cross('nm', elf).splitlines()
          if len(v := line.split()) == 3}
    r.u.mem_map(0x46c00000, 0x20000)
    initial = binary.read_bytes()
    r.u.mem_write(0x46c00000, initial)
    s.update(sy)
    r.s.update(sy)

root, holder, pattern = 0x41000000, 0x41300000, 0x41400000
r.w32(0x40fe4228, holder)
r.w32(holder + 16, root)
r.w32(root + 8, 0x12345678)
r.w32(0x40a7887c, pattern)
r.w32(pattern + 30706, 0)
r.w32(0x40fe4178, 1)
bind(s['mf_old_frame'], lambda _: 0)
bind(s['mf_old_project_encode'], lambda _: 1)
r.call('mf_frame')
assert r.r32(s['mf_mode']) == 0
for id, mode, speed in [(0, 1, 23), (1, 0, 64)]:
    r.w32(pattern + 30706, id)
    r.call('mf_sync_audio')
    r.w32(s['ch_mode'], mode)
    r.w32(s['fx_speed'], speed)
    r.call('mf_legacy_capture')
r.w32(pattern + 30706, 0)
r.call('mf_sync_audio')
assert r.r32(s['ch_mode']) == 1, 'MST : effet perdu au retour sur A'
assert r.r32(s['fx_speed']) == 23
r.call('mf_project_encode', 0, root, 0, 16, 0)
saved = files['/MFX_12345678.cfg']
assert len(saved) == 4624 and saved[16 + 36] == 1
assert saved[16 + 48 + 36] == 0
print('PASS MST : Chorus sur A, Reverb sur B, parametre et sauvegarde projet')
if a.cross:
    r.u.mem_write(0x46c00000, bytes(0x20000))
    r.u.mem_write(0x46c00000, initial)
else:
    f = m['per_track_fx']
    r.u.mem_write(f['bss'], bytes(f['bss_bytes']))
r.w32(s['ch_mode'], 0)
r.call('mf_frame')
assert r.r32(s['ch_mode']) == 1 and r.r32(s['fx_speed']) == 23
r.w32(pattern + 30706, 1)
r.call('mf_sync_audio')
assert r.r32(s['ch_mode']) == 0
r.call('mf_mode_set', 1)
if m.get('gov_inv_master380'):
    assert r.r32(s['mf_mode']) == 0
else:
    r.call('mf_choose', 1, 3, 12)
    assert r.call('mf_choice', 1, 3) == 12
print('PASS relecture froide, retour B, mode TRK et choix POTS')
(a.output / 'proof.json').write_text(json.dumps(dict(
    firmware_sha256=m['sha256'], compiled_fix=bool(a.cross),
    pattern_roundtrip=True, cold_reload=True, hardware_tested=False), indent=2) + '\n')
