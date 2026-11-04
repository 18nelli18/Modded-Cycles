"""Remplacement in situ du texte DX, ABI constprop et etat conserves."""
from pathlib import Path
import hashlib
import subprocess
import struct

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x46700000


def apply(meta, native, runtime, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    sy=meta['cpu_monitor']['symbols'];at=sy['text.constprop.0'];limit=sy['cpu_audio_end']
    assert at<limit and limit-at==346
    # Contrat reel : y=arg1, chaine=arg2, couleur=arg3, x=1 constant.
    old=bytes(runtime[at-BASE:limit-BASE])
    code=0x46927a00;end=0x46928000
    assert not any(runtime[code-BASE:end-BASE])
    assert old[:24]==bytes.fromhex('4fefffd848d77c7c347c0003266f002c242f00342a6f0030')
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    def run(tool,*args):return subprocess.check_output([cross+tool+'.exe',*map(str,args)],text=True)
    (out/'text.ld').write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} .forbidden 0 (NOLOAD) : {{ *(.data*) *(.bss*) *(COMMON) }} /DISCARD/ : {{ *(.comment) *(.note.GNU-stack) }} }}\nASSERT(SIZEOF(.forbidden)==0,"etat interdit")\nASSERT(ADDR(.text)+SIZEOF(.text)<={end:#x},"texte plein")\ncpu_pixels370 = {sy["pixels"]:#x};\ncpu_glyphs370 = {sy["glyphs"]:#x};\n')
    run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-c',ROOT/'tools/machines/track_fx/cpu-text370.c','-o',out/'text.o')
    run('ld','--orphan-handling=error','-T',out/'text.ld','-e','cpu_text370','-o',out/'text.elf',out/'text.o')
    run('objcopy','-O','binary',out/'text.elf',out/'text.bin');blob=(out/'text.bin').read_bytes()
    replacement=bytes.fromhex('4ef9')+struct.pack('>I',code)+bytes.fromhex('4e71')*((len(old)-6)//2)
    assert len(replacement)==len(old)
    runtime[at-BASE:limit-BASE]=replacement
    runtime[code-BASE:code-BASE+len(blob)]=blob
    return dict(code=code,code_bytes=len(blob),reclaimed_bytes=len(old),sha256=hashlib.sha256(blob).hexdigest(),patches=[dict(at=at,region='runtime',old=old.hex(),new=replacement.hex()),dict(at=code,region='runtime',old=bytes(len(blob)).hex(),new=blob.hex())],new_state_bytes=0,audio_hooks_changed=False,hardware_tested=False)
