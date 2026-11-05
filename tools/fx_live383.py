"""Corrige l'ordre des banques FX au raccord live du sequenceur."""
from pathlib import Path
import os,struct,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
BASE,CODE,END=0x46700000,0x467a0e00,0x467a0f00
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
def apply(meta,runtime,out):
    assert meta.get('hide_master_fx382') and not meta.get('fx_live383')
    ui=meta['hide_master_fx382'];assert ui['code']+ui['code_bytes']<=CODE
    assert not any(runtime[CODE-BASE:END-BASE])
    entry=meta['acid_articulation']['symbols']['sg_live_switch']
    old=bytes(runtime[entry-BASE:entry-BASE+6]);assert old==bytes.fromhex('23d140a7887c'),old.hex()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'old.S').write_text('.text\n.globl fl_old_live\nfl_old_live:\n.byte '+','.join(map(str,old))+f'\njmp {entry+6:#x}\n')
    aliases=dict(fl_change=meta['fx_project']['symbols']['fxs_change'],fl_sync=meta['per_track_fx']['symbols']['mf_sync_audio'])
    (out/'live.ld').write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) }} }}\n'+''.join(f'{k} = {v:#x};\n' for k,v in aliases.items()))
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ['PATH']
    def run(t,*args):return subprocess.check_output([CROSS+t+'.exe',*map(str,args)],text=True)
    objects=[]
    for src in (ROOT/'tools/machines/track_fx/fx-live383.S',out/'old.S'):
        obj=out/(src.name+'.o');objects.append(obj);run('gcc','-mcpu=54418','-c',src,'-o',obj)
    elf=out/'live.elf';binary=out/'live.bin';run('ld','-T',out/'live.ld','-o',elf,*objects);run('objcopy','-O','binary',elf,binary)
    raw=binary.read_bytes();assert CODE+len(raw)<=END
    sy={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
    jump=b'\x4e\xf9'+struct.pack('>I',sy['fl_live'])
    runtime[CODE-BASE:CODE-BASE+len(raw)]=raw;runtime[entry-BASE:entry-BASE+6]=jump
    return dict(code=CODE,code_bytes=len(raw),entry=entry,symbols=sy,code_sha256=hashlib.sha256(raw).hexdigest(),file_io=False,hardware_tested=False,patches=[dict(at=CODE,old=bytes(len(raw)).hex(),new=raw.hex()),dict(at=entry,old=old.hex(),new=jump.hex())])
