"""Supprime la ligne FX du rendu Global sans renumeroter les controles natifs."""
from pathlib import Path
import os,struct,subprocess
ROOT=Path(__file__).resolve().parents[1]
BASE,CODE,END=0x46700000,0x467a0800,0x467a0f00
CROSS='H:/CREATURE-source/retrosyn-integration/build/m68k-toolchain/pkg/bin/m68k-elf-'

def apply(meta,native,runtime,out):
    assert meta.get('gov_inv_master380') and not meta.get('hide_master_fx382')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    assert not any(runtime[CODE-BASE:END-BASE])
    for profile in meta.values():
        if not isinstance(profile,dict):continue
        for kind in ('code','bss'):
            at,size=profile.get(kind),profile.get(kind+'_bytes',0)
            if isinstance(at,int) and isinstance(size,int) and size:assert END<=at or at+size<=CODE
    gp=meta['gov_policy372'];sy=gp['symbols'];aliases=gp['aliases']
    from test_seq_gen_menu import Rig
    from unicorn import UC_HOOK_CODE,m68k_const as C
    r=Rig(bytes(native),{'writes':[]},{'writes':[],'symbols':{}});r.u.mem_map(BASE,0x300000);r.u.mem_write(BASE,bytes(runtime));objects=[]
    at=0x400423e4;r.stubs[at]=lambda args:objects.append(args[0]) or 0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    at=sy['gp_old_edit'];r.stubs[at]=lambda args:0;r.u.hook_add(UC_HOOK_CODE,r.stub,begin=at,end=at)
    r.call(sy['gp_global_draw'],0,0x93010000);obj=objects[-1];vt=r.r32(obj);count=r.call(r.r32(vt+12),obj);assert count in (13,14)
    rows=[];labels=[]
    for i in range(count):
        r.u.reg_write(C.UC_M68K_REG_A0,0x931f0000);r.call(r.r32(vt+16),obj,i);item=r.r32(0x931f0000)
        label=r.string(r.r32(item+12));labels.append(label)
        if label!='FX':rows.append(bytes(r.u.mem_read(item,84)))
    assert labels[10]=='FX' and len(rows)==count-1
    template=(ROOT/'tools/machines/direct_jump/global.S').read_text().split('.Llabel0:')[0]
    import re
    template=re.sub(r'    clrb %a0@\(\d+\)\n','',template)
    template=template.replace('mf_global_draw','mr_draw').replace('gc_tree_row','mr_row').replace('ae_global_edit','mr_edit').replace('moveq #11,%d0',f'moveq #{len(rows)},%d0')
    template=template.replace('    jsr mr_row',''.join(f'    clrb %a0@({80+84*i})\n' for i in range(len(rows)))+'    jsr mr_row',1)
    (out/'global.S').write_text(template+'.Lallocator: .byte 0\n.balign 4\n.Lts_rows:\n'+''.join('.byte '+','.join(map(str,row))+'\n' for row in rows))
    (out/'row.c').write_text('typedef unsigned int u32;extern volatile u32 gc_tree_cursor;extern u32 gp_edit(void);\nu32 mr_row(void){u32 r=gc_tree_cursor;return r>=10?r-1:r;}\nu32 mr_edit(void){return gp_edit();}\n')
    os.environ['PATH']=str(Path(CROSS).parent)+os.pathsep+os.environ['PATH']
    def run(tool,*args):return subprocess.check_output([CROSS+tool+'.exe',*map(str,args)],text=True)
    ld=out/'menu.ld';ld.write_text(f'SECTIONS {{ .text {CODE:#x} : {{ *(.text*) *(.rodata*) }} }}\ngc_tree_cursor = {aliases["gc_tree_cursor"]:#x};\ngp_edit = {sy["gp_edit"]:#x};\n')
    objects=[]
    for name in ('global.S','row.c'):
        obj=out/(name+'.o');objects.append(obj);run('gcc','-mcpu=54418','-Os','-ffreestanding','-fno-builtin','-fno-pic','-fno-stack-protector','-c',out/name,'-o',obj)
    elf=out/'menu.elf';binary=out/'menu.bin';run('ld','-T',ld,'-o',elf,*objects);run('objcopy','-O','binary',elf,binary)
    raw=binary.read_bytes();assert CODE+len(raw)<=END,(len(raw),END-CODE)
    symbols={v[2]:int(v[0],16) for line in run('nm',elf).splitlines() if len(v:=line.split())==3}
    at=sy['gp_global_draw'];old=bytes(runtime[at-BASE:at-BASE+6]);jump=b'\x4e\xf9'+struct.pack('>I',symbols['mr_draw'])
    runtime[CODE-BASE:CODE-BASE+len(raw)]=raw;runtime[at-BASE:at-BASE+6]=jump
    gp['global_rows']=count-1
    return dict(code=CODE,code_bytes=len(raw),end=END,symbols=symbols,labels=[x for x in labels if x!='FX'],hardware_tested=False,patches=[dict(at=CODE,old=bytes(len(raw)).hex(),new=raw.hex()),dict(at=at,old=old.hex(),new=jump.hex())])
