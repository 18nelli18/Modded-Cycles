"""Regression du popup P/O/N filtre : vrai corps popup, pile et registres.

Usage : python tools/emu/test_filter_repeat_diagnostic.py ancien.syx corrige.syx
Les allocations/presentation UI sont des fixtures ; le popup lui-meme est natif.
"""
import json
import struct
import sys
from boot_candidate import ROOT, boot
from test_seq_gen_menu import Rig, STACK, STOP, EVENT
from unicorn import UC_HOOK_CODE, m68k_const as C


def run(path, broken):
    path = ROOT / path
    meta = json.loads(path.with_suffix('.json').read_text())
    im, mem = boot(path)
    r = Rig(im, {'writes': []}, {'writes': [], 'symbols': {}})
    u = r.u
    u.mem_map(0x46700000, 0x200000)
    for at, raw in mem:
        u.mem_write(at, raw)
    profile = json.loads((ROOT / 'build/volume-pan-toggle/volume-pan-toggle-test.json').read_text())
    bs = {k: int(v, 16) for t in profile['composedTweaks']
          if t['id'] == 'control-all-beat-repeat' for k, v in t['symbols'].items()}
    bs.update(meta.get('beat_repeat_symbols', {}))
    dx=meta['dx_symbols'];ps={k:dx[v] for k,v in [('pon_peak','dx_peak'),('pon_over','dx_over'),('pon_new','dx_new')]}
    assert r.r32(dx['dx_enabled'])==0
    r.call(dx['dx_set'],expected_on)
    popup_count, texts = [0], []
    def entered(u, pc, size, data):
        popup_count[0] += 1
    u.hook_add(UC_HOOK_CODE, entered, begin=bs['br_popup'], end=bs['br_popup'])
    def bind(at, fn):
        if at not in r.stubs:
            u.hook_add(UC_HOOK_CODE, r.stub, begin=at, end=at)
        r.stubs[at] = fn
    def string(args):
        r.w32(args[0], args[1])
        return args[0]
    def ctor(args):
        texts.append(r.string(r.r32(args[1])))
        return args[0]
    bind(0x400f980c, string)
    bind(0x400747c0, ctor)
    bind(0x400f7d5c, lambda a: 0)
    bind(0x40076c04, lambda a: 0)
    r.w32(0x40fe4178, 0x93005000)
    r.w32(bs['br_history'], 0x93110000)
    diagnostic = expected_on
    fn = dx['dx_beat_key']
    if not diagnostic:
        # Seul le chainage UI suivant est simule ; wrapper et br_key restent reels.
        next_key = r.r32(bs['br_old_key'])
        if next_key:
            bind(next_key, lambda args: r.r32(args[0] + 12))
    for release in (4, 2):
        for cycle in range(4):
            r.w32(bs['br_keys'], 0)
            for code in (2, 4):
                r.call(fn, r.event(code))
            for name, value in [('pon_peak', 108 * 901), ('pon_over', 41), ('pon_new', 39)]:
                if diagnostic:
                    r.w32(ps[name], value)
            # Cadre appelant legitime : l'ancien UNLK sort de ce cadre par erreur.
            fp = 0x93006000
            u.mem_write(fp - 28, bytes(40))
            r.w32(fp, 0x93006100)
            r.w32(fp + 4, STOP)
            regs = {C.UC_M68K_REG_D2: 0x12345678, C.UC_M68K_REG_D3: 0x23456789,
                    C.UC_M68K_REG_A2: 0x34567890, C.UC_M68K_REG_A6: fp}
            for reg, value in regs.items():
                u.reg_write(reg, value)
            before = popup_count[0]
            try:
                r.call(fn, r.event(release, 0))
            except AssertionError:
                assert broken
                assert popup_count[0] == before
                assert u.reg_read(C.UC_M68K_REG_A7) == fp + 8
                print('REPRODUCED: old diagnostic skips popup entry, unwinds caller frame and corrupts stack', flush=True)
                return
            assert not broken, 'ancien defaut non reproduit'
            assert {reg: u.reg_read(reg) for reg in regs} == regs
            assert popup_count[0] == before + int(diagnostic)
            if diagnostic:
                assert texts[-1] == 'P108 O41 N39', texts
                assert all(r.r32(ps[name]) == 0 for name in ('pon_peak', 'pon_over', 'pon_new'))
            else:
                assert not texts
            r.call(fn, r.event(2 if release == 4 else 4, 0))
    print('PASS:', 'actual popup body, native formatter, P/O/N reset;' if diagnostic else 'no diagnostic popup;', 'both release orders x4, stack and callee-saved registers', flush=True)



for expected_on in [False,True]:
 for stem in (sys.argv[1:] or ['all-features-dx-toggle-test-v14','no-filter-dx-toggle-test-v14']):
  run('output/firmware/'+stem+'.syx',False)
