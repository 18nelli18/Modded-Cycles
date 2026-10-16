#!/usr/bin/env python3
"""Preuve RETROSYN : boot, interface OS, six voix, reference C et isolation stock.

python3 tools/emu/test_retrosyn.py --cycles firmware/model-cycles_OS1.13.syx
"""
import argparse
import ctypes
import json
import pathlib
import struct
import subprocess
import sys
import tempfile
import os
import shutil
from types import SimpleNamespace
import numpy as np
from unicorn import UC_HOOK_CODE
from unicorn import m68k_const as mk
HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import gen_retrosyn as R
import gen_macro as gm
import gen_syntakt_engines as gs
import build
import mcengine as E
import test_macro as M
import test_sdvintage_7th as T


def main():
    # Les anciens helpers attendent le nom Homebrew ; alias local, sans installation globale.
    alias_dir = tempfile.TemporaryDirectory()
    objdump = shutil.which('m68k-elf-objdump') or shutil.which('m68k-linux-gnu-objdump')
    if not objdump:
        raise SystemExit('!! objdump m68k requis')
    os.symlink(objdump, pathlib.Path(alias_dir.name) / 'm68k-elf-objdump')
    os.environ['PATH'] = alias_dir.name + os.pathsep + os.environ['PATH']
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cycles', required=True)
    a = ap.parse_args()
    stock = R.g7.cycles_main(a.cycles)
    t = json.loads((R.DEV / '27-retrosyn.json').read_text())
    img, _ = build.apply_writes(stock, [t])
    pl, _ = build.build_payload([t], stock, None)
    pay = int(t['append']['dest'], 16)
    runtime = build.payload_runtime(t, stock, None)
    fw = SimpleNamespace(img=bytes(img)+pl, payload=(pay, runtime), runtime=runtime,
                         tweaks=[dict(t, id='macro-retrosyn')])
    M.boot(fw)
    saved = gm.MACHINE
    gm.MACHINE = R.MACHINE
    try:
        M.interface_alone(stock, fw)
    finally:
        gm.MACHINE = saved
    def engine(patched=True):
        return E.Engine(fw.img if patched else stock, payload=(pay, runtime) if patched else None)
    # Les six machines d'origine conservent exactement leur rendu, meme apres les hooks USB.
    for machine in range(6):
        ea, eb = engine(False), engine()
        for e in (ea, eb):
            for tr in range(6):
                e.machine_defaults(tr, machine)
        for b in range(8):
            assert np.array_equal(ea.block(63 if b == 0 else 0), eb.block(63 if b == 0 else 0)), machine
        print('ok stock identique', machine)
    with tempfile.TemporaryDirectory() as d:
        lib = pathlib.Path(d) / 'ref.so'
        subprocess.run(['gcc','-O2','-shared','-fPIC',str(R.SRC/'retrosyn_ref.c'),'-o',str(lib)],check=True)
        ref = ctypes.CDLL(str(lib))
        ref.rs_new.restype = ctypes.c_void_p
        ref.rs_free.argtypes = [ctypes.c_void_p]
        ref.rs_block_c.argtypes = [ctypes.c_void_p] + [ctypes.c_int]*7 + [ctypes.POINTER(ctypes.c_int)]
        # Capture avant l'enveloppe OS : chaque bloc ColdFire doit etre bit-identique au coeur hote.
        for shape in range(6):
            for color, sweep, contour, punch in [(0,64,0,0),(127,0,127,1),(64,127,48,0)]:
                e = engine()
                for tr in range(6):
                    e.set(tr, machine=6, shape=shape, color=color, sweep=sweep, contour=contour,
                          punch=punch, note=48+tr*3, decay=100)
                e.block(63)  # L'OS applique machine et trig au bloc suivant.
                states = [ref.rs_new() for _ in range(6)]
                captured = []
                current_out = [0]
                def entering(uc, addr, size, data):
                    sp = uc.reg_read(mk.UC_M68K_REG_A7)
                    current_out[0] = struct.unpack('>I', uc.mem_read(sp+4,4))[0]
                entry = int(t['symbols']['retrosyn_render'],16)
                entry_hook = e.uc.hook_add(UC_HOOK_CODE, entering, begin=entry, end=entry)
                def capture(uc, addr, size, data):
                    # Premier appel AMP_ENV : le coeur vient de remplir le buffer de cette piste.
                    ret = struct.unpack('>I',uc.mem_read(uc.reg_read(mk.UC_M68K_REG_A7),4))[0]
                    if pay <= ret < pay + len(bytes.fromhex(t['append']['parts'][0]['hex'])):
                        captured.append(bytes(uc.mem_read(current_out[0], 128)))
                hook = e.uc.hook_add(UC_HOOK_CODE, capture, begin=0x400a9252, end=0x400a9252)
                for b in range(32):
                    captured.clear()
                    e.block(63 if b == 16 else 0)
                    assert len(captured)==6, len(captured)
                    for tr in range(6):
                        buf = (ctypes.c_int*32)()
                        knob = lambda x: x*256 + ((x*256)>>7)
                        ref.rs_block_c(states[tr],(48+tr*3)<<16,int(b in (0,17)),shape*5462+2731,
                                       knob(color),16384 if sweep==64 else knob(sweep),knob(contour),punch,buf)
                        actual = np.frombuffer(captured[tr],dtype='>i4')
                        assert np.array_equal(actual, np.array(buf)), (shape,b,tr,actual[:4],list(buf)[:4])
                for state in states: ref.rs_free(state)
                e.uc.hook_del(hook)
                e.uc.hook_del(entry_hook)
                assert not e.unmapped
            print('ok ColdFire = reference, six pistes, forme', shape)
    e = engine()
    for tr in range(6): e.set(tr,machine=6,sweep=64,decay=100)
    e.block(63)
    e.count_instructions(); e.block(0)
    print('info instructions six voix / bloc',e.instructions)
    assert not T.FAIL, T.FAIL
    print('ok RETROSYN : boot, interface, stock, rendu six pistes')

if __name__=='__main__': main()
