"""Plateau retrig reel : limites, alias avant/apres, ABI et instructions.

python tools/emu/test_retrig_plain367.py --build ../audio-clean365/main/full
 --capture ../audio-clean365/cold/main/full --output ../controls367/proof/retrig/result.json
"""
from pathlib import Path
import argparse
import json
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'tools/emu')]
from test_seq_gen_menu import Rig
from retrig_plain367 import apply
from unicorn import UC_HOOK_CODE, m68k_const as C

p = argparse.ArgumentParser(description=__doc__)
for name in ('build', 'capture', 'output'):
    p.add_argument('--'+name, type=Path, required=True)
a = p.parse_args()
a.output.parent.mkdir(parents=True, exist_ok=True)
meta = json.loads((a.build/'BUILD.json').read_text())
native = bytearray((a.capture/'native.bin').read_bytes())
runtime = bytearray((a.capture/'runtime.bin').read_bytes())
module = apply(meta, native, runtime, a.output.parent/'module')
r = Rig(bytes(native), {'writes': []}, {'writes': [], 'symbols': {}})
u = r.u
u.mem_map(0x46700000, 0x300000)
u.mem_write(0x46700000, bytes(runtime))
regs = [getattr(C, 'UC_M68K_REG_'+name) for name in
        ['D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A4', 'A5', 'A6']]
rng = random.Random(367)
bounds = [-2147483648, 2147483647, 0, -1, 1]
bounds += [q*32768+d for q in (-32768, -32767, -1, 0, 1, 32767, 32768)
           for d in (-1, 0, 1)]
rows = []
for record in (0, 1, 7):
    for alias in (-64, -32, -2, 0, 2, 32, 64, 128):
        for case in range(12):
            channel, write = 0x41001000, 0x41002080
            read = write+alias
            seed = rng.randbytes(1024)
            signal = struct.pack('>32i', *[rng.choice(bounds) if case%2 else rng.randint(-2147483648, 2147483647)
                                         for _ in range(32)])
            outputs, counts = [], []
            for optimized in (False, True):
                u.mem_write(0x41002000, seed)
                u.mem_write(channel-4, b'ABCD'+signal+b'EFGH')
                patch = module['patches'][0]
                raw = bytes.fromhex(patch['new' if optimized else 'old'])
                u.mem_write(patch['at'], raw)
                u.ctl_remove_cache(patch['at'], patch['at']+len(raw))
                for index, reg in enumerate(regs):
                    u.reg_write(reg, 0xc0de0000+index)
                count = [0]
                hook = u.hook_add(UC_HOOK_CODE, lambda *unused: count.__setitem__(0, count[0]+1))
                r.call(module['code'], channel, write, read, record)
                u.hook_del(hook)
                assert [u.reg_read(reg) for reg in regs] == [0xc0de0000+i for i in range(len(regs))]
                outputs.append((bytes(u.mem_read(channel-4, 136)), bytes(u.mem_read(0x41002000, 1024))))
                counts.append(count[0])
            assert outputs[0] == outputs[1], (record, alias, case)
            assert outputs[0][0][:4] == b'ABCD' and outputs[0][0][-4:] == b'EFGH'
            rows.append(dict(record=record, alias=alias, case=case,
                             instructions=counts, saved=counts[0]-counts[1]))
result = dict(module=module, cases=rows, PCM_history_ABI_exact=True,
              saved_instruction_range=[min(x['saved'] for x in rows), max(x['saved'] for x in rows)],
              hardware_cycles_measured=False)
a.output.write_text(json.dumps(result, indent=2)+'\n')
print('PASS', len(rows), 'retrig cases: PCM/history/ABI exact; saved instructions', result['saved_instruction_range'])
