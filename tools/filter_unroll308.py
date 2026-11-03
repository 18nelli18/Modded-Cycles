"""Quatre paires LOW : ordre et bornes inchanges, seulement moins de branches."""
from pathlib import Path
import os,subprocess,struct,hashlib
ROOT=Path(__file__).resolve().parents[1];CODE=0x46703200;LIMIT=0x46703800
def apply(meta,runtime,out):
    base=0x46700000;out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not any(runtime[CODE-base:LIMIT-base])
    assert any(x['kind']=='remove' and x['address']<=CODE and LIMIT<=x['address']+x['bytes'] for x in meta['clean_layout']['retirement']['edits'])
    groups=[('low',meta['recovery_symbols']['pf_run'],meta['recovery_symbols']['pf_end']),('lohi_low',meta['filter_modes']['symbols']['fc_lohi_low'],meta['filter_modes']['symbols']['fc_lohi_low_end'])]
    asm='.text\n';sites=[]
    for name,lo,hi in groups:
        chunk=bytes(runtime[lo-base:hi-base]);start=bytes.fromhex('2c02dc86dc83');end=bytes.fromhex('b3ca6600');assert chunk.count(start)==chunk.count(end)==1
        a=lo+chunk.index(start);b=lo+chunk.index(end);body=bytes(runtime[a-base:b-base]);resume=b+6
        displacement=int.from_bytes(chunk[b-lo+4:b-lo+6],'big',signed=True);assert b+4+displacement==a
        assert len(body)==132 and b>a
        label='fl_'+name;asm+=f'\n.balign 4\n.globl {label}\n{label}:\n.rept 4\n.byte '+','.join(map(str,body))+f'\n.endr\ncmpa.l %a2,%a1\nbne.w {label}\njmp {resume:#x}\n';sites.append((a,label))
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-';os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(t,*v):return subprocess.check_output([cross+t+'.exe',*map(str,v)],text=True)
    (out/'filter-unroll.S').write_text(asm);run('gcc','-mcpu=54418','-c',out/'filter-unroll.S','-o',out/'filter-unroll.o');run('ld','-Ttext',hex(CODE),'-e','fl_low','-o',out/'filter-unroll.elf',out/'filter-unroll.o');run('objcopy','-O','binary',out/'filter-unroll.elf',out/'filter-unroll.bin')
    blob=(out/'filter-unroll.bin').read_bytes();assert CODE+len(blob)<=LIMIT
    sy={v[2]:int(v[0],16) for line in run('nm',out/'filter-unroll.elf').splitlines() if len(v:=line.split())==3 and v[2].startswith('fl_')};patches=[]
    for at,label in sites:
        old=bytes(runtime[at-base:at-base+6]);new=b'\x4e\xf9'+struct.pack('>I',sy[label]);patches.append(dict(at=at,old=old.hex(),new=new.hex()));runtime[at-base:at-base+6]=new
    runtime[CODE-base:CODE-base+len(blob)]=blob
    return dict(code=CODE,code_bytes=len(blob),symbols=sy,patches=patches,sha256=hashlib.sha256(blob).hexdigest(),new_state_bytes=0,pairs_per_iteration=4,quality_unchanged=True,hardware_tested=False)
