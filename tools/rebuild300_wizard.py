"""Compiler le garde Wizard dans ses sections existantes, sans nouveau hook DSP."""
from pathlib import Path
import hashlib
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'


def apply(meta,runtime,output):
    profile=meta['filter_pattern300'];sy=profile['symbols'];base=0x46700000
    before,after=sy['wp_before'],sy['wp_after']
    end=profile['code']+profile['code_bytes']
    assert before<after<end
    src=ROOT/'tools/machines/wizard_priority/control.c';obj=output/'wizard-scope.o';elf=output/'wizard-scope.elf'
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ.get('PATH','')
    def run(tool,*args):return subprocess.check_output([CROSS+tool+'.exe',*map(str,args)],text=True)
    run('gcc','-mcpu=54418','-Os','-ffunction-sections','-ffreestanding','-fno-builtin','-fno-common','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-c',src,'-o',obj)
    linker=output/'wizard-scope.ld'
    linker.write_text(f'SECTIONS {{ .before {before:#x} : {{ *(.text.wp_before) }} .after {after:#x} : {{ *(.text.wp_after) }} .unused : {{ *(.text*) *(.data*) }} .bss {profile["wizard_bss"]:#x} (NOLOAD) : {{ *(.bss*) *(COMMON) }} wp_scope_end = .; }}\nwp_mask_pointer = {sy["wp_mask_pointer"]:#x};\n')
    run('ld','-T',linker,'-o',elf,obj)
    symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
    assert symbols['wp_scope_end']<=profile['wizard_bss_end']
    edits=[]
    for section,lo,hi in (('before',before,after),('after',after,end)):
        target=output/('wizard-'+section+'.bin');run('objcopy','-O','binary','-j','.'+section,elf,target);code=target.read_bytes()
        assert len(code)<=hi-lo,(section,len(code),hi-lo)
        assert runtime[lo-base:lo-base+2]==b'\x4f\xef',hex(lo)
        # Apres la derniere fonction, le module contient encore ses chaines
        # rodata. wp_after est inchange : exiger ses octets exacts et garder
        # tout ce qui suit plutot que d'effacer jusqu'a la fin du module.
        if section=='after':
            assert code==runtime[lo-base:lo-base+len(code)],'unexpected wp_after dependency/layout change'
            capacity=len(code)
        else:capacity=hi-lo
        runtime[lo-base:lo-base+capacity]=code+bytes(capacity-len(code))
        edits.append(dict(address=lo,bytes=len(code),capacity=capacity))
    unused=output/'wizard-unused.bin';run('objcopy','-O','binary','-j','.unused',elf,unused);assert not unused.read_bytes()
    return dict(explicit_parameter_locks_only=True,source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),sections=edits,
                bss=profile['wizard_bss'],bss_end=symbols['wp_scope_end'],audio_hooks_added=False,hardware_tested=False)
