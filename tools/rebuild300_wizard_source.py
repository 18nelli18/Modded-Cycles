"""Compiler l'heritage des parametres des sample-locks dans un corps retire."""
from pathlib import Path
import hashlib
import os
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta,native,runtime,output):
    # Lite ne propose que les six machines stock : ne lui ajouter aucun
    # detour de note pour une machine absente.
    if not meta['activity_masks']['full']:
        return dict(excluded_by_edition=True,reason='Lite has no Sample Wizard machine',code_bytes=0,hooks=[],hardware_tested=False)
    pool=next(x for x in meta['retired_delegates']['removed'] if x['symbol']=='li_dispatch')
    code=pool['address']+6;capacity=pool['bytes'];offset=code-0x46700000
    assert runtime[offset:offset+capacity]==bytes(capacity)
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ.get('PATH','')
    def run(tool,*args):return subprocess.check_output([CROSS+tool+'.exe',*map(str,args)],text=True)
    inputs=[ROOT/'tools/machines/wizard_priority/sample-source.c',ROOT/'tools/machines/wizard_priority/sample-source.S'];objects=[]
    for i,src in enumerate(inputs):
        obj=output/('sample-source-'+str(i)+'.o')
        run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj);objects.append(obj)
    linker=output/'sample-source.ld';linker.write_text(f'SECTIONS {{ .text {code:#x} : {{ *(.text*) *(.rodata*) }} .data : {{ *(.data*) }} .bss (NOLOAD) : {{ *(.bss*) *(COMMON) }} }}\n')
    elf=output/'sample-source.elf';binary=output/'sample-source.bin';run('ld','-T',linker,'-o',elf,*objects);run('objcopy','-O','binary',elf,binary)
    symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
    blob=binary.read_bytes();assert len(blob)<=capacity
    runtime[offset:offset+len(blob)]=blob
    hooks=[]
    for at,old,name in ((0x40058a28,'2002068300000014','ws_copy'),(0x40058308,'4fefffdc202f0028','ws_restore')):
        pos=at-0x40000400;expected=bytes.fromhex(old);assert native[pos:pos+len(expected)]==expected
        new=b'\x4e\xf9'+struct.pack('>I',symbols[name])+b'\x4e\x71';native[pos:pos+len(new)]=new
        hooks.append(dict(address=at,old=old,new=new.hex(),target=symbols[name]))
    return dict(code=code,code_bytes=len(blob),capacity=capacity,symbols=symbols,hooks=hooks,
                source_sha256={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in inputs},
                pool_sound_unchanged=True,parameter_source_only=True,audio_sample_loop_hooks=False,hardware_tested=False)
