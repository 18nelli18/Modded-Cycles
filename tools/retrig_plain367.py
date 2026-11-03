"""Remplace sur place le plateau master retrig, sans nouvelle RAM."""
from pathlib import Path
import hashlib
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x46700000


def apply(meta, native, runtime, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    symbols = meta['recovery_symbols']
    code, limit = symbols['rr_native_plain'], symbols['rr_tracks']
    assert code == 0x467c7760 and limit == 0x467c7920
    old = bytes(runtime[code-BASE:limit-BASE])
    assert old[:8].hex() == '4fefffec48d7043c'
    cross = 'H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH'] = str(Path(cross).parent) + os.pathsep + os.environ.get('PATH', '')

    def run(tool, *args):
        return subprocess.check_output([cross + tool + '.exe', *map(str, args)], text=True)

    run('gcc', '-mcpu=54418', '-c', ROOT/'tools/machines/cpu_audit/retrig-plain367.S', '-o', out/'retrig.o')
    run('ld', '-Ttext', hex(code), '-e', 'rr_plain367', '-o', out/'retrig.elf', out/'retrig.o')
    run('objcopy', '-O', 'binary', out/'retrig.elf', out/'retrig.bin')
    blob = (out/'retrig.bin').read_bytes()
    assert len(blob) <= limit-code
    new = blob.ljust(limit-code, b'\0')
    runtime[code-BASE:limit-BASE] = new
    return dict(code=code, code_bytes=len(blob), previous_bytes=limit-code,
                patches=[dict(at=code, old=old.hex(), new=new.hex())],
                sha256=hashlib.sha256(blob).hexdigest(), in_place=True,
                sample_order_unchanged=True, new_state_bytes=0, hardware_tested=False)
