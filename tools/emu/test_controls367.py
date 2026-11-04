"""Vrais lanceur Song et lecteur de slices : curseur, mutes et FUNC tenu.

Les E/S UI et le setter de chaine sont observes ; pas de faux resultat materiel.
"""
from pathlib import Path
import argparse
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig, STOP, STACK, EVENT, OBJ, RAW
from song_cursor367 import apply
from unicorn import UC_HOOK_CODE, m68k_const as C

p = argparse.ArgumentParser(description=__doc__)
for name in ('build', 'capture', 'output'):
    p.add_argument('--'+name, type=Path, required=True)
a = p.parse_args()
a.output.parent.mkdir(parents=True, exist_ok=True)
m = json.loads((a.build/'BUILD.json').read_text())
n = bytearray((a.capture/'native.bin').read_bytes())
runtime = bytearray((a.capture/'runtime.bin').read_bytes())
module = m.get('song_cursor367') or apply(m, n, runtime, a.output.parent/'module')
r = Rig(bytes(n), {'writes': []}, {'writes': [], 'symbols': {}})
u = r.u
u.mem_map(0x46700000, 0x300000)
u.mem_write(0x46700000, bytes(runtime))
s = m['acid_articulation']['symbols']
chains, notes = [], []
held = [0]
def chain(args):
    entries, count = args[:2]
    chains.append((count, bytes(u.mem_read(entries, count*8))))
    return 0
def install(at, fn):
    if at not in r.stubs:
        u.hook_add(UC_HOOK_CODE, r.stub, begin=at, end=at)
    r.stubs[at] = fn
install(s['sg_sync'], lambda args: 0)
install(0x40055cd6, chain)
install(0x40055f14, lambda args: 0)
install(0x4007faf4, lambda args: held[0] if args[0] == 1 else 0)
install(0x401afeb4, lambda args: 0x41003000)
install(0x4008171e, lambda args: notes.append(tuple(args[:3])) or 0)
install(0x401b02c0, lambda args: 0)
raw = 0x41010000
r.w32(0x40fe4228, 0x41004000)
r.w32(0x41004010, raw)
song_rows = [(0, 2, 1, 0), (1, 1, 5, 0), (2, 3, 32, 0)]
launches = []
for loop in (0, 1):
    for page in (0, 1):
        for cursor in range(4):
            r.w32(s['sg_song'], 3)
            r.w32(s['sg_song']+4, loop)
            u.mem_write(s['sg_song']+8, b''.join(bytes(row) for row in song_rows))
            r.w32(s['sg_page'], page)
            r.w32(s['sg_cursor'], cursor)
            start = cursor if page and cursor < 3 else 0
            assert r.call(s['sg_start']) == 1
            order = list(range(start, 3)) + (list(range(start)) if loop else [])
            expected = [i for i in order for _ in range(song_rows[i][1])]
            count, entries = chains[-1]
            assert count == len(expected) and list(u.mem_read(s['row_map'], count)) == expected
            assert r.r32(s['sg_current']) == start
            assert r.call(s['sg_mutes']) == song_rows[start][2]
            for index, row in enumerate(expected):
                r.w32(0x40a78634, index)
                pattern = raw+28+0x77f6*song_rows[row][0]
                assert struct.unpack_from('>I', entries, index*8)[0] == pattern
                r.call(s['sg_boundary'], pattern)
                assert r.r32(s['sg_current']) == row
                assert r.call(s['sg_mutes']) == song_rows[row][2]
            r.w32(0x40a78634, 0)
            r.call(s['sg_boundary'], raw+28+0x77f6*song_rows[expected[0]][0])
            assert r.r32(s['sg_active']) == loop
            assert r.r32(s['sg_end']) == 1-loop
            launches.append(dict(loop=loop, page=page, cursor=cursor, rows=expected))

# PLAY apres un seul STOP : recompiler meme si l'arrangement reste arme.
r.w32(s['sg_page'], 1)
r.w32(s['sg_cursor'], 1)
r.w32(s['sg_active'], 1)
u.mem_write(EVENT, struct.pack('>6I', 0, 0, 100, 10, 1, 127))
previous = len(chains)
assert r.call(s['sg_prepare_transport'], EVENT) == 1
assert len(chains) == previous+1 and r.r32(s['sg_current']) == 1
r.w32(0x40a78874, 1)
assert r.call(s['sg_prepare_transport'], EVENT) == 1 and len(chains) == previous+1
r.w32(0x40a78874, 0)

# Executer le lecteur natif complet des touches TRIG de l'editeur.
def slice_key(key):
    u.reg_write(C.UC_M68K_REG_A0, EVENT)
    u.reg_write(C.UC_M68K_REG_D0, 16+key)
    return r.call(0x401aed0e)

r.w32(0x41003004, 32)
r.w32(0x401bcc64, 2)
for cached in (0, 1):
    for physical in (0, 1):
        for key in range(16):
            held[0] = physical
            r.w32(0x401bcc70, cached)
            u.mem_write(0x401bcc94, bytes(64))
            u.mem_write(EVENT, struct.pack('>6I', 0, 0, key, 16+key, 1, 127))
            notes.clear()
            slice_key(key)
            expected = 52+key+16*physical
            assert notes == [(2, expected, 100)], (cached, physical, key, notes)
            assert r.r32(0x401bcc68) == key+16*physical
            # Une relecture du meme appui ne redemarre pas la note.
            slice_key(key)
            assert len(notes) == 1
            r.w32(EVENT+16, 16)
            slice_key(key)
            assert r.r32(0x401bcc94+4*key) == 0

# Clavier natif, avec vrai getter KBT dans les donnees de pattern.
# Le recorder recoit ces notes apres traduction, pas un index de touche.
keyboard_notes = []
for at, fn in (
    (0x4007240c, lambda args: r.r32(args[0]+12)),
    (0x400cf9a8, lambda args: 0x41005000),
    (0x4006b978, lambda args: 0),
    (0x4006bb18, lambda args: 0),
    (0x4000eb90, lambda args: 0x41005000),
    (0x40012442, lambda args: 0),
    (0x40012412, lambda args: 0),
    (0x4001e318, lambda args: 0),
    (0x4000f208, lambda args: 0x41005000),
    (0x4000cfcc, lambda args: OBJ),
    (0x4000d0dc, lambda args: 0x41005000),
    (0x4000ccc0, lambda args: 0),
    (0x4018a79e, lambda args: 0),
    (0x40072454, lambda args: 1),
    (0x40072460, lambda args: 0),
    (0x40019f44, lambda args: keyboard_notes.append(tuple(args[:6])) or 0),
):
    install(at, fn)
held[0] = 0
for transpose in (-24, -12, 0, 12, 24):
    u.mem_write(RAW+721, bytes([transpose&255]))
    for key in (0, 8, 15):
        u.mem_write(EVENT, struct.pack('>6I', 0, 0, key, key+16, 1, 127))
        keyboard_notes.clear()
        r.call(0x4001a0d2, 0x41006000, EVENT)
        assert len(keyboard_notes) == 1
        assert keyboard_notes[0][3] == 52+key+transpose, (transpose, key, keyboard_notes)

a.output.write_text(json.dumps(dict(module=module, launches=launches,
    native_slice_key_cases=64, native_boundary_mutes_and_stop=True,
    physical_FUNC_overrides_stale_cache=True, repeated_reads_do_not_retrigger=True,
    key_release_clears_note=True, native_KBT_octave_cases=15,
    hardware_tested=False), indent=2)+'\n')
print('PASS24 Song launches/boundaries,64 native slice-key cases and15 native KBT octave cases')
