"""Selection SIL reelle : ancien echec MD, commits repetes et chemin Stk exact."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/emu')]
import test_keep_machine_params as K
from unicorn import m68k_const as C, UC_HOOK_CODE
from silent_select369 import apply, SITE, CODE

p = argparse.ArgumentParser(description=__doc__)
for key in ('build', 'capture', 'output'):
    p.add_argument('--'+key, type=Path, required=True)
p.add_argument('--apply', action='store_true')
a = p.parse_args()
a.output.parent.mkdir(parents=True, exist_ok=True)
m = json.loads((a.build/'BUILD.json').read_text())
n = bytearray((a.capture/'native.bin').read_bytes())
rt = bytearray((a.capture/'runtime.bin').read_bytes())
module = apply(m, n, rt) if a.apply else m['silent_select369']
K.boot = lambda _: (bytes(n), [(0x46700000, bytes(rt))])
u, obj, snd = K.fixture('unused')
u.uc.mem_map(0xfc070000, 0x1000)
u.uc.mem_write(0xfc07000c, struct.pack('>I', 100000000))
s = m['activity_masks']['symbols']
u.hooks[m['fx_menu']['symbols']['fx_notice']] = ('notice', 0)
u.hooks[0x40076bee] = ('redraw', 0)
u.hooks[0x4007240c] = ('DATA', 32)
for fn in (0x400f44c6, 0x4001416c):
    del u.hooks[fn]
u.hooks[0x400802e0] = ('alloc', 0x93210000)
u.hooks[0x400802ec] = ('free', 0)
# Getter dynamique : le son reel change apres chaque commit, contrairement
# a l ancienne preuve qui renvoyait toujours KICK.
u.uc.mem_write(0x4001e318, bytes.fromhex('70001039')+struct.pack('>I', snd+38)+bytes.fromhex('4e75'))
view, event = 0x93900000, 0x93910000

def w32(at, value):
    u.uc.mem_write(at, struct.pack('>I', value))

def reset(machine):
    u.call(s['mb_cancel'])
    u.uc.mem_write(snd, bytes(100))
    u.uc.mem_write(snd+38, bytes([machine, 0]))
    for t in range(6):
        w32(view+0x70+4*t, machine)
    u.uc.reg_write(C.UC_M68K_REG_D2, 0)
    u.call(m['keep_params']['symbols']['kr_snapshot'], obj)
    u.uc.mem_write(view+136, bytes(u.uc.mem_read(K.T.SCRATCH, 12)))
    w32(s['mb_silent'], 1)

rows = []
reset(0)
for delta, turns in [(1, 4), (1, 7), (-1, 3), (1, 14), (-1, 20), (1, 40), (-1, 40)]:
    old_sound = bytes(u.uc.mem_read(snd, 100))
    for _ in range(turns):
        u.call(0x400a2712, view, delta, 0, 0)
        assert bytes(u.uc.mem_read(snd, 100)) == old_sound
    expected = u.u32(s['mb_candidate'])
    u.uc.mem_write(event, struct.pack('>6I', 0x400fbebc, 0, 0, 32, 1, 0))
    u.call(0x400a292c, view, event)
    actual = u.uc.mem_read(snd+38, 1)[0]
    assert actual == expected, (delta, turns, expected, actual)
    # Relachement DATA : le commit ne doit pas avancer une seconde fois.
    w32(event+16, 0)
    u.call(0x400a292c, view, event)
    assert u.uc.mem_read(snd+38, 1)[0] == expected
    assert not u.bad
    rows.append(dict(delta=delta, turns=turns, selected=actual))

# Stk : meme selecteur, memes instructions et registres apres le detour.
prior = module['prior_selector']
u.uc.hook_add(UC_HOOK_CODE, lambda uc,at,size,data: uc.emu_stop(), begin=0x400148bc, end=0x400148bc)
for current in range(28 if 'dummy300' in m else (25 if m['activity_masks']['full'] else 6)):
    for delta in (0xffffffff, 0, 1):
        states = []
        for entry in (prior, CODE):
            w32(module['committing'], 0)
            # Etat de throttle identique pour les deux executions.
            for section in ('per_track_fx', 'activity_masks'):
                for key, at in m.get(section, {}).get('symbols', {}).items():
                    if key in ('rm_machine_valid', 'rm_machine_stamp', 'rm_machine_result'):
                        w32(at, 0)
            sp = K.T.STACK-0x400
            u.uc.mem_write(sp, struct.pack('>I', K.T.STOP))
            for reg, value in [(C.UC_M68K_REG_A7, sp), (C.UC_M68K_REG_D0, current),
                               (C.UC_M68K_REG_D5, delta), (C.UC_M68K_REG_A0, 0x93100000),
                               (C.UC_M68K_REG_A1, 0x93100010)]:
                u.uc.reg_write(reg, value)
            try: u.uc.emu_start(entry, 0x400148bc, count=100000)
            except Exception: print('FAIL SELECTOR',hex(entry),current,delta,hex(u.uc.reg_read(C.UC_M68K_REG_PC)),u.bad); raise
            assert u.uc.reg_read(C.UC_M68K_REG_PC) == 0x400148bc
            states.append(tuple(u.uc.reg_read(reg) for reg in
                                (C.UC_M68K_REG_D0, C.UC_M68K_REG_D1, C.UC_M68K_REG_A0,
                                 C.UC_M68K_REG_A1, C.UC_M68K_REG_A7)))
        assert states[0] == states[1], (current, delta, states)

a.output.write_text(json.dumps(dict(commits=rows, stock_selector_exact=True,
                                     no_audio_hooks=True, hardware_tested=False), indent=2)+'\n')
print('PASS native repeated SIL commits, DATA release and Stk selector equivalence')

