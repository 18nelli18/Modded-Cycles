"""MST installe : vrais menus, activation et codecs OS, nouvelle instance froide.

Le disque et la presentation UI sont simules ; aucune preuve appareil.
"""
from pathlib import Path
import argparse
import inspect
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/emu')]
import test_fx_menu_control as fx
from test_seq_gen_menu import STACK, STOP
from unicorn import m68k_const as C

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--build', type=Path, required=True)
p.add_argument('--capture', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
m = json.loads((a.build/'BUILD.json').read_text())
fx.metadata = m
fx.boot = lambda _: ((a.capture/'native.bin').read_bytes(),
                      [(0x46700000, (a.capture/'runtime.bin').read_bytes())])
source = inspect.getsource(fx.fixture).replace(
    "m=json.loads((ROOT/'output/firmware'/(stem+'.json')).read_text())", 'm=metadata')
source = source.replace("**m['fx_menu']['symbols']",
    "**m['fx_menu']['symbols'],**m['per_track_fx'].get('aliases',{}),**m['per_track_fx']['symbols'],**m['fx_project']['symbols']")
exec(compile(source, 'mst-native-fixture', 'exec'), fx.__dict__)
RAW, SER, HOLDER, VT, CB = 0x41400000, 0x41800000, 0x41300000, 0x42000000, 0x93015000
SIZE, STRIDE = 0x210404, 30710


def fixture(disk):
    r, s, held, log, files, key, turn, data, bind = fx.fixture('unused')
    files.update(disk)
    r.w32(VT+40, 0x400d3af6)
    r.w32(HOLDER, VT)
    r.w32(HOLDER+16, RAW)
    r.w32(0x40fe4228, HOLDER)
    r.w32(0x40fe4178, 1)
    bind(s['mf_old_frame'], lambda _: 0)
    bind(s['mf_redraw'], lambda _: 0)
    bind(s['fx_previous_draw'], lambda _: 0)
    bind(0x400d0a10, lambda _: 1)
    r.u.mem_map(0x80000000, 0x20000)
    r.u.mem_write(0x80000000, (a.capture/'sram.bin').read_bytes())
    projects = {}
    def writer(args):
        projects[args[1]] = bytes(r.u.mem_read(SER, SIZE))
        return 1
    for at, fn in [(0x400cfdaa, lambda _: 0x93018000),
                   (0x4006a216, lambda _: SER), (0x4006a4d6, writer),
                   (0x4006a3ac, lambda _: SER)]:
        bind(at, fn)
    return r, s, files, projects


def call(fn, *args):
    if isinstance(fn, str):
        fn = s[fn]
    sp = STACK-0x400
    r.u.mem_write(sp, struct.pack('>'+'I'*(len(args)+1), STOP, *args))
    r.u.reg_write(C.UC_M68K_REG_A7, sp)
    r.u.emu_start(fn, STOP, count=250_000_000)
    assert r.u.reg_read(C.UC_M68K_REG_PC) == STOP, (hex(fn), hex(r.u.reg_read(C.UC_M68K_REG_PC)))
    assert r.u.reg_read(C.UC_M68K_REG_A7) == sp+4
    return r.u.reg_read(C.UC_M68K_REG_D0)


def activate(id):
    sp = STACK-0x400
    r.u.mem_write(sp, struct.pack('>I', STOP))
    r.u.reg_write(C.UC_M68K_REG_A7, sp)
    r.u.reg_write(C.UC_M68K_REG_A2, RAW+28+id*STRIDE)
    r.u.emu_start(0x40055c5c, 0x40055c62, count=250_000_000)
    assert r.u.reg_read(C.UC_M68K_REG_PC) == 0x40055c62
    call('mf_sync_audio')


def choose(slot, mode):
    order = (m['fx_menu']['delay_selector_order'] if slot else
             m['fx_menu']['reverb_selector_order'])
    # Le menu installe utilise huit delays, POTS compris.
    if slot:
        order = m['fx_menu']['delay_selector_order'] if m.get('remove_delay384') else [11, 10, 9, 12, 5, 0, 1, 2]
    elif m.get('vinyl_removed'):
        order = [10, 11, 8, 7, 0, 1, 2, 9]
    r.w32(s['fx_menu_open'], 1)
    r.w32(s['fx_menu_slot'], slot)
    r.w32(s['fx_menu_cursor'], order.index(mode))
    call('mf_commit')
    assert r.r32(s['cr_mode' if slot else 'ch_mode']) == mode


initial_files = {'/MFXGlobal.cfg': bytes([77,70,71,49,1,254,165,90])} if m.get('gov_inv_master380') else {}
r, s, files, projects = fixture(initial_files)
r.u.mem_write(CB, bytes(16))
call(0x40061738, RAW)
r.w32(RAW+8, 0x12345678)
call('fxp_sync')
activate(0)
call('mf_frame')
assert r.r32(s['mf_mode']) == 0
if m.get('gov_inv_master380'):
    call('mf_mode_set', 1)
    assert r.r32(s['mf_mode']) == 0
    for name in ('menu','gc_level'):
        r.w32(s[name], 1)
    r.w32(s['gc_tree_cursor'], 9)
    assert call('mf_tree_edit') == 0
    r.u.mem_write(CB, struct.pack('>6I',0x400fc20c,0,0,32,1,0))
    assert call('mf_gc_key', CB) == 1
    assert call('mf_tree_edit') == 0 and r.r32(s['mf_mode']) == 0
    r.w32(s['menu'], 0)
    r.u.mem_write(CB, bytes(16))
choose(0, 1)
choose(1, 11)
activate(1)
choose(0, 0)
choose(1, 0)
activate(0)
assert r.r32(s['ch_mode']) == 1 and r.r32(s['cr_mode']) == 11
activate(1)
assert r.r32(s['ch_mode']) == 0 and r.r32(s['cr_mode']) == 0
assert call(0x4005d18a, SER, RAW, 0, 255, CB) & 255
assert call(0x4000f762, HOLDER, 9, CB) & 255
blob = projects[9]
assert '/MFX_12345678.cfg' in files
disk = dict(files)
print('PASS menus MST installes, hook natif A/B, codec projet OS et fichier MFT1', flush=True)

r, s, files, projects = fixture(disk)
r.u.mem_write(CB, bytes(16))
call(0x40061738, RAW)
r.u.mem_write(SER, blob)
assert call(0x4006a5a0, 0x93018000, 9, RAW, CB) & 255
activate(0)
call('mf_frame')
assert r.r32(s['ch_mode']) == 1 and r.r32(s['cr_mode']) == 11
activate(1)
assert r.r32(s['ch_mode']) == 0 and r.r32(s['cr_mode']) == 0
print('PASS nouvelle instance, chargement OS du projet, Chorus/Phaser A et Reverb/Delay B', flush=True)
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(dict(sha256=m['sha256'], installed_menu=True,
    native_pattern_hook=True, native_project_encode_decode=True, native_save_load_project=True,
    fresh_emulator_reload=True, hardware_tested=False), indent=2)+'\n')
