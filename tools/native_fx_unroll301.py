"""Deroule quatre iterations du diffuseur natif, sans modifier ses operations.

Le corps est extrait du fichier officiel fourni ; aucune instruction ROM n'est
distribuee ici. La banque de transit retiree du chargeur lean sert de code.
"""
from pathlib import Path
import hashlib, os, subprocess, struct

BASE=0x40000400
CODE=0x46700000
COUNTER=0x40057b62
LOOP=0x40057b68
END=0x40057b82
RESUME=0x40057b86
SPECS=[
    ('allpass',COUNTER,LOOP,END,RESUME,'7020','7008'),
    ('delay_input',0x4005751e,0x4005753e,0x40057594,0x4005759a,'48780020','48780008'),
    ('delay_filter',0x400575de,0x400575e0,0x40057620,0x40057624,'7020','7008'),
    ('delay_feedback_a',0x40057642,0x4005764a,0x40057664,0x40057668,'7420','7408'),
    ('delay_feedback_b',0x40057642,0x4005766a,0x40057684,0x40057688,'7420','7408'),
    ('delay_mix',0x400576ca,0x400576cc,0x400576f6,0x400576fa,'7820','7808'),
]

def prepare(meta,native,runtime,stock,out):
    assert meta.get('clean_layout',{}).get('historical_loaders_executed') is False
    retired=meta['clean_layout']['retirement']['edits']
    assert any(x['kind']=='remove' and x['address']==CODE and x['bytes']>=4096 for x in retired)
    assert len(runtime)>=4096 and not any(runtime[:4096])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    asm='.text\n';patches=[]
    for name,counter,loop,end,resume,old,new in SPECS:
        old=bytes.fromhex(old);new=bytes.fromhex(new)
        assert native[counter-BASE:counter-BASE+len(old)]==stock[counter-BASE:counter-BASE+len(old)]==old
        assert native[loop-BASE:resume-BASE]==stock[loop-BASE:resume-BASE]
        body=stock[loop-BASE:end-BASE]
        decrement=stock[end-BASE:end-BASE+2]
        asm+='\n.balign 4\n.globl fu_'+name+'\nfu_'+name+':\n.rept 4\n.byte '+','.join(map(str,body))+'\n.endr\n.byte '+','.join(map(str,decrement))+'\nbne.w fu_'+name+'\njmp '+hex(resume)+'\n'
        if not any(p['at']==counter for p in patches):patches.append(dict(at=counter,old=old,new=new))
    (out/'fx-unroll.S').write_text(asm)
    cross='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'
    os.environ['PATH']=str(Path(cross).parent)+os.pathsep+os.environ.get('PATH','')
    def run(tool,*args):subprocess.run([cross+tool+'.exe',*map(str,args)],check=True)
    run('gcc','-mcpu=54418','-c',out/'fx-unroll.S','-o',out/'fx-unroll.o')
    run('ld','-Ttext',hex(CODE),'-e','fu_allpass','-o',out/'fx-unroll.elf',out/'fx-unroll.o')
    run('objcopy','-O','binary',out/'fx-unroll.elf',out/'fx-unroll.bin')
    code=(out/'fx-unroll.bin').read_bytes();assert len(code)<=1536
    symbols={row[2]:int(row[0],16) for line in subprocess.check_output([cross+'nm.exe',out/'fx-unroll.elf'],text=True).splitlines() if len(row:=line.split())==3}
    for name,counter,loop,end,resume,old,new in SPECS:patches.append(dict(at=loop,old=bytes(native[loop-BASE:loop-BASE+6]),new=b'\x4e\xf9'+struct.pack('>I',symbols['fu_'+name])))
    return code,patches

def apply(meta,native,runtime,stock,out):
    code,patches=prepare(meta,native,runtime,stock,out)
    for p in patches:native[p['at']-BASE:p['at']-BASE+len(p['new'])]=p['new']
    runtime[:len(code)]=code
    return dict(code=CODE,code_bytes=len(code),sha256=hashlib.sha256(code).hexdigest(),factor=4,loops=[dict(name=x[0],at=x[2]) for x in SPECS],original_iterations=32,reverb_outer_stages=8,delay_lengths_unchanged=True,new_state_bytes=0,hardware_tested=False)
